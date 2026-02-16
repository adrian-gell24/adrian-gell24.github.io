#!/usr/bin/env python3
"""
Convert a WordPress WXR (XML) export into Jekyll/Chirpy posts.

Usage:
  python3 scripts/convert_wxr_to_chirpy.py --wxr PATH/TO/export.xml

This will write markdown files to `_posts/` and download media to `assets/img/` by default.
"""
import argparse
import os
import re
import sys
import shutil
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

try:
    import requests
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md
    from dateutil import parser as dateparser
except Exception as e:
    print("Missing dependencies. Install from requirements.txt: pip install -r requirements.txt")
    raise

NS = {
    'wp': 'http://wordpress.org/export/1.2/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
}


def safe_slug(s):
    s = s.strip().lower()
    s = re.sub(r'[^a-z0-9-_]+', '-', s)
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s or 'post'


def filename_for(date_str, slug):
    try:
        dt = dateparser.parse(date_str)
    except Exception:
        dt = None
    if dt:
        date_prefix = dt.strftime('%Y-%m-%d')
    else:
        date_prefix = '1970-01-01'
    return f"{date_prefix}-{slug}.md"


def download_media(url, dest_dir):
    if not url.lower().startswith('http'):
        return None
    os.makedirs(dest_dir, exist_ok=True)
    parsed = urlparse(url)
    name = os.path.basename(parsed.path)
    if not name:
        name = 'file'
    target = os.path.join(dest_dir, name)
    base, ext = os.path.splitext(target)
    i = 1
    while os.path.exists(target):
        target = f"{base}-{i}{ext}"
        i += 1
    try:
        r = requests.get(url, timeout=30, stream=True)
        r.raise_for_status()
        with open(target, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
        return target
    except Exception:
        return None


def convert_item(item, media_dir, posts_dir, download_media=True):
    title_el = item.find('title')
    title = title_el.text or 'Untitled'
    content_el = item.find('content:encoded', NS)
    content_html = content_el.text or ''
    post_date = item.find('wp:post_date', NS)
    post_date_str = post_date.text if post_date is not None else ''
    post_name = item.find('wp:post_name', NS)
    slug = safe_slug(post_name.text if post_name is not None and post_name.text else title)

    # Collect categories/tags
    cats = []
    tags = []
    for cat in item.findall('category'):
        domain = cat.get('domain')
        if domain == 'category':
            cats.append(cat.text or '')
        elif domain == 'post_tag':
            tags.append(cat.text or '')

    # Rewrite image URLs and optionally download
    soup = BeautifulSoup(content_html, 'html.parser')
    for img in soup.find_all('img'):
        src = img.get('src')
        if not src:
            continue
        if download_media:
            saved = download_media(src, media_dir)
            if saved:
                # Use site-relative path inside repo
                rel = '/' + os.path.relpath(saved, start=os.getcwd()).replace('\\', '/')
                img['src'] = rel
        else:
            img['src'] = src

    # Convert HTML to Markdown
    content_html = str(soup)
    content_md = md(content_html, heading_style='ATX')

    # Build front matter for Chirpy/Jekyll
    front = ['---']
    front.append(f"title: \"{title.replace('"', '\\"')}\"")
    if post_date_str:
        front.append(f"date: {post_date_str}")
    front.append('layout: post')
    if cats:
        front.append('categories: [' + ', '.join([f'"{c}"' for c in cats]) + ']')
    if tags:
        front.append('tags: [' + ', '.join([f'"{t}"' for t in tags]) + ']')
    front.append('---\n')

    fname = filename_for(post_date_str, slug)
    os.makedirs(posts_dir, exist_ok=True)
    out_path = os.path.join(posts_dir, fname)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(front))
        f.write('\n')
        f.write(content_md)
    return out_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--wxr', required=True, help='Path to WordPress export XML')
    p.add_argument('--media-dir', default='assets/img', help='Where to store downloaded media')
    p.add_argument('--posts-dir', default='_posts', help='Where to write generated posts')
    p.add_argument('--no-media-download', action='store_true', help='Do not download media, keep original URLs')
    args = p.parse_args()

    tree = ET.parse(args.wxr)
    root = tree.getroot()
    channel = root.find('channel')
    items = channel.findall('item')
    converted = []
    for item in items:
        post_type = item.find('wp:post_type', NS)
        status = item.find('wp:status', NS)
        if post_type is None or post_type.text != 'post':
            continue
        if status is not None and status.text != 'publish':
            continue
        out = convert_item(item, args.media_dir, args.posts_dir, download_media=not args.no_media_download)
        print('Wrote', out)
        converted.append(out)

    print(f'Converted {len(converted)} posts.')


if __name__ == '__main__':
    main()
