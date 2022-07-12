
import string
import camelot
from camelot.core import TableList
import pandas as pd
import traceback
import os
import logging



def get_bus_stop_schedule(pdf_path:string='') -> list[pd.DataFrame]:
    sched:list[pd.DataFrame]=[]
    logger:logging=logging.getLogger(__name__)
    try:
        if not os.path.exists(r"doc\route.csv"):
            logger.info('create schedules csv')
            tables = camelot.read_pdf(pdf_path) 
            tables[0].to_csv(r"doc\route.csv")  #save camelot.Table to csv 
            tables[1].to_csv(r"doc\schedule.csv")

        logger.info('schedules csv detected.Get dataframe from csv')
        sched.append(pd.read_csv("doc/route.csv"))
        sched.append(pd.read_csv("doc/schedule.csv"))
        return sched
    except Exception as e:
        logger.error('Get table error')
        traceback.print_exc()
