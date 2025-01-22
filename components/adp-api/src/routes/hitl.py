"""
Copyright 2024 Google LLC

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

""" hitl endpoints """
from fastapi import APIRouter, HTTPException, Response
from typing import Optional
from common.models import Document
from common.config import CLASSIFICATION_UNDETECTABLE, DOCUMENT_TYPE_UNKNOWN
from common.utils.logging_handler import Logger
from common.config import BUCKET_NAME, DB_KEYS, ENTITY_KEYS
from common.config import STATUS_APPROVED, STATUS_REVIEW, STATUS_REJECTED, \
  STATUS_PENDING
from common.config import STATUS_IN_PROGRESS, STATUS_SUCCESS, \
  STATUS_SPLIT, STATUS_ERROR, STATUS_TIMEOUT, STATUS_PROCESSED
from common.config import PROCESS_TIMEOUT_SECONDS
from common.config import get_document_types_config, \
  get_display_name_by_doc_class
from google.cloud import storage
import datetime
import requests
import fireo
import traceback
import time
from models.search_payload import SearchPayload
from common.utils.stream_to_bq import stream_document_to_bigquery
from common.db_client import bq_client
# disabling for linting to pass
# pylint: disable = broad-except
from common.utils.format_data_for_bq import format_data_for_bq

logger = Logger.get_logger(__name__)
bq = bq_client()

router = APIRouter()
SUCCESS_RESPONSE = {"status": STATUS_SUCCESS}
FAILED_RESPONSE = {"status": STATUS_ERROR}

PROCESS_NEXT_STAGE = {
    "uploaded": "classifying",
    "classification": "extracting",
    "extraction": "validating",
    "validation": "matching",
    "matching": "Auto-approval checking",
}


def to_camel_case(input_str):
  input_str = input_str.replace("_", "")
  temp = input_str.split(' ')
  res = ' '.join([*map(str.title, temp)])
  return res


def get_doc_list_data(docs_list: list):
  start_time = time.time()

  for doc in docs_list:
    start_time_int = time.time()
    logger.debug(f"get_doc_list_data for {doc['uid']} {doc}")
    # name = "N/A"
    # if doc["entities"]:
    #   for entity in doc["entities"]:
    #     if entity["entity"] == "name":
    #       if entity["corrected_value"]:
    #         name = entity["corrected_value"]
    #       elif entity["value"] is not None:
    #         name = entity["value"]
    # doc["applicant_name"] = name
    # logger.debug(
    #   f"get_doc_list_data - 1. Time elapsed: {str(round((time.time() - start_time_int) * 1000))} ms")
    start_time_int = time.time()

    document_type = doc["document_type"]
    if document_type is None:
      doc["document_type"] = DOCUMENT_TYPE_UNKNOWN

    document_class = doc["document_class"]
    document_display_name = None
    if doc["document_display_name"] is None:
      try:
        logger.debug(
            f"One time action to repair existing documents and set document_display_name for {doc}")
        if document_class is not None:
          document_display_name = get_display_name_by_doc_class(document_class)

        # Keep the Old Logic in case
        if document_display_name is None:
          doc_class = to_camel_case(doc['document_class']) if doc[
                                                                'document_class'] is not None else CLASSIFICATION_UNDETECTABLE
          document_display_name = f"{doc_class}"
        document = Document.find_by_uid(doc["uid"])
        document.document_display_name = document_display_name
        document.update()
        doc["document_display_name"] = document_display_name
        logger.debug(
            f"get_doc_list_data - 2. Time elapsed:  {str(round((time.time() - start_time_int) * 1000))} ms")
        start_time_int = time.time()
      except Exception as e:
        logger.error(
          f"Error while setting document_display_name for {doc} - {e}")

    process_stage = "-"
    current_status = "-"
    status_last_updated_by = "-"
    last_status = None
    last_update_timestamp = None
    last_system_status = ""

    all_status_list = (doc.get("hitl_status", []) or []) + (
        doc.get("system_status", []) or [])
    audit_trail = sorted(all_status_list, key=lambda d: d["timestamp"])
    if audit_trail and len(audit_trail) > 0:
      last_status = audit_trail[-1]
      last_update_timestamp = last_status["timestamp"]
      status_last_updated_by = last_status.get("last_status", "System")

    system_status = doc.get("system_status", None)
    if system_status:
      last_system_status = system_status[-1]
      process_stage = (last_system_status["stage"]).lower()

    hitl_status = doc.get("hitl_status", None)
    last_hitl_status = hitl_status[-1] if hitl_status else None

    logger.debug(
        f"get_doc_list_data - 3. Time elapsed: {str(round((time.time() - start_time_int) * 1000))} ms")
    start_time_int = time.time()
    if doc["system_status"]:
      system_status = doc["system_status"]
      last_system_status = system_status[-1]
      status_last_updated_by = "System"

      # If there's HITL status, use the latest HITL status.
      if doc["hitl_status"]:
        last_hitl_status = doc["hitl_status"][-1]

        if last_system_status["timestamp"] > last_hitl_status["timestamp"]:
          if last_system_status["stage"] == "auto_approval":
            if last_system_status["status"] == STATUS_SUCCESS:
              current_status = doc["auto_approval"].title()
            else:
              current_status = STATUS_IN_PROGRESS
          elif last_system_status["status"] == STATUS_SUCCESS:
            current_status = STATUS_IN_PROGRESS
          else:
            current_status = STATUS_ERROR
        else:
          if last_hitl_status["status"] == "reassigned":
            current_status = STATUS_IN_PROGRESS
          else:
            current_status = last_hitl_status["status"].title()
            status_last_updated_by = last_hitl_status["user"]
            last_update_timestamp = last_hitl_status["timestamp"]

      # Otherwise, check the last system status.
      else:
        # Hack for Split Documents
        if last_system_status["stage"] == "classification" and \
            last_system_status["status"] == STATUS_SPLIT:
          current_status = STATUS_PROCESSED.title()
        elif last_system_status["stage"] == "auto_approval":
          if last_system_status["status"] == STATUS_SUCCESS:
            current_status = doc["auto_approval"].title()
          else:
            current_status = STATUS_REVIEW

        elif last_system_status["status"] == STATUS_SUCCESS:
          current_status = STATUS_IN_PROGRESS
        else:
          current_status = STATUS_ERROR

    logger.debug(
        f"get_doc_list_data - 5. Time elapsed: {str(round((time.time() - start_time_int) * 1000))} ms")
    start_time_int = time.time()
    # Show next stage process status.
    if current_status == STATUS_IN_PROGRESS and process_stage in PROCESS_NEXT_STAGE:
      process_stage = PROCESS_NEXT_STAGE[process_stage.lower()] + "..."

    # Update process detail status
    if current_status == STATUS_IN_PROGRESS:
      time_difference = datetime.datetime.now() - last_update_timestamp.replace(
          tzinfo=None)
      if time_difference.seconds > PROCESS_TIMEOUT_SECONDS:
        process_stage = last_system_status["stage"] + " " + STATUS_TIMEOUT
        current_status = STATUS_ERROR

    else:
      process_stage = process_stage + " " + last_system_status["status"]

    doc["process_status"] = process_stage.title()
    doc["current_status"] = current_status
    doc["status_last_updated_by"] = status_last_updated_by
    doc["last_update_timestamp"] = last_update_timestamp
    doc["audit_trail"] = audit_trail
    # print(f"get_doc_list_data after magic for {doc['uid']} {doc}")

  logger.debug(
      f"get_doc_list_data - Total Time elapsed: {str(round((time.time() - start_time) * 1000))} ms")
  return docs_list


@router.get("/report_data")
async def report_data():
  """ reports all data to user
            the database
          Returns:
              200 : fetches all the data from database
              500 : If any error occurs
    """
  docs_list = []
  try:
    # Fetching only active documents
    start_time = time.time()
    docs_list = list(
        map(lambda x: x.to_dict(),
            Document.collection.filter(active="active").fetch()))
    docs_list = sorted(
        docs_list, key=lambda i: i["upload_timestamp"], reverse=True)
    logger.debug(
      f"Fetched Active Data len={len(docs_list)} in  {str(round((time.time() - start_time) * 1000))} ms")
    docs_list = get_doc_list_data(docs_list)
    logger.debug(
        f"report_data - Time elapsed: {str(round((time.time() - start_time) * 1000))} ms")
    logger.debug(f"report_data docs_list len={len(docs_list)}")
    response = {"status": STATUS_SUCCESS, "len": len(docs_list),
                "data": docs_list}
    logger.info(
        f"report_data - Time elapsed: {str(round((time.time() - start_time) * 1000))} ms")
    return response

  except Exception as e:
    print(e)
    logger.error(e)
    err = traceback.format_exc().replace("\n", " ")
    logger.error(err)
    raise HTTPException(
        status_code=500, detail="Error in fetching documents") from e


@router.post("/get_document")
async def get_document(uid: str):
  """ Returns a single document to user using uid from the database
        Args : uid - Unique ID for every document
        Returns:
          200 : Fetches a single document from database
          500 : If any error occurs
    """
  try:
    doc = Document.find_by_uid(uid)
    if not doc or not doc.to_dict()["active"] == "active":
      response = {"status": STATUS_ERROR}
      response["detail"] = "No Document found with the given uid"
      return response
    response = {"status": STATUS_SUCCESS}
    docs = get_doc_list_data([doc.to_dict()])
    response["data"] = docs[0]
    return response

  except Exception as e:
    print(e)
    logger.error(e)
    err = traceback.format_exc().replace("\n", " ")
    logger.error(err)
    raise HTTPException(
        status_code=500, detail="Error in fetching documents") from e


@router.post("/get_queue")
async def get_queue(hitl_status: str):
  """
  Fetches a queue of all documents with the same hitl status
  (approved,rejected,review or pending) from firestore
  Args: hitl_queue - status of the required queue
  Returns:
    200 : Fetches a list of documents with the same status from Firestore
    400 : If hitl_status is invalid
    500 : If there is any error during fetching from firestore
  """

  # Filter function to filter based on current document status
  def filter_status(item):
    return item["current_status"] == hitl_status

  if hitl_status.lower() not in [
      STATUS_APPROVED.lower(),
      STATUS_REJECTED.lower(),
      STATUS_PENDING.lower(),
      STATUS_REVIEW.lower()
  ]:
    raise HTTPException(status_code=400, detail="Invalid Parameter")
  try:
    # Fetching documents and converting to list of dictionaries
    docs = list(
        map(lambda x: x.to_dict(),
            Document.collection.filter(active="active").fetch()))

    # Adding keys like process_status, current_status filtering on current_status
    # And sorting by upload_timestamp in descending order

    result_queue = get_doc_list_data(docs)
    result_queue = filter(filter_status, result_queue)
    result_queue = sorted(
        result_queue, key=lambda i: i["upload_timestamp"], reverse=True)
    logger.debug(f"get_queue result_queue={result_queue}")

    response = {"status": STATUS_SUCCESS, "len": len(result_queue),
                "data": result_queue}
    return response

  except Exception as e:
    print(e)
    logger.error(e)
    err = traceback.format_exc().replace("\n", " ")
    logger.error(err)
    raise HTTPException(
        status_code=500, detail="Error during fetching from Firestore") from e


@router.post("/update_entity")
async def update_entity(uid: str, updated_doc: dict):
  """
    Updates the entity values
    Args : uid - unique id,
    updated_doc - document with updated values in entities field
    Returns 200 : Update was successful
    Returns 500 : If something fails
  """
  try:
    logger.info(f"update_entity with uid={uid}, updated_doc={updated_doc}")
    doc = Document.find_by_uid(uid)
    if not doc or not doc.to_dict()["active"].lower() == "active":
      response = {"status": STATUS_ERROR,
                  "detail": "No Document found with the given uid"}
      return response
    doc.entities = updated_doc["entities"]
    logger.info(f"entities={updated_doc['entities']}")
    doc.update()
    client = bq_client()

    entities = format_data_for_bq(updated_doc["entities"])
    bq_update_status = stream_document_to_bigquery(client,
                                                   updated_doc["case_id"], uid,
                                                   updated_doc[
                                                     "document_class"],
                                                   updated_doc[
                                                     "document_type"],
                                                   entities,
                                                   updated_doc["url"],
                                                   updated_doc["ocr_text"],
                                                   updated_doc[
                                                     "classification_score"],
                                                   updated_doc["is_hitl_classified"])
    if not bq_update_status:
      logger.info(f"returned status {bq_update_status}")
    else:
      logger.error(
          f"Failed streaming to BQ,  returned status {bq_update_status}")
      return {"status": FAILED_RESPONSE}

    return {"status": STATUS_SUCCESS}

  except Exception as e:
    print(e)
    logger.error(e)
    err = traceback.format_exc().replace("\n", " ")
    logger.error(err)
    raise HTTPException(
        status_code=500, detail="Unable to update entity") from e


@router.post("/update_hitl_status")
async def update_hitl_status(uid: str,
    status: str,
    user: str,
    comment: Optional[str] = ""):
  """
    Updates the HITL status
    Args : uid - unique id,status - hitl status,
    user-username, comment - notes or comments by user
    Returns 200 : Update was successful
    Returns 500 : If something fails
  """
  if status.lower() not in [
      STATUS_APPROVED.lower(),
      STATUS_REJECTED.lower(),
      STATUS_PENDING.lower(),
      STATUS_REVIEW.lower()
  ]:
    raise HTTPException(status_code=400, detail="Invalid Parameter")
  try:
    timestamp = datetime.datetime.utcnow()
    print(timestamp)
    hitl_status = {
        "timestamp": timestamp,
        "status": status,
        "user": user,
        "comment": comment
    }

    doc = Document.find_by_uid(uid)
    if not doc or not doc.to_dict()["active"].lower() == "active":
      response = {"status": STATUS_ERROR}
      response["detail"] = "No Document found with the given uid"
      return response
    if doc:
      # create a list push the latest status and update doc
      doc.hitl_status = fireo.ListUnion([hitl_status])
      doc.is_autoapproved = "no"
      doc.update()
    return {"status": STATUS_SUCCESS}

  except Exception as e:
    print(e)
    logger.error(e)
    err = traceback.format_exc().replace("\n", " ")
    logger.error(err)
    raise HTTPException(
        status_code=500, detail="STATUS_ERROR to update hitl status") from e


def get_file_from_bucket(case_id: str,
    uid: str,
    download: Optional[bool] = False):
  storage_client = storage.Client()
  # listing out all blobs with case_id and uid
  blobs = storage_client.list_blobs(
      BUCKET_NAME, prefix=case_id + "/" + uid + "/", delimiter="/")

  target_blob = None
  # Selecting the last blob which would be the pdf file
  for blob in blobs:
    target_blob = blob

  # If file is not found raise 404
  if target_blob is None:
    return None, None

  filename = target_blob.name.split("/")[-1]
  # Downloading the pdf file into a byte string
  return_data = target_blob.download_as_bytes()

  # Checking for download flag and setting headers
  headers = None
  if download:
    headers = {"Content-Disposition": "attachment;filename=" + filename}
  else:
    headers = {"Content-Disposition": "inline;filename=" + filename}
  return (return_data, headers)


@router.get("/fetch_file")
async def fetch_file(case_id: str, uid: str, download: Optional[bool] = False):
  """
  Fetches and returns the file from GCS bucket
  Args : case_id : str, uid : str
  Returns 200: returns the file and displays it
  Returns 404: Document not found
  Returns 500: If something fails
  """
  try:
    return_data, headers = get_file_from_bucket(case_id, uid, download)
    if return_data is None and headers is None:
      raise FileNotFoundError
    return Response(
        content=return_data, headers=headers, media_type="application/pdf")

  except FileNotFoundError as e:
    print(e)
    logger.error(e)
    err = traceback.format_exc().replace("\n", " ")
    logger.error(err)
    raise HTTPException(
        status_code=404, detail="Requested file not found") from e

  except Exception as e:
    print(e)
    logger.error(e)
    err = traceback.format_exc().replace("\n", " ")
    logger.error(err)
    raise HTTPException(
        status_code=500,
        detail="Couldn't fetch the requested file.\
          Try checking if the case_id and uid are correct") from e


@router.get("/get_unclassified")
async def get_unclassified():
  """
  Fetches a queue of all unclassified documents
  Returns:
    200 : Fetches a list of documents with the same status from Firestore
    500 : If there is any error during fetching from firestore
  """
  try:
    docs = list(
        map(lambda x: x.to_dict(),
            Document.collection.filter(active="active").fetch()))
    result_queue = []
    for doc_dict in docs:
      system_trail = doc_dict.get("system_status")
      if system_trail and system_trail[-1]["stage"].lower() == "classification":
        if system_trail[-1]["status"] != STATUS_SUCCESS:
          result_queue.append(doc_dict)
    response = {"status": STATUS_SUCCESS}
    result_queue = get_doc_list_data(result_queue)
    result_queue = sorted(
        result_queue, key=lambda i: i["upload_timestamp"], reverse=True)
    response["len"] = len(result_queue)
    response["data"] = result_queue
    logger.info(f"get_unclassified result_queue={result_queue}")
    return response
  except Exception as e:
    logger.error(e)
    err = traceback.format_exc().replace("\n", " ")
    logger.error(err)
    raise HTTPException(
        status_code=500,
        detail="Error during getting unclassified documents") from e


def update_classification_status(case_id: str,
    uid: str,
    status: str,
    document_class: Optional[str] = None):
  """ Call status update api to update the classification output
    Args:
    case_id (str): Case id of the file ,
     uid (str): unique id for  each document
     status (str): status success/failure depending on the validation_score

    """
  base_url = "http://document-status-service/document_status_service" \
             "/v1/update_classification_status"

  if status == STATUS_SUCCESS:
    req_url = f"{base_url}?case_id={case_id}&uid={uid}" \
              f"&status={status}&is_hitl={True}&document_class={document_class}"
    response = requests.post(req_url)
    return response

  else:
    req_url = f"{base_url}?case_id={case_id}&uid={uid}" \
              f"&status={status}"
    response = requests.post(req_url)
    return response


def call_process_task(case_id: str, uid: str, document_class: str, gcs_uri: str,
    context: str):
  """
    Starts the process task API after hitl classification
  """

  data = {
      "case_id": case_id,
      "uid": uid,
      "gcs_url": gcs_uri,
      "document_class": document_class,
      "context": context
  }
  payload = {"configs": [data]}
  base_url = f"http://upload-service/upload_service/v1/process_task" \
             f"?is_hitl={True}"
  print("params for process task", base_url, payload)
  logger.info(f"Params for process task {payload}")
  response = requests.post(base_url, json=payload)
  return response


@router.post("/update_hitl_classification")
async def update_hitl_classification(case_id: str, uid: str,
    document_class: str, document_type: str = None):
  """
  Updates the hitl classification status flag and doc type and doc class in DB
  and starts the process task
  Args : case_id : str, uid : str
  Returns 200: updates the DB and starts process task
  Returns 400: Invalid Parameters
  Returns 404: Document not found
  Returns 500: If something fails
  """
  try:
    logger.info(
      f"update_hitl_classification with case_id={case_id}, uid={uid}, document_class={document_class}")
    doc = Document.find_by_uid(uid)

    if document_type and document_type != doc.document_type:
      doc.document_type = document_type
      doc.update()
      entities_for_bq = format_data_for_bq(doc.entities)
      bq_update_status = stream_document_to_bigquery(bq, case_id, uid,
                                                     doc.document_class,
                                                     document_type,
                                                     entities_for_bq, doc.url,
                                                     doc.ocr_text,
                                                     doc.classification_score,
                                                     doc.is_hitl_classified)
      if not bq_update_status:
        logger.info(
            f"extraction_api - Successfully streamed data to BQ ")
      else:
        logger.error(
            f"extraction_api - Failed streaming to BQ, returned status {bq_update_status}")

    if doc.document_class != document_class:
      logger.debug(doc.to_dict()["active"].lower())
      if not doc or not doc.to_dict()["active"].lower() == "active":
        logger.error("Document for hitl classification not found")
        raise HTTPException(status_code=404, detail="Document not found")

      document_types_config = get_document_types_config()
      if document_class not in document_types_config.keys():
        logger.error(f"Invalid parameter document_class {document_class}")
        raise HTTPException(
            status_code=400, detail="Invalid Parameter. Document class")

      logger.info(f"Starting manual classification for case_id" \
                  f" {case_id} and uid {uid}")

      # Update DSM
      logger.info("Updating Doc status from Hitl classification for case_id" \
                  f"{case_id} and uid {uid}")
      response = update_classification_status(
          case_id,
          uid,
          STATUS_SUCCESS,
          document_class=document_class
      )
      logger.debug(response)
      if response.status_code != 200:
        logger.error(f"Document status update failed for {case_id} and {uid}")
        raise HTTPException(
            status_code=500, detail="Document status update failed")

      # Call Process task
      logger.info("Starting Process task from hitl classification")
      res = call_process_task(case_id, uid, document_class,
                              doc.url, doc.context)
      if res.status_code == 202:
        return {
            "status": STATUS_SUCCESS,
            "message": "Process task api has been started successfully"
        }

  except HTTPException as e:
    print(e)
    logger.error(e)
    err = traceback.format_exc().replace("\n", " ")
    logger.error(err)
    raise e

  except Exception as e:
    print(e)
    logger.error(e)
    err = traceback.format_exc().replace("\n", " ")
    logger.error(err)
    raise HTTPException(
        status_code=500,
        detail="Couldn't update the classification.\
          Try checking if the case_id and uid are correct") from e


def compare_value(entity, term, entity_key):
  if entity["entity"] == entity_key:

    if isinstance(term, str):
      if entity["corrected_value"] is not None:
        if isinstance(entity["corrected_value"], str):
          return term.lower() in entity["corrected_value"].lower()
        else:
          return False

      else:
        if entity["value"] is not None:
          if isinstance(entity["value"], str):
            return term.lower() in entity["value"].lower()
          else:
            return False
        else:
          return False

    else:
      if entity["corrected_value"] is not None:
        return term == entity["corrected_value"]

      else:
        if entity["value"] is not None:
          return term == entity["value"]
        else:
          return False

  else:
    return False


@router.post("/search")
async def search(search_term: SearchPayload):
  """
  Searches for documents that include the search term in the keys
  present in config
  Args :search_term : SearchPayload
  Returns 200: searches and returns the list of documents
  Returns 400: Invalid Parameters
  Returns 422: Filter key is not filterable(Not present in Config)
  Returns 500: If something fails
  """

  try:
    filter_key = search_term.filter_key
    filter_value = search_term.filter_value
    term = search_term.term
    limit_start = search_term.limit_start
    limit_end = search_term.limit_end

    docs_list = []

    if filter_key is not None and filter_value is not None:
      if not isinstance(filter_key, str):
        raise HTTPException(
            status_code=400,
            detail="Invalid Parameter type.\
              Filter key should be of type string")
      if filter_key in DB_KEYS:
        docs_list = list(
            map(
                lambda x: x.to_dict(),
                Document.collection.filter(active="active").filter(
                    filter_key, "==", filter_value).fetch()))
        docs_list = sorted(
            docs_list, key=lambda i: i["upload_timestamp"], reverse=True)
        if term is None:
          if limit_start is not None and limit_end is not None:
            if not isinstance(limit_start, int) or not isinstance(
                limit_end, int):
              raise HTTPException(
                  status_code=400,
                  detail="Invalid Parameter type.\
                    Limit start and end should be of type int")
            docs_list = docs_list[limit_start:limit_end]
          docs_list = get_doc_list_data(docs_list)
          return {
              "status": STATUS_SUCCESS,
              "len": len(docs_list),
              "data": docs_list
          }
      else:
        raise HTTPException(
            status_code=422, detail="Entered key is not filterable")

    elif term is None:
      raise HTTPException(status_code=400, detail="Search term not found")

    else:
      docs_list = list(
          map(lambda x: x.to_dict(),
              Document.collection.filter(active="active").fetch()))
      docs_list = sorted(
          docs_list, key=lambda i: i["upload_timestamp"], reverse=True)
    resultset = []

    for doc in docs_list:
      for db_key in DB_KEYS:
        if doc in resultset:
          break
        if doc[db_key] is not None:
          if isinstance(term, str) and isinstance(doc[db_key], str):
            if term.lower() in doc[db_key].lower():
              resultset.append(doc)
              break
          else:
            if term == doc[db_key]:
              resultset.append(doc)
              break

      entities = doc.get("entities", None)
      if doc in resultset or entities is None:
        continue
      for entity_key in ENTITY_KEYS:
        temp = [
            doc for entity in entities
            if compare_value(entity, term, entity_key)
        ]
        if len(temp) > 0:
          resultset.extend(temp)
          temp.clear()
          break

    if limit_start is not None and limit_end is not None:
      resultset = resultset[limit_start:limit_end]
    resultset = get_doc_list_data(resultset)
    return {"status": STATUS_SUCCESS, "len": len(resultset), "data": resultset}

  except HTTPException as e:
    print(e)
    logger.error(e)
    err = traceback.format_exc().replace("\n", " ")
    logger.error(err)
    raise e

  except Exception as e:
    print(e)
    logger.error(e)
    err = traceback.format_exc().replace("\n", " ")
    logger.error(err)
    raise HTTPException(
        status_code=500, detail="Error occurred in search") from e
