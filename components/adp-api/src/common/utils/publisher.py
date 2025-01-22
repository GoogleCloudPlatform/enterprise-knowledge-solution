"""
Copyright 2022 Google LLC

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

""" Publishes the messages to pubsub """

import json
from google.cloud import pubsub_v1
from common.config import PROJECT_ID, TOPIC_ID

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)


def publish_document(message_dict):
  # print("inside publisher")
  message_json = json.dumps(message_dict)
  message_json = message_json.encode("utf-8")
  print(f"Publishing {topic_path} topic message: {message_json}")
  future = publisher.publish(topic_path, message_json)
  return future.result()

