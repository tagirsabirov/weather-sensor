#!/usr/bin/env python3

import sys
import requests
import json
import sqlite3

from outlyer_plugin import Plugin, Status


class AccuweatherPlugin(Plugin):
    ACCUWEATHER_API_URL = "http://dataservice.accuweather.com/currentconditions/v1/"

    def collect(self, _):

        apikey = self.get('apikey')
        location = self.get('location')

        if not apikey:
            self.logger.error("ERROR: Must provide an apikey for Accuweather APIs")
            return Status.UNKNOWN
        if not location:
            self.logger.error("ERROR: Must provide a location for the Accuweather APIs")
            return Status.UNKNOWN

        data = self.get_data(location, apikey)
        labels = {
            'location': location
        }

        self.gauge('accuweather.temp_c', labels).set(data[0]['Temperature']['Metric']['Value'])
        self.gauge('accuweather.wind_speed_kmh', labels).set(data[0]['Wind']['Speed']['Metric']['Value'])
        self.gauge('accuweather.windgust_speed_kmh', labels).set(data[0]['WindGust']['Speed']['Metric']['Value'])
        self.gauge('accuweather.uvindex', labels).set(data[0]['UVIndex'])
        self.gauge('accuweather.visibility_km', labels).set(data[0]['Visibility']['Metric']['Value'])
        self.gauge('accuweather.cloudcover_pct', labels).set(data[0]['CloudCover'])
        self.gauge('accuweather.cloud_ceiling_m', labels).set(data[0]['Ceiling']['Metric']['Value'])
        self.gauge('accuweather.pressure_mb', labels).set(data[0]['Pressure']['Metric']['Value'])
        self.gauge('accuweather.precipitation_mm', labels).set(
            data[0]['PrecipitationSummary']['Precipitation']['Metric']['Value'])

        return Status.OK

    def get_data(self, location, apikey):
        """
        Gets JSON data either from local SQLite DB or from APIs directly
        depending on how recent the local data is. If older than 30 mins it
        will refetch and update the data, otherwise use local data.

        :param location:		Accuweather location code
        :param apikey:		Accuweather API Key
        :return: 				JSON Data Response if successful
        """

        # Open SQLite Database for writing - We can only make 50 calls for free a day
        # so we stash the response locally and only update every 30 minutes
        db_file_path = self.get('db_file_path', '/tmp/accuweather.db')
        db = sqlite3.connect(db_file_path)
        # Create a table to store last weather data
        db.execute('''CREATE TABLE IF NOT EXISTS weather
                       (location TEXT PRIMARY KEY, json TEXT, modified INTEGER)''')

        # Check to see if a response has already been saved in last 30 mins
        c = db.cursor()
        local = (location,)
        c.execute("SELECT * FROM weather WHERE location==? AND modified > datetime('now','-30 minutes')", local)
        data = c.fetchone()
        if data:
            self.logger.info(f"Got data from local database last updated on {data[2]}")
            return json.loads(data[1])
        else:
            data = self.get_accuweather_data(location, apikey)
            insert_data = (location, json.dumps(data))
            c.execute("INSERT OR REPLACE INTO weather (location,json,modified) VALUES(?,?,datetime('now'))",
                      insert_data)
            db.commit()
            return data

    def get_accuweather_data(self, location, apikey):
        """
        Makes API Request to Accuweather APIs

        :param location:		Accuweather location code
        :param apikey:		Accuweather API Key
        :return: 				JSON Data Response if successful
        """

        params = {
            'apikey': apikey,
            'language': 'en-us',
            'details': 'true'
        }

        resp = requests.get(self.ACCUWEATHER_API_URL + location, params=params)

        if resp.status_code != 200:
            self.logger.error("ERROR Calling Accuweather APIs: {resp.text}")
            sys.exit(Status.UNKNOWN.value)
        else:
            self.logger.info(f"Successfully got current weather data for location {location}: {resp.json()}")

        return resp.json()


if __name__ == '__main__':
    # To run the collection
    sys.exit(AccuweatherPlugin().run())