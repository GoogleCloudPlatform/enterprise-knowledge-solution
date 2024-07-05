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


import pathlib

from extract_msg import openMsg
from extract_msg.msg_classes import MessageBase
from extract_msg.enums import ErrorBehavior

from processors.base.gcsio import GCSPath
from typing import Dict
import logging


error_behavior = ErrorBehavior.RTFDE | ErrorBehavior.ATTACH_NOT_IMPLEMENTED
MAX_BODY_SIZE = 1024
logger = logging.getLogger(__name__)


def msg_to_dict(msg: MessageBase) -> Dict:
    body = msg.body
    return dict(
        addr_from=msg.sender,
        addr_to=msg.to,
        addr_cc=msg.cc,
        addr_bcc=msg.bcc,
        subject=msg.subject,
        date=msg.date,
        body=body[:MAX_BODY_SIZE] if body else "",
    )


def msg_processor(
    source: GCSPath,
    output_dir: GCSPath,
) -> Dict:
    logger.info(f"Extracting message {source}")

    # Generate generic output
    with (
        source.read_as_file() as r,
        openMsg(r, errorBehavior=error_behavior) as msg,
        output_dir.write_folder() as output,
    ):

        # It is a MessageBase (more exposed functionality)
        nmsg: MessageBase = msg  # pyright: ignore[reportAssignmentType]

        # Extract attachments
        nmsg.save(
            allowFallback=True,
            customPath=output,
            customFilename="att",
            skipBodyNotFound=True,
            extractEmbedded=True,
            skipNotImplemented=True,
            overwriteExisting=True,
            attachmentsOnly=True,
        )

        # Extract message content
        msg_path = pathlib.Path(output, f"{nmsg.defaultFolderName}.txt")  # pylint: disable=no-member
        with open(msg_path, "wb") as f:
            f.write(nmsg.getSaveBody())  # pylint: disable=no-member

        # Capture meta data
        return msg_to_dict(nmsg)
