import time
import datetime
from datetime import datetime,date
import traceback
import pandas as pd
import requests
import base64
import re
from camelot.core import TableList
from bus_schedule_detector import get_bus_stop_schedule  # need tabulate, cv2
import logging
import sys

username = base64.b64decode(b'YWxhbQ==') # decode my base64 encoded username and password
password = base64.b64decode(b'SEtUVi0xMjM=')
pdf_path = r'./doc/將軍澳穿梭巴士時間表.pdf'
working_hr = 9
logging.basicConfig(level=logging.INFO,format='%(levelname)s : %(message)s') # logging.DEBUG show all log, logger.info only show info message
logger = logging.getLogger(__name__)


def timing(f):
    def wrap(*args, **kwargs):
        time1 = time.time()
        ret = f(*args, **kwargs)
        time2 = time.time()
        logger.info(' "{:s}" function runtime {:.3f} s'.format(f.__name__, (time2-time1)))
        return ret
    return wrap

def login() -> any:
    try:
        url = 'https://hrms.hktv.com.hk/api/admin/login'
        data = {'action': 'login', 'fldEmpLoginID': username,
                'fldEmpPwd': password, 'code': 'undefined'}
        response = requests.post(url=url, data=data)
        logging.debug('Login response sent,status={}'.format(
            response.status_code))
        global web_cookie
        web_cookie = response.cookies

    except Exception as e:
        logging.error('Access HR system error')
        traceback.print_exc()
    return


def get_attendance_record() -> dict:

    search_year, search_month, search_day = map(int, time.strftime("%Y %m %d").split())
    # timesheet cutoff is 15th in every month
    if search_day > 15:
        if search_month == 12:
            search_month = 1
            search_year += 1
        else:
            search_month += 1
    try:
        url = "https://hrms.hktv.com.hk/api/Attendance/getpages"
        data = {'page': 1, 'limit': 31,
                'types': 1, 'fldMonth': '{yyyy}-{mm}'.format(yyyy=search_year, mm=search_month), 'fldCatID': '', 'fldBranch': '', 'fldEmpPosition': ''}
        response = requests.get(url=url, cookies=web_cookie, data=data)
        record = response.json()
        logging.debug('Get data response sent,status={}'.format(
            response.status_code))
        return record
    except Exception as e:
        logging.error('Get attendance record error')
        traceback.print_exc()
        return


def logout() -> any:
    try:
        url = 'https://hrms.hktv.com.hk/api/Admin/LogOut'
        response = requests.post(url=url, cookies=web_cookie)
        logging.debug('Logout response sent,status={}'.format(
            response.status_code))
        logging.debug('Logout success')
    except Exception as e:
        logging.error('Logout HR system error')
        traceback.print_exc()
    return


def organize_timetable(tables: TableList) -> tuple[pd.DataFrame, pd.DataFrame]:

    route: pd.DataFrame = tables[0]  # useless route table
    sched: pd.DataFrame = tables[1]
    sched.rename(columns={'開車時間及地點': 'shift', 'Unnamed: 1': 'to_weekday',
                 'Unnamed: 2': 'from_weekday'}, inplace=True)
    del sched['Unnamed: 5'] # delete weekend schedule
    del sched['Unnamed: 6']

    # organize lohas data for weekday only
    lohas_early = sched.loc[2:25]
    lohas_late = sched.loc[36:50]
    lohas_late = lohas_late.drop(columns=['to_weekday', 'from_weekday'])
    lohas_late.rename(columns={'Unnamed: 3': 'to_weekday',
                      'Unnamed: 4': 'from_weekday'}, inplace=True)
    sched_lohas = pd.concat([lohas_early, lohas_late], axis=0)

    # organize tkl data for weekday only
    sched_tkl = sched.loc[28:50]

    del sched_tkl['Unnamed: 3']
    del sched_tkl['Unnamed: 4']
    del sched_lohas['Unnamed: 3']
    del sched_lohas['Unnamed: 4']

    def filter_text(words:str):
        if str(words) != 'nan' and len(words)>3 and "-" not in words:
            t= re.sub(r'[^0-9]', '', words)
            t = datetime.strptime(t, '%H%M').time()
        else:
            t =''
        return t

    
    sched_tkl = sched_tkl.applymap(filter_text)
    sched_lohas = sched_lohas.applymap(filter_text)




    return sched_lohas, sched_tkl


def get_clocktime(record:dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    
    #record={'data':[{'fldDate':"2022-06-21",'fldOriIn1':'09:11'}]} # fake record
    try:
        now = datetime.now()
        attendance_record = [i for i in record['data'] if i['fldDate'] == now.strftime("%Y-%m-%d")]
        
        if attendance_record[0]['fldOriIn1'] != None:
            clockIn = datetime.combine(date(now.year,now.month,now.day),datetime.strptime(attendance_record[0]['fldOriIn1'], '%H:%M').time())
        else:
            logger.info('Attendance no record, Please wait until the HR system update')
            sys.exit()
        
        logger.info('Clock In time = '+str(clockIn))
    except IndexError as e:
        logging.error('No today attendance')
    
    clockOut = clockIn + pd.DateOffset(hours=working_hr)
    logger.info('Clock Out time = '+str(clockOut))

    return clockIn , clockOut

@timing
def main() -> any:
    try:
        logger.info('Current Time : '+datetime.now().strftime("%Y-%m-%d %H:%M"))
        login()
        record = get_attendance_record()
        logout()
        clockIn , clockOut = get_clocktime(record=record)

        tables = get_bus_stop_schedule(pdf_path=pdf_path)
        sched_lohas, sched_tkl = organize_timetable(tables)

        # print("tkl schedule=\n",sched_tkl)
        # print("Lohas schedule=\n",sched_lohas)


        index = sched_tkl['from_weekday'].searchsorted(clockOut.time()) # find index of the row which is nearest to the clock out time
        target_tkl_bus = sched_tkl.iloc[[index]].iloc[0]['from_weekday']
        logger.info('Target bus leave to Tiu Keng Leng = '+str(target_tkl_bus))

        index = sched_lohas['from_weekday'].searchsorted(clockOut.time()) # find index of the row which is nearest to the clock out time
        target_lohas_bus = sched_lohas.iloc[[index]].iloc[0]['from_weekday']
        logger.info('Target bus leave to Lohas Park = '+str(target_lohas_bus))
    except SystemExit as exit:
        logger.debug(exit)
    finally:
        return

if __name__ == "__main__":
    main()        