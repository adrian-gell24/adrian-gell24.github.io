#!/usr/bin/env python3
"""
Fallback WXR -> Jekyll posts converter using only the Python standard library.
Does not download media; image URLs are preserved.

Usage:
  python3 scripts/convert_wxr_fallback.py --wxr FILENAME.xml
"""
import argparse
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

NS = {
    'wp': 'http://wordpress.org/export/1.2/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
}


def safe_slug(s):
    s = (s or '').strip().lower()
    s = re.sub(r'[^a-z0-9-_]+', '-', s)
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s or 'post'


def filename_for(date_str, slug):
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        date_prefix = dt.strftime('%Y-%m-%d')
    except Exception:
        date_prefix = '1970-01-01'
    return f"{date_prefix}-{slug}.md"


def convert_item(item, posts_dir):
    title = (item.find('title').text or 'Untitled')
    content_el = item.find('content:encoded', NS)
    content_html = content_el.text or ''
    post_date = item.find('wp:post_date', NS)
    post_date_str = post_date.text if post_date is not None else ''
    post_name = item.find('wp:post_name', NS)
    slug = safe_slug(post_name.text if post_name is not None and post_name.text else title)

    cats = []
    tags = []
    for cat in item.findall('category'):
        domain = cat.get('domain')
        if domain == 'category':
            cats.append(cat.text or '')
        elif domain == 'post_tag':
            tags.append(cat.text or '')

    front = ['---']
    front.append('title: "{}"'.format(title.replace('"', '\\"')))
    if post_date_str:
        front.append(f'date: {post_date_str}')
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
        # write the HTML content directly
        f.write(content_html)
    return out_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--wxr', required=True)
    p.add_argument('--posts-dir', default='_posts')
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
        out = convert_item(item, args.posts_dir)
        print('Wrote', out)
        converted.append(out)

    print(f'Converted {len(converted)} posts.')


if __name__ == '__main__':
    main()
