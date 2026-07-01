import requests
import xml.etree.ElementTree as ET
import os

FMI_API_URL = "https://opendata.fmi.fi/wfs"
FMI_STATION = os.getenv("FMI_STATION")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TUULIRAJA = 10  # m/s


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
    speed, direction = get_wind_data()

    if speed is None:
        print("FMI ei palauttanut tuulitietoja.")
        send_telegram_message("Tuulitietojen lukeminen FMI:ltä epäonnistui.")
        return

    if speed > TUULIRAJA:
        print(f"Tuuli {speed} m/s – ylittää rajan {TUULIRAJA} m/s.")
        send_telegram_message(
            f"Helsinki Kumpula: tuuli {speed} m/s, suunta {direction}° (raja {TUULIRAJA} m/s)"
        )
    else:
        print(f"Tuuli {speed} m/s – ei ylitä rajaa {TUULIRAJA} m/s.")


if __name__ == "__main__":
    main()
