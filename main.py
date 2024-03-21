"""

Flask App to get Spotify OAuth & User's information
then we pass to streamlit UI in the streamlit_ui() function

"""


import requests
import urllib.parse
import json
from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session
from collections import Counter
import itertools

app = Flask(__name__)
app.secret_key = 'f42fa124d2627f97aad0adbdc1ef089300087684ecd2a990'


"""

Not sure if you'd need to change the PUBLIC_IP part to your own
public ip address in AWS if my instance is not running

"""

PUBLIC_IP = '44.218.178.62'

CLIENT_ID = 'e83d0b4c2eab4287adbd9830d18ac151'
CLIENT_SECRET = 'e3e62bcb12ed41bebadf1951985076b8'
REDIRECT_URI = f'http://{PUBLIC_IP}:5001/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

@app.route('/')
def index():
    return "Welcome to my Spotify app <a href='/login'>Login in with Spotify</a>"

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email user-top-read'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"Error":request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)

        if response.status_code == 200:
            print("Token created successfully.")
            
            token_info = response.json()

            session['access_token'] = token_info['access_token']
            session['refresh_token'] = token_info['refresh_token']
            session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

            return redirect('/streamlit')
        
        else:
            error_message = {'message': 'Failed to create token', 
                             'status_code': response.status_code,
                             'response_error': response.text}
            
            return error_message

@app.route('/playlists')
def get_playlists():

    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        "Authorization": f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)

    if response.status_code == 200:
        playlists = response.json()

        return jsonify(playlists)
    
    else:
        error_message = {'message': 'Failed to get user playlist', 
                         'status_code': response.status_code,
                         'response_error': response.text}
        return error_message
    
@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)

        if response.status_code == 200:
            new_token_info = response.json()

            session['access_token'] = new_token_info['access_token']
            session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

            return redirect('/playlists')
        
        else:
            error_message = {'message': 'Failed to create token', 
                             'status_code': response.status_code,
                             'response_error': response.text}
            
            return error_message
        
@app.route('/streamlit')
def streamlit_ui():
    # Logic to determine whether user is authenticated
    # If authenticated, render Streamlit UI
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        "Authorization": f"Bearer {session['access_token']}"
    }

    user_data = {}

    # GET USERNAME
    response = requests.get(API_BASE_URL + "me", headers=headers)
    if response.status_code == 200:
        user = response.json()
        user_data["username"] = user['display_name']
    
    else:
        error_message = {'message': 'Failed to get user\'s data ', 
                         'status_code': response.status_code,
                         'response_error': response.text}
        return error_message

    # GET TOP ARTISTS

    top_artist_url = API_BASE_URL + "me/top/artists"
    artist_response = requests.get(top_artist_url, headers=headers)

    if artist_response.status_code == 200:
        top_artists = artist_response.json()
        names = [item['name'] for item in top_artists['items']]
        genres = [item['genres'] for item in top_artists['items']]

        user_data["top_artists"] = names
        genres_count = Counter(list(itertools.chain(*genres)))
        user_data["top_genres"] = [genre for genre, _ in genres_count.most_common(10)]
    
    else:
        error_message = {'message': 'Failed to get user\'s top artists ', 
                         'status_code': artist_response.status_code,
                         'response_error': artist_response.text}
        return error_message
    
    # GET TOP TRACKS
    
    top_tracks_url = API_BASE_URL + "me/top/tracks"
    tracks_response = requests.get(top_tracks_url, headers=headers)

    if tracks_response.status_code == 200:
        top_tracks = tracks_response.json()
        track_names = [item['name'] for item in top_tracks['items']]
        
        user_data["top_tracks"] = track_names
    
    else:
        error_message = {'message': 'Failed to get user\'s top tracks ', 
                         'status_code': tracks_response.status_code,
                         'response_error': tracks_response.text}
        return error_message
    
    user_data = json.dumps(user_data)
    print(user_data)


    return redirect(f'http://{PUBLIC_IP}:8501?user={user_data}')  # Replace with your Streamlit UI URL
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

    # To run flask: python3 main.py
