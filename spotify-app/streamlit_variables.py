import streamlit as st
import plotly.express as px
import pandas as pd
import json
import requests
import asyncio
import time

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

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
        user_data = json.loads(query_params['user'])

        print(user_data)

        #user_data = json.loads(user_data)

        print(type(user_data))

        display_name = user_data['username']
        st.title(f"Welcome, {display_name}! :wave:")

        query_artist()
        
        st.title("Your Current Top:", anchor=False)

        col1, col2, col3 = st.columns(3)

        with col1:

            st.header('Artists', anchor=False)
            
            for i in range(len(user_data['top_artists'])):

                c1, c2= st.columns((1,5))

                with c1:
                    st.image(user_data['artist_url'][i], width = 75)

                with c2:
                    st.subheader(f'*{user_data["top_artists"][i]}*', anchor=False)

        with col2:
            st.header('Tracks', anchor=False)
            
            for i in range(len(user_data['top_tracks'])):

                c1, c2= st.columns((1,5))

                with c1:
                    st.image(user_data['track_url'][i], width = 75)

                with c2:
                    st.subheader(f'*{user_data["top_tracks"][i]}*', anchor=False)
        
        with col3:
            st.header('Genres', anchor=False)
            for genre in user_data['top_genres'][:10]:
                st.subheader(f'*{genre}*', anchor=False)

        user_end_time = time.time() - start_time
        print(f"Time taken to load User related information: {user_end_time} seconds")
    

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
    
    st.title(f"{st.session_state.name_artist}'s Discography")
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

            # Streamlit Charts

            # Display the radar chart
            st.write("Radar Chart")
            radar_start = time.time()
            radar_chart(radar_chart_df)
            radar_end_time = time.time() - radar_start
            print(f"Time taken for radar chart: {radar_end_time} seconds")

            ## Tracklist Trend

            st.write("Tracklist Trend")
            tracklist_start = time.time()
            tracklist_trend(df)
            tracklist_end_time = time.time() - tracklist_start
            print(f"Time taken for tracklist trend chart: {tracklist_end_time} seconds")
            
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


    
