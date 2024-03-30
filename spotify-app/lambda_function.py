import io
import boto3
import base64
import random
import pandas as pd
import awswrangler as wr
from decimal import Decimal
from spotify_db import search_view
from spotify_api import SpotifyAPI
import json
import asyncio

global_headers = None

async def wait_search_view(artist_name):

    # Await the asynchronous function call
    df = await search_view(artist_name)

    ## For Radar Chart
    desired_columns = ['instrumentalness', 'acousticness', 'danceability',
                       'energy', 'liveness', 'speechiness', 'valence']
    df_selected = df[desired_columns]

    avg_values = df_selected.mean()

    feature_list = avg_values.index.tolist()
    value_list = avg_values.values.tolist()

    # Construct the dictionary
    avg_dict = {"feature": feature_list, "value": value_list}

    # Convert avg_dict to JSON
    avg_dict_json = json.dumps(avg_dict)

    response = {
        "df": df.to_json(),
        "radar_chart": avg_dict_json
    }
    
    print(response)

    return json.dumps(response)

def wait_recommendations(headers):
    
    spotify_api = SpotifyAPI()

    resp = spotify_api.get_recommendations(headers)

    return resp

def lambda_handler(event, context):
    print(event)

    global global_headers
    
    if event["rawPath"] == "/search":
        params = event["queryStringParameters"]
        artist_name = params["artist"]
            
        result = asyncio.get_event_loop().run_until_complete(wait_search_view(artist_name))
        return result
    
    elif event["rawPath"] == "/user_data":
        print("lambda_function: Getting User Data")

        params = event["queryStringParameters"]
        auth = params['Authorization']

        headers = {
            "Authorization": auth
        }

        global_headers = headers

        spotify_api = SpotifyAPI()

        print("lambda_function.py: Getting User Data")

        resp = spotify_api.get_user_data(headers)

        print(resp)

        return json.dumps(resp)
    
    elif event["rawPath"] == "/get_recommendations":
        print("lambda_function: Getting Recommendations")

        print(global_headers)

        resp = wait_recommendations(global_headers)

        print(resp)

        return resp

