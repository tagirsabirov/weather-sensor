"""
Measures weather sensors on Raspberry PI and sends the data to Outlyer every
30 seconds

@author Tagir Sabirov
"""
import requests
import psutil
import time
import json

SLEEP_TIME = 30
OUTLYER_API_KEY = ""
OUTLYER_API_URL = "https://api2.outlyer.com/v2/accounts/tagir/series"

def send_to_outlyer(metric:str , reading:float):
    """
    Sends a reading to Outlyer

    :param metric:      The name of the metric in Outlyer
    :param reading:     The reading value to send
    """
    print(f"recieved reading for {metric}: {reading}")

    headers = {
        'Authorization': 'Bearer ' + OUTLYER_API_KEY,
        'Content Type': 'application/json',
        'Accepts': 'application/json'
    }

    data = {
        'samples': [
            {
                "host": "raspberry-pi",
                "labels": {},
                "name": metric,
                "timestamp": int(round(time.time() * 1000)),
                "ttl": (SLEEP_TIME * 2),
                "type": "gauge",
                "value": reading
            }
        ]
    }

    resp = requests.post(OUTLYER_API_URL, json=data, headers=headers)

    if resp.status_code != 200:
        print(f"ERROR POSTING DATA TO OUTLYER: {resp.text}")

if __name__ == '__main__':
    while True:
        cpu_usage = psutil.cpu_percent()
        send_to_outlyer("sys.cpu.pct", cpu_usage)

        # Wait
        time.sleep(SLEEP_TIME)


