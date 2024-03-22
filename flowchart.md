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
<div class="mermaid">
graph TD;
    main_py[main.py] -->|Redirects to /login| login[Flask: /login]
    login -->|Redirects to Spotify login page| AUTH_URL[Spotify Authorization URL]
    AUTH_URL --> |Redirects to /streamlit| streamlit
    streamlit --> |Fetches user information| Spotify_API[Spotify API]
    Spotify_API --> |Returns information| streamlit
    streamlit -->|Redirects to Streamlit UI| Streamlit_UI[Streamlit UI]
</div>


# Retrieval of Artist/Album/Track Information

<div class="mermaid">
graph TD;
    
    CheckArtist -->|No| spotify_api_py[spotify_api.py]
    spotify_api_py -->|Interacts with Spotify API| Spotify_API[Spotify API]

    spotify_db_py[spotify_db.py] -->|Check if Artist in DB| CheckArtist{Is Artist in DB?}
    
    CheckArtist -->|Yes| RetrieveInfo[Retrieve information from DB]
    RetrieveInfo -->engine
    engine --> streamlit_variables_py

    streamlit_variables_py -->|Displays visualizations| Streamlit_UI[Streamlit UI]
    
    Spotify_API -->|Fetches relevant information & stores in DB| engine[Database]

</div>
