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


import tempfile
import argparse
import email.utils
from faker import Faker
import datetime
from dotenv import load_dotenv
import os
from processors.base.gcsio import GCSPath
from extract_msg import OleWriter
from extract_msg.enums import PropertiesType
from extract_msg.properties import PropertiesStore
from extract_msg.properties.prop import createNewProp, createProp
from processors.xlsx import XLSXGenerator
import uuid


class emptyDirectoryEntry:
    def __init__(self, name):
        self.name = name
        self.entry_type = 1
        self.clsid = b""
        self.dwUserFlags = 0
        self.createTime = 0
        self.modifyTime = 0


class emptyStorageDirectoryEntry(emptyDirectoryEntry):
    def __init__(self, name):
        super().__init__(name)
        self.entry_type = 2


def create_msg_file(
    omsg: str,
    hdrs: list,
    subject: str,
    body: str,
    timestamp: datetime.datetime,
    att=None,
):
    w = OleWriter()

    new_props = PropertiesStore(data=None, type_=PropertiesType.MESSAGE, writable=True)

    # Property use Unicode strings
    # 340D0003 is hex property, 265849 is value
    x = createNewProp("340D0003")
    x.value = 265849  # pyright: ignore
    new_props.addProperty(x)

    # Add sent time property
    sentTime = createNewProp("00390040")
    sentTime.value = datetime.datetime.now()  # pyright: ignore
    new_props.addProperty(sentTime)

    # Write out properties
    db = new_props.toBytes()
    # Not clear why this is required, but it is
    db = db[:24] + b"\x00\x00\x00\x00\x00\x00\x00\x00" + db[24:]
    w.addOleEntry(
        ["__properties_version1.0"],
        emptyStorageDirectoryEntry("__properties_version1.0"), # pyright: ignore
        db,
    )

    # Set classType
    classType = bytes("IPM.Note", "utf_16_le")
    w.addOleEntry(
        ["__substg1.0_001A001F"],
        emptyStorageDirectoryEntry("__substg1.0_001A001F"),  # pyright: ignore
        classType,
    )

    # Set body
    w.addOleEntry(
        ["__substg1.0_1000001F"],
        emptyStorageDirectoryEntry("__substg1.0_1000001F"),  # pyright: ignore
        bytes(body, "utf_16_le"),
    )

    # Set header
    w.addOleEntry(
        ["__substg1.0_007D001F"],
        emptyStorageDirectoryEntry("__substg1.0_007D001F"),  # pyright: ignore
        bytes("\n".join(hdrs), "utf_16_le"),
    )

    # Set subject
    w.addOleEntry(
        ["__substg1.0_0037001F"],
        emptyStorageDirectoryEntry("__substg1.0_0037001F"),  # pyright: ignore
        bytes(subject, "utf_16_le"),
    )

    # Do the attachments
    if att:
        i = 0
        for k, v in att.items():

            # Attachment properties.
            attach_props = PropertiesStore(
                data=None, type_=PropertiesType.ATTACHMENT, writable=True)
            attach_prop_data = b'\x03\x00\x057\x07\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00'
            attach_props.addProperty(createProp(attach_prop_data), True)

            # Add in Ole entries
            label = f"__attach_version1.0_{i:08d}"
            w.addOleEntry(
                [label],
                emptyDirectoryEntry(label),  # pyright: ignore
                b"")
            w.addOleEntry(
                [label, "__properties_version1.0"],
                emptyStorageDirectoryEntry("__properties_version1.0"), # pyright: ignore
                attach_props.toBytes(),
            )
            w.addOleEntry(
                [label, "__substg1.0_3707001F"],
                emptyStorageDirectoryEntry("__substg1.0_3707001F"),  # pyright: ignore
                bytes(k, "utf_16_le"),
            )
            w.addOleEntry(
                [label, "__substg1.0_37010102"],
                emptyStorageDirectoryEntry("__substg1.0_37010102"),  # pyright: ignore
                v,
            )
            i += 1

    # Pure synthetic producing of data!
    # This is all empty data but still needed
    w.addOleEntry(
        ["__nameid_version1.0"],
        emptyDirectoryEntry("__nameid_version1.0"),  # pyright: ignore
        b""
    )
    for key in ["__substg1.0_00020102", "__substg1.0_00030102", "__substg1.0_00040102"]:
        w.addOleEntry(
            ["__nameid_version1.0", key],
            emptyStorageDirectoryEntry(key),  # pyright: ignore
            b""
        )

    w.write(omsg)


class MSGGenerator:
    def __init__(self):
        self.fake = Faker()

        self.people = []
        for i in range(100):
            self.people.append(f"{self.fake.name()} <{self.fake.company_email()}>")

        self.xlsx_generator = XLSXGenerator()
        self.msg_generator = self

    def get_attachments(self):
        att = dict()

        # Attachments (Excel)
        for fname in self.fake.words(self.fake.random_int(min=0, max=4)):
            att[f"{fname}.xlsx"] = self.xlsx_generator.to_bytes()

        # Attachments (MSG)
        for fname in self.fake.words(self.fake.random_int(min=0, max=1)):
            att[f"{fname}.msg"] = self.msg_generator.to_bytes()

        return att

    def get_person(self):
        return self.fake.random_element(self.people)

    def get_people(self, min=1, max=4):
        return "; ".join(
            self.fake.random_elements(
                self.people,
                length=self.fake.random_int(min=min, max=max),
                unique=True,
            )
        )

    def save(self, msg_file: GCSPath):
        # Timestamp
        ts = self.fake.past_datetime("-5y")

        # Body of email
        body_paragraphs = self.fake.random_int(min=4, max=20)
        paragraphs = (
            [self.fake.sentence(2)]
            + [self.fake.paragraph(10) for i in range(body_paragraphs)]
            + [self.fake.sentence(2)]
        )

        # Create the raw message file
        with msg_file.write_as_file() as f:
            create_msg_file(
                omsg=f,
                hdrs=[
                    f"Date: {email.utils.format_datetime(ts)}",
                    f"From: {self.get_person()}",
                    f"To: {self.get_people(min=1, max=4)}",
                    f"Cc: {self.get_people(min=0, max=10)}",
                ],
                subject=self.fake.sentence(),
                body="\n\n".join(paragraphs),
                timestamp=ts,
                att=self.get_attachments(),
            )

    def to_bytes(self) -> bytes:
        # Save and return as bytes
        with tempfile.NamedTemporaryFile(suffix=".msg") as f:
            self.save(GCSPath(f.name))
            with open(f.name, "rb") as r:
                return r.read()


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        prog="msg_generator",
        description="Generate .msg files for parsing test purposes",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output_dir",
        default=f"gs://{os.getenv('GCS_INPUT_BUCKET')}/input",
        type=str,
        help="Output directory for .msg files")
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Count of .msg files to produce"
    )
    parser.add_argument(
        "--name-prefix",
        type=str,
        default=f"gen-{uuid.uuid1()}",
        help="Prefix of filename"
    )

    args = parser.parse_args()

    generator = MSGGenerator()
    for i in range(args.count):
        generator.save(GCSPath(f"{args.output_dir}/{args.name_prefix}-{i:08d}.msg"))


if __name__ == "__main__":
    main()
