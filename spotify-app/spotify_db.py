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

    table_name = 'spotify_table'

    # Define the query parameters
    query_params = {
        'TableName': table_name,
        'KeyConditionExpression': '#entity_type = :entity_type AND #entity_id = :entity_id',
        'ExpressionAttributeNames': {
            '#entity_type': 'entity_type',
            '#entity_id': 'entity_id'
        },
        'ExpressionAttributeValues': {
            ':entity_type': {'S': 'artist'},
            ':entity_id': {'S': artist_id}
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
        'entity_type': 'artist',
        'entity_id': artist_id,
        'name': artist_data['name'],
        'followers': artist_data['followers']['total'],
        'popularity': artist_data['popularity'],
        'genres': json.dumps(artist_data['genres'])
    }
    print("Artist Create:", artist_dict)
    # Append to Spotify table
    artist_df = pd.DataFrame(artist_dict, index=[0])

    # Put artist entry in DynamoDB
    put_dynamodb_df(artist_df, 'spotify_table')

    start_time = time.time()

    discography_with_features = await spotify_api.get_discography_with_features(artist_id)

    spotify_track_features_time = time.time() - start_time
    print(f"spotify_db: Time taken to get track features from Spotify: {spotify_track_features_time} seconds")

    album_data_list = []
    track_data_list = []

    async def process_album(album_info):
        album_dict = {
            'entity_type': 'album',
            'entity_id': album_info['album_id'],
            'artist_id': artist_id,  # Associate the album with the artist
            'album_type': album_info['album_type'],
            'album_name': album_info['album_name'],
            'total_tracks': album_info['total_tracks'],
            'available_markets': json.dumps(album_info['available_markets']),
            'images': json.dumps(album_info["images"])
        }
        album_data_list.append(album_dict)

    async def process_track(album_info, track_info):
        track_dict = {
            'entity_type': 'track',
            'entity_id': track_info['track_id'],
            'artist_id': artist_id,  # Associate the track with the artist
            'album_name': album_info['album_name'],  # Associate the track with the album
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

    async with aiohttp.ClientSession() as session:
        tasks = []

        for album_info in discography_with_features:
            tasks.append(process_album(album_info))
            for track_info in album_info['tracks']:
                tasks.append(process_track(album_info, track_info))

        task_time = time.time()
        await asyncio.gather(*tasks)
        task_end = time.time() - task_time
        print(f"spotify_db: Time taken to run tasks concurrently: {task_end} seconds")

    
    insert_start = time.time()

    put_dynamodb_df(pd.DataFrame(album_data_list), 'spotify_table')
    put_dynamodb_df(pd.DataFrame(track_data_list), 'spotify_table')

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
    start_time = time.time()
    dynamodb = boto3.client('dynamodb')
    table_name = 'spotify_table'

    # Query track IDs associated with the artist from the table
    artist_time = time.time()
    response = dynamodb.query(
        TableName=table_name,
        IndexName='artist_id-index',  # Assuming an index is created for artist_id
        KeyConditionExpression='#artist_id = :artist_id',
        ExpressionAttributeNames={'#artist_id': 'artist_id'},
        ExpressionAttributeValues={':artist_id': {'S': artist_id}}
    )
    artist_end_time = time.time() - artist_time
    print(f"spotify_db: Time taken for querying artist: {artist_end_time} seconds")
    print(response['Items'])

    # Extract track IDs from the response
    track_ids = [item['entity_id']['S'] for item in response['Items']]

    # Batch fetch track details
    batch_request_items = {
        table_name: {
            'Keys': [{'entity_type': {'S': 'track'}, 'entity_id': {'S': track_id}} for track_id in track_ids]
        }
    }

    response = dynamodb.batch_get_item(RequestItems=batch_request_items)

    df = []

    album_id_time = 0
    album_item_time = 0
    for item in response['Responses'][table_name]:
        track_id = item['entity_id']['S']

        # # Get album ID for the track
        # album_id_start = time.time()
        # album_id = get_album_id_for_track(track_id, dynamodb, table_name)
        # album_id_end = time.time() - album_id_start
        # album_id_time += album_id_end
        # # Get album details
        # album_start_time = time.time()
        # album_item = get_album_details(album_id, dynamodb, table_name)
        # album_end_time = time.time() - album_start_time
        # album_item_time += album_end_time

        track_number = int(item['track_number']['S'])
        energy = float(item['energy']['S'])
        loudness = float(item['loudness']['S'])
        key = int(item['key']['S'])
        tempo = float(item['tempo']['S'])
        speechiness = float(item['speechiness']['S'])
        duration_ms = int(item['duration_ms']['S'])
        valence = float(item['valence']['S'])
        danceability = float(item['danceability']['S'])
        instrumentalness = float(item['instrumentalness']['S'])
        acousticness = float(item['acousticness']['S'])
        time_signature = int(item['time_signature']['S'])
        liveness = float(item['liveness']['S'])

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
            'time_signature': time_signature
        })

    # print(f"spotify_db: Time taken for querying album_id: {album_id_time} seconds")
    # print(f"spotify_db: Time taken for querying album_item: {album_item_time} seconds")

    df = pd.DataFrame(df)
    extract_relevant_info_time = time.time() - start_time
    print(f"spotify_db: Time taken for extracting relevant information: {extract_relevant_info_time} seconds")
    return df

def get_album_id_for_track(track_id, dynamodb, table_name):
    response = dynamodb.query(
        TableName=table_name,
        KeyConditionExpression='#entity_type = :entity_type AND entity_id = :track_id',
        ExpressionAttributeNames={'#entity_type': 'entity_type'},
        ExpressionAttributeValues={':entity_type': {'S': 'track'}, ':track_id': {'S': track_id}}
    )
    if 'Items' in response and len(response['Items']) > 0:
        return response['Items'][0].get('album_id', {}).get('S', None)
    else:
        return None

def get_album_details(album_id, dynamodb, table_name):
    response = dynamodb.query(
        TableName=table_name,
        KeyConditionExpression='#entity_type = :entity_type AND entity_id = :album_id',
        ExpressionAttributeNames={'#entity_type': 'entity_type'},
        ExpressionAttributeValues={':entity_type': {'S': 'album'}, ':album_id': {'S': album_id}}
    )
    if 'Items' in response and len(response['Items']) > 0:
        return response['Items'][0]
    else:
        return None

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

         