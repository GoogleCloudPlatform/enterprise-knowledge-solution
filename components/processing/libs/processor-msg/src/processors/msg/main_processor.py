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
from enum import Enum

from dict import Dict
from optional import Optional
from processors.base.gcsio import GCSPath
from processors.base.result_writer import BigQueryWriter, DocumentMetadata
from processors.msg.msg_processor import msg_processor
from processors.xlsx import xlsx_processor
from processors.zip.unzip_processor import unzip_processor

logger = logging.getLogger(__name__)


class Processors(str, Enum):
    TXT = "txt-processor"
    MSG = "msg-processor"
    ZIP = "zip-processor"
    XLSX = "xlsx-processor"


PROCESSOR_NAMES_TO_CALLABLE = {
    Processors.TXT.value: None,  # Special case - handled inline within code
    Processors.MSG.value: msg_processor,
    Processors.ZIP.value: unzip_processor,
    Processors.XLSX.value: xlsx_processor,
}


def process_all_objects(
    source_dir: GCSPath,
    reject_dir: GCSPath,
    supported_files: Dict[str, str],
    write_json=True,
    write_bigquery: str = "",
):
    all_objects = list(source_dir.list())

    writer = None
    if write_bigquery != "":
        writer = BigQueryWriter(write_bigquery)

    for obj in all_objects:
        process_object(
            obj,
            reject_dir,
            supported_files,
            write_json=write_json,
            bq_writer=writer,
        )


def move_rejected_file(source: GCSPath, reject_dir: GCSPath, error_msg: str):
    source.move(GCSPath(reject_dir, source.name))
    json_err_msg = GCSPath(reject_dir, source.name + ".json")
    json_err_msg.write_text(
        json.dumps(
            {"error_msg": error_msg},
            default=str,
        )
    )


def reject_oversized_file(
    source: GCSPath, reject_dir: GCSPath, file_size_limit_mb: float
) -> bool:
    if source.size > file_size_limit_mb * 1024 * 1024:
        move_rejected_file(
            source,
            reject_dir,
            f"File size: {source.size} exceeding the {file_size_limit_mb}M limit for {source.suffix} files.",
        )
        return True
    return False


def process_recursive(
    source: GCSPath,
    reject_dir: GCSPath,
    supported_files: Dict[str, str],
) -> list[dict]:

    result = {
        "objid": "",
        "uri": str(source),
        "mimetype": source.mimetype,
        "metadata": {},
        "status": "UNPROCESSED",
    }
    results = [result]

    if not supported_files.get(source.suffix, False):
        result["status"] = "Not indexed or expanded"
        result["metadata"]["reason"] = f"file of type {source.suffix} not " f"supported"
        return results
    processor_name = supported_files[source.suffix]

    if processor_name == Processors.TXT.value:

        # current file size limit of 100MB in Data Store
        if reject_oversized_file(source, reject_dir, 100):
            result["status"] = "Rejected -- over 100MB"
            return results

        # current file size limit of 2.5MB for TXT in Data Store
        if source.suffix == ".txt" and reject_oversized_file(source, reject_dir, 2.5):
            result["status"] = "Rejected -- over 2.5MB and text"
            return results

        result["objid"] = source.hash
        result["status"] = "Indexed"
        return results

    # the one special case is txt-processor, that will return None, but this
    # should have been handled above - beware of changes to the order of
    # operations here.
    processor = PROCESSOR_NAMES_TO_CALLABLE.get(processor_name)
    if processor is None:
        result["status"] = "Not indexed or expanded"
        result["metadata"]["reason"] = (
            f"file type {source.suffix} is mapped "
            f"to a processor {processor_name} that "
            f"is not mapped to a callable"
        )
        return results

    # Attempt to use it.
    output = GCSPath(str(source) + ".out")
    if output.exists():
        logger.info("Output directory already exists... what is going on?")
        result["status"] = "Output directory already exists"
        return results

    try:
        # Generate outputs and find more metadata
        metadata = processor(source, output)
        if metadata is None:
            result["status"] = "Processor returned no data"
            return results

        result["status"] = "Expanded"
        result["metadata"] = metadata

    except Exception as e:
        logger.error(f"error running processor: {e}")
        logger.exception(e)

        # Move the failed to process doc to the reject folder
        move_rejected_file(source, reject_dir, f"Doc processor fail with error: {e}")
        result["status"] = f"Processor failed with error {e}"
        return results

    # Return with the children
    for child in list(output.list()):
        results.extend(process_recursive(child, reject_dir, supported_files))

    return results


def process_object(
    source: GCSPath,
    reject_dir: GCSPath,
    supported_files: Dict[str, str],
    write_json=True,
    bq_writer: Optional[BigQueryWriter] = None,
):

    logger.info(f"Processing {source}...")

    # Extract everything
    objs = process_recursive(source, reject_dir, supported_files)

    logger.debug(f"Objects: {objs}")

    # Create a object map with a subset of the data
    obj_keys = ["uri", "objid", "status", "mimetype"]
    obj_map = []
    for obj in objs:
        obj_map.append(dict(((k, obj[k]) for k in obj_keys)))
    logger.debug(f"Object map: {obj_map}")

    for obj in objs:

        # Skip if no 'objid' (not to be indexed)
        if not obj["objid"]:
            continue

        # Object metadata
        obj_metadata = {
            # Map of all related objects
            "objs": obj_map,
            # Metadata for this one object
            "metadata": obj["metadata"],
            # Status of processing
            "status": obj["status"],
        }

        # Write to BigQuery if necessary
        if bq_writer:
            bq_writer.write_results(
                [
                    DocumentMetadata(
                        id=obj["objid"],
                        jsonData=json.dumps(obj_metadata, default=str),
                        content=DocumentMetadata.Content(
                            mimeType=obj["mimetype"],
                            uri=obj["uri"],
                        ),
                    )
                ]
            )

        # Write to JSON
        if write_json:
            json_metadata = GCSPath(str(obj["uri"]) + ".json")
            json_metadata.write_text(
                json.dumps(
                    {
                        "id": obj["objid"],
                        "structData": obj_metadata,
                        "content": {
                            "mimeType": obj["mimetype"],
                            "uri": obj["uri"],
                        },
                    },
                    default=str,
                )
            )
