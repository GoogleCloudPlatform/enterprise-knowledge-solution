from typing import Dict
from typing import List
from common.config import STATUS_APPROVED
from common.config import STATUS_REJECTED
from common.config import STATUS_REVIEW
from common.config import STATUS_SUCCESS
from common.autoapproval_config import AUTO_APPROVAL_MAPPING
import requests
import common.config
from common.utils.logging_handler import Logger
from common.config import get_extraction_confidence_threshold
from common.config import get_extraction_confidence_threshold_per_field

logger = Logger.get_logger(__name__)

def update_autoapproval_status(case_id: str, uid: str, a_status: str,
    autoapproved_status: str, is_autoapproved: str):
  """Update auto approval status"""
  base_url = f"{common.config.get_document_status_service_url()}" \
             "/update_autoapproved_status"
  req_url = f"{base_url}?case_id={case_id}&uid={uid}" \
            f"&status={a_status}&autoapproved_status={autoapproved_status}" \
            f"&is_autoapproved={is_autoapproved}"
  response = requests.post(req_url)
  return response


def validate_match_approve(case_id, uid, extraction_score,
    min_extraction_score_per_field,
    extraction_entities, document_class):
  """Perform validation, matching and autoapproval for supporting documents"""
  validation_score = None
  matching_score = None
  validation_res = get_validation_score(case_id, uid, document_class,
                                        extraction_entities)
  if validation_res.status_code == 200:
    print("====Validation successful==========")
    logger.info(f"Validation successful for case_id: {case_id} uid:{uid}.")
    validation_score = validation_res.json().get("score")
    matching_res = get_matching_score(case_id, uid)
    if matching_res.status_code == 200:
      print("====Matching successful==========")
      logger.info(f"Matching successful for case_id: {case_id} uid:{uid}.")
      matching_score = matching_res.json().get("score")
      update_autoapproval(document_class, case_id, uid,
                          validation_score, extraction_score,
                          min_extraction_score_per_field, matching_score)
    else:
      logger.error(f"Matching FAILED for case_id: {case_id} uid:{uid}")
  else:
    logger.error(f"Validation FAILED for case_id: {case_id} uid:{uid}")
  return validation_score, matching_score


def update_extraction_status(case_id: str, uid: str, extraction_status: str,
    entity: list, extraction_score: float,
    extraction_type: str):
  """
    This function calls the document status service
    to update the extraction status in Database
    Args :
     case_id (str)
     uid (str): unique id for  each document
     status (str): success or fail for extraction process
     entity (list):List of dictionary for entities and value
     extraction_score(float): Extraction score for doument
     extraction_type(str): It's the extraction status if
     like duplicate keys present or not
  """

  base_url = f"{common.config.get_document_status_service_url()}/"
  req_url = f"{base_url}update_extraction_status"
  if extraction_status == STATUS_SUCCESS:
    response = requests.post(
        f"{req_url}?case_id={case_id}"
        f"&uid={uid}&status={extraction_status}"
        f"&extraction_score={extraction_score}&"
        f"extraction_status={extraction_type}",
        json=entity)
  else:
    response = requests.post(f"{req_url}?case_id={case_id}"
                             f"&uid={uid}&status={extraction_status}")
  return response


def update_autoapproval(document_class,
    case_id,
    uid,
    validation_score=None,
    extraction_score=None,
    min_extraction_score_per_field=None,
    matching_score=None):
  """Get the autoapproval status and update."""
  autoapproval_status = get_autoapproval_status(validation_score,
                                                extraction_score,
                                                min_extraction_score_per_field,
                                                matching_score, document_class)
  logger.info(f"autoapproval_status for application:{autoapproval_status}\
      for case_id: {case_id} uid:{uid}")
  update_autoapproval_status(case_id, uid, STATUS_SUCCESS,
                             autoapproval_status[0], "yes")


def get_matching_score(case_id: str, uid: str):
  """Call the matching API and get the matching score"""
  base_url = f"{common.config.get_matching_service_url()}/match_document"
  req_url = f"{base_url}?case_id={case_id}&uid={uid}"
  response = requests.post(req_url)
  return response


def get_validation_score(case_id: str, uid: str, document_class: str,
    extraction_entities: List[Dict]):
  """Call the validation API and get the validation score"""
  base_url = f"{common.config.get_validation_service_url()}/validation/" \
             "validation_api"
  req_url = f"{base_url}?case_id={case_id}&uid={uid}" \
            f"&doc_class={document_class}"
  response = requests.post(req_url, json=extraction_entities)
  return response


def get_autoapproval_status(validation_score, extraction_score,
    min_extraction_score_per_field, matching_score,
    document_label):
  """
  Used to calculate the approval status of a document depending on the
  validation, extraction and Matching Score
  Input:
  validation_score : Validation Score
  extraction_score : Extraction Score
  matching_score : Matching Score
  Output:
  status : Accept/Reject or Review
  flag : Yes or no
  """

  def check_scores():
    return (validation_score > v_limit or v_limit == 0) and \
           extraction_score > e_limit and \
           (matching_score > m_limit or m_limit == 0)

  data = AUTO_APPROVAL_MAPPING

  logger.info(
      f"get_autoapproval_status with Validation_Score:{validation_score}, "
      f"Extraction_score: {extraction_score}, "
      f"Extraction_score per field (min): {min_extraction_score_per_field}, "
      f"Matching_Score:{matching_score}"
      f"DocumentLabel:{document_label}")
  flag = "no"

  global_extraction_confidence_threshold = get_extraction_confidence_threshold()
  global_extraction_confidence_threshold_per_field = get_extraction_confidence_threshold_per_field()

  if document_label not in data.keys():
    status = STATUS_REVIEW
    # Use Global Extraction Score
    print(f"Auto-approval is not configured for {document_label}, "
          f"using global_extraction_confidence_threshold={global_extraction_confidence_threshold} "
          f"and global_extraction_confidence_threshold_per_field={global_extraction_confidence_threshold_per_field}")

    if extraction_score > global_extraction_confidence_threshold and \
        min_extraction_score_per_field > global_extraction_confidence_threshold_per_field:
      logger.info(f"Passing threshold configured for Auto-Approve with "
                  f"min_extraction_score_per_field {min_extraction_score_per_field} > "
                  f"{global_extraction_confidence_threshold_per_field} and "
                  f"extraction_score {extraction_score} >"
                  f" {global_extraction_confidence_threshold}")
      flag = "yes"
      status = STATUS_APPROVED

    logger.info(f"Status: {status}")
    return status, flag

  print(f"data[document_label]={data[document_label]}")
  for i in data[document_label]:
    print(
        f"get_autoapproval_status i={i}, data[document_label][i]={data[document_label][i]}")
    v_limit = data[document_label][i].get("Validation_Score", 0)
    e_limit = data[document_label][i].get("Extraction_Score",
                                          global_extraction_confidence_threshold)
    m_limit = data[document_label][i].get("Matching_Score", 0)
    print(
        f"Expected Limits are: v_limit={v_limit}, e_limit={e_limit}, m_limit={m_limit}")

    if i != "Reject":
      if check_scores():
        flag = "yes"
        status = STATUS_APPROVED
        logger.info(f"Status: {status}")
        return status, flag

    else:
      flag = "no"

      if check_scores():
        status = STATUS_REVIEW
        logger.info(f"Status: {status}")
        return status, flag

      else:
        status = STATUS_REJECTED
        logger.info(f"Status: {status}")
      return status, flag

