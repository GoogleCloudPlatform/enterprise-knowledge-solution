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


from processors.base.gcsio import GCSPath
import tempfile
from faker import Faker
import pyexcel


class XLSXGenerator:
    def __init__(self):
        self.fake = Faker()
        self.COLUMNS = {
            "Address": lambda: self.fake.address(),
            "City": lambda: self.fake.city(),
            "Country": lambda: self.fake.country(),
            "CC": lambda: self.fake.country_code(),
            "ZIP": lambda: self.fake.postalcode(),
            "zipCode": lambda: self.fake.postalcode(),
            "postcode": lambda: self.fake.postalcode(),
            "postal Code": lambda: self.fake.postalcode(),
            "street Address": lambda: self.fake.street_address(),
            "company": lambda: self.fake.company(),
            "price": lambda: self.fake.random_int(min=10, max=50000) / 100,
            "prc?": lambda: self.fake.random_int(min=10, max=50000) / 100,
            "item": lambda: self.fake.bothify("id-???-###"),
            "thing": lambda: self.fake.bothify("id-???-###"),
            "?id": lambda: self.fake.bothify("id-???-###"),
            "????": lambda: self.fake.word(),
        }

    def get_sheet(self, min_cols=2, max_cols=10, min_rows=100, max_rows=1000):
        cols = self.fake.random_elements(
            list(self.COLUMNS.keys()),
            unique=True,
            length=self.fake.random_int(min=min_cols, max=max_cols),
        )

        data = []
        data.append([self.fake.bothify(col) for col in cols])
        for row in range(self.fake.random_int(min=min_rows, max=max_rows)):
            data.append([self.COLUMNS[col]() for col in cols])
        return data

    def save(self, fname: GCSPath, min_sheets=1, max_sheets=4):
        # Get the book
        sheets = {}
        for sheet in self.fake.words(
            self.fake.random_int(min=min_sheets, max=max_sheets)
        ):
            sheets[sheet] = self.get_sheet()
        book = pyexcel.get_book(bookdict=sheets)

        # Save
        with fname.write_as_file() as f:
            book.save_as(f)

    def to_bytes(self, suffix=".xlsx") -> bytes:
        # Save and return as bytes
        with tempfile.NamedTemporaryFile(suffix=suffix) as f:
            self.save(GCSPath(f.name))
            with open(f.name, "rb") as r:
                return r.read()
