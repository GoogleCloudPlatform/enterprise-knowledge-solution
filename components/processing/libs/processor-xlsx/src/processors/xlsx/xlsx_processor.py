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
from typing import Dict

import pyexcel
from markdowngenerator import MarkdownGenerator
from processors.base.gcsio import GCSPath

# mypy: disable-error-code="import-untyped"

logger = logging.getLogger(__name__)


def cleanse_string(c):
    c = str(c)
    c = c.replace("|", "\\|")
    c = c.strip()
    if "\n" in c:
        return c.split("\n")
    return c


def xlsx_processor(source: GCSPath, output_dir: GCSPath) -> Dict:

    # Load the book
    logging.info(f"Extracting spreadsheet {str(source)}")
    with source.read_as_file() as r:
        book = pyexcel.get_book(
            file_name=r,
            force_file_type=source.suffix[1:],
        )

        for name in book.sheet_names():
            sheet = book.sheet_by_name(name)

            # Assume the first row is the header for the data
            sheet.name_columns_by_row(0)

            # Markdown output
            with (
                GCSPath(output_dir, name + ".txt").write_as_file() as f,
                MarkdownGenerator(filename=f) as m,
            ):
                m.addHeader(1, name)

                # Prepare data
                data = []
                first_row = True
                for row in sheet.to_array():
                    if first_row:
                        first_row = False
                        continue
                    data.append([cleanse_string(v) for v in row])

                # Generate the table
                m.addTable(
                    header_names=sheet.colnames, alignment="left", row_elements=data
                )

    return dict()
