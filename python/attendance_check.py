import time
import traceback
import pandas as pd
import numpy as np
import requests
import base64

from camelot.core import TableList
from bus_schedule_detector import get_bus_stop_schedule  # need tabulate, cv2

username = base64.b64decode(b'YWxhbQ==')
password = base64.b64decode(b'SEtUVi0xMjM=')
pdf_path = r'./doc/將軍澳穿梭巴士時間表.pdf'
cookie_file = r'cookie'

year, month, day, hour, min = map(int, time.strftime("%Y %m %d %H %M").split())
# timesheet cutoff is 15th in every month
if day > 15:
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1


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


def main():
    login()
    record = get_attendance_record()
    logout()

    print(record['data'][0])

    tables = get_bus_stop_schedule(pdf_path=pdf_path)
    sched_lohas, sched_tko = organize_timetable(tables)
    # print(sched_lohas)
    return


if __name__ == "__main__":
    main()
