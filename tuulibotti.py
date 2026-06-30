import requests
import xml.etree.ElementTree as ET
import os

FMI_API_URL = "https://opendata.fmi.fi/wfs"
FMI_STATION = os.getenv("FMI_STATION")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_wind_data():
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "getFeature",
        "storedquery_id": "fmi::observations::weather::multipointcoverage",
        "fmisid": FMI_STATION
    }

    r = requests.get(FMI_API_URL, params=params)
    root = ET.fromstring(r.content)

    wind_speed = None
    wind_dir = None

    for elem in root.iter():
        if "WindSpeedMS" in elem.tag:
            wind_speed = float(elem.text)
        if "WindDirection" in elem.tag:
            wind_dir = float(elem.text)

    return wind_speed, wind_dir

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})

def main():
    speed, direction = get_wind_data()

    if speed is None:
        return

    if speed > 10:
        send_telegram_message(f"Tuuli {speed} m/s, suunta {direction}°")

if __name__ == "__main__":
    main()
