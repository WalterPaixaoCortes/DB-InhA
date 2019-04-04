"""
    Wrapper for Google Sheet API
"""
from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

class GSheetWrapper():
    """
        A Wrapper class for basic GSheet API functionalities
    """
    __SCOPES = ['https://www.googleapis.com/auth/contacts.readonly','https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    __service = None
    __drive_service = None
    __valueInputOption = "RAW"
    __sheetRange = "%s!A1:%s%s"


    def __init__(self, credentials_file, client_secret_file):
        store = file.Storage(credentials_file)
        creds = None
        try:
            creds = store.get()
        except:
            if not creds or creds.invalid:
                flow = client.flow_from_clientsecrets(client_secret_file, self.__SCOPES)
                creds = tools.run_flow(flow, store)

        self.__service = build('sheets', 'v4', http=creds.authorize(Http()))
        self.__drive_service = build('drive', 'v3', http=creds.authorize(Http()))


    def create_spreadsheet(self, survey_name):
        """
            Create a new spreadsheet
        """
        spreadsheet_body = { "properties": { "title": survey_name,
                                     "defaultFormat": {"wrapStrategy": "WRAP"}
                                   },
                     "sheets": [
                         { "properties": { "sheetId": 0,
                                           "index": 0,
                                           "title": "Summary"
                                         }
                         }
                     ]
                   }
        request = self.__service.spreadsheets().create(body=spreadsheet_body)
        response = request.execute()
        return response['spreadsheetId']


    def populate_sheet(self, spreadsheet_id, sheet_name, data):
        """
            populate sheets with data
        """
        spreadsheet = self.__service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        for sheet in spreadsheet['sheets']:
            if sheet_name == sheet['properties']['title']:
                raw_request = { "requests": [{ "deleteSheet": { "sheetId": sheet['properties']['sheetId']  } }] }
                request = self.__service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=raw_request)
                response = request.execute()
                break

        raw_request = { "requests": [{ "addSheet": { "properties": { "title": sheet_name, "gridProperties": {"rowCount": str(len(data['values'])), "columnCount": str(len(data['values'][0]))} } } }] }
        request = self.__service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=raw_request)
        response = request.execute()

        return_value = None
        if len(data['values']) > 0:
            max_row = str(len(data['values']))
            max_col = chr(64+len(data['values'][0]))
            request = self.__service.spreadsheets().values().update(spreadsheetId=spreadsheet_id,
                                                                    range=self.__sheetRange % (sheet_name, max_col, max_row),
                                                                    valueInputOption=self.__valueInputOption,
                                                                    body=data)
            return_value = request.execute()
        return return_value


    def append_sheet(self, spreadsheet_id, sheet_name, data):
        """
            Append data to sheet
        """
        return_value = False
        try:
            request = self.__service.spreadsheets().values().append(spreadsheetId=spreadsheet_id,
                                                                    range=sheet_name,
                                                                    valueInputOption='USER_ENTERED',
                                                                    insertDataOption='INSERT_ROWS',
                                                                    body=data)
            response = request.execute()
            return_value = True 
        except Exception:
            pass
        return return_value
    

    def update_sheet(self, spreadsheet_id, sheet_name, data):
        """
            Append data to sheet
        """
        return_value = False
        try:
            raw_data = { "valueInputOption": "USER_ENTERED",
                            "data": [{"range": sheet_name, "majorDimension": "ROWS", "values": data}],
                            "includeValuesInResponse": True,
                            "responseValueRenderOption": "UNFORMATTED_VALUE",
                            "responseDateTimeRenderOption": "FORMATTED_STRING"}
            request = self.__service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=raw_data)
            response = request.execute()
            return_value = True 
        except Exception:
            pass
        return return_value
    

    def spreadsheet_exists(self, spreadsheet_name):
        """
            Check if a spreadsheet exists and return its ID
        """
        return_value = None
        request = self.__drive_service.files().list(q="name='%s'" % spreadsheet_name, spaces='drive', fields='files(id, name)')
        response = request.execute()
        if len(response['files']) > 0:
            return_value = response['files'][0]['id']
        return return_value


    def get_sheet(self, spreadsheet_id, range_name):
        result = self.__service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        return values


    def get_sheets(self, spreadsheet_id):
        spreadsheet = self.__service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        return spreadsheet['sheets']


    def close(self):
        self.__service = None