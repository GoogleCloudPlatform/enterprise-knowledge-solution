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

FROM golang:1.23.2

ARG tf_version=1.8.1-1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install terratest
RUN apt-get update && apt-get install -y gnupg=2.2.40-1.1 software-properties-common=0.99.30-4.1~deb12u1 curl=7.88.1-10+deb12u7 --no-install-recommends \
  && wget -nv -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | tee /usr/share/keyrings/hashicorp-archive-keyring.gpg \
  && echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list \
  && apt-get update \
  && apt-get -y install terraform=${tf_version} --no-install-recommends \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Install gcloud SDK
RUN wget -nv https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-497.0.0-linux-x86_64.tar.gz && \
  tar -xvzf google-cloud-cli-497.0.0-linux-x86_64.tar.gz && \
  ./google-cloud-sdk/install.sh -q && \
  rm google-cloud-cli-497.0.0-linux-x86_64.tar.gz

# make gcloud available on PATH
ENV PATH=$PATH:/go/google-cloud-sdk/bin
