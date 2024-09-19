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

import csv
import hashlib
import uuid

import jsonlines
import markdown
import openpyxl
import pandas as pd
import pdfkit
from google.cloud import storage


def md_to_html(md_filename: str, html_filename: str) -> None:
    # Read the Markdown text from a file
    with open(md_filename, "r") as f:
        markdown_text = f.read()

    # Convert the Markdown text to HTML
    html = markdown.markdown(markdown_text)

    # Write the HTML code to a file
    with open(html_filename, "w") as f:
        f.write(html)


def to_csv(xls_filename, csv_filename) -> None:
    # Load the Excel file
    wb = openpyxl.load_workbook(xls_filename)

    # Create a new CSV file
    with open(csv_filename, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)

        # Iterate over the rows in the Excel file
        for row in wb.active.rows:
            # Write the row data to the CSV file
            writer.writerow([cell.value for cell in row])


def to_csv_pd(xls_filename, csv_filename) -> str:
    read_file = pd.read_excel(xls_filename)
    read_file.to_csv(csv_filename, index=None, header=True)


def xlsx_to_pdf(xls_filename, html_filename, pdf_filename) -> str:
    df = pd.read_excel(xls_filename)
    df.to_html(html_filename)
    pdfkit.from_file(html_filename, pdf_filename)


def generate_document_id(document_str: str):
    # Calculate the hash of the combined string
    hash_value = hashlib.sha256(document_str.encode()).digest()

    # Convert the hash to a UUID
    document_uuid = uuid.UUID(bytes=hash_value[:16])
    return document_uuid


# Change this or override this method
def struct_data(file):
    struct_data = {
        "file_name": file.name,
        "id": file.id,
        "crc32c": file.crc32c,
        "size": file.size,
    }
    return struct_data


storage_client = storage.Client()

mime_types = {
    "MIME_TYPE_PDF": "application/pdf",
    "MIME_TYPE_HTM": "text/html",
    "MIME_TYPE_TXT": "text/plain",
    "MIME_TYPE_PPT": "pplication/vnd.openxmlformats-officedocument.presentationml.presentation",
    "MIME_TYPE_DOC": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def get_mime_type(file_name: str):
    mime_type = None
    if file_name:
        if file_name.endswith(".pdf"):
            mime_type = mime_types["MIME_TYPE_PDF"]
        if file_name.endswith(".html"):
            mime_type = mime_types["MIME_TYPE_HTM"]
        if file_name.endswith(".txt") or file_name.endswith(".json"):
            mime_type = mime_types["MIME_TYPE_TXT"]
        if file_name.endswith(".pptx") or file_name.endswith(".ppt"):
            mime_type = mime_types["MIME_TYPE_PPT"]
        if file_name.endswith(".docx") or file_name.endswith(".doc"):
            mime_type = mime_types["MIME_TYPE_DOC"]

    return mime_type


def write_jsonl(in_bucket_name, in_path, out_bucket_name=None, out_path=None) -> None:
    in_bucket = storage_client.bucket(in_bucket_name)
    if out_bucket_name:
        out_bucket = storage_client.bucket(out_bucket_name)
    else:
        out_bucket = in_bucket
    jsonl_file = "out.jsonl"
    blobs = in_bucket.list_blobs(prefix=in_path)
    with jsonlines.open(jsonl_file, mode="w") as writer:
        for blob in blobs:
            file_name = blob.name
            mime_type = get_mime_type(file_name)
            if mime_type:
                data = {
                    "id": str(generate_document_id(file_name)),
                    "structData": struct_data(blob),
                    "content": {
                        "mimeType": mime_type,
                        "uri": f"gs://{in_bucket_name}/{file_name}",
                    },
                }
                writer.write(data)
    output_file_path = f"{out_path}/{jsonl_file}"
    blob = out_bucket.blob(output_file_path)
    blob.content_type = "application/json"
    blob.upload_from_filename(jsonl_file)
    print(f"JSON files merged and written to gs://{out_bucket_name}/{output_file_path}")
