import logging
from typing import Optional, List
from amadeus import Client, ResponseError
from shared.validation import FlightSearchConfig  # assuming in same dir or update path

logging.basicConfig(level=logging.INFO)


class AmadeusAPI:
    def __init__(self, client_id: str, client_secret: str, client: Optional[Client] = None):
        self.amadeus = client or Client(
            client_id=client_id,
            client_secret=client_secret
        )

    def search_flights(self, config: FlightSearchConfig) -> Optional[List[dict]]:
        try:
            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=config.origin,
                destinationLocationCode=config.destination,
                departureDate=config.departure_date,
                travelClass=config.travel_class,
                adults=config.adults,
                currencyCode=config.currency,
                max=config.max_offers
            )
            return response.data
        except ResponseError as error:
            logging.error("API Error: %s", error)
            return None
