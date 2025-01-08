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
This file is user editable
keys denote --> document type
# which a user has to pass as a 3rd argument in the
match_json.py module. # to find the matching score between the two JSON.
# "match_json.py" will use only the entities listed under a document type
# for matching score calculation.
# The values under each key are mapped to the values mentioned in
# "Entity Standardization" file
# 'COLUMN C' as it is supposed that the values of each key match with the
#  key of the
# input json file.DOB format: yyyy/mm/dd
# Outer key is the doc type and inner keys signifies the keys or the entities
# that needs to be matched with the
# entities of the application doc. Inner keys must be weighted and their total
#  weightage must be equal to 1

# DATES to be provided with their format used in the document
Acceptable format for DATES by Example
   INPUT JSON Date      FORMAT FOR THIS CONFIG
1. 1990/12/02        -->  %Y/%m/%d
2. 1990-12-02        -->  %Y-%m-%d
3. 03/11/21          -->  %d-%m-%y --> %y if year is just two characters
4. 28 09 1990        -->  %d %m %Y
5. 28/Sep/1990       -->  %d/%b/%Y
6. 28/September/1990 -->  %d/%B/%Y
"""
# Values for the keys are just an example
SUPPORT_DOC_TYPE = 'driver_license'
# date format for supporting doc follows American Date Format: 'yyyy/mm/dd'.
MATCHING_USER_KEYS_SUPPORTING_DOC = {
    # 'driver_license': {
    #    'name': 0.16, 'dob': (0.16, '%y/%m/%d'), 'sex': 0.16, 'dl_no': 0.16},
    'driver_license': {
        'name': 0.25,
        'dob': (0.25, '%Y-%m-%d'),
        'dl_no': 0.25,
        'sex': 0.25
    },
    'utility_bill': {
        'name': 0.50,
        'residential_address': 0.50
    },
    'pay_stub': {
        'employee_name': 0.16,
        'ytd': 0.14,
        'rate': 0.14,
        'hours': 0.14,
        'pay_period_from': (0.14, '%Y-%m-%d'),
        'pay_period_to': (0.14, '%Y-%m-%d'),
        'ssn': 0.14
    },
    'claims_form': {
        'employer_info': 0.19,
        'work_start_date': (0.19, '%Y-%m-%d'),
        'employer_name': 0.24,
        'employer_address': 0.19,
        'employer_city': 0.19
    }
}

# date format for application doc will be state-wise
APPLICATION_DOC_TYPE = 'unemployement'
STATE = 'arkansas'

APPLICATION_DOC_DATE_FORMAT = {
    'unemployment_form': {
        'arizona': '%Y-%m-%d',
        'arkansas': '%Y-%m-%d',
        'california': '%Y-%m-%d',
        'illinois': '%Y/%m/%d'
    }
}
