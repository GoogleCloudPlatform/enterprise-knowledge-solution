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

from converter import write_jsonl, xlsx_to_pdf


def jsonl() -> None:
    write_jsonl(
        in_bucket_name="dpu-cardinal-bkt",
        in_path="output",
        out_bucket_name="cardinal_search_bkt",
        out_path="output",
    )


def main() -> None:
    # jsonl()
    # to_csv("./samples/test_file.xlsm", "./samples/out/test_file.csv")
    # to_csv_pd("./samples/test_file.xlsm", "./samples/out/test_file_pd.csv")
    # md_to_html("./samples/test_file.md", "./samples/out/test_file.html")
    xlsx_to_pdf(
        "./samples/test_file.xlsm",
        "./samples/out/test_file.html",
        "./samples/out/test_file.pdf",
    )


if __name__ == "__main__":
    main()
