# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Optional
from google.cloud import storage
from google.api_core.client_info import ClientInfo
import json

class GCSDoc:
    def __init__(self, source_doc_uri: str):
        self.bucket_name, self.blob_name = GCSDoc.extract_bucket_and_blob_name(source_doc_uri)
    
    def get_doc_name(self):
        return self.blob_name.split(r'/')[-1]
    
    def get_doc_type(self):
        return self.get_doc_name().split(r'.')[-1]
  
    @staticmethod
    def extract_bucket_and_blob_name(doc_uri: str):
        """split document uri into bucket and blob_name and file"""
        parts = doc_uri.replace(r"gs://", "").split(r"/")
        bucket_name = parts[0]
        blob_name = "/".join(parts[1:])
        return bucket_name, blob_name

class MoveDoc:
    def __init__(self, source_doc_uri: str, destination_folder_ful_uri: str, move_info: str=""):
        self.source_doc = GCSDoc(source_doc_uri)
        self.dest_doc = GCSDoc(f'{destination_folder_ful_uri}/{self.source_doc.get_doc_name()}')
        self.move_info = move_info
    
    def move(self):
        source_bucket = BucketRegistry.get_bucket(self.source_doc.bucket_name)
        source_blob = source_bucket.blob(self.source_doc.blob_name)
        destination_bucket = BucketRegistry.get_bucket(self.dest_doc.bucket_name)
        source_bucket.copy_blob(source_blob, destination_bucket, self.dest_doc.blob_name)
        if self.move_info:
            destination_bucket.blob(f'{self.dest_doc.blob_name}.json').upload_from_string(
                self.move_info, content_type='application/json'
            )
        source_bucket.delete_blob(self.source_doc.blob_name)
        

class BucketRegistry:
    storage_client: Optional[storage.Client] = None
    bucket_dict = {}
    client_info = ClientInfo(
        user_agent="cloud-solutions/eks-doc-processors-v1"
    )

    @classmethod
    def get_storage_client(cls):
        if cls.storage_client is None:
            cls.storage_client = storage.Client(
                client_info=cls.client_info
            )
        return cls.storage_client
    
    @classmethod
    def get_bucket(cls, bucket_name: str):
        if not bucket_name in cls.bucket_dict:
            cls.bucket_dict[bucket_name] = cls.get_storage_client().bucket(bucket_name)
        return cls.bucket_dict[bucket_name]

def move_duplicated_files(duplicated_file_list_gcs_uri: str, destination_folder_ful_uri: str, process_files_by_type: dict[str, list]):
    duplicated_file_list_doc = GCSDoc(duplicated_file_list_gcs_uri)
    duplicated_file_list_blob = BucketRegistry.get_bucket(duplicated_file_list_doc.bucket_name).blob(duplicated_file_list_doc.blob_name)
    for line in duplicated_file_list_blob.download_as_string().split(b'\n'):
        dup_obj = json.loads(line)        
        move_doc = MoveDoc(dup_obj['doc'], destination_folder_ful_uri, line)
        move_doc.move()
        process_doc_list = process_files_by_type[move_doc.source_doc.get_doc_type()]
        if move_doc.source_doc.get_doc_name() in process_doc_list:
            del process_doc_list[process_doc_list.index(move_doc.source_doc.get_doc_name())]
        