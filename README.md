# QC2Bluesky

A Bluesky bot to post what's currently playing on QCIndie.com. Based off of QC2Mastodon.

# About

This is a Python script to automatically post what's playing on a Icecast/Shoutcast stream to a Bluesky account. The code is based off the Mastodon script seen here: https://github.com/picpakdog/qc2mastodon

# Install/Setup

Install Atproto via pip:

    pip install atproto

Create an app password through https://bsky.app/settings/app-passwords . You'll want to use this as your password when editing your credentials.

Edit qc2bluesky.py with your info, and set up a Cron job to run it as often as you like.

# Credits

Based off of jfs' code at https://stackoverflow.com/a/35104372 and vhxs' code at https://gist.github.com/vhxs/20f2fbc0da08c07317f9d935dbc1f765
