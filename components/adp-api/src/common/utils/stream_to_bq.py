"""
Copyright 2022 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

""" Bigquery claim inserts,updates and deletes """
import copy
import json
from .logging_handler import Logger
from common.config import PROJECT_ID, DATABASE_PREFIX, BIGQUERY_DB
import datetime

logger = Logger.get_logger(__name__)


def stream_claim_to_bigquery(client, claim_dict, operation, timestamp):
  table_id = f"{PROJECT_ID}.{DATABASE_PREFIX}rules_engine.claims"
  new_claim_dict = copy.deepcopy(claim_dict)
  del new_claim_dict["document_details"]
  new_claim_dict["operation"] = operation
  new_claim_dict["timestamp"] = timestamp
  new_claim_dict["created_timestamp"] = timestamp
  new_claim_dict["last_updated_timestamp"] = timestamp
  new_claim_dict["all_document_details"] = json.dumps(
      claim_dict.get("document_details"))
  rows_to_insert = [new_claim_dict]
  # Make an API request
  errors = client.insert_rows_json(table_id, rows_to_insert)
  if errors == []:
    logger.info("New rows have been added.")
  elif isinstance(errors, list):
    error = errors[0].get("errors")
    logger.error(f"Encountered errors while inserting rows: {error}")


def delete_claim_in_bigquery(client, claim_id, timestamp):
  table_id = f"{PROJECT_ID}.{DATABASE_PREFIX}rules_engine.claims"
  claim_dict = {"claim_id": claim_id, "operation": "DELETE",
                "timestamp": timestamp, "created_timestamp": timestamp,
                "last_updated_timestamp": timestamp}
  rows_to_insert = [claim_dict]
  # Make an API request
  errors = client.insert_rows_json(table_id, rows_to_insert)
  if not errors:
    logger.info("New rows have been added.")
  elif isinstance(errors, list):
    error = errors[0].get("errors")
    logger.error(f"Encountered errors while inserting rows: {error}")


def stream_document_to_bigquery(client, case_id, uid,
    document_class, document_type, entities,
    gcs_doc_path, ocr_text, classification_score, is_hitl_classified=False):
  """
    Function insert's data in Bigquery database
    Args :
      entity : string format of entries and values
      case_id : str
      uid : str
      document_class : str
      document_type: str
    output :
      if successfully executed : returns []
      if fails : returns error
  """
  table_id = f"{PROJECT_ID}.{DATABASE_PREFIX}{BIGQUERY_DB}"
  logger.info(f"stream_document_to_bigquery case_id={case_id}, uid={uid}, "
              f"document_class={document_class}, document_type={document_type}, "
              f"table_id={table_id}, gcs_doc_path={gcs_doc_path}, "
              f"ocr_text={ocr_text}, classification_score={classification_score},"
              f"is_hitl_classified={is_hitl_classified}")

  now = datetime.datetime.now(datetime.timezone.utc)
  rows_to_insert = [
      {"case_id": case_id,
       "uid": uid,
       "document_class": document_class,
       "document_type": document_type,
       "entities": entities,
       "timestamp": now.strftime('%Y-%m-%d %H:%M:%S.%f'),
       "gcs_doc_path": gcs_doc_path,
       "ocr_text": ocr_text,
       "classification_score": classification_score,
       "is_hitl_classified": is_hitl_classified
       }
  ]
  errors = client.insert_rows_json(table_id, rows_to_insert)
  if not errors:
    logger.info(f"New rows have been added for "
                f"case_id {case_id} and {uid}")
  elif isinstance(errors, list):
    error = errors[0].get("errors")
    logger.error(f"Encountered errors while inserting rows "
                 f"for case_id {case_id} and uid {uid}: {error}")
  return errors
