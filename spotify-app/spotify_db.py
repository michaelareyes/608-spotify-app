import pandas as pd
from spotify_api import SpotifyAPI
import json
import boto3
import awswrangler as wr
from decimal import Decimal


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

    # Perform the query operation
    response = dynamodb.query(**query_params)

    # Check if any items were returned
    if 'Items' in response and len(response['Items']) > 0:
        return True
    else:
        return False

def create_entries(artist_data, artist_id):
    spotify_api = SpotifyAPI()

    artist_dict = {
        'artist_id': artist_id,
        'name': artist_data['name'],
        'followers': artist_data['followers']['total'],
        'popularity': artist_data['popularity'],
        'genres': json.dumps(artist_data['genres'])
    }

    # Append to Artists db
    artist_df = pd.DataFrame(artist_dict, index=[0])
    print("Creating Artists now...")

    wr.dynamodb.put_df(df=artist_df, table_name='artists')
    
    # Create Albums DB
    discography_with_features = spotify_api.get_discography_with_features(artist_id)

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

    for album_info in discography_with_features:
            
            album_dict = {
                    # 'aritst_id': artist_id,
                    'album_id': album_info['album_id'],
                    'album_type': album_info['album_type'],
                    'album_name': album_info['album_name'],
                    'total_tracks': album_info['total_tracks'],
                    'available_markets': json.dumps(album_info['available_markets']),
                    'images': json.dumps(album_info["images"])
            }

            # Append to Albums list
            print("Creating Albums now...")
            album_data_list.append(album_dict)

            ## Album-Artist association
            album_artist_association_data['artist_id'].append(artist_id)
            album_artist_association_data['album_id'].append(album_info['album_id'])

            # Create Tracks
            print("Creating Tracks now...")
            for track_info in album_info['tracks']:
                track_dict = {
                    'track_id':track_info['track_id'],
                    'track_name':track_info['track_name'],
                    'track_number':track_info['track_number'],
                    'key' : track_info.get('key', None),
                    'duration_ms' : track_info.get('duration_ms', None),
                    'instrumentalness':track_info.get('instrumentalness', None),
                    'acousticness': track_info.get('acousticness', None),
                    'danceability' : track_info.get('danceability', None),
                    'energy' : track_info.get('energy', None),
                    'liveness':track_info.get('liveness', None),
                    'speechiness':track_info.get('speechiness', None),
                    'valence' : track_info.get('valence', None),
                    'loudness' : track_info.get('loudness', None),
                    'tempo':track_info.get('tempo', None),
                    'time_signature':track_info.get('time_signature', None)
                }

                # Append to Tracks db
                track_data_list.append(track_dict)

                ## Track-Artist Association
                track_artist_association_data['artist_id'].append(artist_id)
                track_artist_association_data['track_id'].append(track_info['track_id'])
                

                ## Track-Album Association
                track_album_association_data['album_id'].append(album_info['album_id'])
                track_album_association_data['track_id'].append(track_info['track_id'])

    # Insert into DynamoDB
    album_df = pd.DataFrame(album_data_list)
    track_df = pd.DataFrame(track_data_list)

    float_cols = ['instrumentalness', 'acousticness', 'danceability', 'danceability',
                  'energy', 'liveness', 'speechiness', 'valence', 'loudness', 'tempo']

    for col in float_cols:
        track_df[col] = track_df[col].apply(lambda x: Decimal(str(x)) if pd.notnull(x) else x)

    album_artist_association_df = pd.DataFrame(album_artist_association_data)
    track_artist_association_df = pd.DataFrame(track_artist_association_data)
    track_album_association_df = pd.DataFrame(track_album_association_data)

    wr.dynamodb.put_df(df=album_df, table_name='albums')
    wr.dynamodb.put_df(df=track_df, table_name='tracks')
    wr.dynamodb.put_df(df=album_artist_association_df, table_name='artist_album_association')
    wr.dynamodb.put_df(df=track_artist_association_df, table_name='track_artists_association')
    wr.dynamodb.put_df(df=track_album_association_df, table_name='track_albums_association')

def extract_relevant_info(artist_id):

    dynamodb = boto3.client('dynamodb')

    tracks_table_name = 'tracks'
    track_artists_association_table_name = 'track_artists_association'
    track_albums_association_table_name = 'track_albums_association'
    artists_table_name = 'artists'
    albums_table_name = 'albums'

    # Query track IDs associated with the artist from track_artists_association table
    print("Querying track_artists_association")
    response = dynamodb.query(
        TableName=track_artists_association_table_name,
        KeyConditionExpression='artist_id = :artist_id',
        ExpressionAttributeValues={':artist_id': {'S': artist_id}}
    )
    
    # Extract track IDs from the response
    track_ids = [item['track_id']['S'] for item in response['Items']]

    df = []

    # Iterate over each track ID to fetch additional information
    print("Querying Tracks for loop")
    for track_id in track_ids:
        # Query track details from DynamoDB
        track_response = dynamodb.get_item(
            TableName=tracks_table_name,
            Key={'track_id': {'S': track_id}}
        )
        track_item = track_response['Item']

        # Query associated album details from track_albums_association table
        response_album = dynamodb.query(
            TableName=track_albums_association_table_name,
            KeyConditionExpression='track_id = :track_id',
            ExpressionAttributeValues={':track_id': {'S': track_id}}
        )

        # Extract the album_id from the response
        album_id = response_album['Items'][0]['album_id']['S']

        # Query associated album details from the albums table
        album_response = dynamodb.get_item(
            TableName=albums_table_name,
            Key={'album_id': {'S': album_id}}
        )
        album_item = album_response['Item']

        df.append({
            'track_id': track_item['track_id']['S'],
            'track_name': track_item['track_name']['S'],
            'track_number': int(track_item['track_number']['N']),
            'album_name': album_item['album_name']['S'],
            'artist_names': artist_id,  # Assuming artist ID is used here
            'key': int(track_item['key']['N']),
            'duration_ms': int(track_item['duration_ms']['N']),
            'instrumentalness': float(track_item['instrumentalness']['N']),
            'acousticness': float(track_item['acousticness']['N']),
            'danceability': float(track_item['danceability']['N']),
            'energy': float(track_item['energy']['N']),
            'liveness': float(track_item['liveness']['N']),
            'speechiness': float(track_item['speechiness']['N']),
            'valence': float(track_item['valence']['N']),
            'loudness': float(track_item['loudness']['N']),
            'tempo': float(track_item['tempo']['N']),
            'time_signature': int(track_item['time_signature']['N'])
        })

    df = pd.DataFrame(df)

    return df


def search_view(artist_name):
    
    spotify_api = SpotifyAPI() 
    artist_data = spotify_api.search_for_artist(artist_name)

    if artist_data:
        artist_id = artist_data['id']

        # Check if Artist in our DB
        artist_present = check_artist_existence(artist_id)

        if not artist_present:

            # Artist not in DB, create df
            print("spotify_db: Artist not in DB")
            create_entries(artist_data, artist_id)
        
        print("spotify_db: Extracting relevant information..")
        return extract_relevant_info(artist_id)
    
    else:
        return "No such artist exists!"

         