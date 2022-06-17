import time
from camelot.core import TableList
import pandas as pd
import numpy as np
import requests
import base64
from tabula import read_pdf
from tabulate import tabulate
import camelot
import os

username = base64.b64encode(b'alam')
password = base64.b64encode(b'HKTV-123')
pdf_path = r'D:\git_project\hktv_attendance_check\doc\將軍澳穿梭巴士時間表.pdf'


def login():
    cookies = {'enwiki_session': '17ab96bd8ffbe8ca58a78657a918558'}
    print("username={},password={}".format(username,password))



    return

def get_bus_stop_schedule() -> TableList:
    sched:TableList=[]
    if not os.path.exists(r"doc\route.csv"):
        print('[INFO] create schedules csv')
        sched = camelot.read_pdf(pdf_path) 
        sched[0].to_csv(r"doc\route.csv")
        sched[1].to_csv(r"doc\schedule.csv")
    else:
        print('[INFO] schedules csv detected.Get dataframe from csv')
        sched.append(pd.read_csv("doc/route.csv"))
        sched.append(pd.read_csv("doc/schedule.csv"))
    
    return sched


def main():
    login()
    sched = get_bus_stop_schedule()
    print(sched[1])
    return
    

if __name__ == "__main__":
    main()
