# User Dashboard : Flask App to Streamlit
This also retrieves User-related information via Spotify's own API
```mermaid
graph TD;
    main_py[main.py] -->|Redirects to /login| login[Flask: /login]
    login -->|Redirects to Spotify login page| AUTH_URL[Spotify Authorization URL]
    AUTH_URL ---> |Redirects to /streamlit| streamlit_flask[Flask: /streamlit]
    streamlit_flask --> |Calls /user_data| API[Amazon API Gateway: <br> /user_data]

    API --> |Transforms response| streamlit_flask 

    streamlit_flask -->|Redirects to Streamlit code| streamlit_variables_py[streamlit_variables.py]
    streamlit_variables_py --> |Displays visualization| Streamlit_UI[Streamlit UI]

    AUTH_URL ~~~ streamlit_flask

    subgraph AWSLambda["<i>AWS Lambda</i>"]
        
        API -.-> |Fetches user information| Spotify_API[Spotify API]
        Spotify_API -.-> |Returns information| API
        
    end
```


# Artist Query : Retrieval of Artist/Album/Track Information

```mermaid

graph TB;
    streamlit_variables.py -->|Displays visualizations| Streamlit_UI[Streamlit UI]
    engine --> streamlit_variables.py

    streamlit ~~~ AWS_Lambda
    
    subgraph AWS_Lambda["<i>AWS Lambda</i>"]
        direction TB
        API --> |Calls /search| spotify_db_py
        spotify_db_py[spotify_db.py] -->|Check if Artist in DB| CheckArtist{Is Artist in DB?}
        CheckArtist -->|No| spotify_api_py[spotify_api.py]
        spotify_api_py -->|Interacts with Spotify API| Spotify_API[Spotify API]
        CheckArtist -->|Yes| RetrieveInfo[Retrieve information from DB]
        RetrieveInfo -->engine
        Spotify_API -->|Fetches relevant information & stores in DB| engine[(DynamoDB)]
    end

    subgraph streamlit["User Interface"]
        
        Streamlit_UI ----> |User queries an Artist| API[Amazon API Gateway]
        
        
    end
```

##  DynamoDB - Variables of Interest (1NF)

```mermaid

%%{init: {
  "theme": "default",
  "themeCSS": [
    ".er.relationshipLabel { fill: black; }", 
    ".er.relationshipLabelBox { fill: white; }", 
    "[id^=entity-Spotify] .er.entityBox { fill: pink; }"
    ]
}}%%
erDiagram
    Spotify 

    Spotify {
        string artist_id "PK"
        string track_id "SK"
        int followers ""
        int popularity ""
        JSON genres ""
        string name ""
        string album_id ""
        string album_type ""
        int total_tracks ""
        int track_number ""
        JSON available_markets ""
        JSON images ""
        string album_name ""
        int key ""
        int duration_ms ""
        decimal instrumentalness ""
        decimal acousticness ""
        decimal danceability ""
        decimal energy ""
        decimal liveness ""
        decimal speechiness ""
        decimal valence ""
        decimal loudness ""
        decimal tempo ""
        decimal time_signature ""
        string track_name ""
    }
    
```
