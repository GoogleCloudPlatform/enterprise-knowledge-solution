import json


# read sampledocs_pre.json in a format usable by python
def read_input_docs():
    # stub: this is just using a local file, but it should read the docs from processing bucket
    with open("sampledocs_pre.json", "r") as sampledocs_pre_file:
        return list(sampledocs_pre_file)


# read aclconfig.json in a format usable by python
def read_acl_label_mapping():
    # stub: this is just using a local file, but read the object from somewhere configurable
    with open("acl_label_mapping.json") as labels_json:
        return json.load(labels_json)


def combine_principals(p1, p2):
    """
    Combines the 'users' and 'groups' lists from two 'principals' dictionaries,
    handling missing keys and avoiding duplicates.

    Args:
      p1: The first 'principals' dictionary.
      p2: The second 'principals' dictionary.

    Returns:
      A new 'principals' dictionary with the combined lists.
    """
    combined_principals = {"users": [], "groups": []}

    for p in (p1, p2):
        for key in ("users", "groups"):
            if key in p:
                combined_principals[key].extend(p[key])

    # Remove duplicates
    combined_principals["users"] = list(dict.fromkeys(combined_principals["users"]))
    combined_principals["groups"] = list(dict.fromkeys(combined_principals["groups"]))

    return combined_principals


def update_acl_info(doc, acl_label_mapping_obj):
    # TODO for troubleshooting... I expect that print(acl_label_mapping_obj) should should only contain the operators group, but it contains all the aggregate acl from previous docs

    # check if any labels are applied to this doc
    if (doc["metadata"]) and (doc["metadata"]["labels"]):

        # For each label defined in acl_label_mapping.json, check if the label is present in this doc, then add the principals matching that label to this doc's acl_info
        for label in acl_label_mapping_obj["labels"]:
            updated_principals = combine_principals(
                doc["acl_info"]["readers"]["principals"],
                acl_label_mapping_obj["labels"][label]["principals"],
            )
            doc["acl_info"]["readers"].update({"principals": updated_principals})
            return doc["acl_info"]["readers"]
    else:  # if no labels are defined, return the unmodified value
        return doc["acl_info"]["readers"]


def update_docs_with_new_acl(sampledocs_list_output):
    # stub: this is just showing a python object, but it should rewrite the object to GCS to be uploaded to datastore
    return print(sampledocs_list_output)


def main():
    acl_label_mapping_obj = read_acl_label_mapping()
    sampledocs_list_input = read_input_docs()
    sampledocs_list_output = []  # create a new list with the updated docs

    # For each document, check if the label is present, then set the readers to match what's defined in aclconfig.json
    for json_str in sampledocs_list_input:
        doc = json.loads(json_str)

        # TODO: I know this dict should be assigned before the loop because it's expected to be constant for each doc.
        # But there's some troubleshooting issue I can't work out, if i moved this var outside the loop then somehow
        # the value of acl_label_mapping_obj is getting reassigned in a way that each doc accumulates all the acl info of every previous doc. Which is not intended.
        acl_label_mapping_obj = read_acl_label_mapping()

        # Assigns the acl_info dictionary, which may or may not already be present. This always overwrites the existing acl_info with the default, in case the mapping has changed since last run.
        doc["acl_info"] = {"readers": acl_label_mapping_obj["default"]}

        # assign specific acl_info based on which labels are present in doc, and which principals are configured for that label
        doc["acl_info"]["readers"] = update_acl_info(doc, acl_label_mapping_obj)

        # create a new list with the updated docs
        sampledocs_list_output.append(doc)

    update_docs_with_new_acl(sampledocs_list_output)


main()
