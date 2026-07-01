import requests
import xml.etree.ElementTree as ET
import os

FMI_API_URL = "https://opendata.fmi.fi/wfs"
FMI_STATION = os.getenv("FMI_STATION")  # esim. 101004
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TUULIRAJA = 10  # m/s – muuta halutuksi


def get_wind_data():
    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "getFeature",
        "storedquery_id": "fmi::observations::weather::multipointcoverage",
        "fmisid": FMI_STATION,
        "parameters": "ws_10min,wd_10min"
    }

    r = requests.get(FMI_API_URL, params=params)

    # DEBUG: tulostetaan FMI:n XML-vastaus
    print("DEBUG: FMI raw XML (first 2000 chars):")
    print(r.text[:2000])

    root = ET.fromstring(r.content)

    ws_values = None
    wd_values = None

    # Etsi DataBlock, jossa arvot oikeasti ovat
    for elem in root.iter():
        tag = elem.tag.lower()

        if "datablock" in tag and elem.text:
            values = elem.text.strip().split()

            # DataBlock sisältää kaikki parametrit yhtenä rivinä
            # Oletus: viimeiset kaksi arvoa = tuulen nopeus ja suunta
            if len(values) >= 2:
                ws_values = [values[-2]]
                wd_values = [values[-1]]

    if not ws_values:
        return None, None

    latest_ws = float(ws_values[-1])
    latest_wd = float(wd_values[-1]) if wd_values else None

    return latest_ws, latest_wd


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})


def main():
    speed, direction = get_wind_data()

    if speed is None:
        print("FMI ei palauttanut tuulitietoja.")
        send_telegram_message
