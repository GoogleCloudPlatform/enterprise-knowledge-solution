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

import re
from typing import Optional, Tuple


def is_valid_processor_id(processor_id: str) -> Optional[Tuple[str, str, str]]:
    """
    Validates a GCP DocumentAI processor ID.

    Args:
        processor_id: The processor ID string to validate.

    Returns:
        Tuple (project_id, location, processor_id) if the processor ID is valid, False otherwise.
    """
    pattern = r"^projects\/([a-z][a-z0-9\-]{4,28}[a-z0-9])\/locations\/(us|eu)\/processors\/([a-zA-Z0-9_-]+)$"
    match = re.match(pattern, processor_id)
    if not match:
        return None
    return match.group(1), match.group(2), match.group(3)
