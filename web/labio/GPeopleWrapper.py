"""
    Wrapper for Google People API
"""
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

class PeopleWrapper():
    """
        A Wrapper class for basic People API functionalities
    """
    __SCOPES = ['https://www.googleapis.com/auth/contacts.readonly','https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    __service = None

    def __init__(self, credentials_file=None, client_secret_file=None):
        store = file.Storage(credentials_file)
        #store = None
        creds = None
        try:
            creds = store.get()
        except:
            if not creds or creds.invalid:
                flow = client.flow_from_clientsecrets(client_secret_file, self.__SCOPES)
                creds = tools.run_flow(flow, store)

        self.__service = build('people', 'v1', http=creds.authorize(Http()))

    def get_contacts(self):
        result = self.__service.people().connections().list(resourceName='people/me', personFields='names,emailAddresses').execute()
        values = result.get('connections', [])
        return values

    def close(self):
        self.__service = None


