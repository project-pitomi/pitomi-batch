import os
from bson.objectid import ObjectId
import pymongo
from pymongo import MongoClient
from pymongo import collection


def get_mongo_client():
    uri = os.environ["PITOMI_MONGO_CONNECTION_STRING"]
    return MongoClient(uri)


def query_last_id(client):
    db = client.hitomi
    collection = db.gallery
    doc = collection.find_one(sort=[("origin_at", pymongo.DESCENDING)])
    if doc is not None:
        return doc["id"]
    return None


def query_all_ids(client):
    collection = client.hitomi.gallery
    return list(map(lambda doc: doc["id"], collection.find({}, {"id": True})))


def query_not_fetched(client):
    db = client.hitomi
    collection = db.gallery
    return list(
        collection.find({"status": "not_fetched"}, {"id": 1}).sort("origin_at", -1)
    )


def query_count(client: MongoClient, filter: dict):
    collection = client.hitomi.gallery
    return collection.count_documents(filter)


def insert_new_galleries(client, docs):
    db = client.hitomi
    collection = db.gallery
    collection.insert_many(docs)


def update_doc(client, doc_id, values):
    db = client.hitomi
    collection = db.gallery
    collection.update_one({"_id": doc_id}, {"$set": values}, upsert=True)


def query_non_webp_galleries(client, count):
    db = client.hitomi
    collection = db.gallery
    return list(
        collection.find(
            {"status": "fetched", "blob_names_webp": {"$exists": False}},
            {"_id": True, "id": True, "container_name": True, "blob_names": True},
        )
        .sort("origin_at", -1)
        .limit(count)
    )


def query_by_classify(client: MongoClient, field_name: str, limit: int = 100):
    collection = client.hitomi.gallery
    return (
        collection.find(
            {field_name: {"$nin": [None, []]}, "classified": {"$nin": [field_name]}}
        )
        .sort("origin_at", -1)
        .limit(limit)
    )


def add_classify(client: MongoClient, gallery_id: ObjectId, field_name: str):
    collection = client.hitomi.gallery
    return collection.update_one(
        {"_id": gallery_id}, {"$addToSet": {"classified": field_name}}
    )


def add_gallery_artist(client: MongoClient, artist: str, gallery_id: ObjectId):
    collection = client.hitomi.artist
    return collection.update_one(
        {"artist": artist}, {"$addToSet": {"galleries": gallery_id}}, upsert=True
    )


def add_gallery_group(client: MongoClient, group: str, gallery_id: ObjectId):
    collection = client.hitomi.group
    return collection.update_one(
        {"group": group}, {"$addToSet": {"galleries": gallery_id}}, upsert=True
    )


def add_gallery_type(client: MongoClient, type: str, gallery_id: ObjectId):
    collection = client.hitomi.type
    return collection.update_one(
        {"type": type}, {"$addToSet": {"galleries": gallery_id}}, upsert=True
    )


def add_gallery_series(client: MongoClient, series: str, gallery_id: ObjectId):
    collection = client.hitomi.series
    return collection.update_one(
        {"series": series}, {"$addToSet": {"galleries": gallery_id}}, upsert=True
    )


def add_gallery_tag(
    client: MongoClient, tag_name: str, tag_type: str, gallery_id: ObjectId
):
    collection = client.hitomi.tag
    return collection.update_one(
        {"tagName": tag_name, "tagType": tag_type},
        {"$addToSet": {"galleries": gallery_id}},
        upsert=True,
    )


def update_counts(client: MongoClient, count_name: str, count: int):
    collection = client.hitomi.counts
    return collection.update_one(
        {"name": count_name}, {"$set": {"count": count}}, upsert=True
    )
