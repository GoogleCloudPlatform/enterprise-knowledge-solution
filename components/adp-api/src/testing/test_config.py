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

"""Static Values for Testing"""
supporting_document_data  = {
  "case_id": "123A1",
  "uid": "7CBdJrVpbKolmbm2MYLxx",
  "context": "arkansas",
  "document_class": "driver_license",
  "url": "gs://document-upload-test/123A1/"
         "7CBdJrVpbKolmbm2MYLxx/Illinois2.pdf",
  "entities": [{
    "entity": "name",
    "value": "abc"
  },
    {
      "entity": "last_name",
      "value": "xyzz"
    }]
}

application_document_data  = {
  "case_id": "123A",
  "uid": "7CBdJrVpbKolmbm2MYLX",
  "context": "arkansas",
  "document_class": "unemployment_form",
  "url": "gs://document-upload-test/123A/"
         "7CBdJrVpbKolmbm2MYLX/Illinois2.pdf",
  "entities": [{
    "entity": "name",
    "value": "abc"
  },
    {
      "entity": "last_name",
      "value": "xyzz"
    }]
}
