FROM golang:1.23.2

ARG tf_version=1.8.1-1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install terratest
RUN apt-get update && apt-get install -y gnupg=2.4.5 software-properties-common=0.99.22 curl=8.10.1 --no-install-recommends \
  && wget -nv -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | tee /usr/share/keyrings/hashicorp-archive-keyring.gpg \
  && echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list \
  && apt-get update \
  && apt-get -y install terraform=${tf_version} --no-install-recommends \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

