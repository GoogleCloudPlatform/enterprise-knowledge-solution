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

"""GCS bucket move files function """
import glob
import os

from google.cloud import storage

from common.config import STATUS_SUCCESS
from common.utils.logging_handler import Logger

storage_client = storage.Client()
logger = Logger.get_logger(__name__)

def copy_blob(bucket_name, source_blob_name, destination_blob_name,
    dest_bucket_name=None, delete_original=False):
  dest_bucket_name_str = bucket_name if not dest_bucket_name else dest_bucket_name
  logger.info(f"Copying {source_blob_name} in bucket {bucket_name} to "
              f"{destination_blob_name} inside bucket {dest_bucket_name_str}")
  source_bucket = storage_client.bucket(bucket_name)
  source_blob = source_bucket.blob(source_blob_name)
  if dest_bucket_name is None:
    destination_bucket = storage_client.bucket(bucket_name)
  else:
    destination_bucket = storage_client.bucket(dest_bucket_name)
  blob_copy = source_bucket.copy_blob(source_blob, destination_bucket,
                                      destination_blob_name)
  if delete_original:
    source_bucket.delete_blob(source_blob_name)
  return STATUS_SUCCESS


def move_blob(bucket_name, source_blob_name, destination_blob_name,
    dest_bucket_name=None):
  copy_blob(bucket_name, source_blob_name, destination_blob_name,
            dest_bucket_name=dest_bucket_name, delete_original=True)
  return STATUS_SUCCESS


def upload_file(local_file, bucket_name, prefix):
  assert os.path.isfile(local_file)
  bucket = storage_client.bucket(bucket_name)
  blob = bucket.blob(prefix)
  uri = f"gs://{bucket_name}/{blob.name}"
  print(f"Uploading {local_file} to {uri} ...")
  blob.upload_from_filename(local_file)
  return uri


def upload_dir(local_path, bucket_name, prefix):
  assert os.path.isdir(local_path)
  bucket = storage_client.bucket(bucket_name)
  for local_file in glob.glob(local_path + '/**'):
    if not os.path.isfile(local_file):
      upload_dir(local_file, bucket,
                 prefix + "/" + os.path.basename(local_file))
    else:
      upload_file(local_file, bucket_name, prefix)