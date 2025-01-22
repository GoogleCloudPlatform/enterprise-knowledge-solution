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
  Tests format data for bq function
"""
import os
import json
from .format_data_for_bq import format_data_for_bq

# disabling pylint rules that conflict with pytest fixtures
# pylint: disable=unused-argument,redefined-outer-name,unused-import

os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
os.environ["GOOGLE_CLOUD_PROJECT"] = "fake-project"

def test_format_data_for_bq():
  input_value = [{"entity":"name","value":"Max"},
                 {"entity":"last_naame","value":"Doe"}
                 ]
  output = format_data_for_bq(input_value)
  expected_output = json.dumps(({"last_naame": "Doe", "name": "Max"}))
  assert output==expected_output

