# syntax=docker/dockerfile:1

FROM python:3.11-slim

# # Install required system packages and cleanup to reduce image size
RUN apt-get update -y && \
    apt-get install --no-install-recommends -y -q \
    wkhtmltopdf mime-support media-types && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create user for the application
ENV HOME=/app/
RUN useradd -rm -d $HOME -s /bin/bash -u 1000 app

# Bootstrap uv
RUN python3 -m ensurepip --upgrade
RUN --mount=from=reqs,target=/reqs pip install --require-hashes -r /reqs/requirements_bootstrap.txt
ENV VIRTUAL_ENV=/usr/local

# Copy requirements into the image and install the dependencies
COPY --chown=app requirements.txt $HOME
RUN python3 -m uv pip install --require-hashes -r $HOME/requirements.txt

# Copy and install the libraries to the image
COPY --from=src --chown=app / /components/doc-classifier/src/
RUN python3 -m uv pip install \
  -e components/doc-classifier/src

# Switch to default user
WORKDIR $HOME
USER app

ENTRYPOINT [ "main" ]
