from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import main

DICT_FOR_GLOSSES_ID = ""
GOOGLE_API_CREDENTIALS_PATH = ''
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']   # access modes


def download_glosses_dictionary_from_googleDrive():
    # Set the API scope and authenticate
    scopes = ['https://www.googleapis.com/auth/drive.readonly']
    flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_API_CREDENTIALS_PATH, scopes)
    credentials = flow.run_local_server(port=0)

    # Create a Google Drive API service
    service = build('drive', 'v3', credentials=credentials)

    # Download the file
    request = service.files().get_media(fileId=DICT_FOR_GLOSSES_ID)
    file_data = request.execute()
    with open(main.GLOSSES_DICT_PATH, 'wb') as f:
        f.write(file_data)
