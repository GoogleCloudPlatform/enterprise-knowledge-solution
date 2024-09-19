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
"""Utilities for abstracting over GCS objects, paths, and local files and paths

    These utilities enable to build code that will work equally well using GCS as
    using local filesystems within Python.
"""
import base64
import contextlib
import functools
import hashlib
import json
import logging
import mimetypes
import os
import re
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Iterator, Optional, TypeVar

from google.api_core.client_info import ClientInfo
from google.cloud import storage  # type: ignore[attr-defined, import-untyped]

logger = logging.getLogger(__name__)


# Update the timeout for operations
storage._DEFAULT_TIMEOUT = 300  # pyright: ignore  pylint: disable=protected-access


def GCS_TMP_PREFIX():  # pylint: disable=invalid-name
    """Return the temporary GCS location"""
    return os.environ["GCS_TMP_PREFIX"]


def get_mimetype(path: str) -> str:
    """Infer the mimetype of a path

    Returns application/octet-stream if it fails.
    """
    if path.lower().endswith(".md"):
        return "text/plain"
    mime_type = mimetypes.guess_type(path)[0]
    if mime_type:
        return mime_type
    return "application/octet-stream"


TGCSPath = TypeVar("TGCSPath", bound="GCSPath")  # pylint: disable=invalid-name


class GCSPath:
    """GCSPath - abstraction for a path that can be a local or GCS object or path"""

    client: Optional[storage.Client] = None

    @classmethod
    def open_bucket(cls, bucket: str):
        """Open a bucket."""
        if cls.client is None:
            cls.client = storage.Client(
                client_info=ClientInfo(
                    user_agent="cloud-solutions/eks-doc-processors-v1",
                )
            )
        return cls.client.bucket(bucket)  # pyright: ignore

    def __init__(
        self,
        *paths: TGCSPath | str,
        crc32c: Optional[str] = None,
    ):
        self.bucket: Optional[storage.Bucket] = None
        self.path: str
        self.preset_crc32c = crc32c

        gcs_test_path = "/".join([str(x) for x in paths])
        gcs_match = re.match(r"gs://([^/]+)/(.*)", gcs_test_path)
        if gcs_match:
            self.bucket = self.open_bucket(gcs_match.group(1))
            self.path = gcs_match.group(2)
        else:
            self.path = str(Path(*[str(p) for p in paths]).resolve())

    def is_gcs(self) -> bool:
        """Return if the path is GCS or not (local filesystem)"""
        if self.bucket:
            return True
        return False

    # Only valid if it is GCS
    def as_gcs_link(self):
        """Return HTTPS storage link or file:// for path"""
        if self.bucket:
            return (
                '<a href="https://storage.cloud.google.com/'
                + f'{self.bucket.name}/{self.path}">{str(self)}</a>'
            )
        return f'<a href="file://{self.path}">{str(self)}</a>'

    # See if the file or object exists
    def exists(self) -> bool:
        """Return if object or path exists"""
        if self.bucket:
            return self.bucket.blob(self.path).exists()
        return Path(self.path).exists()

    # Open file/blob for read/write
    def open(self, mode, encoding=None):
        """Open for reading/writing"""
        logger.debug("Opening %s with open %s", str(self), mode)
        if self.bucket:
            if mode[0] == "w":
                return self.bucket.blob(self.path).open(
                    content_type=self.mimetype, mode=mode
                )
            return self.bucket.blob(self.path).open(mode=mode)

        # if writing, ensure output folder exists
        if mode[0] == "w":
            os.makedirs(Path(self.path).parent, exist_ok=True)

        return open(self.path, mode=mode, encoding=encoding)

    # Move objects / files
    def move(self, dest: str | TGCSPath):
        """Move current object (file) to a target object (file)"""
        self.copy(dest, delete_orig=True)

    # Copy objects / files
    def copy(self, idest: str | TGCSPath, delete_orig=False):
        """Move current object (file) to a target object (file), optionally deleting original"""

        if isinstance(idest, str):
            dest = GCSPath(idest)
        else:
            dest = idest

        # If the same, stop now
        if str(self) == str(dest):
            return

        # Copy two GCS objects
        def gcs_rewrite(source, dest):
            src = source.bucket.blob(source.path)
            dst = dest.bucket.blob(dest.path)
            token, _, _ = dst.rewrite(source=src)
            while token is not None:
                token, _, _ = dst.rewrite(source=src, token=token)

        # Make local directories if necessary
        if not dest.bucket:
            os.makedirs(Path(dest.path).parent, exist_ok=True)

        if self.bucket:
            if dest.bucket:
                logger.debug("Copying remotely from %s to %s", str(self), str(dest))
                gcs_rewrite(self, dest)
                if delete_orig:
                    self.delete()
            else:
                # Download from GCS
                logger.debug("Downloading from %s to %s", str(self), str(dest))
                self.bucket.blob(self.path).download_to_filename(dest.path)
                if delete_orig:
                    self.delete()
        else:
            if dest.bucket:
                # Upload to GCS
                logger.debug("Uploading from %s to %s", str(self), str(dest))
                dest.bucket.blob(dest.path).upload_from_filename(
                    str(self),
                    content_type=get_mimetype(dest.path),
                )
                if delete_orig:
                    self.delete()
            else:
                if delete_orig:
                    # Move locally
                    logger.debug("Moving locally from %s to %s", str(self), str(dest))
                    Path(self.path).rename(dest.path)
                else:
                    # Copy locally
                    logger.debug("Copying locally from %s to %s", str(self), str(dest))
                    shutil.copyfile(self.path, dest.path)

    # Write as text the file or object
    def write_text(self, txt, encoding="utf8"):
        """Write text to the object or file"""
        logger.debug("Writing text to %s", str(self))
        if self.bucket:
            self.bucket.blob(self.path).upload_from_string(
                txt, content_type=self.mimetype
            )
            return

        os.makedirs(Path(self.path).parent, exist_ok=True)

        with open(self.path, mode="wt", encoding=encoding) as w:
            w.write(txt)

    # Read as text the file or object
    def write_bytes(self, b):
        """Write bytes to the object or file"""
        logger.debug("Writing bytes to %s", str(self))
        if self.bucket:
            self.bucket.blob(self.path).upload_from_string(
                b, content_type=self.mimetype
            )
            return

        with open(self.path, mode="wb") as w:
            w.write(b)

    # Read as text the file or object
    def read_text(self, encoding="utf8"):
        """Read text from the object or file"""
        logger.debug("Read text from %s", str(self))
        if self.bucket:
            return self.bucket.blob(self.path).download_as_text()

        with open(self.path, mode="rt", encoding=encoding) as r:
            return r.read()

    # Read as text the file or object
    def read_bytes(self):
        """Read bytes from the object or file"""
        logger.debug("Read bytes from %s", str(self))
        if self.bucket:
            return self.bucket.blob(self.path).download_as_bytes()

        with open(self.path, mode="rb") as r:
            return r.read()

    # List within the folder or GCS prefix
    def list(self):
        """List folders or objects below the path"""
        logger.debug("Listing %s", str(self))
        if self.bucket:
            for blob in self.bucket.list_blobs(prefix=self.path):
                yield GCSPath(
                    f"gs://{self.bucket.name}/{blob.name}", crc32c=blob.crc32c
                )
        else:
            for root, _, files in os.walk(self.path):
                for file in files:
                    yield GCSPath(str(Path(root, file)))

    # Delete the file or object
    def delete(self):
        """Delete the file or object"""
        if self.bucket:
            logger.debug("Deleting object %s", str(self))
            self.bucket.delete_blob(self.path)
        else:
            logger.debug("Deleting file %s", str(self))
            Path(self.path).unlink()

    # Open for reading as a file
    @contextlib.contextmanager
    def read_as_file(self):
        """Read the file or object as a local file"""
        logger.debug("Reading %s as file locally", str(self))

        # If a file, read directly
        if not self.bucket:
            yield str(self)
            return

        with tempfile.NamedTemporaryFile(suffix=self.suffix) as w:
            logger.debug("Downloading to local file %s", w.name)
            self.bucket.blob(self.path).download_to_filename(w.name)
            yield w.name

    # Open for reading as an object
    @contextlib.contextmanager
    def read_as_obj(self):
        """Read the file or object as a GCS object"""
        logger.debug("Reading %s as GCS object", str(self))

        # As a bucket, read directly
        if self.bucket:
            yield str(self)
            return

        # Generate a temporary object
        tmp_obj_name = Path(self.path).name
        tmp_obj = GCSPath(
            f"{GCS_TMP_PREFIX}/tmp-prefix-{str(uuid.uuid4())}/{tmp_obj_name}"
        )

        # Upload it to GCS
        self.copy(tmp_obj)

        yield str(tmp_obj)

        tmp_obj.delete()

    # Open for writing as a file
    @contextlib.contextmanager
    def write_as_file(self):
        """Write file or object as a file"""
        logger.debug("Writing %s as file locally", str(self))

        # If a file, read directly (make sure created first)
        if not self.bucket:
            os.makedirs(Path(self.path).parent, exist_ok=True)
            yield str(self)
            return

        with tempfile.NamedTemporaryFile(suffix=self.suffix) as w:
            yield w.name
            self.bucket.blob(self.path).upload_from_filename(
                w.name,
                content_type=get_mimetype(self.path),
            )

    # Open for writing as an object
    @contextlib.contextmanager
    def write_as_obj(self):
        """Write file or object as an object"""
        logger.debug("Writing %s as GCS object", str(self))

        # As a bucket, read directly
        if self.bucket:
            yield str(self)
            return

        # Generate a temporary object
        tmp_obj_name = Path(self.path).name
        tmp_obj = GCSPath(
            f"{GCS_TMP_PREFIX}/tmp-prefix-{str(uuid.uuid4())}/{tmp_obj_name}"
        )

        # Write as the object
        yield str(tmp_obj)

        # Download it to local file
        tmp_obj.copy(self)

        # Delete it
        tmp_obj.delete()

    # Open folder for writing (sync'd with GCS)
    @contextlib.contextmanager
    def write_folder_as_gcs(self) -> Iterator[str]:
        """Writable GCS folder that will downloaded if necessary."""
        logger.debug("Writing to %s as GCS folder", str(self))

        # As GCS, use the prefix directly
        if self.bucket:
            yield str(self)
            return

        # Generate a temporary prefix
        tmp_obj = GCSPath(f"{GCS_TMP_PREFIX}/tmp-prefix-{str(uuid.uuid4())}")

        # Return temporary GCS directory
        yield str(tmp_obj)

        # Download objects to filesystem
        for path in tmp_obj.list():
            # Copy locally
            path.copy(str(Path(self.path, Path(path.path).relative_to(tmp_obj.path))))

            # Remove the object
            path.delete()

    # Open folder for writing (sync'd with GCS)
    @contextlib.contextmanager
    def write_folder(self) -> Iterator[str]:
        """Writable local folder that will uploaded if necessary."""
        logger.debug("Writing to %s as local folder", str(self))

        if not self.bucket:
            yield str(self.path)
            return

        with tempfile.TemporaryDirectory() as d:
            logger.debug("Staging in local folder %s", d)

            # Return temporary directory
            yield d

            # Upload objects to GCS
            for root, _, files in os.walk(d):
                for file in files:
                    obj_path = str(Path(self.path, Path(root).relative_to(d), file))
                    logger.debug("Uploading %s to %s", Path(root, file), obj_path)
                    self.bucket.blob(obj_path).upload_from_filename(
                        Path(root, file),
                        content_type=get_mimetype(obj_path),
                    )

    def __str__(self) -> str:
        return self.friendly_path

    def __hash__(self) -> int:
        return str(self).__hash__()

    def __eq__(self, other) -> bool:
        return str(self).__eq__(other)

    def get_hash(self, extra=None) -> str:
        """Get the hash ID of the file or object as a string"""
        # Construct hash string
        hash_data = json.dumps(
            {
                "obj": [self.friendly_path, self.crc32c],
                "extra": extra,
            },
            default=str,
        )

        # Cosntruct the hash
        return (
            "id-"
            + str(
                base64.urlsafe_b64encode(
                    hashlib.sha256(bytes(hash_data, "utf8")).digest()
                ),
                "utf8",
            )[:-1]
        )

    @functools.cached_property
    def hash(self, extra=None) -> str:
        """Get the hash ID of the file or object as a string"""
        return self.get_hash(extra=extra)

    @functools.cached_property
    def friendly_path(self) -> str:
        """Get the friendly path as a string"""
        if self.bucket:
            return f"gs://{self.bucket.name}/{self.path}"
        return str(self.path)

    @functools.cached_property
    def suffix(self) -> str:
        """Get the suffix (extension) of the file or object"""
        return Path(self.path).suffix

    @functools.cached_property
    def name(self) -> str:
        """Get the basename of the file or object"""
        return Path(self.path).name

    @functools.cached_property
    def mimetype(self) -> str:
        """Get the inferred mimetype  of the file or object"""
        return get_mimetype(self.path)

    @functools.cached_property
    def crc32c(self) -> str:
        """Get the crc32c of the file or object"""
        if self.preset_crc32c:
            return self.preset_crc32c

        if self.bucket:
            obj = self.bucket.blob(self.path)
            obj.reload()
            return obj.crc32c

        # Calculate from local filesystem
        from google_crc32c import Checksum  # pylint: disable=import-outside-toplevel

        crc32c = Checksum()
        size = 4096
        with open(self.path, "rb") as f:
            while True:
                b = f.read(size)
                if not b:
                    break
                crc32c.update(b)
        return str(base64.urlsafe_b64encode(crc32c.digest()), "utf8")

    @functools.cached_property
    def size(self) -> int:
        """Return the size (in bytes) of the object or file"""
        if self.bucket:
            obj = self.bucket.blob(self.path)
            obj.reload()
            return obj.size  # pyright: ignore
        return os.path.getsize(self.path)
