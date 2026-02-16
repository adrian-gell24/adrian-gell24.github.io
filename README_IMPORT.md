# Importing WordPress posts into this Chirpy site

Place your WXR export XML file into the repository (for example at the repo root) and run the conversion script. Example:

```bash
pip install -r requirements.txt
python3 scripts/convert_wxr_to_chirpy.py --wxr ./hobbydiarychronicles.WordPress.2026-02-16.xml
```

By default this writes Markdown posts to `_posts/` and downloads images into `assets/img/`. The script tries to keep WordPress post dates and will name files `YYYY-MM-DD-slug.md` to work with Jekyll/Chirpy.

Options:
- `--media-dir` change where images are saved.
- `--posts-dir` change output folder for posts.
- `--no-media-download` keep original image URLs and do not download files.
