import azure.functions as func
from .function_app import run_flight_offers_job
import logging

app = func.FunctionApp()

@app.schedule(schedule="0 0 */3 * *", arg_name="mytimer", run_on_startup=False, use_monitor=True)
def flight_data_scraper(mytimer: func.TimerRequest) -> None:
    logging.info("✈️ Starting scheduled flight data job")
    run_flight_offers_job()
    logging.info("✅ Finished flight data job")
