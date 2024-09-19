# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os

from dotenv import load_dotenv
from invoke import task

# Find the base directory for invoke
BASE_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.join(BASE_DIR, "../../")


load_dotenv()


@task
def local_dev(c, debug=False):
    """Start local streamlit webui"""
    OPTS = " ".join(
        [
            "--browser.gatherUsageStats=false",  # Disable usage stats
            "--server.headless=true",  # Disable collection of email address
        ]
    )
    if debug:
        OPTS += " --logger.level=DEBUG"
    with c.cd(ROOT_DIR):
        c.run(f"./run.sh streamlit run {OPTS} components/webui/src/Home.py", pty=True)
