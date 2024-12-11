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

from dataclasses import dataclass


@dataclass
class JobConfig:
    gcs_input_prefix: str
    gcs_output_uri: str
    run_id: str


@dataclass
class ProcessorConfig:
    project: str
    location: str
    processor_id: str
    timeout: int


@dataclass
class AlloyDBConfig:
    primary_instance: str
    database: str
    user: str


@dataclass
class BigQueryConfig:
    general_output_table_id: str
