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


import re
import os
from google.cloud import storage
from common.utils.logging_handler import Logger
from common import models
import pandas as pd

storage_client = storage.Client()
logger = Logger.get_logger(__name__)


def split_uri_2_bucket_prefix(uri: str):
  match = re.match(r"gs://([^/]+)/(.+)", uri)
  if not match:
    # just bucket no prefix
    match = re.match(r"gs://([^/]+)", uri)
    return match.group(1), ""
  bucket = match.group(1)
  prefix = match.group(2)
  return bucket, prefix


def get_id_from_file_path(uri: str):
  match = re.match(r"gs://([^/]+)/([^/]+)/([^/]+)/(.+)", uri)
  if len(match.groups()) < 4:
    return None, None

  bucket = match.group(1)
  case_id = match.group(2)
  uid = match.group(3)
  return case_id, uid


def get_document_by_uri(uri: str):
  case_id, uid = get_id_from_file_path(uri)
  if uid is None:
    logger.error(f"Could not retrieve uid from uri {uri}")
    return None
  db_document = models.Document.find_by_uid(uid)
  if db_document is None:
    logger.error(f"Could not retrieve document by uid {uid} ")

  return db_document


def split_uri_2_path_filename(uri: str):
  dirs = os.path.dirname(uri)
  file_name = os.path.basename(uri)
  return dirs, file_name


def get_processor_location(processor_path):
  m = re.match(r'projects/(.+)/locations/(.+)/processors', processor_path)
  if m and len(m.groups()) >= 2:
    return m.group(2)

  return None


def is_date(string: str):
  """
  Return whether the string can be interpreted as a date.
  """
  try:
    converted = pd.to_datetime(string)
    return True

  except Exception:
    return False

