# anytime-anywhere

project structure

project_root/
│
├── flight_function/
│   ├── __init__.py               <- Azure Function entrypoint
│   ├── function_app.py           <- Your existing logic refactored
│   ├── table_utils.py            <- Utility to insert rows into Azure Table
│
├── shared/
│   ├── amadeus_api.py
│   ├── validation.py
│
├── config/
│   ├── config.json
│
├── .env
├── requirements.txt
├── host.json
└── local.settings.json
