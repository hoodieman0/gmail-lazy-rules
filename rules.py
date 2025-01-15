import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import json
import sys

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.labels', # create labels
    'https://www.googleapis.com/auth/gmail.settings.basic', # create filters
    'https://www.googleapis.com/auth/gmail.modify' # updating threads
    ]

# region Mail Threads
def find_matching_threads(service, email: str=None, subject: str=None):
    if email is None and subject is None:
        raise Exception # need at least one query field
    query_string = ''

    if email is not None:
        query_string += f'from:{email} '
    
    if subject is not None:
        query_string += f'subject:{subject}'

    return (
        service
        .users()
        .threads()
        .list(userId='me', q=query_string, maxResults=500)
        .execute()
    )

def update_thread(service, thread_id: str, ids: list, to_inbox: bool):
    """
    TODO optionally label each message in the thread
    Only works on the last 500 messages
    """
    body = { 'addLabelIds' : ids }
    if not to_inbox:
        body['removeLabelIds'] = ['INBOX']
    (
        service
        .users()
        .threads()
        .modify(userId='me', id=thread_id, body=body)
        .execute()
    )

def apply_sender_filters(service, senders: list):
    for profile in senders:
        email = profile['email']
        labels = profile['labels']
        to_inbox = profile['toInbox']
        label_ids = get_label_ids(service, labels)
        query_threads = find_matching_threads(service, email)
        if query_threads['resultSizeEstimate'] == 0: 
            continue # no messages matched the query
        for thread in query_threads['threads']:
            update_thread(service, thread['id'], label_ids, to_inbox)

def apply_subject_filters(service, subjects: list):
    for sub in subjects:
        phrase = sub['contains']
        labels = sub['labels']
        to_inbox = sub['toInbox']
        label_ids = get_label_ids(service, labels)
        query_threads = find_matching_threads(service, subject=phrase)
        if query_threads['resultSizeEstimate'] == 0: 
            continue # no messages matched the query
        for thread in query_threads['threads']:
            update_thread(service, thread['id'], label_ids, to_inbox)

# endregion

# region Filters

def create_filter_body(
        add_labels: list[str] = None, 
        remove_labels: list[str] = None, 
        to: str = None,
        sender: str = None, 
        subject: str = None,
        has_attachment: bool = None,
        size: int = None,
        query: str = None,
        negated_query: str = None
        ) -> dict[str, any]:
    """
    Requires that either add_labels or remove_labels is not None.
    Requires at least one of the criteria is filled.
    """
    if add_labels is None and remove_labels is None:
        raise Exception # no label action to take

    if (to is None 
        and sender is None 
        and subject is None 
        and has_attachment is None 
        and size is None 
        and query is None 
        and negated_query is None):
        raise Exception # No criteria to filter

    # A set of actions to perform on a message. 
    # Action that the filter performs.
    # Message matching criteria. 
    # # Matching criteria for the filter.
    body = { 'action' : {}, 'criteria' : {}}
    
    if add_labels is not None:
        body['action']['addLabelIds'] = add_labels

    if remove_labels is not None:
        body['action']['removeLabelIds'] = remove_labels
    # Resource definition for Gmail filters. 
    # Filters apply to specific messages instead of an entire email thread.

    if to is not None:
        # The recipient's display name or email address. 
        # Includes recipients in the "to", "cc", and "bcc" header fields. 
        # You can use simply the local part of the email address. 
        # For example, "example" and "example@" 
        # both match "example@gmail.com". 
        # This field is case-insensitive.
        body['criteria']['to'] = to

    if sender is not None:
        # The sender's display name or email address.
        body['criteria']['from'] = sender

    if subject is not None:
        # Case-insensitive phrase found in the message's subject. 
        # Trailing and leading whitespace are be trimmed and 
        # adjacent spaces are collapsed.
        body['criteria']['subject'] = subject

    if has_attachment is not None:
        # Whether the message has any attachment.
        body['criteria']['hasAttachment'] = has_attachment
    
    if size is not None:
        # The size of the entire RFC822 message in bytes, 
        # including all headers and attachments.
        body['criteria']['size'] = size
    
    if query is not None:
        # Only return messages matching the specified query. 
        # Supports the same query format as the Gmail search box. 
        # For example, "from:someuser@example.com rfc822msgid: is:unread".
        body['criteria']['query'] = query
    
    if negated_query is not None:
        # Only return messages not matching the specified query. 
        # Supports the same query format as the Gmail search box. 
        # For example, "from:someuser@example.com rfc822msgid: is:unread".
        body['criteria']['negatedQuery'] = negated_query

    return body

def create_filter(service, body: dict):
    return (
        service.users()
        .settings()
        .filters()
        .create(userId="me", body=body)
        .execute()
    )

# endregion

# region Senders

def label_senders(service, senders: list[dict]) -> None:
    for profile in senders:
        email = profile['email']
        labels = profile['labels']
        to_inbox = profile['toInbox']
        label_ids = get_label_ids(service, labels)

        for id in label_ids:
            body = {}
            if not to_inbox:
                body = create_filter_body(
                    add_labels=[id], 
                    remove_labels=['INBOX'], 
                    sender=email
                    )
            else: 
                body = create_filter_body(
                    add_labels=[id], 
                    sender=email
                )

            try: create_filter(service, body)
            except HttpError as error: print(f"An error occurred: {error}")
                
# endregion

# region Subjects

def label_subjects(service, subjects: list[dict]) -> list:
    for sub in subjects:
        phrase = sub['contains']
        labels = sub['labels']
        to_inbox = sub['toInbox']
        label_ids = get_label_ids(service, labels)

        for id in label_ids:
            body = {}
            if not to_inbox:
                body = create_filter_body(
                    add_labels=[id], 
                    remove_labels=['INBOX'], 
                    subject=phrase
                    )
            else: 
                body = create_filter_body(
                    add_labels=[id], 
                    subject=phrase
                )

            try: create_filter(service, body)
            except HttpError as error: print(f"An error occurred: {error}")

# endregion

# region Input
# Should ouptput a dict

def get_json_data(path: str) -> dict:
    with open(path, 'r') as file:
        return json.load(file)
    
# endregion

# region Gmail Calls

def get_email_labels(file_name: str) -> dict[str, list[str]]: # TODO create func
    result = {}
    with open(file_name, 'r') as file:
        while (line := file.readline()) != '':
            vals = line.strip().split(',')
            result[vals[0].strip()] = [tag.strip() for tag in vals[1:]]
    return result

def get_existing_labels(service) -> list[str]:
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])
    if not labels: raise 'No Labels'
    return labels

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

def create_label(service, name: str) -> str:
    body = { 'name' : name }
    result = service.users().labels().create(userId="me", body=body).execute()
    return result.get("id")

# endregion

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
    
    # Call the Gmail API
    try:
        service = build("gmail", "v1", credentials=creds)
    except HttpError as error:
        print(f"An error occurred: {error}")

    JSON_PATH = sys.argv[1]
    data = get_json_data(JSON_PATH)

    try: label_senders(service, data['senders'])
    except: print(f"An error occurred creating filter for senders: {error}")
    
    try: label_subjects(service, data['subjects'])
    except: print(f"An error occurred creating filter for subjects: {error}")
    
    apply_sender_filters(service, data['senders'])
    apply_subject_filters(service, data['subjects'])
    


if __name__ == "__main__":
    main()