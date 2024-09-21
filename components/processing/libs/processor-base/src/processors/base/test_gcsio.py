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


import base64
import unittest
from tempfile import NamedTemporaryFile, TemporaryDirectory

from google_crc32c import Checksum
from processors.base.gcsio import GCS_TMP_PREFIX, GCSPath, get_mimetype


class TestGCSIO(unittest.TestCase):

    def test_mimetype(self):
        self.assertEqual(get_mimetype("something.MD"), "text/plain")
        self.assertEqual(get_mimetype("again/file.txt"), "text/plain")
        self.assertEqual(get_mimetype("xyz.PdF"), "application/pdf")
        self.assertEqual(get_mimetype("xyz.html"), "text/html")
        self.assertEqual(
            get_mimetype("again/file.docx"),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertEqual(
            get_mimetype("folder/xyz.pptx"),
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        self.assertEqual(
            get_mimetype("folder/xyz.xlsx"),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertEqual(get_mimetype("somethingRandom"), "application/octet-stream")

    def do_obj_test(self, obj, token):
        test_str = f"Test string {token}"

        # src does not exist
        self.assertFalse(obj.exists())

        # write/read str
        obj.write_text(test_str)
        self.assertTrue(obj.exists())
        self.assertEqual(obj.read_text(), test_str)

        # Test bytes and crc32c
        test_bytes = bytes(f"Test bytes {token}", "utf8")
        c = Checksum()
        c.update(test_bytes)
        crc32c = str(base64.urlsafe_b64encode(c.digest()), "utf8")

        # write/read bytes
        obj.write_bytes(test_bytes)
        self.assertEqual(obj.read_bytes(), test_bytes)
        self.assertEqual(obj.crc32c, crc32c)

        # Test file size
        file_size = 15
        self.assertEqual(obj.size, file_size)

        # Try reading the source as obj or file..
        with obj.read_as_obj() as r:
            self.assertEqual(GCSPath(r).read_bytes(), test_bytes)
        with obj.read_as_file() as r, open(r, "rt") as rt:
            self.assertEqual(rt.read(), str(test_bytes, "utf-8"))

        obj.delete()
        self.assertFalse(obj.exists())

    def test_obj(self):
        self.do_obj_test(GCSPath(GCS_TMP_PREFIX(), "temp_obj"), "tok1")

        with TemporaryDirectory() as d:
            self.do_obj_test(GCSPath(d, "temp_file"), "tok2")

    def do_pair_test(self, src, dst, token):
        test_bytes = bytes(f"Test bytes {token}", "utf8")

        # src does not exist
        self.assertFalse(src.exists())

        # write/read str
        src.write_bytes(test_bytes)
        self.assertTrue(src.exists())
        self.assertEqual(src.read_bytes(), test_bytes)

        # write/read bytes
        src.write_bytes(test_bytes)

        # Copy it over, and ensure same content
        src.copy(dst)
        self.assertTrue(dst.exists())
        self.assertEqual(dst.read_bytes(), test_bytes)

        # Try again..
        dst.delete()
        self.assertFalse(dst.exists())

        # With string this time
        src.copy(str(dst))
        self.assertTrue(dst.exists())
        self.assertEqual(dst.read_bytes(), test_bytes)

        # Delete dest and try moving it
        dst.delete()
        self.assertFalse(dst.exists())

        # Move it over, and ensure same content
        src.move(dst)
        self.assertTrue(dst.exists())
        self.assertEqual(dst.read_bytes(), test_bytes)
        self.assertFalse(src.exists())

        # delete dest
        dst.delete()
        self.assertFalse(dst.exists())

    def test_write_folder(self):
        files = {
            "file1.txt": "Test content file1.txt",
            "file2.txt": "Test content file2.txt",
        }

        self.do_test_write_folder(True, GCSPath(GCS_TMP_PREFIX(), "temp_output"), files)
        self.do_test_write_folder(
            False, GCSPath(GCS_TMP_PREFIX(), "temp_output"), files
        )

        with TemporaryDirectory() as d:
            self.do_test_write_folder(True, GCSPath(d), files)
            self.do_test_write_folder(False, GCSPath(d), files)

    def do_test_write_folder(self, to_gcs, src_path, files):
        # Write to the correct GCS or local filesystem
        tmp_path = None
        if to_gcs:
            tmp_path = self.do_test_write_folder_gcs(src_path, files)
        else:
            tmp_path = self.do_test_write_folder_local(src_path, files)

        # No longer in temp folder if cross-system, and different folders
        if (src_path.is_gcs() and not to_gcs) or (not src_path.is_gcs() and to_gcs):
            self.assertNotEqual(str(tmp_path), str(src_path))
            for file in files.keys():
                self.assertFalse(GCSPath(tmp_path, file).exists())
        else:
            self.assertEqual(str(tmp_path), str(src_path))

        # Assert the directory listing in the target folder is right
        self.assertEqual(
            sorted([str(x) for x in GCSPath(src_path).list()]),
            sorted([str(GCSPath(src_path, x)) for x in files.keys()]),
        )

        # Assert the content is correct, and delete
        for file, content in files.items():
            self.assertTrue(GCSPath(src_path, file).exists())
            self.assertEqual(GCSPath(src_path, file).read_text(), content)
            GCSPath(src_path, file).delete()

    def do_test_write_folder_local(self, src_path, files):
        with src_path.write_folder() as w:
            for file, content in files.items():
                GCSPath(w, file).write_text(content)
            return w

    def do_test_write_folder_gcs(self, src_path, files):
        with src_path.write_folder_as_gcs() as w:
            for file, content in files.items():
                GCSPath(w, file).write_text(content)
            return w

    def test_pair_tests(self):
        self.do_pair_test(
            GCSPath(GCS_TMP_PREFIX(), "temp_source1"),
            GCSPath(GCS_TMP_PREFIX(), "temp_dest1"),
            "tmp_token1",
        )

        with TemporaryDirectory() as d:
            self.do_pair_test(
                GCSPath(GCS_TMP_PREFIX(), "temp_source2"),
                GCSPath(d, "temp_dest2"),
                "tmp_token2",
            )

        with TemporaryDirectory() as d:
            self.do_pair_test(
                GCSPath(d, "temp_source3"),
                GCSPath(GCS_TMP_PREFIX(), "temp_dest3"),
                "tmp_token3",
            )

        with TemporaryDirectory() as d:
            self.do_pair_test(
                GCSPath(d, "temp_source4"),
                GCSPath(d, "temp_dest4"),
                "tmp_token4",
            )

    def test_write_one(self):
        content = "Test content for file"

        obj_path = GCSPath(GCS_TMP_PREFIX(), "temp_upload", "file.txt")
        with obj_path.write_as_file() as f:
            self.assertTrue(str(obj_path) != f)
            with open(f, "wt") as f:
                f.write(content)

        self.assertTrue(obj_path.read_text(), content)
        obj_path.delete()

        with NamedTemporaryFile() as f:
            with GCSPath(f.name).write_as_obj() as o:
                self.assertTrue(f.name != str(o))
                GCSPath(o).write_text(content)
                self.assertTrue(GCSPath(o).exists())
            self.assertFalse(GCSPath(o).exists())

            with open(f.name, "rt") as ft:
                self.assertTrue(ft.read(), content)
