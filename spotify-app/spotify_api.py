import asyncio
import aiohttp
import os
import requests
import json
import base64
from collections import Counter
import itertools
import time

class SpotifyAPI:
    def __init__(self):
        self.client_id = os.environ['CLIENT_ID']
        self.client_secret = os.environ['CLIENT_SECRET']
        self.base_url = "https://api.spotify.com/v1/"
        self.token = None
    
    async def get_token(self):
        if self.token:
            return self.token
        
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                json_result = await response.json()
                self.token = json_result["access_token"]
                return self.token
    
    async def get_auth_header(self):
        token = await self.get_token()
        return {"Authorization": "Bearer " + token}

    async def search_for_artist(self, artist_name):
        start_time = time.time()
        url = self.base_url + "search"
        headers = await self.get_auth_header()
        query = f"?q={artist_name}&type=artist&limit=1"
        query_url = url + query
        
        async with aiohttp.ClientSession() as session:
            async with session.get(query_url, headers=headers) as response:
                json_result = await response.json()
                artists = json_result.get("artists", {}).get("items", [])
                if not artists:
                    print("No artist with this name exists...")
                    return None
                search_time = time.time() - start_time  # Calculate elapsed time
                print(f"spotify_api: Time taken to search for artist: {search_time} seconds")
                return artists[0]

    async def get_track_features_batch(self, track_ids):
        url = self.base_url + "audio-features"
        headers = await self.get_auth_header()
        params = {'ids': ','.join(track_ids)}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                json_result = await response.json()
                return json_result["audio_features"]

    async def get_album_tracks_with_audio_features(self, album_id):
        url = self.base_url + f"albums/{album_id}/tracks"
        headers = await self.get_auth_header()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                json_result = await response.json()
                track_ids = [track["id"] for track in json_result.get("items", [])]
                track_features = await self.get_track_features_batch(track_ids)
                tracks_info = []
                for track, features in zip(json_result.get("items", []), track_features):
                    tracks_dict = {
                        "track_name": track["name"],
                        "track_id": track["id"],
                        "track_number": track["track_number"],
                        "artists": track["artists"]
                    }
                    tracks_dict.update(features)
                    tracks_info.append(tracks_dict)
                return tracks_info

    async def get_discography_with_features(self, artist_id):
        start_time = time.time()
        url = self.base_url + f"artists/{artist_id}/albums"
        headers = await self.get_auth_header()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                json_result = await response.json()
                discography_with_features = []
                for album in json_result.get("items", []):
                    album_id = album["id"]
                    album_name = album["name"]
                    album_type = album['album_type']
                    total_tracks = album['total_tracks']
                    available_markets = album['available_markets']
                    images = album["images"]
                    artists = album["artists"]
                    album_tracks_with_features = await self.get_album_tracks_with_audio_features(album["id"])
                    discography_with_features.append({
                        "album_id": album_id,
                        "album_name": album_name,
                        "album_type": album_type,
                        "total_tracks": total_tracks,
                        "available_markets": available_markets,
                        "images": images,
                        "artists": artists,
                        "tracks": album_tracks_with_features
                    })
                get_discography_time = time.time() - start_time  # Calculate elapsed time
                print(f"spotify_api: Time taken to get discography's features: {get_discography_time} seconds")
                return discography_with_features
            
    def get_recommendations(self, headers):
        url = self.base_url + "recommendations"
        top_artist_url = self.base_url + "me/top/artists?time_range=short_term&limit=5"

        # Get the seeds for the top 5 artists
        artist_response = requests.get(top_artist_url, headers=headers)

        if artist_response.status_code == 200:
            top_artists = artist_response.json()
            id = [item['id'] for item in top_artists['items']]

            # Get recommendations based off of these top 5 artists that the user is CURRENTLY listening to
            payload = {'seed_artists': id, 'limit':8}
            recommendations_response = requests.get(url, headers=headers, params=payload)

            if recommendations_response.status_code == 200:
                recommendations_response = recommendations_response.json()
                resp = []
                for track in recommendations_response["tracks"]:
                    track_info = {
                        "track_name": track["name"],
                        "image_url": track["album"]["images"][1]["url"],
                        "artists": [artist["name"] for artist in track["artists"]],
                        "album": track["album"]["name"]
                    }

                    resp.append(track_info)
                print(resp)
                # return json.dumps(resp)

                return resp

            else:
                error_message = {'message': 'Failed to get recommendations', 
                                'status_code': recommendations_response.status_code,
                                'response_error': recommendations_response.text}
                return error_message

        else:
            error_message = {'message': 'Failed to get user\'s top artists ', 
                            'status_code': artist_response.status_code,
                            'response_error': artist_response.text}
            return error_message

    def get_user_data(self, headers):

        start_time = time.time()
    
        user_data = {}

        # GET USERNAME
        response = requests.get(self.base_url + "me", headers=headers)
        if response.status_code == 200:
            user = response.json()
            user_data["username"] = user['display_name']
        
        else:
            error_message = {'message': 'Failed to get user\'s data ', 
                            'status_code': response.status_code,
                            'response_error': response.text}
            return error_message

        # GET TOP 10 ARTISTS
        start_artist_time = time.time()
        top_artist_url = self.base_url + "me/top/artists?limit=10"
        artist_response = requests.get(top_artist_url, headers=headers)

        if artist_response.status_code == 200:
            top_artists = artist_response.json()
            names = [item['name'] for item in top_artists['items']]
            artist_image_urls = [item['images'][2]["url"] for item in top_artists['items']] # get the one for 160px
            genres = [item['genres'] for item in top_artists['items']]

            user_data["top_artists"] = names
            user_data["artist_url"] = artist_image_urls
            genres_count = Counter(list(itertools.chain(*genres)))
            user_data["top_genres"] = [genre for genre, _ in genres_count.most_common(10)]

            artist_time = time.time() - start_artist_time
            print(f"spotify_api: Time taken for obtaining top artists: {artist_time} seconds")
        
        else:
            error_message = {'message': 'Failed to get user\'s top artists ', 
                            'status_code': artist_response.status_code,
                            'response_error': artist_response.text}
            return error_message
        
        # GET TOP 10 TRACKS
        start_track_time = time.time()
        top_tracks_url = self.base_url + "me/top/tracks?limit=10"
        tracks_response = requests.get(top_tracks_url, headers=headers)

        if tracks_response.status_code == 200:
            top_tracks = tracks_response.json()
            track_names = [item['name'] for item in top_tracks['items']]
            track_image_urls = [item["album"]['images'][2]["url"]for item in top_tracks['items']] # get the one for 160px
            
            user_data["top_tracks"] = track_names
            user_data["track_url"] = track_image_urls

            tracks_time = time.time() - start_track_time
            print(f"spotify_api: Time taken for obtaining top tracks: {tracks_time} seconds")
        
        else:
            error_message = {'message': 'Failed to get user\'s top tracks ', 
                            'status_code': tracks_response.status_code,
                            'response_error': tracks_response.text}
            return error_message
        
        # GET RECOMMENDATIONS
        recommendations = self.get_recommendations(headers)

        user_data["recommendations"] = recommendations
        
        end_time = time.time() - start_time
        print(f"spotify_api: Time taken to get ALL OF user's data: {end_time} seconds")
        return user_data

async def main():
    spotify_api = SpotifyAPI()
	
if __name__ == "__main__":
    asyncio.run(main())
