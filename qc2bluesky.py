from __future__ import print_function
import requests
import os
from datetime import datetime, timezone
from atproto import Client

import re
import struct
import sys
try:
    import urllib2
except ImportError:  # Python 3
    import urllib.request as urllib2

# the bulk of this code is taken from https://stackoverflow.com/a/35104372 with Bluesky-specific tweaks
# edit values as needed

# Fetch the current time
# Using a trailing "Z" is preferred over the "+00:00" format
now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


url = 'https://stream.qcindie.com/;'  # radio stream
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
            result = "Now Playing " + bskytitle + " on QCIndie.com #qcindie #regina #yqr #indierock #internetradio"
            print(result)
            break
else: 
    sys.exit('no title found')
print(title.decode(encoding, errors='replace'))

# Required fields that each post must include
post = {
    "$type": "app.bsky.feed.post",
    "text": result,
    "createdAt": now,
}

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
