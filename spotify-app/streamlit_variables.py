import streamlit as st
import plotly.express as px
import pandas as pd
from spotify_db import search_view
import json

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")

query_params = st.query_params.to_dict()

if 'user' in query_params:
    # Extract user-related data from query parameters
    user_data = json.loads(query_params['user'])

    display_name = user_data['username']
    st.title(f"Welcome, {display_name}!")
    
    st.write("Top Tracks:")
    top_tracks = user_data['top_tracks']
    st.table(top_tracks)

    st.write("Top Artists:")
    top_artists = user_data['top_artists']
    st.table(top_artists)

    st.write("Top Genres:")
    top_genres = user_data['top_genres']
    st.table(top_genres)

st.title("Discography Features")
Name_of_Artist = st.text_input("Artist Name")

if 'button_clicked' not in st.session_state:
    st.session_state.button_clicked = False

button_clicked = st.button("OK")

if button_clicked:
    st.session_state.button_clicked = True

if not st.session_state.button_clicked:
    st.warning("Please enter an artist name.")
else:
    if Name_of_Artist:
        df = search_view(Name_of_Artist)

        # Select only the desired columns
        desired_columns = ['instrumentalness', 'acousticness', 'danceability',
                            'energy', 'liveness', 'speechiness', 'valence']
        df_selected = df[desired_columns]

        # Streamlit Charts

        def radar_chart(df):

            avg_values = df.mean()

            avg_df = pd.DataFrame({"feature": avg_values.index, "value": avg_values.values})

            # Create a radar chart using Plotly Express
            fig = px.line_polar(
                avg_df, r="value", theta="feature", line_close=True,
                title="Average Features Radar Chart"
            )
            
            # Display the radar chart
            st.plotly_chart(fig)

        # Display the radar chart
        st.write("Radar Chart")
        radar_chart(df_selected)

        ## Tracklist Trend

        def tracklist_trend(df):

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

        st.write("Tracklist Trend")
        tracklist_trend(df)
    else:
        st.warning("Please enter an artist name.")
