import uuid
import os
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError


def connect_to_storage():
    storage_connect_str = os.environ["PITOMI_AZURE_STORAGE_ACCOUNT_CONNECTION_STRING"]
    return BlobServiceClient.from_connection_string(storage_connect_str)


def create_storage_container(client, container_prefix):
    container_name = f"{container_prefix}-{uuid.uuid4()}"
    return client.create_container(container_name), container_name


def upload_files(client, container_name, filenames):
    blob_names = []
    for i, filename in enumerate(filenames):
        blob_name = filename
        try:
            blob_client = client.get_blob_client(
                container=container_name, blob=blob_name
            )
            with open(f"resource/{filename}", "rb") as data:
                blob_client.upload_blob(data)
        except ResourceExistsError:
            pass
        blob_names.append(blob_name)

    return blob_names


def download_blobs(storage_client: BlobServiceClient, container_name, blob_names):
    for blob_name in blob_names:
        path = os.path.join("resource", blob_name)
        if os.path.isfile(path):
            continue
        with open(path, "wb") as file:
            file.write(
                storage_client.get_blob_client(container_name, blob_name)
                .download_blob()
                .readall()
            )

    return blob_names


def upload_blobs(storage_client: BlobServiceClient, container_name, file_names):
    for file_name in file_names:
        with open(os.path.join("resource", file_name), "rb") as data:
            try:
                storage_client.get_blob_client(container_name, file_name).upload_blob(
                    data
                )
            except ResourceExistsError as e:
                pass
    return file_names
