from __future__ import print_function
import requests
import os
from datetime import datetime, timezone
from atproto import Client
from typing import List, Dict

import re
import struct
import sys
try:
    import urllib2
except ImportError:  # Python 3
    import urllib.request as urllib2
    
# code credits: https://stackoverflow.com/a/35104372 / https://gist.github.com/vhxs/20f2fbc0da08c07317f9d935dbc1f765
# to-do: clickable links, hashtags

# edit values as needed

# Fetch the current time
# Using a trailing "Z" is preferred over the "+00:00" format
now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

url = 'https://YOUR RADIO STREAM.url'  # radio stream
encoding = 'iso-8859-1' # default: iso-8859-1 for mp3 and utf-8 for ogg streams
request = urllib2.Request(url, headers={'Icy-MetaData': 1})  # request metadata
response = urllib2.urlopen(request)
print(response.headers, file=sys.stderr)
metaint = int(response.headers['icy-metaint'])
for _ in range(10): # # title may be empty initially, try several times
    response.read(metaint)  # skip to metadata
    metadata_length = struct.unpack('B', response.read(1))[0] * 16  # length byte
    metadata = response.read(metadata_length).rstrip(b'\0')
    print(metadata, file=sys.stderr)
    # extract title from the metadata
    m = re.search(br"StreamTitle='([^']*)';", metadata)
    if m:
        title = m.group(1)
        if title:
            bskytitle = title.decode('iso-8859-1')
            result = "#NowPlaying " + bskytitle + " on https://QCIndie.com #qcindie #regina #yqr #indierock #internetradio"
            print(result)
            break
else: 
    sys.exit('no title found')
print(title.decode(encoding, errors='replace'))

def parse_tags(results: str) -> List[Dict]:
    spans = []
    tag_regex = rb"(#+[a-zA-Z0-9(_)]{1,})"
    text_bytes = results.encode("UTF-8")
    print(text_bytes)
    for t in re.finditer(tag_regex, text_bytes):
        spans.append(
            {
                "start": t.start(1),
                "end": t.end(1),
                "tag": t.group(1).decode("UTF-8"),
            }
        )
    return spans
    
def parse_urls(results: str) -> List[Dict]:
    spans = []
    # partial/naive URL regex based on: https://stackoverflow.com/a/3809435
    # tweaked to disallow some trailing punctuation
    url_regex = rb"[$|\W](https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*[-a-zA-Z0-9@%_\+~#//=])?)"
    text_bytes = results.encode("UTF-8")
    for m in re.finditer(url_regex, text_bytes):
        spans.append(
            {
                "start": m.start(1),
                "end": m.end(1),
                "url": m.group(1).decode("UTF-8"),
            }
        )
    return spans


def parse_facets(result: str) -> List[Dict]:
    """
    parses post text and returns a list of app.bsky.richtext.facet objects for any mentions (@handle.example.com) or URLs (https://example.com)

    indexing must work with UTF-8 encoded bytestring offsets, not regular unicode string offsets, to match Bluesky API expectations
    """
    facets = []
    for t in parse_tags(result):
        facets.append(
            {
                "index": {
                    "byteStart": t["start"],
                    "byteEnd": t["end"],
                },
                "features": [
                    {
                        "$type": "app.bsky.richtext.facet#tag",
                        "tag": t["tag"],
                    }
                ],
            }
        )
    for u in parse_urls(result):
        facets.append(
            {
                "index": {
                    "byteStart": u["start"],
                    "byteEnd": u["end"],
                },
                "features": [
                    {
                        "$type": "app.bsky.richtext.facet#link",
                        # NOTE: URI ("I") not URL ("L")
                        "uri": u["url"],
                    }
                ],
            }
        )
    return facets

def parse_uri(uri: str) -> Dict:
    if uri.startswith("at://"):
        repo, collection, rkey = uri.split("/")[2:5]
        return {"repo": repo, "collection": collection, "rkey": rkey}
    elif uri.startswith("https://bsky.app/"):
        repo, collection, rkey = uri.split("/")[4:7]
        if collection == "post":
            collection = "app.bsky.feed.post"
        elif collection == "lists":
            collection = "app.bsky.graph.list"
        elif collection == "feed":
            collection = "app.bsky.feed.generator"
        return {"repo": repo, "collection": collection, "rkey": rkey}
    else:
        raise Exception("unhandled URI format: " + uri)

# Required fields that each post must include
post = {
    "$type": "app.bsky.feed.post",
    "text": result,
    "createdAt": now,
}

    # parse out mentions and URLs as "facets"
if len(result) > 0:
        facets = parse_facets(result)
        if facets:
            post["facets"] = facets

# create a session
# edit the identifier and password values with your email address and app password
resp = requests.post(
    "https://bsky.social/xrpc/com.atproto.server.createSession",
    json={
        "identifier": "EMAIL ADDRESS",
        "password": "APP PASSWORD"
    },
)
resp.raise_for_status()
session = resp.json()

# post!
resp = requests.post(
    "https://bsky.social/xrpc/com.atproto.repo.createRecord",
    headers={"Authorization": "Bearer " + session["accessJwt"]},
    json={
        "repo": session["did"],
        "collection": "app.bsky.feed.post",
        "record": post,
    },
)
resp.raise_for_status()
