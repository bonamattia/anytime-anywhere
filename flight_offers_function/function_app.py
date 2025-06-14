import os
import json
import logging
import pandas as pd
from dotenv import load_dotenv
from shared.validation import FlightSearchConfig
from shared.amadeus_api import AmadeusAPI
from .table_utils import save_df_to_azure_table

# Optional in Azure, but useful locally
load_dotenv()


def offer_to_row(offer: dict, config: FlightSearchConfig) -> dict:
    segments = offer['itineraries'][0]['segments']
    fare_details = offer.get('travelerPricings', [{}])[0].get('fareDetailsBySegment', [{}])[0]

    cabin_bags_each = fare_details.get('includedCabinBags', {}).get('quantity', 0)
    checked_bags_each = fare_details.get('includedCheckedBags', {}).get('quantity', 0)

    return {
        'PartitionKey': f"{config.origin}-{config.destination}",
        'RowKey': offer['id'],
        'DepartureDate': config.departure_date,
        'PriceEUR': offer['price']['total'],
        'Airline': offer['validatingAirlineCodes'][0],
        'Stops': len(segments) - 1,
        'Duration': offer['itineraries'][0]['duration'],
        'Departure': segments[0]['departure']['at'],
        'Arrival': segments[-1]['arrival']['at'],
        'Upsell': offer.get('isUpsellOffer', False),
        'BookableSeats': offer.get('numberOfBookableSeats', 'N/A'),
        'FareBasis': fare_details.get('fareBasis', 'N/A'),
        'BrandedFare': fare_details.get('brandedFare', 'N/A'),
        'TotalCabinBags': cabin_bags_each * config.adults,
        'TotalCheckedBags': checked_bags_each * config.adults
    }


def run_flight_offers_job():
    client_id = os.getenv("amadeus_api_key")
    client_secret = os.getenv("amadeus_api_secret")
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")

    api = AmadeusAPI(client_id=client_id, client_secret=client_secret)

    with open(config_path) as f:
        raw_configs = json.load(f)

    rows = []
    for route_name, route_data in raw_configs.items():
        try:
            config = FlightSearchConfig(**route_data)
            offers = api.search_flights(config)

            if offers:
                for offer in offers:
                    rows.append(offer_to_row(offer, config))
        except Exception as e:
            logging.exception(f"❌ Failed processing route {route_name}: {str(e)}")

    if rows:
        df = pd.DataFrame(rows)
        save_df_to_azure_table(df, os.getenv("AZURE_TABLE_NAME"))
    else:
        logging.info("📭 No rows to save")
