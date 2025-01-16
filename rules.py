import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import json
import sys

# region Constants
# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.labels', # create labels
    'https://www.googleapis.com/auth/gmail.settings.basic', # create filters
    'https://www.googleapis.com/auth/gmail.modify' # updating threads
    ]

DEFAULT_TEXT_COLOR = '#000000'
DEFAULT_BACKGROUND_COLOR = '#cccccc'

# endregion

# region Mail Threads
def find_matching_threads(service, email: str=None, subject: str=None):
    """
    Construct a query and return matching threads (email chains) via the api 
    
    service: gmail build resource object
    email: email that filter queried threads by senders with that email
    subject: words that filter queried threads by subjects with those words 
    """
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

def update_thread(
    service, 
    thread_id: str, 
    label_ids: list[str], 
    to_inbox: bool
    ):
    """
    Update the thread with the given ID with the given labels.
    Note: Only works on the last 500 messages.

    service: gmail build resource object
    thread_id: the gmail thread id of the thread to update
    label_ids: the gmail ids of the labels to apply to the thread
    to_inbox: whether or not the thread keeps the INBOX label
    """
    body = { 'addLabelIds' : label_ids } 
    if not to_inbox:
        body['removeLabelIds'] = ['INBOX']
    (
        service
        .users()
        .threads()
        .modify(userId='me', id=thread_id, body=body) 
        # TODO optionally label each message in the thread
        .execute()
    )

def apply_sender_filters(service, senders: list[dict]):
    """
    Given a list with valid 'sender' dicts, update threads matching the 
    from criteria with corresponding labels.

    service: gmail build resource object
    senders: a list of dicts found from the inputted json file that tells how 
    to filter the senders.
    The dicts need the following structure:
    {
        'email' : string,
        'labels' : list[str],
        'toInbox' : bool
    }
    """
    for profile in senders:
        email = profile['email']
        labels = profile['labels']
        to_inbox = profile['toInbox']
        label_ids = get_label_ids(service, labels)
        query_threads = find_matching_threads(service, email)
        if query_threads['resultSizeEstimate'] == 0: 
            continue # no messages matched the query
        for thread in query_threads['threads']:
            try:
                update_thread(service, thread['id'], label_ids, to_inbox)
            except HttpError as error:
                print(
                    f'''Unable to add labels 
                    to thread {thread['id']}: {error.reason}'''
                )

def apply_subject_filters(service, subjects: list[dict]):
    """
    Given a list with valid 'subject' dicts, update threads matching the 
    subject criteria with corresponding labels.

    service: gmail build resource object
    subjects: a list of dicts found from the inputted json file that tells how 
    to filter the subjects.
    The dicts need the following structure:
    {
        'contains' : string,
        'labels' : list[str],
        'toInbox' : bool
    }
    """
    for sub in subjects:
        phrase = sub['contains']
        labels = sub['labels']
        to_inbox = sub['toInbox']
        label_ids = get_label_ids(service, labels)
        query_threads = find_matching_threads(service, subject=phrase)
        if query_threads['resultSizeEstimate'] == 0: 
            continue # no messages matched the query
        for thread in query_threads['threads']:
            try:
                update_thread(service, thread['id'], label_ids, to_inbox)
            except HttpError as error:
                print(
                    f'''Unable to add labels 
                    to thread {thread['id']}: {error.reason}'''
                )

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
    Format a dict that works the the gmail api filter().create() function.
    Note: Requires that either add_labels or remove_labels is not None.
    Note: Requires at least one of the criteria is filled.

    add_labels: the label ids to add to filtered messages
    remove_labels: the label ids to remove from filtered messages
    to: criteria that filters by who message is sent to
    sender: criteria that filters by who sent the message
    subject: criteria that filters by the subject of the message
    has_attachment: criteria that filters if the message has an attachment
    size: criteria that filters by the relative size of the message
    query: criteria that filters by a custom gmail query 
    negated_query: criteria that filters by a custom negated gmail query
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
    """
    Given a list with valid 'sender' dicts, create a corresponding filter in
    gmail that matches the inputs.

    service: gmail build resource object
    senders: a list of dicts found from the inputted json file that tells how 
    to filter the senders.
    The dicts need the following structure:
    {
        'email' : string,
        'labels' : list[str],
        'toInbox' : bool
    }
    """
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
            except HttpError as error: 
                print(f"Couldn't label sender: {error.reason}")
                
# endregion

# region Subjects

def label_subjects(service, subjects: list[dict]) -> list:
    """
    Given a list with valid 'subject' dicts, create a corresponding filter in
    gmail that matches the inputs.

    service: gmail build resource object
    subjects: a list of dicts found from the inputted json file that tells how 
    to filter the subjects.
    The dicts need the following structure:
    {
        'contains' : string,
        'labels' : list[str],
        'toInbox' : bool
    }
    """
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
            except HttpError as error: 
                print(f"Couldn't label subject: {error.reason}")

# endregion

# region Labels

def get_existing_labels(service) -> list[dict]:
    """
    Queries gmail to find all labels that exist.

    service: gmail build resource object
    """
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])
    if not labels: raise 'No Labels'
    return labels

def get_label_ids(service, labels: list[str]) -> list[str]:
    """
    Get the IDs of the given label names. If the label name does not have an
    ID, that label is created and the new ID is returned.

    service: gmail build resource object
    labels: names of labels to get ID's of
    """
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

def create_label(
        service, 
        name: str, 
        text_color: str = None, 
        background_color: str = None
        ) -> str:
    """
    Creates a gmail label with the given name and coloring scheme.

    service: gmail build resource object
    name: the name of the label to create
    text_color: the hexcode of the color to color the label text with
    background_color: the hexcode of the color to color the label background 
    with
    """
    body = { 
            'name' : name, 
            'color' : {
                'textColor' : DEFAULT_TEXT_COLOR,
                'backgroundColor' : DEFAULT_BACKGROUND_COLOR
            }
        }

    if text_color is not None:
        body['color']['textColor'] = text_color
    if background_color is not None:
        body['color']['backgroundColor'] = background_color
            
    result = (
        service
        .users()
        .labels()
        .create(userId="me", body=body)
        .execute()
    )
    return result.get("id")

def update_label(
        service, 
        id: str, 
        name: str = None, 
        text_color: str = None,
        background_color: str = None
    ) -> str:
    """
    Updates a gmail label with the given name and coloring scheme.

    service: gmail build resource object
    id: the ID of the label to change
    name: the new name of the label
    text_color: the hexcode of the color to color the label text with
    background_color: the hexcode of the color to color the label background 
    with
    """
    if id is None:
        raise Exception # no id to update
    if name is None and text_color is None:
        raise Exception # nothing to update
    body = {}
    if name is not None:
        body['name'] = name

    if text_color is not None:
        body['color'] = { 
            'textColor' : text_color,
            'backgroundColor' : DEFAULT_BACKGROUND_COLOR
            }
    if background_color is not None:
        if text_color is not None: 
            body['color']['backgroundColor'] = background_color
        else:
            body['color'] = { 
                'textColor' :  DEFAULT_TEXT_COLOR,
                'backgroundColor' : background_color 
                }
    
    result = (
        service
        .users()
        .labels()
        .update(userId="me", id=id, body=body)
        .execute()
    )
    return result.get("id")

def process_labels(service, labels: list[dict]) -> None:
    """
    Given a list with valid 'label' dicts, update labels with matching names.

    service: gmail build resource object
    labels: a list of dicts found from the inputted json file that tells how 
    to update the labels.
    The dicts need the following structure, with at least one updatable field:
    {
        'id' : string,
        (optional) 'newName' : string,
        (optional) 'textColor' : hex color string,
        (optional) 'backgroundColor' : hex color string
    }
    """
    existing_labels = get_existing_labels(service)
    for lab in existing_labels:
        for new in labels:
            if new['name'] == lab['name']:
                try: 
                    update_label(
                        service, 
                        lab['id'], 
                        new.get('newName', None), 
                        new.get('textColor', None),
                        new.get('backgroundColor', None)
                    )
                except HttpError as error: 
                    # Could be because newName property already exists
                    print(
                        f'''Error updating label {lab['id']} 
                          {new.get('newName', None)}:
                          \n\t{error.reason}'''
                    )
                finally:
                    labels.remove(new)
    for new in labels:
        name = new.get('newName', new.get('name', ''))
        if name == '': raise Exception # can't label without a proper name 
        create_label(
            service,
            name,
            new.get('textColor', None)
            )

#endregion

# region Input
# Should ouptput a dict

def get_json_data(path: str) -> dict:
    """
    Attempt to create a dictionary from a given json file.

    path: the path to the json file
    """
    with open(path, 'r') as file:
        return json.load(file)
    
# endregion

def main() -> None:
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """

    if len(sys.argv) < 1:
        raise Exception # no args given
    
    JSON_PATH = sys.argv[1]
    try: data = get_json_data(JSON_PATH)
    except: 
        print(f'Invalid json file')
        raise Exception # Not a valid json file
    
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

    try: process_labels(service, data['labels'])
    except HttpError as error: 
        print(f"An error occurred processing labels section: {error}")

    try: label_senders(service, data['senders'])
    except HttpError as error: 
        print(f"An error occurred creating filter for senders: {error}")
    
    try: label_subjects(service, data['subjects'])
    except HttpError as error: 
        print(f"An error occurred creating filter for subjects: {error}")
    
    apply_sender_filters(service, data['senders'])
    apply_subject_filters(service, data['subjects'])
    


if __name__ == "__main__":
    main()