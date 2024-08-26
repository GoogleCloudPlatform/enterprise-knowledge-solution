import random
import string
from collections import defaultdict
from datetime import datetime


def supported_files_by_type(file_list, file_type_to_processor):
    supported_file_types = set(
        item["file-suffix"].lower() for item in file_type_to_processor
    )
    files_by_type = defaultdict(list)
    for input_file in file_list:
        file_type = input_file.split(".")[-1].lower()
        if file_type in supported_file_types:
            files_by_type[file_type].append(input_file)
    return files_by_type

def get_random_process_folder_name():
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits,
                                    k=8))
    process_folder = (f"docs-processing-{datetime.now().strftime('%d-%m-%Y')}-"
                      f"{suffix}")
    return process_folder


def get_mv_params(files_to_process, input_folder, process_bucket,
                  process_folder):
    input_folder_with_prefix = f"{input_folder}/" if input_folder else ""
    parameter_obj_list = []
    for typ in files_to_process.keys():
        parameter_obj = {
            "source_object":      f"{input_folder_with_prefix}*.{typ}",
            "destination_bucket": process_bucket,
            "destination_object": f"{process_folder}/{typ}/",
        }
        parameter_obj_list.append(parameter_obj)
    return parameter_obj_list