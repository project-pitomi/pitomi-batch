import glob
import os


def extract_new_item_list(fresh_list, last_id):
    return list(reversed(fresh_list[: fresh_list.index(last_id)]))


def clean_resource():
    files_to_clean = glob.glob("resource/*")
    for f in files_to_clean:
        os.remove(f)


def extract_missing_galleries(fresh_list, owned_ids):
    owned_set = set(owned_ids)
    return list(filter(lambda id: id not in owned_set, fresh_list))
