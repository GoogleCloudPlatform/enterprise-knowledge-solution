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

""" Arguments Classess """
# pylint:disable=E0401,R0903,E0611
from pydantic import BaseModel
from typing import Optional


class SearchPayload(BaseModel):
  """ Argument class for Search
  """
  term: Optional[object] = None
  filter_key: Optional[str] = None
  filter_value: Optional[object] = None
  limit_start: Optional[int] = None
  limit_end: Optional[int] = None
