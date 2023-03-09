
import Gsheet.google_sheet as google_sheet
from algos import Breakout, Pullback

from utils import PrintException

import time
import asyncio

import uvicorn
from fastapi import FastAPI
import requests
#from datetime import datetime
import datetime
import pandas as pd
import time,sys,os,json

import linecache
import sys


import time
import asyncio

import uvicorn
from fastapi import FastAPI
from swing_loop import BackgroundRunner

app = FastAPI()
#__init__(self, class_settings, df_symbols, gsheet_info):

with open('settings.json') as f:
    settings_data = json.load(f)

BackgroundRunner_settings = {
    "start_time" : datetime.time(settings_data["start_time"]),
    "end_time": datetime.time(settings_data["end_time"]),
    "loop_time": settings_data['loop_time'],
    "ignore_time": settings_data["ignore_time"]
    }
    
gsheet_info = { 'credentials_file': "testgsheets-creds.json", 'spreadsheet_name' : "Prints", 'worksheet_name':'test'}
runner = BackgroundRunner(class_settings=BackgroundRunner_settings, gsheet_info= gsheet_info)

@app.on_event('startup')
async def app_startup():
    asyncio.create_task(runner.run_main())


@app.get("/")
def root():
    return runner.iterations

@app.post("/stop_backgroundtask")
def stop():
    runner.continue_loop = False

@app.post("/read_gsheet")
def stop():
    runner.read_data = True

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)