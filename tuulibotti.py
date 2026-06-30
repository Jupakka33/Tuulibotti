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
    root = ET.fromstring(r.content)

    ws_values = None
    wd_values = None

    # Etsi multipointcoverage-arvot
    for elem in root.iter():
        tag = elem.tag.lower()

        if "ws_10min" in tag:
            ws_values = elem.text.split()

        if "wd_10min" in tag:
            wd_values = elem.text.split()

    if not ws_values:
        return None, None

    # Uusin mittaus on listan viimeinen
    latest_ws = float(ws_values[-1])
    latest_wd = float(wd_values[-1]) if wd_values else None

    return latest_ws, latest_wd


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})


def main():
    speed, direction = get_wind_data()

    if speed is None:
        send_telegram_message("Tuulitietojen lukeminen FMI:ltä epäonnistui.")
        return

    if speed > TUULIRAJA:
        send_telegram_message(
            f"Oulu Vihreäsaari: tuuli {speed} m/s, suunta {direction}° (raja {TUULIRAJA} m/s)"
        )
    else:
        print(f"Tuuli {speed} m/s — ei yl
