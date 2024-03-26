# Spotify Data App

The Spotify Data App is a comprehensive web application designed to provide users with insights into their music preferences and detailed information about their favorite artists. Built on Flask, the app seamlessly integrates with Spotify's API to fetch and analyze user data. Here's how our app works:

## User Dashboard
Our app features a user-friendly dashboard that offers a personalized overview of the user's music preferences. Through OAuth authentication, users grant our app access to their Spotify account, enabling us to retrieve data such as top artists, tracks and genres. This data is then displayed in the UI, allowing users to explore their music habits in depth. The dashboard provides valuable insights into the user's listening habits and possibly help them discover new music tailored to their tastes (*This is still a work in progress; assessing viability*). To enhance the user experience, we leverage Streamlit UI to seamlessly integrate our Flask app, providing a smooth and interactive dashboard experience.

## Artist Query
In addition to the user dashboard, our app allows users to query specific artists to access detailed information about them. Users can search for their favorite artists, and our app retrieves comprehensive data about the artist's tracks, including features such as duration, tempo, energy, and more. This feature enables users to dive deeper into their favorite artists' music and gain a better understanding of their style and sound.


# Overview

The application to run our codes consists of several files, each serving a specific purpose and interconnected to provide the desired functionality:

1. **main.py**: This file contains the Flask web application, which serves as the main entry point for the Spotify Data Analyzer. It handles user authentication via OAuth, interacts with the Spotify API to fetch user data, and renders the Streamlit UI for data visualization.

2. **spotify_api.py**: This module provides a class `SpotifyAPI` responsible for interacting with Spotify's API. It includes methods for obtaining OAuth tokens, searching for artists, fetching track features, and retrieving artist discography with features.

3. **spotify_db.py**: This script defines the database schema using SQLAlchemy ORM and interacts with the PostgreSQL database to store artist, album, and track data. It includes functions to check for artist existence, create database entries, and extract relevant information from the database.

4. **create_artist_table.py**: This file defines the schema for the database tables related to artists, albums, and tracks. It sets up the necessary associations between artists and albums, as well as tracks and artists. *Uncomment line 113 if the tables do **not** exist yet*.

5. **streamlit_variables.py**: This script utilizes the Streamlit library to create a web-based UI for visualizing user data. It communicates with the Flask application to fetch and display insights such as top artists, tracks, and track features.

## Connecting Files

1. **streamlit_variables.py** interacts with **spotify_db.py** to send in User's queried Artist and fetch its related information from either our DB or Spotify's API.
2. **spotify_db.py** communicates with **spotify_api.py** to store and retrieve artist, album, and track data in the PostgreSQL database.
3. **main.py** renders the Streamlit UI using **streamlit_variables.py**, which displays insights based on the fetched user data.

## Setup

To set up the Spotify Data application, follow the instructions provided in the section below.

## To Run the Application

1. If the tables do not exist yet, uncomment line 113 in create_artist_table.py and create DB tables using `python create_artist_table.py` or `python3 create_artist_table.py`
2. Our Flask app is running on port 5001, we had to modify my instance's security group and add an inbound rule for this port (similar to adding port 8501 for streamlit as we have done in class)
3. Run the Flask application using `python main.py` or `python3 main.py`.
4. In another terminal, run the Streamlit application using `streamlit run streamlit_variables.py`. If you get an error regarding `OSError: [Errno 28] inotify watch limit reached`, try running the app using `streamlit run streamlit_variables.py --server.fileWatcherType none` instead.

### Running Both Files Simultaneously
To run both files simultaneously, we recommend using a tool like tmux to manage multiple terminal sessions efficiently:

*(Read more about tmux [here](https://github.com/tmux/tmux/wiki) and its possible commands [here](https://tmuxcheatsheet.com/))*

1. Open a new tmux session by typing tmux in your terminal and pressing Enter.
2. Split the window vertically or horizontally using the appropriate tmux commands.
3. Navigate to the directory containing your Flask and Streamlit files in each tmux pane.
4. Run python main.py (or python3 main.py) in one pane and streamlit run streamlit_variables.py in the other.
5. You can switch between tmux panes using the designated tmux shortcuts.

By following these steps, you can run both the Flask and Streamlit applications simultaneously within the same tmux session, making it easier to manage and monitor the application's execution.


## Things to Note

1. If modifying database structure (ie. adding/removing declared features in a table), uncomment lines 113 and 110 in `create_artist_table.py`, save and run the file to wipe out everything and create new empty tables. (There's possibly better ways to do this and definitely not best practice in real world scenarios but since we're just starting to build our DB and do not have much data yet, I think this is the simplest way to do it right now)
2. Might need to change the `PUBLIC_IP` variable to your own instance's public ip address in `main.py` line 28.

## Usage

After setting up the application, users can access the web interface through their browser, log in with their Spotify account, and explore various functionalities for analyzing their Spotify usage data.