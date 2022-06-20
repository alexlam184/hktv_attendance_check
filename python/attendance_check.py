import time
import datetime
from datetime import datetime,timedelta,date
import traceback
import pandas as pd
import numpy as np
import requests
import base64
import re

from camelot.core import TableList
from bus_schedule_detector import get_bus_stop_schedule  # need tabulate, cv2

username = base64.b64decode(b'YWxhbQ==') # decode my base64 encoded username and password
password = base64.b64decode(b'SEtUVi0xMjM=')
pdf_path = r'./doc/將軍澳穿梭巴士時間表.pdf'
working_hr = 9

year, month, day, hour, min = map(int, time.strftime("%Y %m %d %H %M").split())
# timesheet cutoff is 15th in every month
if day > 15:
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1

def timing(f):
    def wrap(*args, **kwargs):
        time1 = time.time()
        ret = f(*args, **kwargs)
        time2 = time.time()
        print('{:s} function took {:.3f} s'.format(f.__name__, (time2-time1)))
        return ret
    return wrap

def login() -> any:
    try:
        url = 'https://hrms.hktv.com.hk/api/admin/login'
        data = {'action': 'login', 'fldEmpLoginID': username,
                'fldEmpPwd': password, 'code': 'undefined'}
        response = requests.post(url=url, data=data)
        print('[INFO] login response sent,status={}'.format(
            response.status_code))
        global web_cookie
        web_cookie = response.cookies

    except Exception as e:
        print('[ERROR] access HR system error')
        traceback.print_exc()
    return


def get_attendance_record() -> dict:
    try:
        url = "https://hrms.hktv.com.hk/api/Attendance/getpages"
        data = {'page': 1, 'limit': 31,
                'types': 1, 'fldMonth': '{yyyy}-{mm}'.format(yyyy=year, mm=month), 'fldCatID': '', 'fldBranch': '', 'fldEmpPosition': ''}
        response = requests.get(url=url, cookies=web_cookie, data=data)
        record = response.json()
        print('[INFO] get data response sent,status={}'.format(
            response.status_code))
        return record
    except Exception as e:
        print('[ERROR] get attendance record error')
        traceback.print_exc()
        return


def logout() -> any:
    try:
        url = 'https://hrms.hktv.com.hk/api/Admin/LogOut'
        response = requests.post(url=url, cookies=web_cookie)
        print('[INFO] logout response sent,status={}'.format(
            response.status_code))
        print('logout success')
    except Exception as e:
        print('[ERROR] logout HR system error')
        traceback.print_exc()
    return


def organize_timetable(tables: TableList) -> tuple[pd.DataFrame, pd.DataFrame]:
    route: pd.DataFrame = tables[0]  # useless route table
    sched: pd.DataFrame = tables[1]
    sched.rename(columns={'開車時間及地點': 'shift', 'Unnamed: 1': 'to_weekday',
                 'Unnamed: 2': 'from_weekday'}, inplace=True)

    # organize lohas data for weekday only
    lohas_early = sched.loc[2:25]
    lohas_late = sched.loc[36:50]
    lohas_late = lohas_late.drop(columns=['to_weekday', 'from_weekday'])
    lohas_late.rename(columns={'Unnamed: 3': 'to_weekday',
                      'Unnamed: 4': 'from_weekday'}, inplace=True)
    sched_lohas = pd.concat([lohas_early, lohas_late], axis=0)

    # organize tko data for weekday only
    sched_tko = sched.loc[28:50]

    return sched_lohas, sched_tko

@timing
def main():
    login()
    record = get_attendance_record()
    logout()

    try:
        today_date = time.strftime("%Y-%m-%d")
        keys = [i for i in record['data'] if i['fldDate'] == today_date]
        now = datetime.now()
        clockIn = datetime.combine(date(now.year,now.month,now.day),datetime.strptime(keys[0]['fldOriIn1'], '%H:%M').time())
        print('Today clock In time = '+str(clockIn))
    except IndexError as e:
        print('[ERROR] no today attendance')
    
    clockOut = clockIn + pd.DateOffset(hours=working_hr)
    print('Predicted clock Out time = '+str(clockOut))


    tables = get_bus_stop_schedule(pdf_path=pdf_path)
    sched_lohas, sched_tko = organize_timetable(tables)


    def filter_text(words:str):
            #print('original='+str(words))
            if str(words) != 'nan':
                t= re.sub(r'[^0-9]', '', words)
            else:
                t =''
            #print('filter='+t)
            return t

    
    # filter tko time only
    sched_tko = sched_tko.loc[sched_tko['from_weekday'] != '---']
    sched_tko = sched_tko.applymap(filter_text)
    sched_tko[sched_tko.from_weekday!='']
    sched_tko['from_weekday'] = pd.to_datetime(sched_tko['from_weekday'], format='%H%M')
    print(sched_tko)

    # print(sched_lohas)
    return


if __name__ == "__main__":
    main()
