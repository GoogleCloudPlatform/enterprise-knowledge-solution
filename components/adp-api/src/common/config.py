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
import os
import datetime
import time
from google.cloud import storage
from common.utils.logging_handler import Logger

"""
Config module to setup common environment
"""

logger = Logger.get_logger(__name__)

# ========= Overall =============================
PROJECT_ID = os.environ.get("PROJECT_ID", "")
if PROJECT_ID != "":
  os.environ["GOOGLE_CLOUD_PROJECT"] = PROJECT_ID
assert PROJECT_ID, "Env var PROJECT_ID is not set."

REGION = os.environ.get("REGION", "us-central1")
PROCESS_TIMEOUT_SECONDS = 600

API_DOMAIN = os.getenv("API_DOMAIN")

IAP_SECRET_NAME = os.getenv("IAP_SECRET_NAME", "cda-iap-secret")
USE_EXTERNAL_URL = os.getenv("EXTERNAL", False)

# Doc approval status, will reflect on the Frontend app.
STATUS_APPROVED = "Approved"
STATUS_REVIEW = "Need Review"
STATUS_REJECTED = "Rejected"
STATUS_PENDING = "Pending"
STATUS_IN_PROGRESS = "Processing"

STATUS_PROCESSED = "Processed"
STATUS_SUCCESS = "Complete"
STATUS_ERROR = "Error"
STATUS_SPLIT = "Split"
STATUS_TIMEOUT = "Timeout"

PDF_MIME_TYPE = "application/pdf"

# For inter-process requests
BASE_URL = os.getenv("BASE_URL", "http:/")

DOC_CLASS_SPLIT_DISPLAY_NAME = "Sub-documents"
DOC_TYPE_SPLIT_DISPLAY_NAME = "Package"

# ========= Document upload ======================
BUCKET_NAME = f"{PROJECT_ID}-document-upload"
TOPIC_ID = "queue-topic"
UPLOAD_API_PATH = "/upload_service/v1"
PROCESS_TASK_API_PATH = f"{UPLOAD_API_PATH}/process_task"
DOCUMENT_STATUS_API_PATH = "document_status_service/v1"
EXTRACTION_API_PATH = "extraction_service/v1"
VALIDATION_API_PATH = "validation_service/v1"
MATCHING_API_PATH = "matching_service/v1"

# ========= Validation ===========================
BUCKET_NAME_VALIDATION = PROJECT_ID
PATH = f"gs://{PROJECT_ID}/Validation/rules.json"
PATH_TEMPLATE = f"gs://{PROJECT_ID}/Validation/templates.json"
BIGQUERY_DB = "validation.validation_table"
VALIDATION_TABLE = f"{PROJECT_ID}.validation.validation_table"

CLASSIFIER = "classifier"
CONFIG_BUCKET = os.environ.get("CONFIG_BUCKET")
CONFIG_FILE_NAME = "config.json"
CLASSIFICATION_UNDETECTABLE = "unclassified"
DOCUMENT_TYPE_UNKNOWN = "unknown"

# ===== Start Pipeline ===========================
START_PIPELINE_FILENAME = os.environ.get("START_PIPELINE_NAME",
                                         "START_PIPELINE")


# Global variables
gcs = None
bucket = None
last_modified_time_of_object = datetime.datetime.now()
config_data = None


def init_bucket(bucketname, filename):
  logger.debug(f"init_bucket with bucketname={bucketname}")
  global gcs
  if not gcs:
    gcs = storage.Client()

  global bucket
  if not bucket:
    if bucketname and gcs.get_bucket(bucketname).exists():
      bucket = gcs.get_bucket(bucketname)
    else:
      logger.error(
          f"Error: file does not exist gs://{bucketname}/{filename}")


def load_config(bucketname, filename):
  logger.debug(f"load_config with bucketname={bucketname}")
  global bucket
  if not bucket:
    init_bucket(bucketname, filename)

  blob = bucket.get_blob(filename)
  last_modified_time = blob.updated
  global last_modified_time_of_object
  global config_data
  logger.debug(
      f"last_modified_time_of_object = {last_modified_time_of_object} & last_modified_time = {last_modified_time}")
  if last_modified_time == last_modified_time_of_object:
    return config_data
  else:
    logger.info(
        f"Reloading config from: {filename}")
    try:
      if blob.exists():
        config_data = json.loads(blob.download_as_text(encoding="utf-8"))
        last_modified_time_of_object = last_modified_time
        return config_data
      else:
        logger.error(f"Error: file does not exist gs://{bucketname}/{filename}")
    except Exception as e:
      logger.error(
          f"Error: while obtaining file from GCS gs://{bucketname}/{filename} {e}")
      # Fall-back to local file
      logger.warning(f"load_config - Warning: Using local {filename}")
      json_file = open(
          os.path.join(os.path.dirname(__file__), "config", filename))
      config_data = json.load(json_file)
      return config_data


def get_config(config_name=None):
  start_time = time.time()

  config_data = load_config(CONFIG_BUCKET, CONFIG_FILE_NAME)

  assert config_data, f"get_config - Unable to locate '{config_name} or incorrect JSON file'"

  if config_name:
    config_item = config_data.get(config_name, {})
    logger.debug(f"{config_name}={config_item}")
  else:
    config_item = config_data

  process_time = time.time() - start_time
  time_elapsed = round(process_time * 1000)
  logger.debug(
      f"Retrieving config_name={config_name} took : {str(time_elapsed)} ms")
  return config_item


def get_parser_config():
  return get_config("parser_config")


def get_document_types_config():
  return get_config("document_types_config")


def get_document_type_from_config(doc_class: str):
  doc_type = get_doc_type_by_doc_class(doc_class)
  doc_types = []
  if type(doc_type) == list:
    for d_type in doc_type:
      doc_types.append(d_type)
  return doc_type


def get_docai_warehouse(doc_class):
  doc = get_document_types_config().get(doc_class)
  if not doc:
    logger.error(
        f"doc_class {doc_class} not present in document_types_config")
    return None
  return doc.get("document_ai_warehouse")


def get_parser_by_doc_class(doc_class):
  logger.debug(f"{doc_class}")
  doc = get_document_types_config().get(doc_class)
  if not doc:
    logger.error(
        f"doc_class {doc_class} not present in document_types_config")
    return None

  parser_name = doc.get("parser")
  logger.debug(f"Using doc_class={doc_class}, parser_name={parser_name}")
  return get_parser_config().get(parser_name)


def get_doc_type_by_doc_class(doc_class):
  logger.debug(f"{doc_class}")
  doc = get_document_types_config().get(doc_class)
  if not doc:
    logger.error(
        f"doc_class {doc_class} not present in document_types_config")
    return None

  return doc.get("doc_type")


def get_parser_name_by_doc_class(doc_class):
  logger.debug(f" {doc_class}")
  doc = get_document_types_config().get(doc_class)
  if not doc:
    logger.error(
        f"doc_class {doc_class} not present in document_types_config")
    return None

  parser_name = doc.get("parser")
  logger.debug(f"Using doc_class={doc_class}, parser_name={parser_name}")
  return parser_name


def get_parser_by_name(parser_name):
  return get_parser_config().get(parser_name)


def get_docai_entity_mapping():
  return get_config("docai_entity_mapping")


def get_docai_settings():
  return get_config("settings_config")


# Fall back value (when auto-approval config is not available for the form) - to trigger Need Review State
def get_extraction_confidence_threshold():
  settings = get_docai_settings()
  return float(settings.get("extraction_confidence_threshold", 0.85))


# Fall back value (when auto-approval config is not available for the form) - to trigger Need Review State
def get_extraction_confidence_threshold_per_field():
  settings = get_docai_settings()
  return float(settings.get("field_extraction_confidence_threshold", 0))


# Prediction Confidence threshold for the classifier to reject any prediction
# less than the threshold value.
def get_classification_confidence_threshold():
  settings = get_docai_settings()
  return float(settings.get("classification_confidence_threshold", 0.85))


def get_classification_default_class():
  settings = get_docai_settings()
  classification_default_class = settings.get("classification_default_class",
                                              CLASSIFICATION_UNDETECTABLE)
  parser = get_parser_by_doc_class(classification_default_class)
  if parser:
    return classification_default_class

  logger.warning(
      f"Classification default label {classification_default_class} is not a valid Label or missing a corresponding parser in parser_config")
  return CLASSIFICATION_UNDETECTABLE


def get_document_type(doc_name):
  doc = get_document_types_config().get(doc_name)
  if doc:
    return doc.get("doc_type")
  logger.error(f"doc_type property is not set for {doc_name}")
  return None


def get_display_name_by_doc_class(doc_class):
  if doc_class is None:
    return None

  doc = get_document_types_config().get(doc_class)
  if not doc:
    if doc_class != DOC_CLASS_SPLIT_DISPLAY_NAME:
      logger.warning(
          f"doc_class {doc_class} not present in document_types_config")
    return doc_class

  display_name = doc.get("display_name")
  logger.debug(f"Using doc_class={doc_class}, display_name={display_name}")
  return display_name


def get_document_class_by_classifier_label(label_name):
  for k, v in get_document_types_config().items():
    if v.get("classifier_label") == label_name:
      return k
  logger.error(
      f"classifier_label={label_name} is not assigned to any document in the config")
  return None


# ========= HITL and Frontend UI =======================

# List of database keys and extracted entities that are searchable
DB_KEYS = [
    "active",
    "auto_approval",
    "is_autoapproved",
    "matching_score",
    "case_id",
    "uid",
    "url",
    "context",
    "document_class",
    "document_display_name",
    "upload_timestamp",
    "extraction_score",
    "is_hitl_classified",
]
ENTITY_KEYS = [
    "name",
    "dob",
    "residential_address",
    "email",
    "phone_no",
]

# Misc

# Used by E2E testing. Leave as blank by default.
DATABASE_PREFIX = os.getenv("DATABASE_PREFIX", "")


def get_url(service_name):
  if USE_EXTERNAL_URL:
    return f"{BASE_URL}/{API_DOMAIN}"
  else:
    return f"{BASE_URL}/{service_name}"


def get_document_status_service_url():
  return f"{get_url('document-status-service')}/{DOCUMENT_STATUS_API_PATH}"


def get_extraction_service_url():
  return f"{get_url('extraction-service')}/{EXTRACTION_API_PATH}"


def get_validation_service_url():
  return f"{get_url('validation-service')}/{VALIDATION_API_PATH}"


def get_matching_service_url():
  return f"{get_url('matching-service')}/{MATCHING_API_PATH}"
