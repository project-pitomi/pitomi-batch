from ..lib.query import (
    get_mongo_client,
    query_by_classify,
    add_gallery_artist,
    add_gallery_group,
    add_gallery_series,
    add_gallery_type,
    add_gallery_tag,
    add_classify,
)


def handle_artist(client, count):
    for gallery in query_by_classify(client, "artists", count):
        gallery_id = gallery["_id"]
        artists = gallery["artists"]
        for artist in artists:
            add_gallery_artist(client, artist, gallery_id)
        add_classify(client, gallery_id, "artists")


def handle_group(client, count):
    for gallery in query_by_classify(client, "group", count):
        gallery_id = gallery["_id"]
        groups = gallery["group"]
        for group in groups:
            add_gallery_group(client, group, gallery_id)
        add_classify(client, gallery_id, "group")


def handle_type(client, count):
    for gallery in query_by_classify(client, "type", count):
        gallery_id = gallery["_id"]
        type = gallery["type"]
        add_gallery_type(client, type, gallery_id)
        add_classify(client, gallery_id, "type")


def handle_series(client, count):
    for gallery in query_by_classify(client, "series", count):
        gallery_id = gallery["_id"]
        series = gallery["series"]
        for s in series:
            add_gallery_series(client, s, gallery_id)
        add_classify(client, gallery_id, "series")


def handle_tag(client, count):
    for gallery in query_by_classify(client, "tags", count):
        gallery_id = gallery["_id"]
        tags = gallery["tags"]
        for tag in tags:
            if "male" in tag and tag["male"] == 1:
                tag_type = "male"
            elif "female" in tag and tag["female"] == 1:
                tag_type = "female"
            else:
                tag_type = None
            add_gallery_tag(client, tag["tag"], tag_type, gallery_id)
        add_classify(client, gallery_id, "tags")


async def execute(count=100):
    client = get_mongo_client()
    handle_artist(client, count)
    handle_group(client, count)
    handle_type(client, count)
    handle_series(client, count)
    handle_tag(client, count)
