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
neo4j script to handle new claims via API and insert real time
"""

import os
import re
import pandas as pd
from common.config import NEO4J_URI, DOCUMENT_DICT
from neo4j import GraphDatabase
from google.cloud import secretmanager

PROJECT_ID = os.environ.get("PROJECT_ID", os.environ.get("PROJECT_ID", ""))
DATABASE_PREFIX = os.getenv("DATABASE_PREFIX", "")


def authenticate_neo4j(neo4j_uri=NEO4J_URI):
  client = secretmanager.SecretManagerServiceClient()

  # pylint: disable-next = line-too-long
  user_key = f"projects/{PROJECT_ID}/secrets/{PROJECT_ID}-neo4j-user/versions/latest"
  response = client.access_secret_version(request={"name": user_key})
  neo4j_user = response.payload.data.decode("UTF-8")

  # pylint: disable-next = line-too-long
  pw_key = f"projects/{PROJECT_ID}/secrets/{PROJECT_ID}-neo4j-password/versions/latest"
  response = client.access_secret_version(request={"name": pw_key})
  neo4j_password = response.payload.data.decode("UTF-8")

  graph = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
  return graph

def map_key_names(claim_dict):
  doc_key_list = []
  for key in claim_dict["document_details"].keys():
    doc_key_list.append(key)

  for key in doc_key_list:
    if key in DOCUMENT_DICT:
      new_key = DOCUMENT_DICT[key]
      claim_dict["document_details"][new_key] = claim_dict\
        ["document_details"][key]
      del claim_dict["document_details"][key]
    else:
      pass

  return claim_dict

def modify_claim_fields(claim_dict):
  claim_dict = map_key_names(claim_dict)
  if "driver_license" in claim_dict["document_details"].keys():
    claim_dict["driver_license_id_number"] = claim_dict["document_details"]\
    ["driver_license"]["id_number"]
  else:
    claim_dict["driver_license_id_number"] = ""
  if "rec_id" in claim_dict["document_details"].keys():
    claim_dict["rec_id_number"] = claim_dict["document_details"]\
      ["rec_id"]["id_number"]
  else:
    claim_dict["rec_id_number"] = ""
  if "foreign_passport" in claim_dict["document_details"].keys():
    claim_dict["foreign_passport_number"] = claim_dict["document_details"]\
      ["foreign_passport"]["passport_number"]
  else:
    claim_dict["foreign_passport_number"] = ""
  if "us_passport" in claim_dict["document_details"].keys():
    claim_dict["us_passport_document_id"] = claim_dict["document_details"]\
      ["us_passport"]["document_id"]
  else:
    claim_dict["us_passport_document_id"] = ""
  del claim_dict["document_details"]

  new_claim_df = pd.DataFrame([claim_dict], columns=claim_dict.keys())
  #replace null values
  new_claim_df.fillna(value="", inplace=True)
  #create new columns
  new_claim_df["email_username"] = new_claim_df["email_address"].apply\
  (lambda x:x.split("@")[0])
  new_claim_df["email_tokenised"] = new_claim_df["email_username"].apply\
  (lambda x: re.sub(r"[^A-Za-z]+", "", x).lower())
  new_claim_df["full_name"] = new_claim_df["first_name"] + " " +\
  new_claim_df["middle_name"] + " "+ new_claim_df["last_name"]
  new_claim_df["full_name"] = new_claim_df["full_name"].str.lower()
  new_claim_df["res_address"] = new_claim_df["res_address_line1"]+" "+\
  new_claim_df["res_address_line2"]+" "+ new_claim_df["res_address_city"]+" "+\
  new_claim_df["res_address_state"]
  new_claim_df["res_address"] = new_claim_df["res_address"].apply\
  (lambda x: re.sub(" +", " ", x).lower())
  new_claim_df["mail_address"] = new_claim_df["mail_address_line1"]+" "+\
  new_claim_df["mail_address_line2"]+" "+new_claim_df["mail_address_city"]+" "+\
  new_claim_df["mail_address_state"]
  new_claim_df["mail_address"] = new_claim_df["mail_address"].apply\
  (lambda x: re.sub(" +", " ", x).lower())

  col_list = [
      "claim_id", "full_name", "date_of_birth", "res_address", "mail_address",
      "res_address_zipcode", "email_address", "email_username",
      "email_tokenised", "phone_num", "itin_number", "tf_number",
      "driver_license_id_number", "register_ip_address", "rec_id_number",
      "foreign_passport_number", "us_passport_document_id"
  ]
  new_claim_df = new_claim_df[col_list]
  claim_dict = new_claim_df.to_dict("records")[0]
  return claim_dict


def delete_existing_claim(graph_session, claim_record):
  graph_session.run("""
    MATCH (c:claim)
    WHERE c.claim_id = $claim_id
    DETACH DELETE c
  """,
                    parameters={"claim_id": claim_record["claim_id"]})


def add_to_graph(graph_session, claim_record):
  graph_session.run("""
    MERGE (c:claim {claim_id:$claim_id})
    SET c.processed_flag = "false"
    MERGE (fn:full_name {full_name:$full_name})
    MERGE (dob:date_of_birth {date_of_birth:$date_of_birth})
    MERGE (ra:res_address {res_address:$res_address})
    MERGE (ma:mail_address {mail_address:$mail_address})

    MERGE (rzip: r_zip{res_address_zipcode:$res_address_zipcode})

    MERGE (e:email {email_address:$email_address})
    MERGE (eu:email_username {email_username:$email_username})
    MERGE (et:email_tokenised {email_tokenised:$email_tokenised})

    MERGE (ph:phone_num {phone_num:$phone_num})
    MERGE (tn:itin_no {itin_number:$itin_number})
    MERGE (tf:tf_no {tf_number:$tf_number})
    MERGE (dl:dl_no {dl_id_number:$dl_id_number})
    MERGE (ip:ip_address {register_ip_address:$register_ip_address})

    MERGE(recid:rec_id {rec_id_number:$rec_id_number})
    MERGE(fpno:fp_no {foreign_passport_number:$foreign_passport_number})
    MERGE(uspid:usp_id {us_passport_document_id:$us_passport_document_id})

    MERGE (fn)-[:ATTACHED_TO]-(c)
    MERGE (dob)-[:ATTACHED_TO]-(c)
    MERGE (ra)-[:ATTACHED_TO]-(c)
    MERGE (ma)-[:ATTACHED_TO]-(c)

    MERGE (rzip)-[:ATTACHED_TO]-(c)

    MERGE (e)-[:ATTACHED_TO]-(c)
    MERGE (eu)-[:ATTACHED_TO]-(c)
    MERGE (et)-[:ATTACHED_TO]-(c)

    MERGE (ph)-[:ATTACHED_TO]-(c)
    MERGE (tn)-[:ATTACHED_TO]-(c)
    MERGE (tf)-[:ATTACHED_TO]-(c)
    MERGE (dl)-[:ATTACHED_TO]-(c)

    MERGE(ip)-[:ATTACHED_TO]-(c)

    MERGE (recid)-[:ATTACHED_TO]-(c)
    MERGE (fpno)-[:ATTACHED_TO]-(c)
    MERGE (uspid)-[:ATTACHED_TO]-(c)
  """,
                    parameters={
                        "claim_id":
                        claim_record["claim_id"],
                        "full_name":
                        claim_record["full_name"],
                        "date_of_birth":
                        claim_record["date_of_birth"],
                        "res_address_zipcode":
                        claim_record["res_address_zipcode"],
                        "email_address":
                        claim_record["email_address"],
                        "email_username":
                        claim_record["email_username"],
                        "email_tokenised":
                        claim_record["email_tokenised"],
                        "phone_num":
                        claim_record["phone_num"],
                        "itin_number":
                        claim_record["itin_number"],
                        "tf_number":
                        claim_record["tf_number"],
                        "dl_id_number":
                        claim_record["driver_license_id_number"],
                        "register_ip_address":
                        claim_record["register_ip_address"],
                        "rec_id_number":
                        claim_record["rec_id_number"],
                        "foreign_passport_number":
                        claim_record["foreign_passport_number"],
                        "us_passport_document_id":
                        claim_record["us_passport_document_id"],
                        "res_address":
                        claim_record["res_address"],
                        "mail_address":
                        claim_record["mail_address"]
                    })


def delete_empty_nodes(graph_session, claim_record):
  #delete empty nodes
  graph_session.run("""
    MATCH (tf:tf_no {tf_number: ""})-[]-(c:claim)
    WHERE c.claim_id = $claim_id
    WITH tf as tf
    DETACH DELETE tf
    """,
                    parameters={"claim_id": claim_record["claim_id"]})

  graph_session.run("""
    MATCH (tn:itin_no {itin_number: ""})-[]-(c:claim)
    WHERE c.claim_id = $claim_id
    WITH tn as tn
    DETACH DELETE tn
    """,
                    parameters={"claim_id": claim_record["claim_id"]})

  graph_session.run("""
    MATCH (dl:dl_no {dl_id_number: ""})-[]-(c:claim)
    WHERE c.claim_id = $claim_id
    WITH dl as dl
    DETACH DELETE dl
    """,
                    parameters={"claim_id": claim_record["claim_id"]})

  graph_session.run("""
    MATCH (recid:rec_id {rec_id_number: ""})-[]-(c:claim)
    WHERE c.claim_id = $claim_id
    WITH recid as recid
    DETACH DELETE recid
    """,
                    parameters={"claim_id": claim_record["claim_id"]})

  graph_session.run("""
    MATCH (fpno:fp_no {foreign_passport_number: ""})-[]-(c:claim)
    WHERE c.claim_id = $claim_id
    WITH fpno as fpno
    DETACH DELETE fpno
    """,
                    parameters={"claim_id": claim_record["claim_id"]})

  graph_session.run("""
    MATCH (uspid:usp_id {us_passport_document_id: ""})-[]-(c:claim)
    WHERE c.claim_id = $claim_id
    WITH uspid as uspid
    DETACH DELETE uspid
    """,
                    parameters={"claim_id": claim_record["claim_id"]})


def connect_claims_in_graph(graph_session, claim_id):
  graph_session.run("""
    MATCH (c1:claim)-[]-(rzip:r_zip)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_RZIP]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(fn:full_name)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_FN]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(dob:date_of_birth)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_DOB]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(ra:res_address)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_RA]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(ma:mail_address)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_MA]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(e:email)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_EMAIL]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(eu:email_username)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_EMAIL_U]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(et:email_tokenised)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_EMAIL_T]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(ph:phone_num)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_PH]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(tn:itin_no)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_TN]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(tf:tf_no)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_TF]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(dl:dl_no)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_DL]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(ip:ip_address)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_IP]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(recid:rec_id)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_RECID]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(fpno:fp_no)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_FPNO]-(c2)

    UNION ALL

    MATCH (c1:claim)-[]-(uspid:usp_id)-[]-(c2:claim)
    WHERE c1.claim_id = $claim_id
    MERGE (c1)-[:SAME_USPID]-(c2)

    UNION ALL

    MATCH (c1:claim)
    WHERE c1.claim_id = $claim_id
    SET c1.processed_flag = "true"
  """,
                    parameters={"claim_id": claim_id})


def clean_graph_db():
  graph = authenticate_neo4j()
  graph_session = graph.session()
  graph_session.run("""
    MATCH (n)
    WHERE NOT (n:claim) AND NOT (n)-[]-(:claim)
    DELETE n
    """)


def create_claim_neo4j(claim_dict):
  claim_dict = modify_claim_fields(claim_dict)
  graph = authenticate_neo4j()
  graph_session = graph.session()
  add_to_graph(graph_session, claim_dict)
  delete_empty_nodes(graph_session, claim_dict)
  #connect_claims_in_graph(graph_session, claim_dict)


def update_claim_neo4j(claim_dict):
  claim_dict = modify_claim_fields(claim_dict)
  graph = authenticate_neo4j()
  graph_session = graph.session()
  delete_existing_claim(graph_session, claim_dict)
  add_to_graph(graph_session, claim_dict)
  delete_empty_nodes(graph_session, claim_dict)
  #connect_claims_in_graph(graph_session, claim_dict)


def delete_claim_neo4j(claim_dict):
  graph = authenticate_neo4j()
  graph_session = graph.session()
  delete_existing_claim(graph_session, claim_dict)
