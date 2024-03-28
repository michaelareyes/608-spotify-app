import pandas as pd
from spotify_api import SpotifyAPI
import json
import boto3
import awswrangler as wr
from decimal import Decimal
import asyncio
import aiohttp
import time


def check_artist_existence(artist_id):

    dynamodb = boto3.client('dynamodb')

    table_name = 'artists'

    # Define the query parameters
    query_params = {
        'TableName': table_name,
        'KeyConditionExpression': 'artist_id = :artist_id',
        'ExpressionAttributeValues': {
            ':artist_id': {'S': artist_id} 
        }
    }
    start_time = time.time()  # Record start time
    # Perform the query operation
    response = dynamodb.query(**query_params)

    artist_time = time.time() - start_time  # Calculate elapsed time
    print(f"spotify_db.py: Time taken for checking artist's existence: {artist_time} seconds")

    # Check if any items were returned
    if 'Items' in response and len(response['Items']) > 0:
        return True
    else:
        return False


async def create_entries(artist_data, artist_id):
    spotify_api = SpotifyAPI()
    
    artist_dict = {
        'artist_id': artist_id,
        'name': artist_data['name'],
        'followers': artist_data['followers']['total'],
        'popularity': artist_data['popularity'],
        'genres': json.dumps(artist_data['genres'])
    }

    # Append to Artists table
    artist_df = pd.DataFrame(artist_dict, index=[0])

    wr.dynamodb.put_df(df=artist_df, table_name='artists')

    start_time = time.time()

    discography_with_features = await spotify_api.get_discography_with_features(artist_id)

    spotify_track_features_time = time.time() - start_time
    print(f"spotify_db: Time taken to get track features from Spotify: {spotify_track_features_time} seconds")

    album_data_list = []
    track_data_list = []
    album_artist_association_data = {
        'artist_id': [],
        'album_id': []
    }
    track_artist_association_data = {
        'track_id': [],
        'artist_id': []
    }
    track_album_association_data = {
        'track_id': [],
        'album_id': []
    }

    # Process albums and tracks asynchronously
    async def process_album(album_info):
        album_dict = {
            'album_id': album_info['album_id'],
            'album_type': album_info['album_type'],
            'album_name': album_info['album_name'],
            'total_tracks': album_info['total_tracks'],
            'available_markets': json.dumps(album_info['available_markets']),
            'images': json.dumps(album_info["images"])
        }
        album_data_list.append(album_dict)

        # Album-Artist association
        album_artist_association_data['artist_id'].append(artist_id)
        album_artist_association_data['album_id'].append(album_info['album_id'])

    async def process_track(album_info, track_info):
        track_dict = {
            'track_id': track_info['track_id'],
            'track_name': track_info['track_name'],
            'track_number': track_info['track_number'],
            'key': track_info.get('key', None),
            'duration_ms': track_info.get('duration_ms', None),
            'instrumentalness': Decimal(str(track_info['instrumentalness'])) if track_info.get('instrumentalness') is not None else None,
            'acousticness': Decimal(str(track_info['acousticness'])) if track_info.get('acousticness') is not None else None,
            'danceability': Decimal(str(track_info['danceability'])) if track_info.get('danceability') is not None else None,
            'energy': Decimal(str(track_info['energy'])) if track_info.get('energy') is not None else None,
            'liveness': Decimal(str(track_info['liveness'])) if track_info.get('liveness') is not None else None,
            'speechiness': Decimal(str(track_info['speechiness'])) if track_info.get('speechiness') is not None else None,
            'valence': Decimal(str(track_info['valence'])) if track_info.get('valence') is not None else None,
            'loudness': Decimal(str(track_info['loudness'])) if track_info.get('loudness') is not None else None,
            'tempo': Decimal(str(track_info['tempo'])) if track_info.get('tempo') is not None else None,
            'time_signature': track_info.get('time_signature', None)
        }
        track_data_list.append(track_dict)

        # Track-Artist Association
        track_artist_association_data['artist_id'].append(artist_id)
        track_artist_association_data['track_id'].append(track_info['track_id'])

        # Track-Album Association
        track_album_association_data['album_id'].append(album_info['album_id'])
        track_album_association_data['track_id'].append(track_info['track_id'])

    # Run tasks concurrently
    async with aiohttp.ClientSession() as session:
        tasks = []
        tracks_time = 0

        album_start = time.time()
        for album_info in discography_with_features:
            tracks_start = time.time()
            tasks.append(process_album(album_info))
            for track_info in album_info['tracks']:
                tasks.append(process_track(album_info, track_info))
                tracks_end = time.time() - tracks_start
                tracks_time += tracks_end
        album_end = time.time() - album_start
        print(f"spotify_db: Time taken for looping through albums: {album_end} seconds")
        print(f"spotify_db: Time taken for looping through tracks: {tracks_time} seconds")

        task_time = time.time()
        await asyncio.gather(*tasks)
        task_end = time.time() - task_time
        print(f"spotify_db: Time taken to run tasks concurrently: {task_end} seconds")


    insert_start = time.time()

    wr.dynamodb.put_df(df=pd.DataFrame(album_data_list), table_name='albums')
    wr.dynamodb.put_df(df=pd.DataFrame(track_data_list), table_name='tracks')
    wr.dynamodb.put_df(df=pd.DataFrame(album_artist_association_data), table_name='artist_album_association')
    wr.dynamodb.put_df(df=pd.DataFrame(track_artist_association_data), table_name='track_artists_association')
    wr.dynamodb.put_df(df=pd.DataFrame(track_album_association_data), table_name='track_albums_association')

    insert_end = time.time() - insert_start
    print(f"spotify_db: Time taken to insert to DB: {insert_end} seconds")

    return


def extract_relevant_info(artist_id):
    start_time = time.time()
    dynamodb = boto3.client('dynamodb')

    tracks_table_name = 'tracks'
    track_artists_association_table_name = 'track_artists_association'
    track_albums_association_table_name = 'track_albums_association'
    albums_table_name = 'albums'

    # Query track IDs associated with the artist from track_artists_association table
    response = dynamodb.query(
        TableName=track_artists_association_table_name,
        KeyConditionExpression='artist_id = :artist_id',
        ExpressionAttributeValues={':artist_id': {'S': artist_id}}
    )

    # Extract track IDs from the response
    track_ids = [item['track_id']['S'] for item in response['Items']]

    # Batch fetch track details
    batch_request_items = {
        tracks_table_name: {
            'Keys': [{'track_id': {'S': track_id}} for track_id in track_ids]
        }
    }

    response = dynamodb.batch_get_item(RequestItems=batch_request_items)

    df = []

    for item in response['Responses'][tracks_table_name]:
        track_id = item['track_id']['S']
        album_id = get_album_id_for_track(track_id, dynamodb, track_albums_association_table_name)
        album_item = get_album_details(album_id, dynamodb, albums_table_name)

        df.append({
            'track_id': track_id,
            'track_name': item['track_name']['S'],
            'track_number': int(item['track_number']['N']),
            'album_name': album_item['album_name']['S'],
            # 'artist_names': artist_id,  # Assuming artist ID is used here
            'key': int(item['key']['N']),
            'duration_ms': int(item['duration_ms']['N']),
            'instrumentalness': float(item['instrumentalness']['N']),
            'acousticness': float(item['acousticness']['N']),
            'danceability': float(item['danceability']['N']),
            'energy': float(item['energy']['N']),
            'liveness': float(item['liveness']['N']),
            'speechiness': float(item['speechiness']['N']),
            'valence': float(item['valence']['N']),
            'loudness': float(item['loudness']['N']),
            'tempo': float(item['tempo']['N']),
            'time_signature': int(item['time_signature']['N'])
        })

    df = pd.DataFrame(df)
    extract_relevant_info_time = time.time() - start_time
    print(f"spotify_db: Time taken for extracting relevant information: {extract_relevant_info_time} seconds")
    return df

def get_album_id_for_track(track_id, dynamodb, track_albums_association_table_name):
    response = dynamodb.query(
        TableName=track_albums_association_table_name,
        KeyConditionExpression='track_id = :track_id',
        ExpressionAttributeValues={':track_id': {'S': track_id}}
    )
    return response['Items'][0]['album_id']['S']

def get_album_details(album_id, dynamodb, albums_table_name):
    response = dynamodb.get_item(
        TableName=albums_table_name,
        Key={'album_id': {'S': album_id}}
    )
    return response['Item']

async def search_view(artist_name):

    start_time = time.time()
    
    spotify_api = SpotifyAPI() 
    artist_data = await spotify_api.search_for_artist(artist_name)

    artist_time = time.time() - start_time

    print(f"spotify_db: Time taken to search Spotify API: {artist_time} seconds")

    if artist_data:
        artist_id = artist_data['id']

        # Check if Artist in our DB
        artist_present = check_artist_existence(artist_id)

        if not artist_present:

            # Artist not in DB, create df
            print("spotify_db: Artist not in DB")
            await create_entries(artist_data, artist_id)
        
        print("spotify_db: Extracting relevant information..")
        return extract_relevant_info(artist_id)
    
    else:
        return "No such artist exists!"

         