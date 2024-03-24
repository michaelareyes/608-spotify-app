import sqlalchemy
import pandas as pd
from sqlalchemy import create_engine, inspect
from spotify_api import SpotifyAPI
import json
from create_artist_table import Tracks, Albums, Artists
from sqlalchemy.orm import sessionmaker

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


def check_artist_existence(artist_id):
    query = f"""

    SELECT EXISTS (
        SELECT 1 
        FROM artists 
        WHERE artist_id = %s
    );

    """

    query_boolean = pd.read_sql_query(query, engine, params=(artist_id,))

    return query_boolean.iloc[0, 0]

async def create_entries(artist_data, artist_id):
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

    artist_df.to_sql('artists', engine, index=False, if_exists='append')
    
    # Create Albums DB
    discography_with_features = await spotify_api.get_discography_with_features(artist_id)

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

            # Append to Albums db
            print("Creating Albums now...")
            album_df = pd.DataFrame(album_dict, index=[0])

            album_df.to_sql('albums', engine, index=False, if_exists='append')

            album_artist_association_data = {
                    'artist_id': artist_id,
                    'album_id': album_info['album_id']
                }
            album_artist_association_df = pd.DataFrame(album_artist_association_data, index=[0])
            album_artist_association_df.to_sql('artist_album_association', engine, index=False, if_exists='append')

            # Create Tracks
            print("Creating Tracks now...")
            for track_info in album_info['tracks']:
                track_dict = {
                    # 'aritst_id': artist_id,
                    # 'album_id': album_info['album_id'],
                    'track_id':track_info['track_id'],
                    'track_name':track_info['track_name'],
                    'track_number':track_info['track_number'],
                    'key' : track_info['features']['key'],
                    'duration_ms' : track_info['features']['duration_ms'],
                    'instrumentalness':track_info['features']['instrumentalness'],
                    'acousticness': track_info['features']['acousticness'],
                    'danceability' : track_info['features']['danceability'],
                    'energy' : track_info['features']['energy'],
                    'liveness':track_info['features']['liveness'],
                    'speechiness':track_info['features']['speechiness'],
                    'valence' : track_info['features']['valence'],
                    'loudness' : track_info['features']['loudness'],
                    'tempo':track_info['features']['tempo'],
                    'time_signature':track_info['features']['time_signature']
                }

                # Append to Tracks db
                track_df = pd.DataFrame(track_dict, index=[0])
                
                track_df.to_sql('tracks', engine, index=False, if_exists='append')

                artist_association_data = {
                    'track_id': track_info['track_id'],
                    'artist_id': artist_id
                }
                association_df = pd.DataFrame(artist_association_data, index=[0])
                association_df.to_sql('track_artists_association', engine, index=False, if_exists='append')

                album_association_data = {
                    'track_id': track_info['track_id'],
                    'album_id': album_info['album_id']
                }
                album_association_df = pd.DataFrame(album_association_data, index=[0])
                album_association_df.to_sql('track_albums_association', engine, index=False, if_exists='append')

def extract_relevant_info(artist_id):
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