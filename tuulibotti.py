import requests
import os

CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TOKEN = os.getenv("TELEGRAM_TOKEN")

FMI_URL = (
    "https://opendata.fmi.fi/wfs?"
    "service=WFS&version=2.0.0&request=getFeature&"
    "storedquery_id=fmi::observations::weather::multipointcoverage&"
    "fmisid=101004&parameters=ws_10min"
)

TUULIRAJA = 8  # m/s

def hae_tuuli():
    data = requests.get(FMI_URL).json()
    # Puretaan FMI:n multipointcoverage-rakenne
    ws_values = data["coverage"]["ranges"]["ws_10min"]["value"]
    # Otetaan uusin mittaus
    return ws_values[-1]

def laheta_viesti(teksti):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": teksti})

def main():
    tuuli = hae_tuuli()
    if tuuli > TUULIRAJA:
        laheta_viesti(f"Vihreäsaaren tuuli {tuuli} m/s — ylittää rajan {TUULIRAJA} m/s!")
    else:
        print(f"Tuuli {tuuli} m/s — ei ylitä rajaa.")

if __name__ == "__main__":
    main()


