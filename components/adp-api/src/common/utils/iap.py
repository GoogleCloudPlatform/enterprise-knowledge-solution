"""
Copyright 2023 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


from google.auth.transport.requests import Request
from google.oauth2 import id_token
import requests
from common.utils.logging_handler import Logger
from common.config import PROJECT_ID, IAP_SECRET_NAME
from google.cloud import secretmanager

logger = Logger.get_logger(__name__)

client = secretmanager.SecretManagerServiceClient()


def get_secret(project_name, secret_name, version_num):
  try:
    logger.info(f"get_secret with project_name={project_name} secret_name={secret_name} version_num={version_num}")
    # Returns secret payload from Cloud Secret Manager
    client = secretmanager.SecretManagerServiceClient()
    name = client.secret_version_path(project_name, secret_name, version_num)
    response = client.access_secret_version(request={"name": name})
    payload = response.payload.data.decode("UTF-8")
    logger.info(f"get_secret with payload={payload}")
    return payload
  except Exception as exc:
    logger.info(f"get_secret skipping .. ")
    return None


def send_iap_request(url, method="GET", **kwargs):
  logger.info(f"send_iap_request with url={url}, method={method}, {kwargs}")
  client_id = get_secret(PROJECT_ID, IAP_SECRET_NAME, "latest")
  logger.info(f"send_iap_request client_id={client_id}")
  if client_id is not None:
    response = make_iap_request(url, client_id, method=method, **kwargs)
  else:
    response = requests.post(url, **kwargs)
  return response


def make_iap_request(url, client_id, method='GET', **kwargs):
  """Makes a request to an application protected by Identity-Aware Proxy.

  Args:
    url: The Identity-Aware Proxy-protected URL to fetch.
    client_id: The client ID used by Identity-Aware Proxy.
    method: The request method to use
            ('GET', 'OPTIONS', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE')
    **kwargs: Any of the parameters defined for the request function:
              https://github.com/requests/requests/blob/master/requests/api.py
              If no timeout is provided, it is set to 90 by default.

  Returns:
    The page body, or raises an exception if the page couldn't be retrieved.
  """
  # Set the default timeout, if missing
  if 'timeout' not in kwargs:
    kwargs['timeout'] = 90

  open_id_connect_token = ""

  # Obtain an OpenID Connect (OIDC) token from metadata server or using service
  # account.
  try:
    open_id_connect_token = id_token.fetch_id_token(Request(), client_id)
    logger.info(f"make_iap_request with open_id_connect_token={open_id_connect_token} for client_id={client_id}")
  except Exception as exc:
    logger.warning(f"make_iap_request could not get open_id_connect_token for client_id={client_id}")
    logger.error(exc)

  # Fetch the Identity-Aware Proxy-protected URL, including an
  # Authorization header containing "Bearer " followed by a
  # Google-issued OpenID Connect token for the service account.
  resp = requests.request(
      method, url,
      headers={'Authorization': 'Bearer {}'.format(
          open_id_connect_token)}, **kwargs)
  if resp.status_code == 403:
    raise Exception('Service account does not have permission to '
                    'access the IAP-protected application.')
  else:
    return resp

