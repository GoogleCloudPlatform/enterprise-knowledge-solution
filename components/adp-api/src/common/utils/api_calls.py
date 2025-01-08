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

"""
Following methods should be moved away from classification service when switching to pub/sub system 
to eliminate high-coupling between microservices
"""

from typing import Dict
from typing import List

import requests

import common.config
from common.utils.logging_handler import Logger
logger = Logger.get_logger(__name__)



def extract_documents(docs: List[Dict], parser_name: str):
  """Perform extraction for application or supporting documents"""
  logger.info(f"extract_documents with {len(docs)} docs={docs}, "
              f"parser_name={parser_name}")

  extr_result = send_extraction_request(docs, parser_name)

  if extr_result and extr_result.status_code == 200:
    logger.info(f"extract_documents - response received {extr_result}")
  else:
    logger.error(
        f"extraction failed for "
        f"parser_name={parser_name} docs={docs}")


def send_extraction_request(uids: List[Dict], parser_name: str):
  """Call the Extraction API and get the extraction score"""
  try:
    base_url = f"{common.config.get_extraction_service_url()}/extraction_api"
    configs = []
    logger.info(f"send_extraction_request - Received  {len(uids)} uids.")
    for uid in uids:
      config = {"uid": uid}
      configs.append(config)
    payload = {"configs": configs, "parser_name": parser_name}
    logger.info(
        f"send_extraction_request sending to base_url={base_url}, payload={payload}")
    response = requests.post(base_url, json=payload)
    logger.info(f"send_extraction_request response {response} for {payload}")
    return response
  except requests.exceptions.RequestException as err:
    logger.error(err)
