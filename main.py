# from __future__ import print_function
import palm
import calendar
import requests
from google.cloud import secretmanager
from google.cloud import storage
from google.cloud import aiplatform
import os
import re
import json
import vertexai
from vertexai.language_models import TextGenerationModel
import random
import datetime
import time
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from google.protobuf import timestamp_pb2
from dateutil import parser
from datetime import timedelta

import functions_framework

SCOPES = ["https://www.googleapis.com/auth/calendar"]
# SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
# CLIENT_SECRET_FILE = "credentials.json"
API_NAME = "calendar"
API_VERSION = "v3"
# CLIENT_ID = "376068948945-pr8ghf5fu7bgu4kvdmv00h72rvp0i7rl.apps.googleusercontent.com"
# CALENDAR_ID = "d3b87f208a55822dca1833e047ad6cd84200beb4fda89b729325ebb3b011c546@group.calendar.google.com"
CUSTOM_DATE_FLAG = 0
TODAY_ONLY_FLAG = 1
CUSTOM_DATE = "20230819"
TRAINING_SESSION_START_TIME = "T07:00:00"
TIME_BETWEEN_WODS = "15"
running_time = TRAINING_SESSION_START_TIME
ACTIVE_FLAG = 1


def get_secret(project_id, secret_name):
    # Initialize the Secret Manager client
    client = secretmanager.SecretManagerServiceClient()
    # Build the secret resource name
    secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    # Access the secret
    response = client.access_secret_version(request={"name": secret_path})
    # Return the secret value
    return response.payload.data.decode("UTF-8")


def get_track_request(api_key):
    url = f"https://api.sugarwod.com/v2/tracks?apiKey={api_key}"
    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def get_wod_request(date, track_id, api_key):
    url = f"https://api.sugarwod.com/v2/workouts?dates={date}&track_id={track_id}&apiKey={api_key}"
    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


def extract_track_ids(data):
    # Initialize an empty dictionary to store the name and id pairs
    name_id_dict = {}
    # Loop through each track object in the 'data' array
    for track in data["data"]:
        # Extract the name and id from the track object
        name = track["attributes"]["name"]
        track_id = track["id"]
        # Add the name-id pair to the dictionary
        name_id_dict[name] = track_id
    # filter out any individual tracks
    filtered_data = {
        name: track_id
        for name, track_id in name_id_dict.items()
        if not re.match(r"^(ID - |BTCP - )", name)
    }
    return filtered_data


def get_track_id(track_name, track_data):
    for name, track_id in track_data.items():
        if name == track_name:
            return track_id
    return None  # Return None if the track_name is not found in the dictionary


def get_wods_for_day(date, track_name, track_dict, api_key):
    track_id = get_track_id(track_name, track_dict)
    # check if track exists in dict
    if track_id is None:
        print(f"'{track_name}' not found in the dictionary.")
        return
    # print(f'{track_name} - {track_id} - {date}')
    raw_wod_data = get_wod_request(date, track_id, api_key)
    # print(raw_wod_data)
    return raw_wod_data


def parse_wod_data(workouts):
    workout_dict = {}
    for workout in workouts["data"]:
        if workout is not None:
            # print(workout["attributes"]["title"])
            if workout["attributes"]["title"] in workout_dict.keys():
                workout_dict[
                    workout["attributes"]["title"] + f" {random.randint(1, 9)}"
                ] = workout["attributes"]["description"]
            else:
                workout_dict[workout["attributes"]["title"]] = workout["attributes"][
                    "description"
                ]
    return workout_dict


def call_model(input):
    vertexai.init(project="wodcal", location="us-central1")
    parameters = {
        "temperature": 0.2,
        "max_output_tokens": 256,
        "top_p": 0.8,
        "top_k": 40,
    }
    model = TextGenerationModel.from_pretrained("text-bison@001")
    response = model.predict(generate_prompt(input), **parameters)
    # print(f"Response from Model: {response.text}")
    return response.text


def generate_prompt(input):
    training_data = get_wod_training_data()
    prompt = f"""{training_data} {input}
        output:
        """
    return prompt


def make_time_prediction(wod_input):
    # prediction
    prediction = call_model(wod_input)
    return prediction


def get_cal_token():
    bucket_name = "cal_token_bucket"
    json_object_name = "token.json"
    storage_client = storage.Client()
    # Get the bucket
    bucket = storage_client.bucket(bucket_name)
    # Get the blob (JSON object) from the bucket
    blob = bucket.blob(json_object_name)
    # Download the JSON object as a string
    json_string = blob.download_as_text()
    return json_string


def get_wod_training_data():
    bucket_name = "wod_cal_training_data"
    txt_object_name = "wod_training_data.txt"
    storage_client = storage.Client()
    # Get the bucket
    bucket = storage_client.bucket(bucket_name)
    # Get the blob (txt object) from the bucket
    blob = bucket.blob(txt_object_name)
    # Download the txt object as a string
    txt_string = blob.download_as_text()
    return txt_string


def create_cal_event(summary, description, wod_time):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    project_id = "wodcal"
    # secret_name = "misha_k_calendar_id"
    secret_name = "wod_calendar_cal_id"
    # Retrieve the secret value
    calendar_secret_value = get_secret(project_id, secret_name)
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    # if os.path.exists("token.json"):
    #     creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # # If there are no (valid) credentials available, let the user log in.
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    #         creds = flow.run_local_server(port=0)
    #     # Save the credentials for the next run
    #     with open("token.json", "w") as token:
    #         token.write(creds.to_json())

    token = get_cal_token()
    creds = Credentials.from_authorized_user_info(json.loads(token), SCOPES)

    try:
        service = build("calendar", "v3", credentials=creds)
        global running_time
        start_time = create_gcal_date_string() + running_time
        end_time = create_gcal_date_string() + add_minutes_to_time(start_time, wod_time)
        running_time = add_minutes_to_time(end_time, TIME_BETWEEN_WODS)
        # print(start_time)
        # print(end_time)
        # start_time = "2021-08-16T09:00:00-07:00"
        # end_time = "2021-08-16T10:00:00-07:00"
        # print(start_time)
        # print(end_time)
        # Call the Calendar API
        event = {
            "summary": summary + " - " + str(wod_time) + " minutes",
            "location": "427 Washington Rd, Pittsburgh, PA 15228",
            "description": description,
            "start": {
                "dateTime": start_time,
                "timeZone": "America/New_York",
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "America/New_York",
            },
        }

        event = (
            service.events()
            .insert(
                calendarId=calendar_secret_value,
                body=event,
            )
            .execute()
        )
        print("Event created: %s" % (event.get("htmlLink")))

    except HttpError as error:
        print("An error occurred: %s" % error)


def sugarwodInit():
    project_id = "wodcal"
    secret_name = "sugarwod-api-key"
    # Retrieve the secret value
    secret_value = get_secret(project_id, secret_name)
    # get raw track data
    raw_track_data = get_track_request(secret_value)
    # create track name:id dict
    track_dict = extract_track_ids(raw_track_data)
    # get raw wod data for a given day
    raw_wod_data = get_wods_for_day(
        create_sugarwod_date_string(), "Compete", track_dict, secret_value
    )
    # create wod_name:wod_description dict
    parsed_wod_data = parse_wod_data(raw_wod_data)
    # inner_dict = {}
    outer_dict = {}
    for each in parsed_wod_data.items():
        # print(each)
        inner_dict = {}
        inner_dict = {each[0]: each[1]}
        key_tuple = tuple(inner_dict.items())
        outer_dict[key_tuple] = make_time_prediction(each[1])

    # print(type(parsed_wod_data))
    # print_predicted_wods(parsed_wod_data)
    return outer_dict


def create_sugarwod_date_string():
    if CUSTOM_DATE_FLAG == 1:
        return CUSTOM_DATE
    else:
        dateStr = ""
        today = datetime.date.today()
        dateStr += str(today.year)
        if today.month < 10:
            dateStr += "0"
        dateStr += str(today.month)
        if today.day < 10:
            dateStr += "0"
        dateStr += str(today.day)
        return dateStr


def create_gcal_date_string():
    # take todays date and make it a string in format time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
    dateStr = ""
    today = datetime.date.today()
    dateStr += str(today.year)
    dateStr += "-"
    if today.month < 10:
        dateStr += "0"
    dateStr += str(today.month)
    dateStr += "-"
    if today.day < 10:
        dateStr += "0"
    dateStr += str(today.day)
    # dateStr += "T09:00:00-07:00"
    return dateStr


def add_minutes_to_time(time_string, minutes_to_add):
    # Parse the original time string using dateutil.parser
    original_time = parser.parse(time_string)
    # Convert minutes to timedelta
    # print(int(minutes_to_add))
    delta = timedelta(minutes=int(minutes_to_add))
    # Add the timedelta to the original time
    new_time = original_time + delta
    # Format the new time to the desired string format
    new_time_string = new_time.strftime("T%H:%M:%S%z")
    return new_time_string


# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def wodcal_pubsub(cloud_event):
    # if whole week flag is set, loop through each day of the week and create a dict of wods
    # if whole week flag is not set, create a dict of wods for a single day
    if ACTIVE_FLAG == 1:
        if TODAY_ONLY_FLAG == 1:
            wod_predictions = sugarwodInit()
            # print(wod_predictions)
            # loop through each entry in the dict, create a calendar event
            for key, value in wod_predictions.items():
                # print(key[0][0])
                # print(key[0][1])
                # print(value)
                create_cal_event(key[0][0], key[0][1], value)
        else:
            pass

    # time in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
    # start_time = "2021-08-16T09:00:00-07:00"
    # end_time = "2021-08-16T10:00:00-07:00"
    return ('ok',200)