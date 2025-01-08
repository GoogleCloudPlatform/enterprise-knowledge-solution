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
Unit Tests for Claim ORM object
"""

from common.models import Claim


def test_new_claim():
  # a placeholder unit test so github actions runs until we add more
  claim_id = "test_id123"
  claim = Claim(claim_id=claim_id)

  assert claim.claim_id == claim_id
