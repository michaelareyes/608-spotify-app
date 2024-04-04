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
    table_name = 'spotidy-1nf'

    query_params = {
        'TableName': table_name,
        'KeyConditionExpression': '#artist_id = :artist_id',
        'ExpressionAttributeNames': {
            '#artist_id': 'artist_id'
        },
        'ExpressionAttributeValues': {
            ':artist_id': {'S': artist_id}
        }
    }

    start_time = time.time()

    response = dynamodb.query(**query_params)

    artist_time = time.time() - start_time  # Calculate elapsed time
    print(f"spotify_db.py: Time taken for checking artist's existence: {artist_time} seconds")

    # Check if any items were returned
    return len(response['Items']) > 0


async def create_entries(artist_data, artist_id):
    dynamodb = boto3.resource('dynamodb')
    spotify_api = SpotifyAPI()
    table_name = 'spotidy-1nf'

    start_time = time.time()
    discography_with_features = await spotify_api.get_discography_with_features(artist_id)
    spotify_track_features_time = time.time() - start_time
    print(f"spotify_db: Time taken to get track features from Spotify: {spotify_track_features_time} seconds")

    batch_requests = []
    insert_start = time.time()
    for album_info in discography_with_features:
        for track_info in album_info['tracks']:
            entry = {
                'artist_id': artist_id,
                'name': artist_data['name'],
                'followers': artist_data['followers']['total'],
                'popularity': artist_data['popularity'],
                'genres': json.dumps(artist_data['genres']),

                'album_type': album_info['album_type'],
                'album_name': album_info['album_name'],
                'total_tracks': album_info['total_tracks'],
                'available_markets': json.dumps(album_info['available_markets']),
                'images': json.dumps(album_info["images"]),

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

            batch_requests.append(entry)
            # batch_requests.append({'PutRequest': {'Item': entry}})

            # # Perform batch write if the number of batch requests reaches 25
            # if len(batch_requests) == 25:
            #     dynamodb.batch_write_item(RequestItems={table_name: batch_requests})
            #     batch_requests = []

    if batch_requests:
        #dynamodb.batch_write_item(RequestItems={table_name: batch_requests})
        batch_size = 25
        num_batches = (len(batch_requests) + batch_size - 1) // batch_size  # Calculate total number of batches

        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(batch_requests))  # Calculate end index of the batch

            batch = batch_requests[start_idx:end_idx]  # Get the current batch
            if batch:
                batch_df = pd.DataFrame(batch)
                wr.dynamodb.put_df(df=batch_df, table_name=table_name)

    # put_dynamodb_df(pd.DataFrame(lst),table_name)
    insert_end = time.time() - insert_start
    print(f"spotify_db: Time taken to insert to DB: {insert_end} seconds")

    return

def put_dynamodb_df(df, table_name):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    with table.batch_writer() as batch:
        for idx, row in df.iterrows():
            item = {key: str(value) for key, value in row.items()}
            batch.put_item(Item=item)


def extract_relevant_info(artist_id):
    dynamodb = boto3.client('dynamodb')
    table_name = 'spotidy-1nf'

    start_time = time.time()

    response = dynamodb.query(
        TableName=table_name,
        KeyConditionExpression='#artist_id = :artist_id',
        ExpressionAttributeNames={'#artist_id': 'artist_id'},
        ExpressionAttributeValues={':artist_id': {'S': artist_id}}
    )

    print(response['Items'])

    df = []

    for item in response['Items']:
        track_id = item['track_id']['S']
        track_number = int(item['track_number']['N'])
        energy = float(item['energy']['N'])
        loudness = float(item['loudness']['N'])
        key = int(item['key']['N'])
        tempo = float(item['tempo']['N'])
        speechiness = float(item['speechiness']['N'])
        duration_ms = int(item['duration_ms']['N'])
        valence = float(item['valence']['N'])
        danceability = float(item['danceability']['N'])
        instrumentalness = float(item['instrumentalness']['N'])
        acousticness = float(item['acousticness']['N'])
        time_signature = int(item['time_signature']['N'])
        liveness = float(item['liveness']['N'])
        images = json.loads(item['images']['S'])[0]["url"]

        df.append({
            'track_id': track_id,
            'track_name': item['track_name']['S'],
            'track_number': track_number,
            'album_name': item['album_name']['S'],
            'key': key,
            'duration_ms': duration_ms,
            'instrumentalness': instrumentalness,
            'acousticness': acousticness,
            'danceability': danceability,
            'energy': energy,
            'liveness': liveness,
            'speechiness': speechiness,
            'valence': valence,
            'loudness': loudness,
            'tempo': tempo,
            'time_signature': time_signature,
            'images': images
        })
    
    df = pd.DataFrame(df)
    
    print(df, "recommendations")

    extract_relevant_info_time = time.time() - start_time
    print(f"spotify_db: Time taken for extracting relevant information: {extract_relevant_info_time} seconds")
    
    return df

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

         