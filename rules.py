import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import json

FROM_TAG_PATH = 'inputs/Tag-From.csv'
JSON_PATH = 'inputs/examples.json'

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    ]

def get_json_data(path: str):
    with open(path, 'r') as file:
        return json.load(file)

def get_email_labels(file_name: str) -> dict[str, list[str]]:
    result = {}
    with open(file_name, 'r') as file:
        while (line := file.readline()) != '':
            vals = line.strip().split(',')
            result[vals[0].strip()] = [tag.strip() for tag in vals[1:]]
    return result

def get_email_filters(file_name: str):
    raise NotImplementedError

def get_existing_labels(service) -> list[str]:
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])
    if not labels: raise 'No Labels'
    # return [label['name'] for label in labels]
    return labels

def create_label(service, name: str) -> str:
    body = {
        'name' : name,
    }
    result = service.users().labels().create(userId="me", body=body).execute()
    return result.get("id")

def get_label_ids(service, labels: list[str]):
    ids = []
    existing_labels = get_existing_labels(service)
    for label in labels:
            found = False
            for label_info in existing_labels:
                if label == label_info['name']:
                    ids.append(label_info['id'])
                    found = True
                    break
            if not found: ids.append(create_label(service, label))
            else: found = False
    return ids

# region Filters
def create_tag_filters(service, data: dict) -> None:
    def create_filter(email: str, label_ids:list[str]):
        for id in label_ids:
            filter_content = {
                "criteria": {"from": email},
                "action": {
                    "addLabelIds": [id],
                    "removeLabelIds": ["INBOX"],
                },
            }
            try:
                result = (
                    service.users()
                    .settings()
                    .filters()
                    .create(userId="me", body=filter_content)
                    .execute()
                )
            except: print(f'Failed to label emails from {email} with ID {id}.')

    for profile in data['request']:
        email = profile['email']
        labels = profile['labels']
        to_inbox = profile['toInbox']
        label_ids = get_label_ids(service, labels)
        
        try:
            create_filter(email, label_ids)
        except HttpError as error:
            print(f"An error occurred: {error}")

    
#endregion

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        data = get_json_data(JSON_PATH)
        create_tag_filters(service, data)
    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()