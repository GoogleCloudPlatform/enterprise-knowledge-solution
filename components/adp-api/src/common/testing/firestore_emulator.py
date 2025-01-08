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
Firestore emulator fixture for re-use in testing
"""

import os
import subprocess
import time

import requests

import pytest

# disabling pylint rules that conflict with pytest fixtures
# pylint: disable=unused-argument,redefined-outer-name


# recreate the emulator each module - could consider changing to session
# pylint: disable = consider-using-with, subprocess-popen-preexec-fn
@pytest.fixture(scope="module")
def firestore_emulator():

  emulator = subprocess.Popen(
      "firebase emulators:start --only firestore --project fake-project",
      shell=True,
  )
  time.sleep(15)

  os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
  os.environ["GOOGLE_CLOUD_PROJECT"] = "fake-project"
  os.environ["PROJECT_ID"] = "fake-project"

  # yield so emulator isn't recreated each test
  yield emulator

  # os.killpg(os.getpgid(emulator.pid), signal.SIGTERM) #commenting this line
  # delete debug files
  # some get deleted, not all

  try:
    os.remove("firestore-debug.log")
    os.remove("ui-debug.log")
  except OSError:
    pass

  # TODO: script to unset / reset the environmental variables
  # instead of just delete


# pylint: disable = line-too-long
@pytest.fixture
def clean_firestore(firestore_emulator):
  requests.delete(
      "http://localhost:8080/emulator/v1/projects/fake-project/databases/(default)/documents"
  )
