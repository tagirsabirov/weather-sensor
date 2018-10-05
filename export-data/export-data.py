"""
Exports the weather data to a CSV file for Excel analysis from Outlyer.

Usage:
        python3 export-data.py --apikey={PUT OUTLYER API KEY HERE}

@author Tagir Sabirov
"""

from argparse import ArgumentParser
import requests
import time
import csv

METRICS = [
    'accuweather.temp_c',
    'accuweather.wind_speed_kmh',
    'accuweather.windgust_speed_kmh',
    'accuweather.uvindex',
    'accuweather.visibility_km',
    'accuweather.cloudcover_pct',
    'accuweather.cloud_ceiling_m',
    'accuweather.pressure_mb',
    'accuweather.precipitation_mm',
    'pi.wind_speed',
    'pi.pressure',
    'pi.temperature',
    'pi.humidity'
]

class OutlyerAPI(object):

    OUTLYER_API_URL = "https://api2.outlyer.com/v2/accounts/"

    def __init__(self, apiKey:str, account: str):
        self.apiKey = apiKey
        self.account = account

    def queryOutlyerSeries(self, startTime:str, query:str, endTime:str = "now"):
        """
        Sends a reading to Outlyer

        :param data:      Array of samples
        """

        headers = {
            'Authorization': 'Bearer ' + self.apiKey,
            'Content Type': 'application/json',
            'Accepts': 'application/json'
        }

        params = {
            'e': endTime,
            's': startTime,
            'q': query
        }

        resp = requests.get(self.OUTLYER_API_URL + self.account + "/series",
                            headers=headers, params=params)

        if resp.status_code != 200:
            print("ERROR POSTING DATA TO OUTLYER: " + {resp.text})
            return None

        return resp.json()

if __name__ == '__main__':

    # Get command line arguments to get Outlyer API key
    parser = ArgumentParser()
    parser.add_argument("-k", "--apikey", dest="apikey",
                        help="Pass in your Outlyer API Key", required=True)
    parser.add_argument("-a", "--account", dest="account",
                        help="Pass in your Outlyer Account Name", required=True)
    parser.add_argument("-f", "--file", dest="file",
                        help="Path to output CSV File", default='weather_data.csv')

    args = parser.parse_args()
    exporter = OutlyerAPI(args.apikey, args.account)

    print(f"Writing to file {args.file}")

    with open(args.file, "w+") as csvfile:

        csvwriter = csv.writer(csvfile, delimiter=',',
                        quotechar='|', quoting=csv.QUOTE_MINIMAL)

        header = None

        # Get last week of data for each metric
        for metric in METRICS:
            query = f"name,{metric},:eq,:max,:cf-max"
            data = exporter.queryOutlyerSeries("e-1w", query)

            interval = data['interval']
            start = data['start']
            end = data['end']
            values = data['values'][0]

            print(f"{metric}: Downloaded {len(values)} datapoints between "
                  f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start / 1000))} and "
                  f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end / 1000))} "
                  f"every interval {interval / 60000} minutes.")

            # Only write header if first metric
            if not header:
                timestamp = start
                header = ['metric']
                while timestamp <= end:
                    header.append(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp / 1000)))
                    timestamp += interval
                csvwriter.writerow(header)

            # Change None values to empty string values
            row = [metric]
            for value in values:
                if value:
                    row.append(str("%.4f" % round(value,4)))
                else:
                    row.append('')

            csvwriter.writerow(row)
