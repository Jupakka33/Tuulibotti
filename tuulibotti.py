import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime, timedelta

FMI_API_URL = "https://opendata.fmi.fi/wfs"
FMI_STATION = os.getenv("FMI_STATION")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MIN_SPEED = 3.0
MIN_DIR = 225
MAX_DIR = 315

ALERT_FILE = "last_alert.txt"


def get_last_alert_time():
    if not os.path.exists(ALERT_FILE):
        return None

    try:
        with open(ALERT_FILE, "r") as f:
            ts = f.read().strip()
            return datetime.fromisoformat(ts)
    except:
        return None


def set_last_alert_time():
    now = datetime.utcnow()
    with open(ALERT_FILE, "w") as f:
        f.write(now.isoformat())


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

    # Tallennetaan XML
    with open("fmi_raw.xml", "w", encoding="utf-8") as f:
        f.write(r.text)

    root = ET.fromstring(r.content)

    tuples = None
    for elem in root.iter():
        if elem.tag.endswith("doubleOrNilReasonTupleList"):
            tuples = elem.text.strip().split()
            break

    if not tuples:
        return None, None

    pairs = []
    for i in range(0, len(tuples), 2):
        ws = float(tuples[i])
        wd = float(tuples[i + 1])
        pairs.append((ws, wd))

    return pairs[-1]  # viimeisin mittaus


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})


def main():
    # Ajo vain klo 08–20 Suomen aikaa (UTC+3)
    now = datetime.utcnow() + timedelta(hours=3)
    hour = now.hour

    if hour < 8 or hour >= 20:
        print(f"Kello {hour}:00 — ei ajeta (vain 08–20).")
        return

    speed, direction = get_wind_data()

    if speed is None:
        print("FMI ei palauttanut tuulitietoja.")
        return

    print(f"Tuuli {speed} m/s, suunta {direction}°")

    # Tarkista 3 h hälytysrajoitus
    last_alert = get_last_alert_time()
    if last_alert:
        if datetime.utcnow() < last_alert + timedelta(hours=3):
            print("Hälytys lähetetty alle 3 h sitten — ei uutta hälytystä.")
            return

    # Ehdot: nopeus + suunta
    if speed >= MIN_SPEED and MIN_DIR <= direction <= MAX_DIR:
        msg = (
            f"Keli päällä!\n"
            f"Nopeus: {speed} m/s\n"
            f"Suunta: {direction}° (länsi)\n"
            f"."
        )
        print(msg)
        send_telegram_message(msg)
        set_last_alert_time()
    else:
        print("Ehdot eivät täyttyneet.")


if __name__ == "__main__":
    main()
