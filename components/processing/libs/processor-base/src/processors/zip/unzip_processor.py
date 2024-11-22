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

import logging
import zipfile
from typing import Dict

from processors.base.gcsio import GCSPath

# mypy: disable-error-code="import-untyped"


logger = logging.getLogger(__name__)


def unzip_processor(source: GCSPath, output_dir: GCSPath) -> Dict:
    # Unzip the zip archive
    logger.info(f"Unzipping {str(source)}")
    with (
        source.read_as_file() as r,
        zipfile.ZipFile(r) as z,
        output_dir.write_folder() as output,
    ):
        z.extractall(output)

    # Add it in as a rendered type
    return dict()
