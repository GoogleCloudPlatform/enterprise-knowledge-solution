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

import json
import logging
from typing import Optional

from google.api_core.client_info import ClientInfo
from google.cloud import documentai, storage


class GCSDoc:
    def __init__(self, source_doc_uri: str):
        self.bucket_name, self.blob_name = GCSDoc.extract_bucket_and_blob_name(
            source_doc_uri
        )

    def get_doc_name(self):
        return self.blob_name.split(r"/")[-1]

    def get_doc_type(self):
        return self.get_doc_name().split(r".")[-1]

    @staticmethod
    def extract_bucket_and_blob_name(doc_uri: str):
        """split document uri into bucket and blob_name and file"""
        parts = doc_uri.replace(r"gs://", "").split(r"/")
        bucket_name = parts[0]
        blob_name = "/".join(parts[1:])
        return bucket_name, blob_name


class MoveDoc:
    def __init__(
        self, source_doc_uri: str, destination_folder_ful_uri: str, move_info: str = ""
    ):
        self.source_doc = GCSDoc(source_doc_uri)
        self.dest_doc = GCSDoc(
            f"{destination_folder_ful_uri}/{self.source_doc.get_doc_name()}"
        )
        self.move_info = move_info

    def move(self):
        source_bucket = BucketRegistry.get_bucket(self.source_doc.bucket_name)
        source_blob = source_bucket.blob(self.source_doc.blob_name)
        destination_bucket = BucketRegistry.get_bucket(self.dest_doc.bucket_name)
        source_bucket.copy_blob(
            source_blob, destination_bucket, self.dest_doc.blob_name
        )
        if self.move_info:
            destination_bucket.blob(
                f"{self.dest_doc.blob_name}.json"
            ).upload_from_string(self.move_info, content_type="application/json")
        source_bucket.delete_blob(self.source_doc.blob_name)
        logging.info(
            f"Moved {self.source_doc.bucket_name}/{self.source_doc.blob_name} "
            f"to {self.dest_doc.bucket_name}/{self.dest_doc.blob_name}"
        )


class BucketRegistry:
    storage_client: Optional[storage.Client] = None
    bucket_dict: dict = {}
    client_info = ClientInfo(user_agent="cloud-solutions/eks-doc-processors-v1")

    @classmethod
    def get_storage_client(cls):
        if cls.storage_client is None:
            cls.storage_client = storage.Client(client_info=cls.client_info)
        return cls.storage_client

    @classmethod
    def get_bucket(cls, bucket_name: str):
        if bucket_name not in cls.bucket_dict:
            cls.bucket_dict[bucket_name] = cls.get_storage_client().bucket(bucket_name)
        return cls.bucket_dict[bucket_name]


class ClassifierResultEntity:
    def __init__(self, entity: dict):
        self.confidence = entity["confidence"]
        self.id = entity["id"]
        self.type = entity["type"]

    def __str__(self):
        return json.dumps(self.__dict__)

    def is_match(self, match_types: list[str], threshold_score: float):
        return (
            any(match_type.lower() == self.type.lower() for match_type in match_types)
            and self.confidence > threshold_score
        )


class FormClassifierResult:

    OBJ_ARRAY_END_IDENTIFIER: bytes = b"}]"
    OBJ_TERMINATION_CHAR: bytes = b"}"
    CONTENT_TYPE_JSON: str = "application/json"

    @staticmethod
    def transform_docai_entity_to_obj(entity):
        return ClassifierResultEntity(
            {"confidence": entity.confidence, "id": entity.id, "type": entity.type}
        )

    @staticmethod
    def is_json(blob):
        is_json = blob.content_type == FormClassifierResult.CONTENT_TYPE_JSON
        if not is_json:
            logging.info(
                f"Skipping non-supported file: {blob.name} - Mimetype: "
                f"{blob.content_type}"
            )
        return is_json

    def __init__(
        self,
        bucket_name: str,
        processing_prefix: str,
        input_file_type: str,
        result_folder_prefix: str,
        result_content_keywords: list[bytes],
        partial_read_length: int = 128,
    ):
        self.bucket_name = bucket_name
        self.processing_prefix = processing_prefix
        self.input_file_type = input_file_type
        self.result_folder_prefix = result_folder_prefix
        self.content_keywords = result_content_keywords
        self.partial_read_length = partial_read_length
        self.results: dict = {}

    def derive_input_blob_name(self, result_blob_name: str):
        result_doc = GCSDoc(f"{self.bucket_name}/{result_blob_name}")
        input_doc_name = r"-".join(result_doc.get_doc_name().split(r"-")[:-1])
        return f"{self.processing_prefix}/{self.input_file_type}/{input_doc_name}.{self.input_file_type}"

    def extract_classifier_result(self, blob):
        """
        Extracts classifier results from the classifier output JSON file Cloud Storage bucket.

        This function efficiently extracts classifier results for the JSON file.
        To optimize performance, it first attempts to partially download the file
        (up to `self.partial_read_length` bytes) since classifier results are typically located
        at the beginning of the file.

        It checks for the presence of specific keywords ('entities', 'form', '}]')
        to ensure the partial download contains the complete result set. If successful,
        it parses the downloaded string and returns the extracted entities.

        If partial download fails or encounters errors, it falls back to downloading
        the entire file and uses the DocAI library for parsing.
        Args:
            blob: The blob object containing the classifier result JSON file.

        Returns:
            A list of `ClassifierResultEntity` objects representing the extracted entities.
        """

        try:
            download_str = blob.download_as_string(
                start=0, end=self.partial_read_length
            )
            if FormClassifierResult.OBJ_ARRAY_END_IDENTIFIER in download_str and all(
                keyword.lower() in download_str.lower()
                for keyword in self.content_keywords
            ):
                result_obj_str = (
                    download_str[
                        : download_str.index(
                            FormClassifierResult.OBJ_ARRAY_END_IDENTIFIER
                        )
                        + 2
                    ]
                    + FormClassifierResult.OBJ_TERMINATION_CHAR
                )
                result_obj = json.loads(result_obj_str)
                return [ClassifierResultEntity(ent) for ent in result_obj["entities"]]
        except Exception as e:
            logging.info(
                f"Fail to extract classifier result using partial download for file: {blob.name}, with error: {e},"
                f" fall back to download the complete file and use DocAI library to deserialize the result"
            )
        document = documentai.Document.from_json(
            blob.download_as_bytes(), ignore_unknown_fields=True
        )
        return [
            FormClassifierResult.transform_docai_entity_to_obj(e)
            for e in document.entities
        ]

    def load_results(self):
        blobs = BucketRegistry.get_bucket(self.bucket_name).list_blobs(
            prefix=f"{self.processing_prefix}/{self.result_folder_prefix}",
            match_glob="**/*.json",
        )
        results = {}

        for blob in blobs:
            if not FormClassifierResult.is_json(blob):
                continue

            input_blob_name = self.derive_input_blob_name(blob.name)
            if input_blob_name not in results:
                results[input_blob_name] = []

            results[input_blob_name].extend(self.extract_classifier_result(blob))

        self.results = results

    def get_results(self):
        if not self.results:
            self.load_results()
        return self.results


def move_classifier_matched_files(
    process_bucket: str,
    process_folder: str,
    input_file_type: str,
    known_labels: list[str],
    classifier_result_folder: str = "classified_pdfs_results",
    result_content_keywords: list[bytes] = [b"entities", b"form"],
    threshold: float = 0.7,
):
    classifier_results = FormClassifierResult(
        process_bucket,
        process_folder,
        input_file_type,
        classifier_result_folder,
        result_content_keywords,
    )
    classification_mv_params = []
    for blob_path in classifier_results.get_results():
        matched_entries = sorted(
            filter(
                lambda e: e.is_match(known_labels, threshold),
                classifier_results.results[blob_path],
            ),
            key=lambda ent: ent.confidence,
            reverse=True,
        )
        if matched_entries:
            logging.info(f"Doc: {blob_path} is classified as {matched_entries[0].type}")
            move_doc = MoveDoc(
                f"{process_bucket}/{blob_path}",
                f"{process_bucket}/{process_folder}/{input_file_type}-{matched_entries[0].type.lower()}/input",
            )
            move_doc.move()
            classification_mv_params.append(
                {
                    "source_object": blob_path,
                    "destination_bucket": move_doc.dest_doc.bucket_name,
                    "destination_object": move_doc.dest_doc.blob_name,
                }
            )
    return classification_mv_params


def move_duplicated_files(
    duplicated_file_list_gcs_uri: str,
    destination_folder_ful_uri: str,
    process_files_by_type: dict[str, list],
):
    duplicated_file_list_doc = GCSDoc(duplicated_file_list_gcs_uri)
    duplicated_file_list_blob = BucketRegistry.get_bucket(
        duplicated_file_list_doc.bucket_name
    ).blob(duplicated_file_list_doc.blob_name)
    for line in duplicated_file_list_blob.download_as_string().split(b"\n"):
        if line:
            dup_obj = json.loads(line)
            move_doc = MoveDoc(dup_obj["doc"], destination_folder_ful_uri, line)
            move_doc.move()
            process_doc_list = process_files_by_type[move_doc.source_doc.get_doc_type()]
            if move_doc.source_doc.get_doc_name() in process_doc_list:
                del process_doc_list[
                    process_doc_list.index(move_doc.source_doc.get_doc_name())
                ]
