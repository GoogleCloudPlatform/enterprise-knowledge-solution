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

### DocAI parser and extraction configuration
import os
from typing import List

PROJECT_ID = os.environ.get("PROJECT_ID", "")
assert PROJECT_ID, "Env var PROJECT_ID is not set."

# GCS temp folder to store async form parser output
DOCAI_OUTPUT_BUCKET_NAME = f"{PROJECT_ID}-docai-output"

# Attributes not required from specialized parser raw json
DOCAI_ATTRIBUTES_TO_IGNORE = [
    "textStyles", "textChanges", "revisions", "pages.image"
]

class ExtractionOutput:
  def __init__(self, uid: str, extracted_entities: List, extraction_status: str,
      extraction_field_min_score: float, extraction_score: float, ocr_text: str) -> None:
    self.uid = uid
    self.extracted_entities = extracted_entities
    self.extraction_status = extraction_status
    self.extraction_field_min_score = extraction_field_min_score
    self.extraction_score = extraction_score
    self.ocr_text = ocr_text

  def __str__(self):
    return f"uid={self.uid}, extraction_status={self.extraction_status}, " \
           f"extraction_field_min_score={self.extraction_field_min_score}, " \
           f"extraction_score={self.extraction_score}"


# This is depricated, using docai_entity_mapping.json and DOCAI_ENTITY_MAPPING_FILE instead
# Full mapping of entity's and column names, grouped by document class.
# DOCAI_ENTITY_MAPPING = {
#     # State or program specific docs
#     "arizona": {
#         "unemployment_form": {
#             "default_entities": {
#                 "Social Security Number:": ["Social Security Number"],
#                 "Date:": ["Date"],
#                 "Primary Phone: ": ["Employee Primary Phone"],
#                 "First Name": ["Employee First Name"],
#                 "Last Name": ["Employee Last Name"],
#                 "Mailing Address (No., Street, Apt., P.O. Box) ": [
#                     "Employee Mailing Address (No., Street, Apt., P.O.Box)"
#                 ],
#                 "E-MAIL Address (Optional but Encouraged) ": [
#                     "Employee E-MAIL Address (Optional but Encouraged)"
#                 ],
#                 "Gender": ["Employee Gender"],
#                 "Race": ["Employee Race"],
#                 "Ethnicity": ["Employee Ethnicity"],
#                 "Language": ["Employee Language"],
#                 "Mailing Address (No., Street, Apt., P.O. Box, City)": [
#                     "Employer Mailing Address (No., Street, Apt., P.O.Box, City)"
#                 ],
#                 "Date": ["Date"],
#                 "City": ["Employee City", "Employee Residence City"],
#                 "State": [
#                     "Employee State", "Employee Residence State",
#                     "Employer State"
#                 ],
#                 "Employer's Phone No.": ["Employer's Phone No."],
#                 "Claimant's Signature": ["Claimant's Signature"],
#                 "Company's Name ": ["Company's Name"],
#                 "ZIP": [
#                     "Employee ZIP", "Employee Residence ZIP", "Employer ZIP"
#                 ],
#                 "Month": ["Employee DOB Month", "Month (Last Day of Work)"],
#                 "Day": ["Employee DOB Day", "Day (Last Day of Work)"],
#                 "Year": ["Employee DOB Year", "Year (Last Day of Work)"]
#             }
#         },
#         "claims_form": {
#             "default_entities": {
#                 "Social Security Number": ["Social Security Number"],
#                 "Name": ["Employee Name"],
#                 "Week Ending Date": ["Week Ending Date"],
#                 "What were your gross earnings before deductions?": [
#                     "What were your gross earnings before deductions?"
#                 ],
#                 "What was your last day of work?": [
#                     "What was your last day of work?"
#                 ],
#                 "Claimant's Signature": ["Claimant's Signature "]
#             },
#             "table_entities": {
#                 "isheader":
#                     True,
#                 # if table and page number is unknown mark the variables to 0
#                 "table_num":
#                     0,
#                 "page_num":
#                     0,
#                 "headers": [
#                     "Date",
#                     "Name of Employer/Company/ Union and Address (City, State and Zip Code)",
#                     "Website URL or Name of person contacted",
#                     "Method (In person, Internet, mail)", "Type of work sought",
#                     "Action taken on the date of contact"
#                 ],
#                 # entity name will be constructed based on the col
#                 # number provided
#                 # for an employer
#                 "entity_extraction": [
#                     {
#                         "entity_suffix": "(employer 1)",
#                         "col": 0,
#                         "row_no": 1
#                     },
#                     {
#                         "entity_suffix": "(employer 2)",
#                         "col": 0,
#                         "row_no": 2
#                     },
#                     {
#                         "entity_suffix": "(employer 1)",
#                         "col": 2,
#                         "row_no": 2
#                     },
#                     {
#                         "entity_suffix": "(employer 1)",
#                         "col": 3,
#                         "row_no": 1
#                     },
#                     {
#                         "entity_suffix": "(employer 1)",
#                         "col": 4,
#                         "row_no": 1
#                     },
#                     {
#                         "entity_suffix": "(employer 2)",
#                         "col": 3,
#                         "row_no": 2
#                     },
#                     {
#                         "entity_suffix": "(employer 2)",
#                         "col": 2,
#                         "row_no": 3
#                     },
#                     {
#                         "entity_suffix": "(employer 3)",
#                         "col": 0,
#                         "row_no": 3
#                     },
#                 ],
#             }
#         },
#     },
#     "california": {
#         "unemployment_form": {
#             "default_entities": {
#                 "Name of issuing State/entity": [
#                     "Name of issuing Stata/entity"
#                 ],
#                 "Driver License Number": ["Driver License Number"],
#                 "Race": ["Employee Race"],
#                 "Ethnicity": ["Employee Ethnicity"],
#                 "Language": ["Employee Language"],
#                 "22. Employer name": ["Longest Employer name"],
#                 "Months": ["Months worked for longest employer"]
#             },
#             "derived_entities": {
#                 "What is your birth date?": {
#                     "rule":
#                         r"What is your birth date\?\n\d\.(.*?)\((mm/dd/yyyy)"
#                 },
#                 "What is your gender?": {
#                     "rule": r"What is your gender\?\n\d\.(.*?)\n\d"
#                 },
#                 "Expiration Date (EXP)": {
#                     "rule":
#                         r"\sAlien Registration Number \(A#\)\n3\)\s(\d{4}-\d{2}-\d{2})\n"
#                 }
#             }
#         },
#     },
#     "arkansas": {
#         "unemployment_form": {
#             "default_entities": {
#                 "TODAY'S DATE": ["TODAY'S DATE"],
#                 "SOCIAL SECURITY NUMBER": ["SOCIAL SECURITY NUMBER"],
#                 "EFFECTIVE DATE: (Local Office Only)": [
#                     "EFFECTIVE DATE: (Local Office Only)"
#                 ],
#                 "FIRST NAME": ["EMPLOYEE FIRST NAME"],
#                 "MIDDLE INITIAL": ["EMPLOYEE MIDDLE INITIAL"],
#                 "LAST NAME": ["EMPLOYEE LAST NAME"],
#                 "Mailing Address": ["EMPLOYEE Mailing Address"],
#                 "State of Residence": ["Employee State of Residence"],
#                 "County of Residence": ["Employee County of Residence"],
#                 "DATE OF BIRTH": ["EMPLOYEE DATE OF BIRTH"],
#                 "EMPLOYER NAME": ["EMPLOYER NAME"],
#                 "STREET NAME": ["EMPLOYER STREET NAME"],
#                 "COUNTY": ["EMPLOYER COUNTY"],
#                 "EMPLOYER PHONE": ["EMPLOYER PHONE"],
#                 "FIRST DATE WORKED AT YOUR LAST JOB": [
#                     "FIRST DATE WORKED AT YOUR LAST JOB"
#                 ],
#                 "DATE LAST WORK ENDED": ["DATE LAST WORK ENDED"],
#                 "What kind of work did you do on your last job": [
#                     "What kind of work did you do on your last job?"
#                 ],
#                 "Date": ["Date"],
#                 "Signature": ["Signature"],
#                 "E-Mail Address": ["Employee E-Mail Address"]
#             }
#         },
#         "claims_form": {
#             "default_entities": {
#                 "Date:": ["DATE"],
#                 "Name:": ["NAME"],
#                 "Occupation:": ["OCCUPATION"],
#                 "Emergency Contact:": ["EMERGENCY_CONTACT"],
#                 "Referred By:": ["REFERRED_BY"],
#                 "Gender:": ["GENDER"],
#                 "DOB:": ["DOB"],
#                 "Email:": ["EMAIL"],
#                 "City:": ["CITY"],
#                 "State:": ["STATE"],
#                 "Address:": ["ADDRESS"],
#                 "Zip:": ["ZIP"],
#                 "Emergency Contact Phone:": ["EMERGENCY_CONTACT_PHONE"],
#                 "Marital Status:": ["MARITAL_STATUS"],
#                 "Are you currently taking any medication? (If yes, please describe):": ["ARE_YOU_CURRENTLY_TAKING_"],
#                 "Phone #:": ["PHONE_"],
#                 "Describe your medical concerns (symptoms, diagnoses, etc):": ["DESCRIBE_YOUR_MEDICAL_CON"],
#             }
#         },
#     },
#     "illinois": {
#         "unemployment_form": {
#             "default_entities": {
#                 "Claimant ID": ["Claimant ID"],
#                 "SSN": ["SSN"],
#                 "First Name": ["Employee First Name"],
#                 "MI": ["Employee MI"],
#                 "Last Name": ["Employee Last Name"],
#                 "Date of Birth: (mm/dd/yyyy)": ["Date of Birth: (mm/dd/yyyy)"],
#                 "E-Mail Address": ["Employee E-Mail Address"],
#                 "Driver's License Number": ["Driving Licence Number"],
#                 "Primary Telephone": ["Employee Mailing Primary Telephone"],
#                 "Employer Name": ["Employer Name"],
#                 "Expiration Date": ["Expiration Date"],
#                 "Document Type": ["Document Type"],
#                 "Gender": ["Employee Gender"],
#                 "Ethnicity": ["Employee Ethinicity"],
#                 "Company Phone": ["Company Phone"],
#                 "For this period of employment, what date did you start": [
#                     "For this period of employment, what date did you start?"
#                 ],
#                 "Last date worked": ["Last date worked"],
#                 "CLAIMANT SIGNATURE": ["CLAIMANT SIGNATURE"],
#                 "DATE": ["DATE"]
#             }
#         },
#     },
#
#     # Generic document types, mostly supporting docs.
#     "all": {
#         "utility_bill": {
#             "default_entities": {
#                 "receiver_name": ["name"],
#                 "supplier_address": ["reciever address"],
#                 "due_date": ["due date"],
#                 "invoice_date": ["Invoice date"],
#                 "supplier_account_number": ["Account no"],
#             }
#         },
#         "driver_license": {
#             "default_entities": {
#                 "Document Id": ["DLN"],
#                 "Expiration Date": ["EXP"],
#                 "Date Of Birth": ["DOB"],
#                 "Family Name": ["LN"],
#                 "Given Names": ["FN"],
#                 "Issue Date": ["ISS"],
#                 "Address": ["Address"],
#             },
#             "derived_entities": {
#                 "SEX": {
#                     "rule": r"SEX.*?(?<!\w)(F|M)(?!\w)"
#                 }
#             }
#         },
#         "prior_auth_form": {
#             "default_entities": {
#               "rpName": ["rpName"],
#               "rpDate": ["rpDate"],
#               "rpPhone": ["rpPhone"],
#               "rpFax": ["rpFax"],
#               "rpNPI": ["rpNPI"],
#               "rpSpecialty": ["rpSpecialty"],
#               "rpContactName": ["rpContactName"],
#               "rpContactPhone": ["rpContactPhone"],
#               "requestTypeExtension": ["requestTypeExtension"],
#               "requestTypeInitial": ["requestTypeInitial"],
#               "prevAuthNumber": ["prevAuthNumber"],
#               "reviewTypeUrgent": ["reviewTypeUrgent"],
#               "reviewTypeNonUrgent": ["reviewTypeNonUrgent"],
#               "clinicalReasonForUrgency": ["clinicalReasonForUrgency"],
#               "pcpPhone": ["pcpPhone"],
#               "pcpFax": ["pcpFax"],
#               "pcpName": ["pcpName"],
#               "spPhone": ["spPhone"],
#               "spFax": ["spFax"],
#               "spNPI": ["spNPI"],
#               "spSpecialty": ["spSpecialty"],
#               "genderOther": ["genderOther"],
#               "genderUnknown": ["genderUnknown"],
#               "patientName": ["patientName"],
#               "patientPhone": ["patientPhone"],
#               "patientDoB": ["patientDoB"],
#               "subscriberName": ["subscriberName"],
#               "memberID": ["memberID"],
#               "groupNumber": ["groupNumber"],
#               "genderFemale": ["genderFemale"],
#               "genderMale": ["genderMale"],
#               "issuerPhone": ["issuerPhone"],
#               "issuerFax": ["issuerFax"],
#               "issuerDate": ["issuerDate"]
#             }
#
#         },
#         "pay_stub": {
#             "default_entities": {
#                 "employee_address": ["EMPLOYER ADDRESS"],
#                 "employee_name": ["EMPLOYEE NAME"],
#                 "end_date": ["PAY PERIOD(TO)"],
#                 "gross_earnings_ytd": ["YTD Gross"],
#                 "pay_date": ["PAY DATE"],
#                 "ssn": ["SSN"],
#                 "start_date": ["PAY PERIOD(FROM)"]
#             },
#             "derived_entities": {
#                 "EMPLOYER NAME": {
#                     "rule": r"([a-zA-Z ]*)\d*.*"
#                 },
#                 "RATE": {
#                     "rule": "Regular\n(.*?)\n"
#                 },
#                 "HOURS": {
#                     "rule": "Regular\n.*?\n(.*?)\n"
#                 }
#             }
#         },
#         "claims_form": {
#             "default_entities": {
#                 "Date": ["date"],
#                 "Name": ["name"],
#                 "Occupation": ["occupation"],
#                 "Emergency Contact": ["emergency_contact"],
#                 "Referred By": ["referred_by"],
#                 "Gender": ["gender"],
#                 "DOB": ["dob"],
#                 "Email": ["email"],
#                 "City": ["city"],
#                 "State": ["state"],
#                 "Address": ["address"],
#                 "Zip": ["zip"],
#                 "Emergency Contact Phone": ["emergency_contact_phone"],
#                 "Marital Status": ["marital_status"],
#                 "Are you currently taking any medication? (If y...": ["medications"],
#                 "_Phone": ["PHONE"],
#                 "Describe your medical concerns (symptoms, diag...": ["medical_condition"],
#             }
#         },
#     },
# }
