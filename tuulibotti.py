import requests
import xml.etree.ElementTree as ET
import os
from datetime import datetime

FMI_API_URL = "https://opendata.fmi.fi/wfs"
FMI_STATION = os.getenv("FMI_STATION")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MIN_SPEED = 7.0
MIN_DIR = 225
MAX_DIR = 270


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

    # Tallennetaan XML tiedostoksi
    output_path = os.path.join(os.getcwd(), "fmi_raw.xml")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(r.text)

    print(f"DEBUG: FMI XML tallennettu: {output_path}")

    root = ET.fromstring(r.content)

    # Etsi doubleOrNilReasonTupleList
    tuples = None
    for elem in root.iter():
        if elem.tag.endswith("doubleOrNilReasonTupleList"):
            tuples = elem.text.strip().split()
            break

    if not tuples:
        return None, None

    # Muunna arvot pareiksi (nopeus, suunta)
    pairs = []
    for i in range(0, len(tuples), 2):
        ws = float(tuples[i])
        wd = float(tuples[i + 1])
        pairs.append((ws, wd))

    latest_ws, latest_wd = pairs[-1]  # viimeisin mittaus

    return latest_ws, latest_wd


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})


def main():
    # Ajoaika: vain klo 08–20
    now = datetime.utcnow()
    hour = now.hour + 3  # Suomen aika (UTC+3 kesällä)

    if hour < 8 or hour >= 20:
        print(f"Kello {hour}:00 — ei ajeta (vain 08–20).")
        return

    speed, direction = get_wind_data()

    if speed is None:
        print("FMI ei palauttanut tuulitietoja.")
        send_telegram_message("Tuulitietojen lukeminen FMI:ltä epäonnistui.")
        return

    print(f"Tuuli {speed} m/s, suunta {direction}°")

    # Ehdot:
    # 1) Nopeus vähintään 7 m/s
    # 2) Suunta 225–270° (länsi)
    if speed >= MIN_SPEED and MIN_DIR <= direction <= MAX_DIR:
        msg = (
            f"Tuulihälytys!\n"
            f"Nopeus: {speed} m/s\n"
            f"Suunta: {direction}° (länsi)\n"
            f"Ehdot täyttyivät."
        )
        print(msg)
        send_telegram_message(msg)
    else:
        print("Ehdot eivät täyttyneet.")


if __name__ == "__main__":
    main()
