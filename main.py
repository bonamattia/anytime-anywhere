import os
import csv
import json
from dotenv import load_dotenv
from shared.amadeus_api import AmadeusAPI
from shared.validation import FlightSearchConfig
from datetime import datetime
import pytz


# Load environment variables from .env file
load_dotenv()


def load_config(config_path: str, route_key: str) -> FlightSearchConfig:
    """
    Load the flight search configuration for a specific route from the JSON file.
    """
    with open(config_path, 'r') as file:
        config_data = json.load(file)
    if route_key not in config_data:
        raise ValueError(f"Route '{route_key}' not found in configuration file.")
    return FlightSearchConfig(**config_data[route_key])


def save_to_csv(flight_offers, file_name: str):
    """
    Save flight offers to a CSV file with an additional column for the search timestamp.
    """
    rome_tz = pytz.timezone('Europe/Rome')
    search_timestamp = datetime.now(rome_tz).strftime('%Y-%m-%dT%H:%M:%S')  # Current timestamp in Rome timezone

    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            'Research Date', 'Price (EUR)', 'Airline', 'Stops', 'Duration',
            'Departure', 'Arrival', 'Upsell', 'Bookable Seats',
            'Fare Basis', 'Branded Fare', 'Total Cabin Bags', 'Total Checked Bags',
        ])

        for offer in flight_offers:
            price = offer['price']['total']
            airline = offer['validatingAirlineCodes'][0]
            segments = offer['itineraries'][0]['segments']
            stops = len(segments) - 1
            duration = offer['itineraries'][0]['duration']
            departure_time = segments[0]['departure']['at']
            arrival_time = segments[-1]['arrival']['at']
            is_upsell = offer.get('isUpsellOffer', False)
            bookable_seats = offer.get('numberOfBookableSeats', 'N/A')

            try:
                fare_details = offer['travelerPricings'][0]['fareDetailsBySegment'][0]
                fare_basis = fare_details.get('fareBasis', 'N/A')
                branded_fare = fare_details.get('brandedFare', 'N/A')

                # Baggage per person
                cabin_bags_each = fare_details.get('includedCabinBags', {}).get('quantity', 0)
                checked_bags_each = fare_details.get('includedCheckedBags', {}).get('quantity', 0)

                # Multiply by number of travelers
                total_cabin_bags = cabin_bags_each * config.adults
                total_checked_bags = checked_bags_each * config.adults

            except (KeyError, IndexError):
                fare_basis = branded_fare = 'N/A'
                total_cabin_bags = total_checked_bags = 'N/A'

            writer.writerow([
                search_timestamp, price, airline, stops, duration,
                departure_time, arrival_time, is_upsell, bookable_seats,
                fare_basis, branded_fare, total_cabin_bags, total_checked_bags
            ])


if __name__ == '__main__':
    # Load Amadeus API credentials
    client_id = os.getenv('AMADEUS_API_KEY')
    client_secret = os.getenv('AMADEUS_API_SECRET')

    if not client_id or not client_secret:
        raise EnvironmentError("Amadeus API credentials are missing in the environment variables.")

    # Initialize AmadeusAPI
    amadeus_api = AmadeusAPI(client_id=client_id, client_secret=client_secret)

    # Define the route key to search for (e.g., "BLQ-TFS")
    route_key = "BLQ-TFS"

    try:
        # Load the configuration for the specified route
        config = load_config('config/config.json', route_key)

        # Perform the flight search
        flight_offers = amadeus_api.search_flights(config)

        if flight_offers:
            print(f"✅ Found {len(flight_offers)} flight offers for route {route_key}.")
            csv_file_name = f"flights_{config.origin}_{config.destination}_{config.departure_date}.csv"
            save_to_csv(flight_offers, csv_file_name)
            print(f"✅ Saved flight offers to {csv_file_name}.")
        else:
            print(f"❌ No flight offers found for route {route_key}.")

    except Exception as e:
        print(f"❌ An error occurred: {e}")