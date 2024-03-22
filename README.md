# Spotify Data App

This is a Flask web application integrated with Spotify's API to fetch and analyze user data, including top artists, tracks, playlists, and more. The application utilizes OAuth authentication for user authorization and interacts with the Spotify API to retrieve user-specific information.

## Overview

The application consists of several files, each serving a specific purpose and interconnected to provide the desired functionality:

1. **main.py**: This file contains the Flask web application, which serves as the main entry point for the Spotify Data Analyzer. It handles user authentication via OAuth, interacts with the Spotify API to fetch user data, and renders the Streamlit UI for data visualization.

2. **spotify_api.py**: This module provides a class `SpotifyAPI` responsible for interacting with Spotify's API. It includes methods for obtaining OAuth tokens, searching for artists, fetching track features, and retrieving artist discography with features.

3. **spotify_db.py**: This script defines the database schema using SQLAlchemy ORM and interacts with the PostgreSQL database to store artist, album, and track data. It includes functions to check for artist existence, create database entries, and extract relevant information from the database.

4. **create_artist_table.py**: This file defines the schema for the database tables related to artists, albums, and tracks. It sets up the necessary associations between artists and albums, as well as tracks and artists. *Uncomment line 113 if the tables do **not** exist yet*.

5. **streamlit_variables.py**: This script utilizes the Streamlit library to create a web-based UI for visualizing user data. It communicates with the Flask application to fetch and display insights such as top artists, tracks, and track features.

## Connecting Files

1. **main.py** interacts with **spotify_api.py** to fetch user data from Spotify's API based on user authorization.
2. **spotify_api.py** communicates with **spotify_db.py** to store and retrieve artist, album, and track data in the PostgreSQL database.
3. **main.py** renders the Streamlit UI using **streamlit_variables.py**, which displays insights based on the fetched user data.

## Setup

To set up the Spotify Data application, follow the instructions provided in the section below.

## To Run the Application

1. If the tables do not exist yet, uncomment line 113 in create_artist_table.py and create DB tables using `python create_artist_table.py` or `python3 create_artist_table.py`
2. My Flask app is running on port 5001, I had to modify my instance's security group and add an inbound rule for this port (similar to adding port 8501 for streamlit as we have done in class)
3. Run the Flask application using `python main.py` or `python3 main.py`.
4. In another terminal, run the Streamlit application using `streamlit run streamlit_variables.py`. If you get an error regarding `OSError: [Errno 28] inotify watch limit reached`, try running the app using `streamlit run streamlit_variables.py --server.fileWatcherType none` instead.


## Things to Note

1. If modifying database structure (ie. adding/removing declared features in a table), uncomment lines 113 and 110 in `create_artist_table.py`, save and run the file to wipe out everything and create new empty tables. (There's possibly better ways to do this and definitely not best practice in real world scenarios but since we're just starting to build our DB and do not have much data yet, I think this is the simplest way to do it right now)
2. Might need to change the `PUBLIC_IP` variable to your own instance's public ip address in `main.py` line 28.

## Usage

After setting up the application, users can access the web interface through their browser, log in with their Spotify account, and explore various functionalities for analyzing their Spotify usage data.