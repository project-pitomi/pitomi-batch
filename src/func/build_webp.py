from azure.storage import blob
from wand.image import Image
import os
import aiohttp
import re

from ..lib.fetch import fetch_gallery_webp_images, NotAvailableGalleryError
from ..lib.query import get_mongo_client, update_doc, query_non_webp_galleries
from ..lib.storage import connect_to_storage, download_blobs, upload_blobs
from ..lib.etc import clean_resource


image_pattern_compatible_with_ios = re.compile(".+\.(jpg|jpeg|png|apng|gif|svg|webp)")


def build_webp(filenames):
    ret = []
    for filename in filenames:
        if filename.split(".")[-1] == "webp":
            ret.append(filename)
            continue
        out_filename = f"{'.'.join(filename.split('.')[:-1])}.webp"
        with Image(filename=os.path.join("resource", filename)) as img:
            if 16383 < img.width or 16383 < img.height:
                r = min(16383 / img.width, 16383 / img.height)
                img.resize(int(r * img.width), int(r * img.height))
            img.format = "webp"
            img.save(filename=os.path.join("resource", out_filename))
        ret.append(out_filename)
    return ret


async def execute(count=10):
    client = get_mongo_client()
    storage_client = connect_to_storage()

    galleries_to_generate_webp = query_non_webp_galleries(client, count)

    for gallery in galleries_to_generate_webp:
        doc_id = gallery["_id"]
        gallery_id = gallery["id"]
        print(gallery_id)
        container_name = gallery["container_name"]
        hash_format_mapping = {}
        try:
            async with aiohttp.ClientSession() as session:
                fetch_results = await fetch_gallery_webp_images(session, gallery_id)
            hashes_to_trans = set(
                map(
                    lambda result: result[0],
                    filter(lambda result: result[1] == False, fetch_results),
                )
            )

            for blob_name in gallery["blob_names"]:
                blob_hash = ".".join(blob_name.split(".")[:-1])
                if blob_hash not in hashes_to_trans:
                    hash_format_mapping[blob_hash] = "webp"

            blob_names = list(
                filter(
                    lambda blob_name: ".".join(blob_name.split(".")[:-1])
                    in hashes_to_trans,
                    gallery["blob_names"],
                )
            )
        except NotAvailableGalleryError:
            blob_names = gallery["blob_names"]

        file_names = download_blobs(storage_client, container_name, blob_names)
        for file_name in filter(
            lambda filename: image_pattern_compatible_with_ios.match(filename)
            is not None,
            file_names,
        ):
            file_hash = ".".join(file_name.split(".")[:-1])
            hash_format_mapping[file_hash] = file_name.split(".")[-1]

        webp_file_names = build_webp(
            filter(
                lambda filename: image_pattern_compatible_with_ios.match(filename)
                is None,
                file_names,
            )
        )
        for file_name in webp_file_names:
            file_hash = ".".join(file_name.split(".")[:-1])
            hash_format_mapping[file_hash] = "webp"

        blob_names = upload_blobs(
            storage_client,
            container_name,
            list(
                map(
                    lambda blob_hash: blob_hash + "." + hash_format_mapping[blob_hash],
                    map(
                        lambda blob_name: ".".join(blob_name.split(".")[:-1]),
                        gallery["blob_names"],
                    ),
                )
            ),
        )
        clean_resource()
        update_doc(client, doc_id, {"blob_names_webp": blob_names})
