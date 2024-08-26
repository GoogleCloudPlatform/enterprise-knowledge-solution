from google.api_core.client_options import ClientOptions  # type: ignore
from google.api_core.gapic_v1.client_info import ClientInfo  # type: ignore
from google.cloud import discoveryengine, storage


USER_AGENT = "cloud-solutions/eks-agent-builder-v1"


def import_docs_to_datastore(bq_table, data_store_region, datastore_id):
    client_options = (
        ClientOptions(
            api_endpoint=f"{data_store_region}-discoveryengine.googleapis.com"
        )
        if data_store_region != "global"
        else None
    )
    client = discoveryengine.DocumentServiceClient(
        client_options=client_options,
        client_info=ClientInfo(user_agent=USER_AGENT)
    )
    parent = client.branch_path(
        project=bq_table["project_id"],
        location=data_store_region,  # pyright: ignore[reportArgumentType]
        data_store=datastore_id,
        # pyright: ignore[reportArgumentType]
        branch="default_branch",
    )
    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        bigquery_source=discoveryengine.BigQuerySource(
            project_id=bq_table["project_id"],
            dataset_id=bq_table["dataset_id"],
            table_id=bq_table["table_id"],
            data_schema="document",
        ),
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.INCREMENTAL,
    )
    operation = client.import_documents(request=request)
    response = operation.result()
    metadata = discoveryengine.ImportDocumentsMetadata(operation.metadata)
    print(response)
    print(metadata)
    return operation.operation.name