# syntax=docker/dockerfile:1

FROM python:3.11-slim

# # Install required system packages and cleanup to reduce image size
RUN apt-get update -y && \
  apt-get install --no-install-recommends -y -q \
  wkhtmltopdf=0.12.6-2 mime-support=3.66 media-types=10.1.0 && \
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
COPY --from=libs --chown=app / /components/processing/libs/
RUN python3 -m uv pip install --no-cache-dir \
  -e components/processing/libs/processor-base \
  -e components/processing/libs/processor-msg \
  -e components/processing/libs/processor-xlsx

# Switch to default user
WORKDIR $HOME
USER app

ENTRYPOINT [ "msg_processor" ]
