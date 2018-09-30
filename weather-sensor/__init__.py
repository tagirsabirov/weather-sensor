"""
Measures weather sensors on Raspberry PI and sends the data to Outlyer every
30 seconds

@author Tagir Sabirov
"""
import requests
import time

# Import SPI library (for hardware SPI) and MCP3008 library.
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008

# Import bme280 script
import bme280

# Software SPI configuration for ADC:
CLK  = 18
MISO = 23
MOSI = 24
CS   = 25
mcp = Adafruit_MCP3008.MCP3008(clk=CLK, cs=CS, miso=MISO, mosi=MOSI)

SLEEP_TIME = 30
OUTLYER_API_KEY = ""
OUTLYER_API_URL = "https://api2.outlyer.com/v2/accounts/tagir/series"

def send_to_outlyer(data):
    """
    Sends a reading to Outlyer

    :param data:      Array of samples
    """

    headers = {
        'Authorization': 'Bearer ' + OUTLYER_API_KEY,
        'Content Type': 'application/json',
        'Accepts': 'application/json'
    }

    resp = requests.post(OUTLYER_API_URL, json=data, headers=headers)

    if resp.status_code != 200:
        print("ERROR POSTING DATA TO OUTLYER: " +  {resp.text})

if __name__ == '__main__':
    while True:

        # Read all the ADC channel 1.
        adc_0 = mcp.read_adc(0)
        # 0.4V (125) = 0m/s -> 2.0v (625) = 32.4m/s
        # 500 steps, each step = 0.0648m/s
        wind_speed = (adc_0 - 125) * 0.0648

        # Read BME280 Readings
        temperature, pressure, humidity = bme280.readBME280All()

        # Print readings
        print("Wind Speed: " + str(wind_speed) + "m/s | Pressure: " + str(pressure) + "hPa | Temperature: "
              + str(temperature) + "C | Humidity: " + str(humidity))

        data = {
            'samples': [
                {
                    "host": "raspberry-pi",
                    "labels": {},
                    "name": "pi.wind_speed",
                    "timestamp": int(round(time.time() * 1000)),
                    "ttl": (SLEEP_TIME * 2),
                    "type": "gauge",
                    "value": wind_speed
                },
                {
                    "host": "raspberry-pi",
                    "labels": {},
                    "name": "pi.pressure",
                    "timestamp": int(round(time.time() * 1000)),
                    "ttl": (SLEEP_TIME * 2),
                    "type": "gauge",
                    "value": pressure
                },
                {
                    "host": "raspberry-pi",
                    "labels": {},
                    "name": "pi.temperature",
                    "timestamp": int(round(time.time() * 1000)),
                    "ttl": (SLEEP_TIME * 2),
                    "type": "gauge",
                    "value": temperature
                },
                {
                    "host": "raspberry-pi",
                    "labels": {},
                    "name": "pi.humidity",
                    "timestamp": int(round(time.time() * 1000)),
                    "ttl": (SLEEP_TIME * 2),
                    "type": "gauge",
                    "value": humidity
                },

            ]
        }

        send_to_outlyer(data)

        # Wait
        time.sleep(SLEEP_TIME)