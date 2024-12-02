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

# derp