import os
import json
import logging
import pandas as pd
import pytz
from datetime import datetime

import azure.functions as func
from azure.functions import HttpResponse
import datetime

from dotenv import load_dotenv
from pandas import DataFrame

from shared.validation import FlightSearchConfig  # :contentReference[oaicite:0]{index=0}
from shared.amadeus_api import AmadeusAPI
from shared.table_utils import save_df_to_azure_table  # :contentReference[oaicite:1]{index=1}

# Carica le variabili da .env (utile in locale)
load_dotenv()

# Istanza FunctionApp che raccoglie tutti i decorator
app = func.FunctionApp()


# ——————————————————————————————————————————————
# 1️⃣ Timer trigger: ogni lunedì alle 12 e al deploy
# ——————————————————————————————————————————————
@app.function_name(name="ScheduledFlightJob")
@app.schedule(
    schedule="0 12 * * 1",     # secondi|minuti|ore|giorno|mese|weekday
    # schedule="*/1 * * * *",
    # schedule="0 */10 * * * *",
    arg_name="mytimer",
    run_on_startup=True,
    use_monitor=True
)
def scheduled_flight_job() -> None:
    logging.info("⏰ [Timer] Avvio flight_scraper ogni 3 giorni…")
    flight_scraper()
    logging.info("✅ [Timer] Job completato.")


# ——————————————————————————————————————————————
# 2️⃣ HTTP trigger “on-demand”
# ——————————————————————————————————————————————
@app.function_name(name="HttpFlightJob")
@app.route(route="flight-job", methods=["POST"], auth_level=func.AuthLevel.ANONYMOUS)
def http_flight_job() -> HttpResponse:
    logging.info("🔔 [HTTP] Chiamata POST /api/flight-job")
    try:
        flight_scraper()
        return HttpResponse("✅ Flight job eseguito correttamente.", status_code=200)
    except Exception as e:
        logging.exception("❌ Errore durante l'esecuzione del flight job")
        return HttpResponse(f"Errore: {str(e)}", status_code=500)


# ——————————————————————————————————————————————
# 3️⃣ Funzione principale di scraping
# ——————————————————————————————————————————————

def daterange(start_date, end_date):
    for n in range((end_date - start_date).days + 1):
        yield (start_date + datetime.timedelta(days=n)).strftime('%Y-%m-%d')


def flight_scraper(return_df=False) -> DataFrame | None:
    client_id = os.getenv("AMADEUS_API_KEY")
    client_secret = os.getenv("AMADEUS_API_SECRET")
    config_path = os.path.join(os.getcwd(), "config", "config.json")

    api = AmadeusAPI(client_id=client_id, client_secret=client_secret)

    with open(config_path, 'r', encoding='utf-8') as f:
        raw_configs = json.load(f)

    rows = []
    for route_name, route_data in raw_configs.items():
        try:
            start_date = datetime.datetime.strptime(route_data["start_date"], "%Y-%m-%d")
            end_date = datetime.datetime.strptime(route_data["end_date"], "%Y-%m-%d")
            for dep_date in daterange(start_date, end_date):
                route_data["departure_date"] = dep_date
                cfg = FlightSearchConfig(**route_data)
                offers = api.search_flights(cfg)
                if offers:
                    for offer in offers:
                        rows.append(offer_to_row(offer, cfg))
        except Exception as e:
            logging.exception(f"❌ Fallito processing route {route_name}: {e}")
    if rows:
        df = pd.DataFrame(rows)
        if return_df:
            return df
        save_df_to_azure_table(df, os.getenv("AZURE_TABLE_NAME"))
    else:
        logging.info("📭 Nessuna offerta trovata; niente da salvare.")
        if return_df:
            return pd.DataFrame()


# ——————————————————————————————————————————————
# 4️⃣ Helper: da ogni offer ricavo una riga di tabella
# ——————————————————————————————————————————————
def offer_to_row(offer: dict, config: FlightSearchConfig) -> dict:
    segments = offer['itineraries'][0]['segments']
    rome_tz = pytz.timezone('Europe/Rome')
    research_date = datetime.datetime.now(rome_tz).strftime('%Y-%m-%d')

    try:
        fd = offer['travelerPricings'][0]['fareDetailsBySegment'][0]
        fare_basis = fd.get('fareBasis', 'N/A')
        branded_fare = fd.get('brandedFare', 'N/A')
        cabin_each = fd.get('includedCabinBags', {}).get('quantity', 0)
        checked_each = fd.get('includedCheckedBags', {}).get('quantity', 0)
        total_cabin = cabin_each * config.adults
        total_checked = checked_each * config.adults
    except (KeyError, IndexError):
        fare_basis = branded_fare = 'N/A'
        total_cabin = total_checked = 'N/A'

    return {
        'PartitionKey': research_date,
        'RowKey': offer['id'],
        'Route_Name': f"{config.origin}-{config.destination}",
        'Price_EUR': offer['price']['total'],
        'Airline': offer['validatingAirlineCodes'][0],
        'Stops': len(segments) - 1,
        'Duration': offer['itineraries'][0]['duration'],
        'Departure': segments[0]['departure']['at'],
        'Arrival': segments[-1]['arrival']['at'],
        'Upsell': offer.get('isUpsellOffer', False),
        'Bookable_Seats': offer.get('numberOfBookableSeats', 'N/A'),
        'Fare_Basis': fare_basis,
        'Branded_Fare': branded_fare,
        'Total_Cabin_Bags': total_cabin,
        'Total_Checked_Bags': total_checked,
    }
