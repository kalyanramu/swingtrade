import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from gspread_dataframe import set_with_dataframe

class gsheet:
    def __init__(self, credentials_file, spreadsheet_name):
        self._scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
        "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_file, self._scope)
        client = gspread.authorize(creds)
        sheet = client.open(spreadsheet_name)
        self.spreadsheet_name = spreadsheet_name
        self.sheet = sheet

    def test_connection(self):
        print(f'Accessing Gsheet {self.spreadsheet_name}')

    def read(self,work_sheet) :
        data = self.sheet.worksheet(work_sheet).get_all_records()
        return data
    
    def read_df(self,work_sheet):
        data = self.read(work_sheet)
        df = pd.DataFrame.from_records(data)
        return df
    
    def write_df(self,work_sheet, df):
        data = df.values.tolist()
        worksheet_in = self.sheet.worksheet(work_sheet)
        set_with_dataframe(worksheet_in, df)





