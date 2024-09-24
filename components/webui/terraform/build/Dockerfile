# syntax=docker/dockerfile:1

FROM python:3.11-slim

# Install required system packages and cleanup to reduce image size
RUN apt-get update -y && \
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

# Copy app source filed
COPY --from=libs --chown=app /app $HOME/app/
COPY --from=libs --chown=app /src $HOME/src/

# Expose port you want your app on
EXPOSE 8080

# Copy app code and set working directory
WORKDIR $HOME
USER app

# TODO - Implement Sign On in the App and use the service account to access the GCP APIs
# ENV GOOGLE_APPLICATION_CREDENTIALS=./adc.json
# Explicitly set a user to avoid running as root
ENTRYPOINT ["streamlit", "run", "src/Home.py", "--server.port=8080", "--server.address=0.0.0.0"]
