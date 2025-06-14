import os
from dotenv import load_dotenv
from amadeus import Client, ResponseError
import csv

# Load environment variables from .env file
load_dotenv()

if __name__ == '__main__':

    client_id = os.getenv('amadeus_api_key')
    client_secret = os.getenv('amadeus_api_secret')

    amadeus = Client(
        client_id=client_id,
        client_secret=client_secret
    )



    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            travelClass=travelClass,
            adults=adults,
            currencyCode=currency,
            max=max_offers
        )

        # Save to CSV
        with open(f'flights_{origin}_{destination}_{departure_date}.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'Price (EUR)', 'Airline', 'Stops', 'Duration',
                'Departure', 'Arrival', 'Upsell', 'Bookable Seats',
                'Fare Basis', 'Branded Fare', 'Total Cabin Bags', 'Total Checked Bags'
            ])

            for offer in response.data:
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
                    total_cabin_bags = cabin_bags_each * adults
                    total_checked_bags = checked_bags_each * adults

                except (KeyError, IndexError):
                    fare_basis = branded_fare = 'N/A'
                    total_cabin_bags = total_checked_bags = 'N/A'

                writer.writerow([
                    price, airline, stops, duration,
                    departure_time, arrival_time, is_upsell, bookable_seats,
                    fare_basis, branded_fare, total_cabin_bags, total_checked_bags
                ])

        print(f"✅ Saved {len(response.data)} flight offers to CSV.")

    except ResponseError as error:
        print("❌ API Error:", error)
