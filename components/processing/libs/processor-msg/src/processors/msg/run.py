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


import argparse
import logging

from processors.base.gcsio import GCSPath
from processors.msg.main_processor import process_all_objects, Processors

# Specialized action to parse multiple key-value pairs into a dict
class keyvalue(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None, 
                 *args, **kwargs):
        # if this is the first time we call this, we need to make sure that 
        # the namespace contains a dict for our `dest`
        if (not hasattr(namespace, self.dest) or not 
            getattr(namespace, self.dest)):
            setattr(namespace, self.dest, dict())
        
        # for each key-value pair, parse the key-value (seperated by an equal
        # sign), validate the key (starts with a dot) and store in the dict
        for value in values:
            key, value = list(map(lambda x: x.strip(), value.split(":")))
            if not key.startswith("."):
                key = "." + key
            getattr(namespace, self.dest)[key] = value


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="process msgs",
        description="process and extract messages",
    )
    parser.add_argument("process_dir", type=str, help="Process folder to process")
    parser.add_argument("reject_dir", type=str, help="Reject folder for files that fail")
    parser.add_argument(
        "--write_json", type=bool, default=True, help="Write JSON files"
    )
    parser.add_argument("-l", "--log",
                        dest="logLevel",
                        choices=['DEBUG', 'INFO', 'WARNING',
                                 'ERROR', 'CRITICAL'],
                        default='INFO',
                        help="Set the logging level")
    parser.add_argument(
        "--write_bigquery",
        type=str,
        default="",
        help="BigQuery fully qualified table to write results",
    )
    all_processors = ", ".join([x.value for x in Processors])
    parser.add_argument("--file-type", 
                        metavar="KEY:VALUE",
                        dest="supported_files",
                        help="Set all supported file types in the form of "
                             "FILE_TYPE:PROCESSOR. Minimum one is required. "
                             "Multiple entries are possible. Supported "
                             f"processors are {all_processors}",
                        nargs="+",
                        required=True,
                        action=keyvalue)

    args = parser.parse_args()

    logging.basicConfig(level=logging.getLevelName(args.logLevel))

    # Process everything
    process_all_objects(
        GCSPath(args.process_dir),
        GCSPath(args.reject_dir),
        args.supported_files,    
        write_json=args.write_json,
        write_bigquery=args.write_bigquery,
    )


if __name__ == "__main__":
    main()
