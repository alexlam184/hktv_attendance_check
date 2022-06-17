import time
import pandas as pd
import numpy as np
import requests
import base64

username = base64.b64encode(b'alam')
password = base64.b64encode(b'HKTV-123')


def login():
    cookies = {'enwiki_session': '17ab96bd8ffbe8ca58a78657a918558'}
    print("username={},password={}".format(username,password))



    return



def main():
    login()
    return
    

if __name__ == "__main__":
    main()
