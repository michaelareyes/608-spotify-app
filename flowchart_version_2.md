# Creating Tables in DB

```mermaid
graph LR;
    create_artist_table_py[create_artist_table.py] -->|Creates empty DB tables| engine[Database]

```

## Current ERD Diagram (actual variables subject to change)
This is just what I have right now

```mermaid

%%{init: {
  "theme": "default",
  "themeCSS": [
    ".er.relationshipLabel { fill: black; }", 
    ".er.relationshipLabelBox { fill: white; }", 
    ".er.entityBox { fill: pink; }",
    "[id^=entity-Album] .er.entityBox { fill: lightgreen;} ",
    "[id^=entity-Track] .er.entityBox { fill: powderblue;} "
    ]
}}%%
erDiagram
    Artist ||--|| Album:""
    Artist ||--|| Track: ""
    Album ||--|| Track: ""
    Artist {
        varchar artist_id "PK"
        int followers ""
        int popularity ""
        JSON genres ""
        varchar name ""
    }
    Album {
        varchar album_id "PK"
        varchar album_type ""
        int total_tracks ""
        int track_number ""
        JSON available_markets ""
        JSON images ""
        varchar album_name ""
        varchar artist_id "FK"
    }
    Track {
        varchar track_id "PK"
        varchar album_id "FK"
        varchar artist_id "FK"
        int key ""
        int duration_ms ""
        float instrumentalness ""
        float acousticness ""
        float danceability ""
        float energy ""
        float liveness ""
        float speechiness ""
        float valence ""
        float loudness ""
        float tempo ""
        float time_signature ""
        varchar track_name ""
    }

    
```


# Flask App to Streamlit
This also retrieves User-related information
```mermaid
sequenceDiagram
    participant main_py as main.py
    participant login as Flask: /login
    participant AUTH_URL as Spotify Authorization URL
    participant streamlit as /streamlit
    participant Spotify_API as Spotify API
    participant streamlit_variables as streamlit_variables.py

    main_py->>login: Redirects to /login
    login->>AUTH_URL: Redirects to Spotify login page
    AUTH_URL->>streamlit: Redirects to /streamlit
    streamlit->>Spotify_API: Fetches user information
    Spotify_API->>streamlit: Returns information
    streamlit->>streamlit_variables: Redirects to Streamlit code
    streamlit_variables->>Streamlit UI: Redirects to Streamlit UI

```


# Retrieval of Artist/Album/Track Information

```mermaid
sequenceDiagram
    participant Streamlit_UI as Streamlit UI
    participant spotify_db_py as spotify_db.py
    participant spotify_api_py as spotify_api.py
    participant streamlit_variables_py as streamlit_variables.py
    participant engine as Database

    Streamlit_UI->>spotify_db_py: User queries an Artist
    spotify_db_py->>engine: Check if Artist in DB
    alt Artist not in DB
        engine->>spotify_api_py: No
        spotify_api_py->>Spotify_API: Interacts with Spotify API
        Spotify_API->>engine: Fetches relevant information & stores in DB
        engine->>spotify_db_py: Returns information
    else Artist in DB
        engine->>spotify_db_py: Yes, returns information
    end
    spotify_db_py->>streamlit_variables_py: Returns information
    streamlit_variables_py->>Streamlit_UI: Displays visualizations

```
