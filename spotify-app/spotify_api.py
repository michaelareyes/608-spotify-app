import os
import requests
import json
import requests
import base64
from collections import Counter
import itertools

class SpotifyAPI:
    def __init__(self):
        self.client_id = os.environ['CLIENT_ID']
        self.client_secret = os.environ['CLIENT_SECRET']
        self.base_url = "https://api.spotify.com/v1/"
    
    def get_token(self):
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        result = requests.post(url, headers=headers, data=data)
        json_result = json.loads(result.content)
        token = json_result["access_token"]
        return token
    
    def get_auth_header(self, token):
        return {"Authorization": "Bearer " + token}

    def search_for_artist(self, artist_name):
        url = self.base_url + "search"
        token = self.get_token()
        headers = self.get_auth_header(token)
        query = f"?q={artist_name}&type=artist&limit=1"
        query_url = url + query
        response = requests.get(query_url, headers=headers)
        json_result = response.json()["artists"]["items"]
        if not json_result:
            print("No artist with this name exists...")
            return None
        
        return json_result[0]

    def get_track_features_batch(self, track_ids):

        url = self.base_url + "audio-features"
        token = self.get_token()
        headers = self.get_auth_header(token)
        params = {'ids': ','.join(track_ids)}
        response = requests.get(url, headers=headers, params=params)
        json_result = response.json()["audio_features"]

        return json_result

    def get_album_tracks_with_audio_features(self, album_id):

        url = self.base_url + f"albums/{album_id}/tracks"
        token = self.get_token()
        headers = self.get_auth_header(token)
        response = requests.get(url, headers=headers)
        json_result = response.json()["items"]

        track_ids = [track["id"] for track in json_result]
        track_features = self.get_track_features_batch(track_ids)

        tracks_info = []
        for track, features in zip(json_result, track_features):
            tracks_dict = {
                "track_name": track["name"],
                "track_id": track["id"],
                "track_number": track["track_number"],
                "artists": track["artists"]
            }
            tracks_dict.update(features)
            tracks_info.append(tracks_dict)

        return tracks_info

    def get_discography_with_features(self, artist_id):

        url = self.base_url + f"artists/{artist_id}/albums"
        token = self.get_token()
        headers = self.get_auth_header(token)
        response = requests.get(url, headers=headers)
        json_result = response.json()["items"]

        discography_with_features = []
        for album in json_result:
            album_id = album["id"]
            album_name = album["name"]
            album_type = album['album_type']
            total_tracks = album['total_tracks']
            available_markets = album['available_markets']
            images = album["images"]
            artists = album["artists"]
            album_tracks_with_features = self.get_album_tracks_with_audio_features(album["id"])
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

        return discography_with_features
    
    def get_user_data(self, headers):

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
        
        else:
            error_message = {'message': 'Failed to get user\'s top artists ', 
                            'status_code': artist_response.status_code,
                            'response_error': artist_response.text}
            return error_message
        
        # GET TOP 10 TRACKS
        
        top_tracks_url = self.base_url + "me/top/tracks?limit=10"
        tracks_response = requests.get(top_tracks_url, headers=headers)

        if tracks_response.status_code == 200:
            top_tracks = tracks_response.json()
            track_names = [item['name'] for item in top_tracks['items']]
            track_image_urls = [item["album"]['images'][2]["url"]for item in top_tracks['items']] # get the one for 160px
            
            user_data["top_tracks"] = track_names
            user_data["track_url"] = track_image_urls
        
        else:
            error_message = {'message': 'Failed to get user\'s top tracks ', 
                            'status_code': tracks_response.status_code,
                            'response_error': tracks_response.text}
            return error_message
        
        return user_data
