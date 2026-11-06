"""Rebuild the locally hosted guide photos from the reviewed Commons selection.

Requires Pillow. Run from any directory. Source URLs, authors, licensing and the
original metadata are retained; only resizing / format conversion is applied.
"""
import hashlib
import html
import io
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / 'scripts/landmark-photo-selection.json'
OUTPUT = ROOT / 'public/photos/landmarks'
AUDIT = ROOT / 'artifacts/landmark-guide'
HEADERS = {'User-Agent': 'NanjingCitySandbox/1.0 (educational landmark guide)'}


def fetch(url):
    for attempt in range(4):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=40).read()
        except urllib.error.HTTPError as error:
            if error.code not in (429, 502, 503, 504) or attempt == 3:
                raise
            time.sleep(8 * (attempt + 1))


def plain(value):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', value))).strip()


def main():
    selection = json.loads(SELECTION.read_text())
    titles = [p['title'] for photos in selection.values() for p in photos]
    params = {'action': 'query', 'titles': '|'.join(titles), 'prop': 'imageinfo',
              'iiprop': 'url|extmetadata|size', 'iiurlwidth': 1280, 'format': 'json'}
    raw = json.loads(fetch('https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(params)))
    pages = {p['title']: p for p in raw['query']['pages'].values()}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / 'selected-source-metadata.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2))
    library = {}
    for landmark_id, photos in selection.items():
        library[landmark_id] = []
        for index, selected in enumerate(photos):
            info = pages[selected['title']]['imageinfo'][0]
            metadata = info['extmetadata']
            get = lambda name: plain(metadata.get(name, {}).get('value', ''))
            license_name, license_url, author = get('LicenseShortName'), get('LicenseUrl'), get('Artist')
            if not license_name.startswith(('CC BY ', 'CC BY-SA ', 'CC0')) or not license_url or not author:
                raise ValueError(f'Unreviewed or incomplete license: {selected["title"]}')
            source_key = hashlib.sha256(selected['title'].encode()).hexdigest()[:8]
            filename = f'{landmark_id}-{index + 1}-{source_key}.webp'
            target = OUTPUT / filename
            if not target.exists():
                download_url = info['url'] if info['width'] <= 1280 else info.get('thumburl', info['url'])
                image = ImageOps.exif_transpose(Image.open(io.BytesIO(fetch(download_url)))).convert('RGB')
                image.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
                image.save(target, 'WEBP', quality=83, method=6)
            image = Image.open(target)
            thumbnail_name = f'{landmark_id}-{index + 1}-{source_key}-thumb.webp'
            thumb = image.copy()
            thumb.thumbnail((160, 120), Image.Resampling.LANCZOS)
            thumb.save(OUTPUT / thumbnail_name, 'WEBP', quality=76, method=6)
            date_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', get('DateTimeOriginal'))
            entry = {**selected, 'src': f'/photos/landmarks/{filename}',
                     'thumbnail': f'/photos/landmarks/{thumbnail_name}',
                     'width': image.width, 'height': image.height,
                     'author': author, 'license': license_name, 'licenseUrl': license_url,
                     'sourceUrl': info['descriptionurl'], 'originalUrl': info['url'],
                     'date': date_match.group() if date_match else '', 'retrievedAt': '2026-10-30',
                     'modifications': 'Resized and converted to WebP; preview may be cropped by CSS.',
                     'bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
            library[landmark_id].append(entry)
            print(landmark_id, index + 1, entry['bytes'], license_name, flush=True)
    output = json.dumps(library, ensure_ascii=False, indent=2) + '\n'
    (ROOT / 'src/landmark-photos.json').write_text(output)
    (OUTPUT / 'credits.json').write_text(output)
    print('Saved', sum(map(len, library.values())), 'photos; bytes:',
          sum(p['bytes'] for photos in library.values() for p in photos), flush=True)


if __name__ == '__main__':
    main()
