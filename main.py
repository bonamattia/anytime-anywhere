import pandas as pd
from function_app import flight_scraper
from amadeus import Client, ResponseError
import os

if __name__ == "__main__":
    # df = flight_scraper(return_df=True)
    # if not df.empty:
    #     df.to_csv("flight_offers_debug.csv", index=False)
    #     print("✅ CSV salvato come flight_offers_debug.csv")
    # else:
    #     print("❌ Nessuna offerta trovata.")

    amadeus = Client(
        client_id=os.getenv("AMADEUS_API_KEY"),
        client_secret=os.getenv("AMADEUS_API_SECRET")
    )

    try:
        response = amadeus.shopping.flight_destinations.get(
            origin='FCO',  # Roma (più grande, più risultati)
            departureDate='2025-08-15',  # solo mese → più flessibile
            duration='7-10',
            maxPrice=1000,
            currency='EUR'
        )

        print("✅ Risultati trovati:")
        for item in response.data:
            print(f"{item['origin']} → {item['destination']}, "
                  f"Partenza: {item['departureDate']}, "
                  f"Ritorno: {item.get('returnDate')}, "
                  f"Prezzo: {item['price']['total']} €")
    except ResponseError as e:
        print("❌ Errore:", e)
        print("📄 Codice HTTP:", e.response.status_code)
        print("📦 Corpo risposta:", e.response.body)