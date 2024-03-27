# Creating Tables in DB

```mermaid
    graph TD
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
graph TD;
    main_py[main.py] -->|Redirects to /login| login[Flask: /login]
    login -->|Redirects to Spotify login page| AUTH_URL[Spotify Authorization URL]
    AUTH_URL --> |"<i>[Amazon API Gateway]</i>" <br>Calls /user_data</br| AWS_Lambda[AWS Lambda]
    AWS_Lambda --> |Fetches user information| Spotify_API[Spotify API]
    Spotify_API --> |Returns information| AWS_Lambda
    AWS_Lambda --> |Transforms response| streamlit_flask[Flask: /streamlit]
    streamlit_flask -->|Redirects to Streamlit code| streamlit_variables_py[streamlit_variables.py]
    streamlit_variables_py --> |Displays visualization| Streamlit_UI[Streamlit UI]
```


# Retrieval of Artist/Album/Track Information

```mermaid
graph TB;
    Streamlit_UI --> |User queries an Artist| API[Amazon API Gateway]
    API --> |Calls /search| spotify_db_py
    CheckArtist -->|No| spotify_api_py[spotify_api.py]
    spotify_api_py -->|Interacts with Spotify API| Spotify_API[Spotify API]

    spotify_db_py[spotify_db.py] -->|Check if Artist in DB| CheckArtist{Is Artist in DB?}
    
    CheckArtist -->|Yes| RetrieveInfo[Retrieve information from DB]
    RetrieveInfo -->engine
    engine --> streamlit_variables.py

    streamlit_variables.py -->|Displays visualizations| Streamlit_UI[Streamlit UI]
    
    Spotify_API -->|Fetches relevant information & stores in DB| engine[Database]

```
