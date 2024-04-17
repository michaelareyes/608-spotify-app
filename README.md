# Spotify Data App

The Spotify Data App is a comprehensive web application designed to provide users with insights into their music preferences and detailed information about their favorite artists. Built on Flask, the app seamlessly integrates with Spotify's API to fetch and analyze user data. Here's how our app works:

## User Dashboard
Our app features a user-friendly dashboard that offers a personalized overview of the user's music preferences. Through OAuth authentication, users grant our app access to their Spotify account, enabling us to retrieve data such as top artists, tracks and genres. This data is then displayed in the UI, allowing users to explore their music habits in depth. The dashboard provides valuable insights into the user's listening habits and possibly help them discover new music tailored to their tastes using Spotify's API. To enhance the user experience, we leverage Streamlit UI to seamlessly integrate our Flask app, providing a smooth and interactive dashboard experience.

## Artist Query
In addition to the user dashboard, our app allows users to query specific artists to access detailed information about them. Users can search for their favorite artists, and our app retrieves comprehensive data about the artist's tracks, including features such as duration, tempo, energy, and more. This feature enables users to dive deeper into their favorite artists' music and gain a better understanding of their style and sound.

A simple demo of our application:

[![Watch the video](https://img.youtube.com/vi/e73Uf9bYfAE/maxresdefault.jpg)](https://youtu.be/e73Uf9bYfAE)

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

## Python Package Descriptions

| Package Name    | Description                                                                                     |
|-----------------|-------------------------------------------------------------------------------------------------|
| requests        | A Python HTTP library that allows sending HTTP requests easily, making API calls and handling responses. |
| urllib.parse    | A Python library for parsing and manipulating URLs.                                             |
| json            | A Python library for encoding and decoding JSON data.                                            |
| datetime        | A Python module for manipulating dates and times.                                                |
| flask           | A lightweight web application framework for Python.                                              |
| collections     | A Python module that provides specialized container datatypes, such as Counter.                  |
| itertools       | A module providing functions creating iterators for efficient looping.                           |
| os              | A module in Python that provides a way of using operating system dependent functionality.         |
| dotenv          | A Python module that allows loading environment variables from a .env file.                      |
| io              | A core Python module for handling I/O operations.                                                |
| boto3           | The Amazon Web Services (AWS) SDK for Python.                                                    |
| base64          | A Python module for encoding and decoding base64-encoded strings.                                 |
| random          | A Python module that generates random numbers.                                                    |
| pandas          | A powerful data analysis and manipulation library for Python.                                     |
| awswrangler     | A utility library for simplifying the interaction with AWS services, particularly Amazon Redshift and S3. |
| sqlalchemy      | A SQL toolkit and Object-Relational Mapping (ORM) library for Python.                             |
| aiohttp         | An asynchronous HTTP client/server framework for Python.                                          |
| plotly.express  | A Python library for creating interactive plots and figures.                                      |
| streamlit       | A Python library for creating interactive web apps for data science and machine learning projects. |
| dotenv          | A Python module that allows loading environment variables from a .env file.                      |



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
   
   Set up DynamoDB table for `spotify`.

   - Let `primary_key = artist_id` and `sort_key = track_id`.

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

## Usage

After setting up the application, users can access the web interface through their browser, log in with their Spotify account, and explore various functionalities for analyzing their Spotify usage data.
