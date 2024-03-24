import asyncio
import aiohttp
import os
import base64
import json

class SpotifyAPI:
    def __init__(self):
        self.client_id = 'e83d0b4c2eab4287adbd9830d18ac151'
        self.client_secret = 'e3e62bcb12ed41bebadf1951985076b8'
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
                    tracks_info.append({
                        "track_name": track["name"],
                        "track_id": track["id"],
                        "track_number": track["track_number"],
                        "artists": track["artists"],
                        "features": features
                    })
                return tracks_info

    async def get_discography_with_features(self, artist_id):
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
                    
                return discography_with_features

async def main():
    spotify_api = SpotifyAPI()

if __name__ == "__main__":
    asyncio.run(main())
