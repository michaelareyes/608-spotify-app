import streamlit as st
import plotly.express as px
import pandas as pd
import json
import requests
import asyncio
import time
import urllib.parse
from spotify_api import SpotifyAPI
from dotenv import load_dotenv

load_dotenv()

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Testing Embedding
def spotify_embed(embed_code):
    st.components.v1.html(embed_code, height=400)

def query_artist():
    # Get the artist name from user input
    artist_name = st.text_input("Enter the artist's name:")
    
    # Call the function to get the top tracks
    if st.button("Get Top Tracks"):
        # Initialize SpotifyAPI Instance
        spotify_api = SpotifyAPI()
        # Obtain access token
        token = spotify_api.get_token()
        # Get top tracks
        top_tracks = spotify_api.get_artist_top_tracks(token, artist_name)
        # Display top tracks
        if top_tracks:
            st.write("Top Tracks:")
            for track in top_tracks:
                st.write(track["name"])
        else:
            st.write("Failed to get top tracks.")



# HTML and CSS to set background color for a section
section_style = """
    <style>
        .section {
            background-color: #f0f0f0; /* Change the color code to your desired background color */
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
            text-align: center;
        }
    </style>
"""

# Function to create a section with a custom background color
def custom_section(title, content):
    st.markdown(f"<div class='section'><h1>{title}</h1>{content}</div>", unsafe_allow_html=True)

#local_css("style.css")
        
# Use the full page instead of a narrow central column
st.set_page_config(
    page_title="Spotify App",
    page_icon=":notes:",
    layout="wide"
)

query_params = st.query_params.to_dict()

def display_image(url):
    return f'<img src="{url}" width="100">'

def format_artist_names(artist_list):
    return ', '.join(artist_list)

def display_recommendations(df):
    images = df["image_url"]
    df["artists"] = df["artists"].apply(format_artist_names)
    artist_names = df["artists"]
    track_names = df["track_name"]
    album_names = df["album"]

    image_css = """
        <style>
            .center-align {
                text-align: center;
            }
            .left-align {
                text-align: left;
            }
            .image-container {
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            .image-container img {
                width: 200px;
                height: auto;
            }
        </style>
    """

    st.markdown(image_css, unsafe_allow_html=True)

    for i in range(0, len(images), 4):
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        for j, col in enumerate([col1, col3, col5, col7]):
            index = i + j
            if index < len(images):
                with col:
                    st.markdown(image_css, unsafe_allow_html=True)
                    st.image(images[index], width=200)
                    st.markdown(f'<div style="text-align: center;"><b>{track_names[index]}</b></div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="text-align: center;"><i>Artist: {artist_names[index]}</i></div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="text-align: center;"><i>Album: {album_names[index]}</i></div>', unsafe_allow_html=True)

def query_artist():

    # my_expander = st.expander("**Search and Discover an Artist's Discography Features**", expanded=True)
    
    # with my_expander:
    
    if 'button_clicked' not in st.session_state:
        st.session_state.button_clicked = False

    # if not st.session_state.button_clicked:
    #     text_col.warning("Please enter an artist name.")
    st.header("Search and Discover an Artist's Discography Features", anchor=False)

    Name_of_Artist = st.text_input("**Search and Discover an Artist's Discography Features**", 
                                   placeholder="search artist name here...", 
                                   label_visibility = "collapsed"
                                    )

    button_clicked = st.button("OK", key="stButtonVoice")

    if button_clicked:
        st.session_state.currentPage = "page2"
        st.session_state.button_clicked = True
        st.session_state.name_artist = Name_of_Artist
        st.rerun()

def render_page_1():
    
    if 'user' in query_params:
        start_time = time.time()
    # Extract user-related data from query parameters
        user_data_decoded = urllib.parse.unquote(query_params['user'])

        print(type(query_params['user']))

        print(query_params['user'])

        user_data = json.loads(user_data_decoded)

        print(user_data)

        #user_data = json.loads(user_data)

        print(type(user_data))

        display_name = user_data['username']
        st.title(f"Welcome, :rainbow[{display_name}!] :wave:")

        query_artist()
        
        st.title("Your Current Top:", anchor=False)

        col1, col2, col3 = st.columns(3)

        with col1:

            st.header('Artists', anchor=False)
            
            for i in range(len(user_data['top_artists'])):

                c1, c2= st.columns((1,4))

                with c1:
                    st.image(user_data['artist_url'][i], width = 100)

                with c2:
                    st.subheader(f'*{user_data["top_artists"][i]}*', anchor=False)

        with col2:
            st.header('Tracks', anchor=False)
            
            for i in range(len(user_data['top_tracks'])):

                c1, c2= st.columns((1,4))

                with c1:
                    st.image(user_data['track_url'][i], width = 100)

                with c2:
                    st.subheader(f'*{user_data["top_tracks"][i]}*', anchor=False)
        
        with col3:
            st.header('Genres', anchor=False)
            for genre in user_data['top_genres'][:10]:
                st.subheader(f'*{genre}*', anchor=False)

        user_end_time = time.time() - start_time
        print(f"Time taken to load User related information: {user_end_time} seconds")

        st.title("Recommendations")

        recommendations = user_data['recommendations']
        print("recommendations:", recommendations)

        recommendations = pd.DataFrame(recommendations)

        display_recommendations(recommendations)

base_url = 'https://9e49g24h2h.execute-api.us-east-1.amazonaws.com/'

def radar_chart(avg_df):

    # Create a radar chart using Plotly Express
    fig = px.line_polar(
        avg_df, r="value", theta="feature", line_close=True,
        title="Average Features Radar Chart"
    )
    
    # Display the radar chart
    st.plotly_chart(fig)

def tracklist_trend(df):

    desired_columns = ['instrumentalness', 'acousticness', 'danceability',
                        'energy', 'liveness', 'speechiness', 'valence']

    # Default selection for feature and albums
    selected_feature = st.selectbox("Select Feature", desired_columns, index=desired_columns.index('energy'))
    selected_albums = df['album_name'].unique()[:5]

    # Create multiselect for selecting albums
    selected_albums = st.multiselect("Select Albums", df['album_name'].unique(), default=selected_albums)

    # Limit the number of selected albums to 5
    if len(selected_albums) > 5:
        st.warning("Please select only 5 albums.")
        selected_albums = selected_albums[:5]

    # Filter data based on user selections
    filtered_df = df[df['album_name'].isin(selected_albums)]
    filtered_df = filtered_df.groupby('album_name').apply(lambda x: x.sort_values('track_number')).reset_index(drop=True)
    filtered_df = filtered_df.rename(columns={'album_name': 'Album', 'track_number': 'Track Number', selected_feature:selected_feature.capitalize()})

    # Plot default line chart
    if not filtered_df.empty:
        fig = px.line(filtered_df, x='Track Number', y=selected_feature.capitalize(), color='Album', title=f"{selected_feature.capitalize()} Comparison for Selected Albums")

        # Customize legend labels to cut album names but show full name when hovered
        fig.for_each_trace(lambda trace: trace.update(name=trace.name[:20] + '...' if len(trace.name) > 20 else trace.name))
        fig.update_traces(mode="markers+lines")

        st.plotly_chart(fig)
    else:
        st.write("No data available for selected albums.")

# Function to render page 2 content
async def render_page_2():

    st.title("I see you have great taste, {display_name}... :eye::lips::eye:")

    # Create a popover for the search functionality
    with st.popover("Search for another artist...", use_container_width=True):

        # Display search text input
        Name_of_Artist = st.text_input("Search for Another Artist...")
        button_clicked = st.button("Search")
        if button_clicked:
            st.session_state.name_artist = Name_of_Artist
            st.rerun()

    if 'name_artist' in st.session_state and st.session_state.name_artist is not None:
        Name_of_Artist = st.session_state.name_artist
        params = {'artist': Name_of_Artist}
        artist_time = time.time()

        # Make an HTTP GET request to the API endpoint for SEARCH
        response = requests.get(base_url + "search", params=params)

        artist_end_time = time.time() - artist_time
        print(f"Time taken for search_view function: {artist_end_time} seconds")

        if response.status_code == 200:
            
            data = response.json()

            df = pd.read_json(data["df"])

            radar_chart_df = pd.read_json(data["radar_chart"])

            # Display Artist name
            st.markdown(f"<h1 style='text-align: center; font-size: 100px;'>{st.session_state.name_artist}'s Discography</h1>", unsafe_allow_html=True)
            # Display Artist Profile Photo
            col1, col2, col3 = st.columns(3)
            with col1:
                st.image(df['images'][1])
            with col2:
                st.image(df['images'][2])
            with col3:
                st.image(df['images'][3])

            # Streamlit Charts

            with st.container(border=True):
                col1, col2 = st.columns(2)

                # Display the radar chart
                with col1:
                    st.title("Radar Chart")
                    radar_start = time.time()
                    radar_chart(radar_chart_df)
                    radar_end_time = time.time() - radar_start
                    print(f"Time taken for radar chart: {radar_end_time} seconds")

                ## Tracklist Trend
                with col2:
                    st.title("Tracklist Trend")
                    st.subheader("Shows the trend of tracks by track features:")
                    tracklist_start = time.time()
                    tracklist_trend(df)
                    tracklist_end_time = time.time() - tracklist_start
                    print(f"Time taken for tracklist trend chart: {tracklist_end_time} seconds")

            ## Top Tracks by track_features
            
            # Initialize the toggle button state
            show_most = True
            

            # Render the custom section
            st.markdown(section_style, unsafe_allow_html=True)
            custom_section("Track Features Analysis","")

            show_most = st.checkbox("Show Most", value=True)

            with st.container(border=True):
                col1, col2 = st.columns(2)

                with col1:
                    
                    # Display top energetic tracks
                    if show_most:
                        st.title(":zap: Most Energetic Tracks")
                        st.subheader("Energetic tracks feel upbeat, fast, and loud.")
                        top_energy_tracks_df = df.sort_values('energy', ascending=False).head(3)
                    else:
                        st.title(":rain_cloud: Least Energetic Tracks")
                        st.subheader("Unenergetic tracks feel downbeat, slow, and quiet.")
                        top_energy_tracks_df = df.sort_values('energy', ascending=True).head(3)
                    
                    top_energy_track_names = top_energy_tracks_df['track_name'].tolist()
                    
                    for index, row in top_energy_tracks_df.iterrows():
                        track_id = row['track_id']
                        embed_code = f'<iframe src="https://open.spotify.com/embed/track/{track_id}" width="100%" height="80" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'
                        st.markdown(embed_code, unsafe_allow_html=True)

                with col2:
                    # Display top acoustic tracks
                    if show_most:
                        st.title(":guitar: Most Acoustic Tracks")
                        st.subheader("Acoustic tracks feel more instrumental, vocal, and raw.")
                        top_acoustic_tracks_df = df.sort_values('acousticness', ascending=False).head(3)
                    else:
                        st.title(":radio: Least Acoustic Tracks")
                        st.subheader("Unacoustic tracks feel less instrumental, vocal, and raw.")
                        top_acoustic_tracks_df = df.sort_values('acousticness', ascending=True).head(3)

                    top_acoustic_track_names = top_acoustic_tracks_df['track_name'].tolist()
                    
                    for index, row in top_acoustic_tracks_df.iterrows():
                        track_id = row['track_id']
                        embed_code = f'<iframe src="https://open.spotify.com/embed/track/{track_id}" width="100%" height="80" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'
                        st.markdown(embed_code, unsafe_allow_html=True)
            
            with st.container(border=True):
                col1, col2 = st.columns(2)

                with col1:
                    # Display top danceable songs
                    if show_most:
                        st.title(":dancer: Most Danceable Tracks:")
                        st.subheader("Danceable songs have strong beats, stable rhythms, and regular tempos!")
                        top_danceability_tracks_df = df.sort_values('danceability', ascending=False).head(3)
                    else:
                        st.title(":sleeping: Least Danceable Tracks:")
                        st.subheader("Undanceable songs have weak beats, unstable rhythms, and irregular tempos")
                        top_danceability_tracks_df = df.sort_values('danceability', ascending=True).head(3)

                    top_danceability_track_names = top_danceability_tracks_df['track_name'].tolist()
                    
                    for index, row in top_danceability_tracks_df.iterrows():
                        track_id = row['track_id']
                        embed_code = f'<iframe src="https://open.spotify.com/embed/track/{track_id}" width="100%" height="80" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'
                        st.markdown(embed_code, unsafe_allow_html=True)

                with col2:
                    # Display top happy songs
                    if show_most:
                        st.title(":smile_cat: Most Happy Tracks:")
                        st.subheader("Happy songs are measured by musical positivety that likely make you feel cheerful or euphoric.")
                        top_valence_tracks_df = df.sort_values('valence', ascending=False).head(3)
                    else:
                        st.title(":crying_cat_face: Least Happy Tracks:")
                        st.subheader("Unhappy songs are measured by musical positivety that likely make you feel upset or emotional.")
                        top_valence_tracks_df = df.sort_values('valence', ascending=True).head(3)

                    top_valence_track_names = top_valence_tracks_df['track_name'].tolist()

                    for index, row in top_valence_tracks_df.iterrows():
                        track_id = row['track_id']
                        embed_code = f'<iframe src="https://open.spotify.com/embed/track/{track_id}" width="100%" height="80" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>'
                        st.markdown(embed_code, unsafe_allow_html=True)

            
        else:
            return {
                'Error': 'Error in search_view()',
                'status_code': response.status_code,
                'message': response.text
            }
    else:
        st.warning("Please enter an artist name.")

    if st.button("Go back to User Dashboard"):
        st.session_state.currentPage = "page1"
        st.rerun()

def main():
    # Initialize session state
    if 'currentPage' not in st.session_state:
        st.session_state.currentPage = "page1"

    # Render content based on current page
    if st.session_state.currentPage == "page1":
        render_page_1()
    elif st.session_state.currentPage == "page2":
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(render_page_2())

if __name__ == "__main__":
    main()


    
