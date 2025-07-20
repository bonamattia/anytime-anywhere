import os
import pandas as pd
from azure.data.tables import TableServiceClient, UpdateMode
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential

def _get_table_service_client() -> TableServiceClient:
    # 1) primo tentativo: connession string (locale / Azurite)
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING") or os.getenv("AzureWebJobsStorage")
    if conn_str:
        return TableServiceClient.from_connection_string(conn_str)

    # 2) altrimenti siamo in prod: usiamo Managed Identity
    account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL")           # es. https://mioaccount.table.core.windows.net
    client_id   = os.getenv("USER_ASSIGNED_CLIENT_ID") or None     # se non ne hai, lascia vuoto

    if client_id:
        credential = ManagedIdentityCredential(client_id=client_id)
    else:
        credential = DefaultAzureCredential()

    return TableServiceClient(endpoint=account_url, credential=credential)


def save_df_to_azure_table(df: pd.DataFrame, table_name: str):
    svc = _get_table_service_client()
    # se non esiste la tabella, creala
    try:
        svc.create_table(table_name)
    except Exception:
        pass

    tbl = svc.get_table_client(table_name=table_name)
    for _, row in df.iterrows():
        entity = row.to_dict()
        tbl.upsert_entity(mode=UpdateMode.MERGE, entity=entity)
