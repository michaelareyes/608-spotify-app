# Spotify Data App

The Spotify Data App is a comprehensive web application designed to provide users with insights into their music preferences and detailed information about their favorite artists. Built on Flask, the app seamlessly integrates with Spotify's API to fetch and analyze user data. Here's how our app works:

## User Dashboard
Our app features a user-friendly dashboard that offers a personalized overview of the user's music preferences. Through OAuth authentication, users grant our app access to their Spotify account, enabling us to retrieve data such as top artists, tracks and genres. This data is then displayed in the UI, allowing users to explore their music habits in depth. The dashboard provides valuable insights into the user's listening habits and possibly help them discover new music tailored to their tastes (*This is still a work in progress; assessing viability*). To enhance the user experience, we leverage Streamlit UI to seamlessly integrate our Flask app, providing a smooth and interactive dashboard experience.

## Artist Query
In addition to the user dashboard, our app allows users to query specific artists to access detailed information about them. Users can search for their favorite artists, and our app retrieves comprehensive data about the artist's tracks, including features such as duration, tempo, energy, and more. This feature enables users to dive deeper into their favorite artists' music and gain a better understanding of their style and sound.


# Overview

The application to run our codes consists of several files, each serving a specific purpose and interconnected to provide the desired functionality:

1. **main.py**: This file contains the Flask web application, which serves as the main entry point for the Spotify Data Analyzer. It handles user authentication via OAuth, interacts with Amazon API Gateway to call the Spotify API (located in AWS Lambda) to fetch user data, and renders the Streamlit UI for data visualization.

2. **spotify_api.py**: This module provides a class `SpotifyAPI` responsible for interacting with Spotify's API. It includes methods for obtaining OAuth tokens, searching for artists, fetching track features, and retrieving artist discography with features. 
   
   This is deployed on AWS Lambda and configured to trigger when a user first authorizes authentication to their Spotify account. This allows seamless integration with the Spotify API, enabling applications to access artist information and track features programmatically.


4. **spotify_db.py**: This script defines functions to interact with the DynamoDB database to store artist, album, and track data. It includes functions to check for artist existence, create database entries, and extract relevant information from the database.

    The script utilizes the `boto3` library to communicate with the DynamoDB service and the `awswrangler` library for easy DataFrame interaction with DynamoDB. Here's a breakdown of the functionalities:

   - **check_artist_existence(artist_id)**: This function checks if an artist exists in the DynamoDB table.
   - **create_entries(artist_data, artist_id)**: This function creates entries for an artist, their albums, and tracks in the DynamoDB tables. It also establishes associations between artists, albums, and tracks.
   - **extract_relevant_info(artist_id)**: This function extracts relevant information about tracks associated with an artist from the DynamoDB tables.
   - **search_view(artist_name)**: This function serves as an entry point to search for an artist. It queries the Spotify API for artist data, checks if the artist exists in the DynamoDB table, creates entries if necessary, and then extracts relevant information.
   
    This script is deployed as an AWS Lambda function. The function is configured to trigger in response to an API Gateway request when a user queries an artist, allowing seamless integration with other AWS services.

5. **streamlit_variables.py**: This script leverages the Streamlit library to craft an interactive web-based interface tailored for visualizing user data. It serves as the front-end component of the application, seamlessly communicating with both the Flask application and AWS Lambda function. Through the Flask application, it retrieves insights on the user's top artists, tracks, and genres, providing a comprehensive overview of their music preferences. Moreover, it seamlessly integrates with the AWS Lambda function to dynamically fetch and exhibit detailed insights when a user queries an artist, offering comprehensive analyses of their track features. 


## Connecting Files

1. **streamlit_variables.py** interacts with **lambda_function.py** to send a user's queried artist and fetch related information from the AWS Lambda function.

2. **lambda_function.py** serves as the AWS Lambda function that handles requests from **main.py** and **streamlit_variables.py**. The function provides endpoints for fetching insights on an artist's discography features and user data. It communicates with AWS DynamoDB to store and retrieve artist, album, and track data.

3. **spotify_db.py** is used internally by **lambda_function.py** to interact with DynamoDB for storing and retrieving data. It communicates with **spotify_api.py** to retrieve artist, album, and track data

4. **main.py** renders the Streamlit UI using **streamlit_variables.py**, which displays insights based on the fetched user data.


## Setup

To set up the Spotify Data application, follow the instructions provided in the section below.

## To Run the Application

1. **Set up Spotify for Developers App**
   
   To obtain the access token required for authorization with Spotify's API, you first need to set up a Spotify for Developers App. Detailed instructions on how to do this can be found [here](https://developer.spotify.com/documentation/web-api). Follow the steps provided in the documentation to create your app and obtain the necessary credentials for authentication and authorization. 

2. **Create DynamoDB Tables in AWS**
   
   Set up DynamoDB tables for `Artists`, `Albums`, `Tracks`, `artist_album_association`, `track_album_association`, and `track_artists_association`.

   - **Artists Table**: Stores information about artists.
   - **Albums Table**: Stores information about albums.
   - **Tracks Table**: Stores information about tracks.
   - **artist_album_association Table**: Represents a many-to-many relationship between artists and albums. It associates each artist with the albums they have contributed to.
   - **track_album_association Table**: Represents a many-to-many relationship between tracks and albums. It associates each track with the albums it belongs to.
   - **track_artists_association Table**: Represents a many-to-many relationship between tracks and artists. It associates each track with the artists who have contributed to it.

   These association tables allow for efficient querying and retrieval of data, enabling the application to handle complex relationships between artists, albums, and tracks effectively. For detailed information on the attributes in each table, please refer to the Entity-Relationship Diagram (ERD) provided in `flowchart.md`.

3. **Create Amazon API Gateway endpoints for:**

    - `/search`: Enables searching for artists.
    - `/user_data`: Facilitates retrieving user-related information.

4. **Modify Instance\'s Security Groups**
   
   Update the inbound rules to include ports:
    - 5001: This port hosts the Flask application.
    - 8501: Streamlit's port.

5. **Modify Amazon Lambda's Configurations**
   
   - Increase time out (1 minute) and memory (1000MB)

6. **Modify .env file**

    Update the .env file with your IP address, Spotify's Client ID, and Secret Key. These credentials are necessary for authenticating and accessing Spotify's API. Ensure that the file contains the correct values for these variables to enable seamless interaction with Spotify's services.

    Remember to configure the environment variables in AWS Lambda as well.
   
7. **In the EC2 Instance:**
   - Install all required packages using `pip install -r requirements.txt`.
   - Run the Flask application using `python main.py` or `python3 main.py`.
   - In another terminal, run the Streamlit application using `streamlit run streamlit_variables.py`. If you get an error regarding `OSError: [Errno 28] inotify watch limit reached`, try running the app using `streamlit run streamlit_variables.py --server.fileWatcherType none` instead.
  
    Please see below on how to run both files in the instance simultaneously.

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