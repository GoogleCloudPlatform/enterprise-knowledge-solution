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

""" reassign endpoints """
from fastapi import APIRouter, Response, status, HTTPException
from typing import List, Dict
from common.models import Document
from common.db_client import bq_client
from common.utils.format_data_for_bq import format_data_for_bq
from common.utils.stream_to_bq import stream_document_to_bigquery
# from common.utils.copy_gcs_documents import copy_blob
from common.utils.logging_handler import Logger
from common.config import BUCKET_NAME
from common.config import STATUS_IN_PROGRESS, STATUS_SUCCESS, STATUS_ERROR
from common.config import PROCESS_TASK_API_PATH
from google.cloud import storage
# disabling for linting to pass
# pylint: disable = broad-except
import re
import datetime
import requests
from models.reassign import Reassign
import fireo
import traceback

router = APIRouter()
logger = Logger.get_logger(__name__)

@router.post("/reassign_case_id")
async def reassign_case_id(reassign: Reassign, response: Response):
  """
  Reassigns case_id of given document
    Args:
    old_case_id (str): Case id of the supporting
    document which need to be reassigned ,
    uid (str) : unique Id of the supporting document
    new_case_id :existing application form case_id
    user : username of person who is reassigning the document
    comment : comment put by user
    Returns:
      200 : Successfully reassigned the document
      404 :document to be reassign is not found
      404 : new_case_id application not found
      400 : If old case_id and new_case_id is same
      406 : if given document with old case_id is
      application and cannot be reassigned
      500 :  Some unexpected error occurred
    """
  try:
    reassign_dict = reassign.dict()
    uid = reassign_dict.get("uid")
    old_case_id = reassign_dict.get("old_case_id")
    new_case_id = reassign_dict.get("new_case_id")
    user = reassign_dict.get("user")
    comment = reassign_dict.get("comment")

    #Check if the old case_id and new_case_id is same
    #send bad request error
    # if old_case_id == new_case_id:
    #   response.status_code = status.HTTP_400_BAD_REQUEST
    #   response.body = f"The  existing case_id {old_case_id}and new " \
    #               f"case_id {new_case_id} is" \
    #               f" same enter different case_id"
    #   return {"message": response.body}

    document = Document.find_by_uid(uid)
    #If document with given uid does not exist send 404
    # not found error
    if document is None:
      logger.error(f"document to be reassigned with case_id {old_case_id}"
                   f" and uid {uid} does not exist in database")
      response.status_code = status.HTTP_404_NOT_FOUND
      response.body = f"document to be reassigned with case_id {old_case_id} " \
                      f"and uid {uid} does not exist in database"
      return {"message": response.body}

    #if given document with old case_id is application and cannot be
    # reassigned send user response that this file is not acceptable

    new_case_id_document  = Document.collection.filter(case_id=new_case_id).get()
    print("After new case_id check")
    print(f"new_case_id_document: {new_case_id_document}")
    #application with new case case_id does not exist in db
    #send 404 not found error
    if not new_case_id_document:
      logger.error(
          f"Document with case_id {new_case_id} not found for reassign")
      response.status_code = status.HTTP_404_NOT_FOUND
      response.body = f"Application with case_id {new_case_id}" \
      f" does not exist in database to reassigne supporting doc " \
      f"{old_case_id} and uid {uid}"
      return {"message": response.body}

    client = bq_client()
    gcs_source_url = document.url
    document_class = document.document_class
    document_type = document.document_type
    entities = document.entities
    context = document.context
    extraction_score = document.extraction_score

    #remove the prefix of bucket name from gcs_url to get blob name
    prefix_name = f"gs://{BUCKET_NAME}/"
    source_blob_name = re.sub(prefix_name, "", gcs_source_url, 1)
    print(f"source_blob_name: {source_blob_name}")

    #remove the prefix of old_case_id and give new case_id for
    # destination folder in gcs
    destination_blob_name = re.sub(old_case_id, new_case_id, source_blob_name,
                                   1)
    print(f"destination_blob_name: {destination_blob_name}")

    if source_blob_name == destination_blob_name:
      return {"status": STATUS_SUCCESS, "url": document.url}

    status_copy_blob = copy_blob(BUCKET_NAME, source_blob_name,
                                 destination_blob_name)

    # check if moving file in gcs is sucess
    if status_copy_blob != STATUS_SUCCESS:
      response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
      response.body = f"Error in copying files in " \
     f"gcs bucket from source folder {old_case_id},destination" \
          f" {new_case_id} "
      return {"message": response.body}

    print("----------Updating firestore-----------")
    #Update Firestore databse
    document.case_id = new_case_id
    updated_url = prefix_name + destination_blob_name
    document.url = updated_url
    # Update HITL audit trail for reassigned action
    hitl_audit_trail = {
        "status": "reassigned",
        "timestamp": datetime.datetime.utcnow(),
        "user": user,
        "comment": comment,
        "old_case_id": old_case_id,
        "new_case_id": new_case_id,
        "action": f"reassigned from {old_case_id} to {new_case_id}"
    }
    document.hitl_status = fireo.ListUnion([hitl_audit_trail])
    document.update()
    #Update Bigquery database
    entities_for_bq = format_data_for_bq(entities)
    update_bq = stream_document_to_bigquery(client, new_case_id, uid,
                                            document_class, document_type,
                                            entities_for_bq, updated_url,
                                            document.ocr_text,
                                            document.classification_score)
    print("--------firestore db ----------------")
    # status_process_task =
    response_process_task = call_process_task(new_case_id, uid, document_class,
                                              updated_url,
                                              context, extraction_score,
                                              entities)
    if update_bq == [] and response_process_task.status_code == 202:

      logger.info(
          f"ressign case_id from {old_case_id} to {new_case_id} is successfull")
      return {"status": STATUS_SUCCESS, "url": document.url}
    else:
      print("inside else")
      response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
      response.body = "Error in updating bigquery database"

  except Exception as e:
    err = traceback.format_exc().replace("\n", " ")
    logger.error(err)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e


# disabling for linting to pass for blob_copy variable
# pylint: disable = unused-variable
def copy_blob(bucket_name, source_blob_name, destination_blob_name):
  print(f"copy_blob: bucket_name = {bucket_name}")
  print(f"copy_blob: source_blob_name = {source_blob_name}")
  print(f"copy_blob: destination_blob_name = {destination_blob_name}")

  storage_client = storage.Client()
  source_bucket = storage_client.bucket(bucket_name)
  source_blob = source_bucket.blob(source_blob_name)
  destination_bucket = storage_client.bucket(bucket_name)
  source_bucket.copy_blob(source_blob, destination_bucket,
                          destination_blob_name)
  source_bucket.delete_blob(source_blob_name)
  return STATUS_SUCCESS


def call_process_task(case_id: str, uid: str, document_class: str,
                      gcs_uri: str, context: str,
                      extraction_score: float, entities: List[Dict]):
  """
    Starts the process task API after reassign
  """

  data = {
      "case_id": case_id,
      "uid": uid,
      "context": context,
      "gcs_url": gcs_uri,
      "document_class": document_class,
      "extraction_score": extraction_score,
      "extraction_entities": entities
  }
  payload = {"configs": [data]}
  base_url = f"http://upload-service/{PROCESS_TASK_API_PATH}?is_reassign=true"
  logger.info(f"Params for process task {payload}")
  response = requests.post(base_url, json=payload)
  return response
