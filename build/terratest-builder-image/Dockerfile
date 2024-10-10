FROM golang:latest

ARG tf_version=1.8.1-1

# Install gcloud CLI
RUN apt-get update && \
    apt-get install -y apt-transport-https ca-certificates gnupg software-properties-common && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main"  | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list   && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && \
    apt-get install -y google-cloud-sdk

# Install terratest
RUN apt-get update && apt-get install -y gnupg software-properties-common curl \
    && wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | tee /usr/share/keyrings/hashicorp-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list \
    && apt-get update \
    && apt-get install terraform=${tf_version}

# Set the working directory
WORKDIR /app