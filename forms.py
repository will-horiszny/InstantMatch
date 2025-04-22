import os
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import process

# Configuration
SCOPES = [
    'https://www.googleapis.com/auth/forms.body.readonly',
    'https://www.googleapis.com/auth/forms.responses.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]
FORM_ID = 'YOUR_FORM_ID_HERE'  # Replace with your form ID
POLL_INTERVAL = 60  # Check for new responses every 60 seconds
PROCESSED_FILE = 'processed_responses.txt'  # File to track processed responses IDs


def get_form_questions(forms_service):
    """Map question IDs to their text using Forms API"""
    form = forms_service.forms().get(formId=FORM_ID).execute()
    question_map = {}

    for item in form.get('items', []):
        if 'questionItem' in item:
            try:
                qid = item['questionItem']['question']['questionId']
                question_map[qid] = item['title']
            except KeyError as e:
                print(f"Skipping malformed question item: {e}")

    return question_map


def load_processed_responses():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, 'r') as f:
        return set(f.read().splitlines())


def save_processed_response(response_id):
    with open(PROCESSED_FILE, 'a') as f:
        f.write(f"{response_id}\n")


def get_credentials():
    """Retrieves credentials, refreshing or authenticating as needed."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def get_form_service(creds):
    """Builds the Google Forms service using the provided credentials."""
    return build('forms', 'v1', credentials=creds)


def get_gmail_service(creds):
    """Builds the Gmail service using the provided credentials."""
    return build('gmail', 'v1', credentials=creds)


def poll_responses():
    # Retrieve credentials once and reuse for both services
    creds = get_credentials()
    form_service = get_form_service(creds)
    gmail_service = get_gmail_service(creds)
    question_map = get_form_questions(form_service)
    processed = load_processed_responses()

    while True:
        try:
            result = form_service.forms().responses().list(formId=FORM_ID).execute()
            responses = result.get('responses', [])

            for response in responses:
                response_id = response['responseId']
                if response_id not in processed:
                    success = process.process_response(response, gmail_service, question_map)
                    if success:
                        save_processed_response(response_id)
                        processed.add(response_id)

            time.sleep(POLL_INTERVAL)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)


if __name__ == '__main__':
    poll_responses()
