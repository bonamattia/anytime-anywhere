from azure.data.tables import TableServiceClient, UpdateMode
import os


def save_df_to_azure_table(df, table_name: str):
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    service = TableServiceClient.from_connection_string(conn_str)
    table_client = service.get_table_client(table_name=table_name)

    for _, row in df.iterrows():
        entity = row.to_dict()
        table_client.upsert_entity(mode=UpdateMode.MERGE, entity=entity)
