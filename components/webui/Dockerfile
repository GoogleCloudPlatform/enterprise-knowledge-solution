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


# Initialize a new build stage and set the
FROM python:3.10

# Explicitly set a user to avoid running as root
USER daemon

# Expose port you want your app on
EXPOSE 8080

# Copy app code and set working directory
WORKDIR /app
COPY . ./

# Upgrade pip, install requirements and install curl
RUN python -m pip install --no-cache-dir --upgrade pip==24.2
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

# TODO - Implement Sign On in the App and use the service account to access the GCP APIs
# ENV GOOGLE_APPLICATION_CREDENTIALS=./adc.json
ENTRYPOINT ["streamlit", "run", "src/Home.py", "--server.port=8080", "--server.address=0.0.0.0"]