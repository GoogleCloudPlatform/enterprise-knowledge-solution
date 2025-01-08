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

import json
from common.utils.logging_handler import Logger
logger = Logger.get_logger(__name__)

"""
Function to format data to be inserted in BigQuery
"""


def format_data_for_bq(entities):
  """
    Takes list of dictionaries as input and converts it
    for BQ compatible format as string of dictionaries
    Args :
    entity : list of dictionaries
    output : string format of entities and values
  """
  logger.info(f"entities={entities}")
  if entities is not None:
    new_list = []
    for i in entities:
      entity_dict = {"name": i.get("entity"),
                     "value": i.get("value"),
                     "confidence": i.get("extraction_confidence"),
                     "corrected_value": i.get("corrected_value"),
                     "page_no": i.get("page_no")}
      new_list.append(entity_dict)
    # res = dict(ChainMap(*new_list))
    new_json = json.dumps(new_list)
    return new_json
  else:
    return None
