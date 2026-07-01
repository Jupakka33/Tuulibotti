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

    # ⭐ Tallennetaan XML varmasti oikeaan hakemistoon
    output_path = os.path.join(os.getcwd(), "fmi_raw.xml")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(r.text)

    print(f"DEBUG: FMI XML tallennettu: {output_path}")

    root = ET.fromstring(r.content)

    ws_values = None
    wd_values = None

    # Etsi DataBlock (FMI:n nykyinen formaatti)
    for elem in root.iter():
        tag = elem.tag.lower()

        if "datablock" in tag and elem.text:
            values = elem.text.strip().split()

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
        send_telegram_message("Tuulitietojen lukeminen FMI:ltä epäonnistui.")
        return

    if speed > TUULIRAJA:
        print(f"Tuuli {speed} m/s – ylittää rajan {TUULIRAJA} m/s.")
        send_telegram_message(
            f"Oulu Vihreäsaari: tuuli {speed} m/s, suunta {direction}° (raja {TUULIRAJA} m/s)"
        )
    else:
        print(f"Tuuli {speed} m/s – ei ylitä rajaa {TUULIRAJA} m/s.")


if __name__ == "__main__":
    main()
