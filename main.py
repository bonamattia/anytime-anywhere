import pandas as pd
from function_app import flight_scraper

if __name__ == "__main__":
    df = flight_scraper(return_df=True)
    if not df.empty:
        df.to_csv("flight_offers_debug.csv", index=False)
        print("✅ CSV salvato come flight_offers_debug.csv")
    else:
        print("❌ Nessuna offerta trovata.")