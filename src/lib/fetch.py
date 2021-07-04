import os
import aiohttp
import asyncio
from datetime import datetime
import json
from bs4 import BeautifulSoup


class NotAvailableGalleryError(Exception):
    pass


def async_retry(count):
    def _async_retry(func):
        async def wrap_func(*args, **kwargs):
            _count = count
            last_exception = None
            while 0 < _count:
                is_ok = True
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    is_ok = False
                    last_exception = e
                if is_ok:
                    break
                _count -= 1
            raise last_exception

        return wrap_func

    return _async_retry


def decode_nozomi(body):
    return [
        int.from_bytes(body[4 * i : 4 * i + 4], "big") for i in range(len(body) // 4)
    ]


def parse_gallery_page(body):
    soup = BeautifulSoup(body, features="html.parser")
    infos = soup.find("div", {"class": "gallery"})
    card_table = infos.find("div", {"class": "gallery-info"}).table.find_all("tr")

    _title = infos.h1.a.string.strip()

    _artists = None
    try:
        _artists = list(map(lambda x: x.a.string.strip(), infos.h2.ul.find_all("li")))
    except (AttributeError, TypeError):
        pass

    _group = []
    try:
        _group = list(
            map(
                lambda x: x.a.string.strip(),
                card_table[0].find_all("td")[1].ul.find_all("li"),
            )
        )
    except (AttributeError, TypeError):
        pass

    _type = None
    try:
        _type = card_table[1].find_all("td")[1].a.string.strip()
    except AttributeError:
        pass

    _series = []
    try:
        _series = list(
            map(
                lambda x: x.a.string.strip(),
                card_table[3].find_all("td")[1].find_all("li"),
            )
        )
    except (AttributeError, TypeError):
        pass

    _charaters = []
    try:
        _characters = list(
            map(
                lambda x: x.a.string.strip(),
                card_table[4].find_all("td")[1].ul.find_all("li"),
            )
        )
    except (AttributeError, TypeError):
        pass

    # _tags = []
    # try:
    #     _tags = list(map(lambda x: x.a.string.strip(), card_table[5].find_all('td')[1].ul.find_all('li')))
    # except (AttributeError, TypeError):
    #     pass

    _origin_at = datetime.now()
    try:
        _origin_at = datetime.strptime(
            infos.find("span", {"class": "date"}).string.strip() + "00",
            "%Y-%m-%d %H:%M:%S%z",
        )
    except Exception:
        pass

    return {
        "title": _title,
        "artists": _artists,
        "group": _group,
        "type": _type,
        "series": _series,
        "characters": _characters,
        # 'tags': _tags,
        "origin_at": _origin_at,
    }


def parse_gallery_url(body):
    soup = BeautifulSoup(body, features="html.parser")
    return soup.div.h1.a["href"]


async def fetch_list():
    url = "https://ltn.hitomi.la/index-korean.nozomi"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception("Failed to fetch list")
            return decode_nozomi(await resp.read())


def decode_metadata(code):
    meta = json.loads(code[code.index("{") :])
    meta.pop("language", None)
    meta.pop("language_localname", None)
    meta.pop("japanese_title", None)
    meta["origin_at"] = datetime.strptime(f'{meta["date"]}00', "%Y-%m-%d %H:%M:%S%z")
    meta.pop("date", None)
    if "tags" in meta and meta["tags"] is not None:
        for i in range(len(meta["tags"])):
            meta["tags"][i].pop("url")
    return meta


@async_retry(10)
async def get_gallery_js_meta(session, id):
    url = f"https://ltn.hitomi.la/galleries/{id}.js"
    async with session.get(url) as resp:
        if resp.status != 200:
            raise NotAvailableGalleryError(
                f"Failed to fetch js meta with code({resp.status}) of {id}"
            )
        return decode_metadata(await resp.text())


@async_retry(10)
async def get_gallery_meta(session, id):
    url = f"https://ltn.hitomi.la/galleryblock/{id}.html"
    async with session.get(url) as resp:
        if resp.status != 200:
            raise Exception("Failed to fetch block")
        gallery_url = "https://hitomi.la" + parse_gallery_url(await resp.text())
        async with session.get(gallery_url) as resp:
            if resp.status != 200:
                raise Exception("Failed to fetch meta")
            return parse_gallery_page(await resp.text())


async def build_docs(gallery_ids):
    inserted_at = datetime.utcnow()
    docs = list(
        map(
            lambda x: {"id": x, "status": "not_fetched", "inserted_at": inserted_at},
            gallery_ids,
        )
    )
    async with aiohttp.ClientSession() as session:
        metas = await asyncio.gather(
            *list(
                map(
                    lambda gallery_id: get_gallery_meta(session, gallery_id),
                    gallery_ids,
                )
            )
        )
        return [{**metas[i], **docs[i]} for i in range(len(gallery_ids))]


def subdomains(hash, suffix="b"):
    return ["a" + suffix, "b" + suffix, "c" + suffix]


async def get_url(session, id, url, filepath, filename):
    async with session.get(
        url, headers={"referer": f"https://hitomi.la/reader/{id}.html"}
    ) as resp:
        if resp.status != 200:
            return False
        with open(os.path.join(filepath, filename), "wb") as f:
            f.write(await resp.read())
        return filename


@async_retry(100)
async def fetch_image(session, id, file):
    format = file["name"].split(".")[-1]
    if file["hasavif"] == 1:
        format = "avif"
    elif file["haswebp"] == 1:
        format = "webp"

    if format in ["webp", "avif"]:
        sds = subdomains(file["hash"], suffix="a")
        category = format
    else:
        sds = subdomains(file["hash"])
        category = "images"

    urls = map(
        lambda sd: f"https://{sd}.hitomi.la/{category}/{file['hash']}.{format}"
        if len(file["hash"]) < 3
        else f"https://{sd}.hitomi.la/{category}/{file['hash'][-1]}/{file['hash'][-3:-1]}/{file['hash']}.{format}",
        sds,
    )
    fetch_results = await asyncio.gather(
        *[
            get_url(session, id, url, "resource", f'{file["hash"]}.{format}')
            for url in urls
        ]
    )
    for fetch_result in fetch_results:
        if fetch_result:
            return fetch_result

    raise Exception(f"Image Not Found {id}, {file}")


async def fetch_gallery_images(session, client, id):
    jsmetas_to_fetch = await get_gallery_js_meta(session, id)
    saved_files = []
    for files_chunk in (
        jsmetas_to_fetch["files"][i : i + 8]
        for i in range(0, len(jsmetas_to_fetch["files"]), 8)
    ):
        saved_files += await asyncio.gather(
            *[fetch_image(session, id, file) for file in files_chunk]
        )
    return saved_files, jsmetas_to_fetch["tags"]


@async_retry(100)
async def fetch_webp(session, id, file):
    if file["haswebp"] != 1:
        return False

    format = "webp"
    sds = subdomains(file["hash"], suffix="a")
    category = format

    urls = map(
        lambda sd: f"https://{sd}.hitomi.la/{category}/{file['hash']}.{format}"
        if len(file["hash"]) < 3
        else f"https://{sd}.hitomi.la/{category}/{file['hash'][-1]}/{file['hash'][-3:-1]}/{file['hash']}.{format}",
        sds,
    )

    fetch_results = await asyncio.gather(
        *[
            get_url(session, id, url, "resource", f'{file["hash"]}.{format}')
            for url in urls
        ]
    )
    for fetch_result in fetch_results:
        if fetch_result:
            return fetch_result
    return False


async def fetch_gallery_webp_images(session, id):
    jsmetas_to_fetch = await get_gallery_js_meta(session, id)
    files = jsmetas_to_fetch["files"]

    result = []
    for files_chunk in (files[i : i + 8] for i in range(0, len(files), 8)):
        hashes = list(map(lambda file: file["hash"], files_chunk))
        result.extend(
            zip(
                hashes,
                await asyncio.gather(
                    *[fetch_webp(session, id, file) for file in files_chunk]
                ),
            )
        )
    return result
