import sqlalchemy
from sqlalchemy import insert
import pandas as pd
from sqlalchemy import create_engine, inspect
from spotify_api import SpotifyAPI
import json
from create_artist_table import Tracks, Albums, Artists, artist_album_association, track_artists_association, track_albums_association
from sqlalchemy.orm import sessionmaker
import time
import aiohttp
import asyncio

# write out connection details
conf ={
    'host':"spotify-db.c7g00umc0fcv.us-east-1.rds.amazonaws.com",
    'port':'5432',
    'database':"spotify-db",
    'user':"postgres",
    'password':"ILoveSpotify"
}

# create an engine that we can use to interact with our database
engine = create_engine("postgresql://{user}:{password}@{host}/{user}".format(**conf))
print(engine)

# build an inspector
inspector = inspect(engine)

# use the inspector to find all the tables on the RDS
tables = inspector.get_table_names()

Session = sessionmaker(bind=engine)
session = Session()


def check_artist_existence(artist_id):
    start_time = time.time()  # Record start time
    query = f"""

    SELECT EXISTS (
        SELECT 1 
        FROM artists 
        WHERE artist_id = %s
    );

    """

    query_boolean = pd.read_sql_query(query, engine, params=(artist_id,))

    artist_time = time.time() - start_time  # Calculate elapsed time
    print(f"spotify_db.py: Time taken for checking artist's existence: {artist_time} seconds")

    return query_boolean.iloc[0, 0]

async def create_entries(artist_data, artist_id):
    spotify_api = SpotifyAPI()

    try:
        # Artist data
        artist_dict = {
            'artist_id': artist_id,
            'name': artist_data['name'],
            'followers': artist_data['followers']['total'],
            'popularity': artist_data['popularity'],
            'genres': json.dumps(artist_data['genres'])
        }

        # Append to Artists table
        session.bulk_insert_mappings(Artists, [artist_dict])

        # Create Albums DB
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

        async def process_album(album_info):
            album_data = {
                'album_id': album_info['album_id'],
                'album_type': album_info['album_type'],
                'album_name': album_info['album_name'],
                'total_tracks': album_info['total_tracks'],
                'available_markets': json.dumps(album_info['available_markets']),
                'images': json.dumps(album_info["images"])
            }
            album_data_list.append(album_data)

            ## Album-Artist association
            album_artist_association_data['artist_id'].append(artist_id)
            album_artist_association_data['album_id'].append(album_info['album_id'])
        
        async def process_track(album_info, track_info):
            track_data = {
                'track_id': track_info['track_id'],
                'track_name': track_info['track_name'],
                'track_number': track_info['track_number'],
                'key' : track_info['features'].get('key', None),
                'duration_ms' : track_info['features'].get('duration_ms', None),
                'instrumentalness':track_info['features'].get('instrumentalness', None),
                'acousticness': track_info['features'].get('acousticness', None),
                'danceability' : track_info['features'].get('danceability', None),
                'energy' : track_info['features'].get('energy', None),
                'liveness':track_info['features'].get('liveness', None),
                'speechiness':track_info['features'].get('speechiness', None),
                'valence' : track_info['features'].get('valence', None),
                'loudness' : track_info['features'].get('loudness', None),
                'tempo':track_info['features'].get('tempo', None),
                'time_signature':track_info['features'].get('time_signature', None)
            }
            track_data_list.append(track_data)

            ## Track-Artist Association
            track_artist_association_data['artist_id'].append(artist_id)
            track_artist_association_data['track_id'].append(track_info['track_id'])
            

            ## Track-Album Association
            track_album_association_data['album_id'].append(album_info['album_id'])
            track_album_association_data['track_id'].append(track_info['track_id'])

        # Run tasks concurrently
        async with aiohttp.ClientSession() as session_async:
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
            

        # Bulk insertion for Albums and Tracks
        insert_start = time.time()
        session.bulk_insert_mappings(Albums, album_data_list)
        session.bulk_insert_mappings(Tracks, track_data_list)

        session.commit()

        # Bulk insertion for the many-to-many relationships

        album_artist_association_df = pd.DataFrame(album_artist_association_data)
        album_artist_association_df.to_sql('artist_album_association', engine, index=False, if_exists='append')

        association_df = pd.DataFrame(track_artist_association_data)
        association_df.to_sql('track_artists_association', engine, index=False, if_exists='append')

        album_association_df = pd.DataFrame(track_album_association_data)
        album_association_df.to_sql('track_albums_association', engine, index=False, if_exists='append')

        insert_end = time.time() - insert_start
        print(f"spotify_db: Time taken to insert to DB: {insert_end} seconds")

    except Exception as e:
        # Rollback the transaction if an error occurs
        session.rollback()
        raise e

    finally:
        # Close the session
        session.close()


def extract_relevant_info(artist_id):
    start_time = time.time()
    Session = sessionmaker(bind=engine)

    # Create a session
    session = Session()

    ## Query tracks with related artists
    tracks = session.query(Tracks).filter(Tracks.artists.any(artist_id=artist_id)).all()

    # Create a DataFrame with track information and associated artists' names
    df = pd.DataFrame([
        {'track_id': track.track_id,
        'track_name': track.track_name,
        'track_number': track.track_number,
        'album_name': track.albums[0].album_name,
        'artist_names': ', '.join([artist.name for artist in track.artists]),
        'key' : track.key,
        'duration_ms' : track.duration_ms,
        'instrumentalness': track.instrumentalness,
        'acousticness': track.acousticness,
        'danceability' : track.danceability,
        'energy' : track.energy,
        'liveness': track.liveness,
        'speechiness': track.speechiness,
        'valence' : track.valence,
        'loudness' : track.loudness,
        'tempo': track.tempo,
        'time_signature': track.time_signature
        } 
        for track in tracks
    ])
    extract_relevant_info_time = time.time() - start_time
    print(f"spotify_db: Time taken for extracting relevant information: {extract_relevant_info_time} seconds")
    # Print the DataFrame
    return df


async def search_view(artist_name):
    
    spotify_api = SpotifyAPI() 
    artist_data = await spotify_api.search_for_artist(artist_name)

    if artist_data:
        artist_id = artist_data['id']

        # Check if Artist in our DB
        artist_present = check_artist_existence(artist_id)

        if not artist_present:

            # Artist not in DB, create df
            await create_entries(artist_data, artist_id)
        
        return extract_relevant_info(artist_id)
    
    else:
        return "No such artist exists!"