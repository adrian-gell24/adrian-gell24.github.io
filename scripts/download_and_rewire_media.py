#!/usr/bin/env python3
"""
Download external images referenced in `_posts/` and rewire URLs to `assets/img/`.
Uses only the Python standard library.

Usage:
  python3 scripts/download_and_rewire_media.py
"""
import os
import re
import sys
from urllib.parse import urlparse
from urllib.request import urlopen, Request

POSTS_DIR = '_posts'
MEDIA_DIR = 'assets/img'

IMG_URL_REGEX = re.compile(r'(https?://[^"\)\s]+\.(?:png|jpe?g|gif|svg)(?:\?[^"\)\s]*)?)', re.IGNORECASE)


def ensure_dir(p):
    if not os.path.isdir(p):
        os.makedirs(p, exist_ok=True)


def unique_filename(dest_dir, name):
    base, ext = os.path.splitext(name)
    candidate = name
    i = 1
    while os.path.exists(os.path.join(dest_dir, candidate)):
        candidate = f"{base}-{i}{ext}"
        i += 1
    return candidate


def download_url(url, dest_dir):
    try:
        parsed = urlparse(url)
        name = os.path.basename(parsed.path) or 'file'
        name = name.split('?')[0]
        name = unique_filename(dest_dir, name)
        dest_path = os.path.join(dest_dir, name)
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117 Safari/537.36'})
        with urlopen(req, timeout=30) as src, open(dest_path, 'wb') as dst:
            dst.write(src.read())
        return dest_path
    except Exception as e:
        print('Failed to download', url, '->', e)
        return None


def process_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        txt = f.read()

    found = IMG_URL_REGEX.findall(txt)
    if not found:
        return 0

    ensure_dir(MEDIA_DIR)
    replaced = 0
    for url in set(found):
        local = download_url(url, MEDIA_DIR)
        if local:
            rel = '/' + os.path.relpath(local, start=os.getcwd()).replace('\\', '/')
            txt = txt.replace(url, rel)
            replaced += 1

    if replaced:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(txt)
    return replaced


def main():
    if not os.path.isdir(POSTS_DIR):
        print('No', POSTS_DIR, 'directory found. Nothing to do.')
        return
    total = 0
    for name in os.listdir(POSTS_DIR):
        if not name.lower().endswith('.md'):
            continue
        p = os.path.join(POSTS_DIR, name)
        r = process_file(p)
        if r:
            print('Rewired', r, 'images in', p)
            total += r
    print('Total rewired images:', total)


if __name__ == '__main__':
    main()
