# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

ENV HOME=/app
WORKDIR $HOME

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Bootstrap venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the dependencies into venv
RUN --mount=from=libs,target=/libs pip install --no-cache-dir --require-hashes -r /libs/requirements.txt

# Final stage
FROM python:3.12-slim

# Create user for the application
ENV HOME=/app
# Explicitly set a user to avoid running as root
RUN useradd -rm -d $HOME -s /bin/bash -u 1000 app
USER app

# Copy venv from builder
COPY --from=builder --chown=app /opt/venv /opt/venv
# Copy app source filed from named context: libs
# hadolint ignore=DL3022
COPY --from=libs --chown=app /app $HOME/app/
# hadolint ignore=DL3022
COPY --from=libs --chown=app /src $HOME/src/

WORKDIR $HOME
ENV PATH="/opt/venv/bin:$PATH"

# Expose port you want your app on
EXPOSE 8080

ENTRYPOINT ["streamlit"]
CMD ["run", "src/Home.py", "--server.port=8080", "--server.address=0.0.0.0"]
