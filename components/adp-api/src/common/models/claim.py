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
Claim object in the ORM
"""

import os

import common.config as global_config
from common.db_client import bq_client
from common.models import BaseModel
from fireo.fields import Field, TextField

DATABASE_PREFIX = os.getenv("DATABASE_PREFIX", "")
PROJECT_ID = os.environ.get("PROJECT_ID", "")


# sample class
class Claim(BaseModel):
  """Claim ORM class
  """
  claim_id = TextField()
  first_name = TextField()
  middle_name = TextField()
  last_name = TextField()
  date_of_birth = TextField()
  mail_address_line1 = TextField()
  mail_address_line2 = TextField()
  mail_address_city = TextField()
  mail_address_state = TextField()
  mail_address_zipcode = TextField()
  res_address_line1 = TextField()
  res_address_line2 = TextField()
  res_address_city = TextField()
  res_address_state = TextField()
  res_address_zipcode = TextField()
  email_address = TextField()
  phone_num = TextField()
  itin_number = TextField()
  tf_number = TextField()
  dl_number = TextField()
  register_ip_address = TextField()
  document_details = Field()
  created_timestamp = TextField()
  last_updated_timestamp = TextField()

  class Meta:
    ignore_none_field = False
    collection_name = DATABASE_PREFIX + "claims"

  # pylint: disable = line-too-long
  @classmethod
  def get_rules_engine_score(cls, claim_id):
    query = f"SELECT * FROM {global_config.PROJECT_ID}.{global_config.DATABASE_PREFIX}rules_engine.final_rules_engine_score WHERE claim_id = \"{claim_id}\""

    client = bq_client()
    query_job = client.query(query)
    results = query_job.result()
    records = [dict(row) for row in results]
    if records != []:
      return records[0]
    else:
      return {}

  # pylint: enable= line-too-long

  @classmethod
  def find_by_claim_id(cls, uuid):
    """Find the claim using claim id(UUID)
    Args:
        uuid (string): Claim ID
    Returns:
        Claim: Claim Object
    """
    return Claim.collection.filter("claim_id", "==", uuid).get()
