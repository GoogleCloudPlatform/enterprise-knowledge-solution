# syntax=docker/dockerfile:1
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


FROM python:3.11-slim

# # Install required system packages and cleanup to reduce image size
RUN apt-get update -y && \
  apt-get install --no-install-recommends -y -q \
  wkhtmltopdf=0.12.6-2+b1 mime-support=3.66 media-types=10.0.0 && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create user for the application
ENV HOME=/app/
RUN useradd -rm -d $HOME -s /bin/bash -u 1000 app

# Bootstrap uv
RUN python3 -m ensurepip --upgrade
RUN --mount=from=reqs,target=/reqs pip install --no-cache-dir --require-hashes -r /reqs/requirements_bootstrap.txt
ENV VIRTUAL_ENV=/usr/local

# Copy requirements into the image and install the dependencies
COPY --chown=app requirements.txt $HOME
RUN python3 -m uv pip install --no-cache-dir --require-hashes -r $HOME/requirements.txt

# Copy and install the libraries to the image
# hadolint ignore=DL3022
COPY --from=libs --chown=app / /components/processing/libs/
RUN python3 -m uv pip install --no-cache-dir \
  -e components/processing/libs/processor-base \
  -e components/processing/libs/processor-msg \
  -e components/processing/libs/processor-xlsx

# Switch to default user
WORKDIR $HOME
USER app

ENTRYPOINT [ "msg_processor" ]
