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
        "parameters": "ws
