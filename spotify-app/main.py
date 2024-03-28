import requests
import urllib.parse
import json
from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session
from collections import Counter
import itertools
import os
from dotenv import load_dotenv
import time

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

PUBLIC_IP = os.getenv("PUBLIC_IP")

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = f'http://{PUBLIC_IP}:5001/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

@app.route('/')
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to my Spotify app</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f0f0f0;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 600px;
                margin: 100px auto;
                padding: 20px;
                background-color: #fff;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            h1 {
                color: #333;
                text-align: center;
            }
            p {
                color: #666;
                text-align: center;
            }
            a {
                color: #007bff;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome to my Spotify app</h1>
            <p><a href="/login">Login in with Spotify</a></p>
        </div>
    </body>
    </html>
    """

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

    start_time = time.time()

    get_data_url = 'https://9qw0fmwpv2.execute-api.us-east-1.amazonaws.com/user_data'

    response = requests.get(get_data_url, params=headers)

    if response.status_code == 200:
    
        user_data = json.dumps(response.json())

        user_end_time = time.time() - start_time

        print(f"Flask Spotify: Time taken for obtaining user info: {user_end_time} seconds")

        return redirect(f'http://{PUBLIC_IP}:8501?user={user_data}')
    
    else:

        return {
            'Error': 'Error in streamlit_ui()',
            'status_code': response.status_code,
            'message': response.text
        }
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

    # To run flask: python3 main.py
