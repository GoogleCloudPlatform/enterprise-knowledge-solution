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

"""
  Pytest Fixture for getting testclient from fastapi
"""
import pytest
# disabling pylint rules that conflict with pytest fixtures
# pylint: disable=unused-argument,redefined-outer-name,unused-import
from common.testing.firestore_emulator import firestore_emulator, clean_firestore
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client_with_emulator(clean_firestore, scope="module"):
  test_client = TestClient(app)
  yield test_client
