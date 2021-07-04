import aiohttp
import logging

from ..lib.query import (
    get_mongo_client,
    insert_new_galleries,
    query_not_fetched,
    update_doc,
    query_all_ids,
    update_counts,
    query_count,
)
from ..lib.fetch import (
    fetch_list,
    build_docs,
    NotAvailableGalleryError,
    fetch_gallery_images,
)
from ..lib.storage import connect_to_storage, create_storage_container, upload_files
from ..lib.etc import extract_new_item_list, clean_resource, extract_missing_galleries


async def execute(count=100):
    client = get_mongo_client()
    storage_client = connect_to_storage()

    fresh_gallery_ids = await fetch_list()
    owned_ids = query_all_ids(client)
    new_gallery_ids = extract_missing_galleries(fresh_gallery_ids, owned_ids)

    new_gallery_ids = new_gallery_ids[: min(len(new_gallery_ids), count)]

    for id_chunk in (
        new_gallery_ids[i : i + 8] for i in range(0, len(new_gallery_ids), 8)
    ):
        docs = await build_docs(id_chunk)
        insert_new_galleries(client, docs)

    ids_to_fetch = query_not_fetched(client)
    for id_to_fetch in ids_to_fetch:
        target_id = id_to_fetch["id"]

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(sock_connect=5)
            ) as session:
                image_names, tags = await fetch_gallery_images(
                    session, client, target_id
                )
        except NotAvailableGalleryError as e:
            logging.info(f"Maybe Gallery {target_id} is not available")
            update_doc(client, id_to_fetch["_id"], {"status": "not_available"})
            print(e)
            continue

        container_client, container_name = create_storage_container(
            storage_client, target_id
        )
        blob_names = upload_files(storage_client, container_name, image_names)
        clean_resource()
        update_doc(
            client,
            id_to_fetch["_id"],
            {
                "status": "fetched",
                "container_name": container_name,
                "blob_names": blob_names,
                "tags": tags,
            },
        )
    update_counts(client, "status=fetched", query_count(client, {"status": "fetched"}))
