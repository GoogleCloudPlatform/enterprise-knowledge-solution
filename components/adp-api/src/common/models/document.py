"""
Copyright 2022 Google LLC

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
Document Status object in the ORM
"""
import os
from common.models import BaseModel
from fireo.fields import TextField, ListField, NumberField, BooleanField, DateTime

DATABASE_PREFIX = os.getenv("DATABASE_PREFIX", "")
PROJECT_ID = os.environ.get("PROJECT_ID", "")


class Document(BaseModel):
  """Documentstatus ORM class  """
  case_id = TextField()
  uid = TextField()
  url = TextField()
  document_type = TextField()
  classification_score = NumberField()
  document_class = TextField()
  document_display_name = TextField()
  context = TextField()
  ocr_text = TextField()
  system_status = ListField()
  hitl_status = ListField()
  active = TextField()
  upload_timestamp = DateTime(auto=True)
  entities = ListField()
  extraction_score = NumberField()
  validation_score = NumberField()
  matching_score = NumberField()
  auto_approval = TextField()
  is_autoapproved = TextField()
  is_hitl_classified = BooleanField()
  external_case_id = TextField()
  extraction_status = TextField()
  error_detail = TextField()

  class Meta:
    ignore_none_field = False
    collection_name = DATABASE_PREFIX + "document"

  @classmethod
  def find_by_uid(cls, uid):
    """Find the document  using  uid
    Args:
        uid (string):  UID
    Returns:
        Document: Document Object
    """
    return Document.collection.filter("uid", "==", uid).get()
