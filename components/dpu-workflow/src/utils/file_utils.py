# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import random
import string
from collections import defaultdict
from datetime import datetime
from typing import Dict, Tuple, List




def supported_files_by_type(file_list, file_type_to_processor) -> \
    Tuple[Dict[str, List[str]], List[str]]:
    supported_file_types = set(
        item["file-suffix"].lower() for item in file_type_to_processor
    )
    unsupported_files = []
    files_by_type = defaultdict(list)
    for input_file in file_list:
        file_type = input_file.split(".")[-1].lower()
        if file_type in supported_file_types:
            files_by_type[file_type].append(input_file)
        else:
            unsupported_files.append(input_file)
    return files_by_type, unsupported_files

def get_random_process_folder_name():
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits,
                                    k=8))
    process_folder = (f"docs-processing-{datetime.now().strftime('%d-%m-%Y')}-"
                      f"{suffix}")
    return process_folder


def get_mv_params(files_to_process, input_folder, process_bucket,
                  process_folder):
    input_folder_with_prefix = f"{input_folder}/" if input_folder else ""
    parameter_obj_list = []
    for typ in files_to_process.keys():
        parameter_obj = {
            "source_object":      f"{input_folder_with_prefix}*.{typ}",
            "destination_bucket": process_bucket,
            "destination_object": f"{process_folder}/{typ}/",
        }
        parameter_obj_list.append(parameter_obj)
    return parameter_obj_list