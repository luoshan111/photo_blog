"""Fetch the pinned, integrity-checked KaTeX browser files for local hosting.

Run only to restore the vendored assets. Normal builds never access the network.
"""
import base64
import hashlib
import io
from pathlib import Path
import tarfile
import urllib.request

VERSION = '0.19.0'
INTEGRITY = 'v6Tznz3zJ7u3niRCoDTsumM2+HA2XXcCu+WAacCeHD2z3p9A9Ks987o5FzfTGBN0e8A0vjEgIDvLbICrXpdw/Q=='
URL = f'https://registry.npmjs.org/katex/-/katex-{VERSION}.tgz'
target = Path(__file__).resolve().parents[1] / 'src/modules/blog/vendor/katex'
archive = urllib.request.urlopen(URL, timeout=30).read()
if base64.b64encode(hashlib.sha512(archive).digest()).decode() != INTEGRITY:
    raise ValueError('KaTeX archive integrity mismatch')
count = 0
with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as package:
    for member in package.getmembers():
        name = member.name
        if name in ('package/dist/katex.mjs', 'package/dist/katex.min.css'):
            relative = Path(name).name
        elif name == 'package/LICENSE': relative = 'LICENSE'
        elif name.startswith('package/dist/fonts/') and member.isfile():
            relative = 'fonts/' + Path(name).name
        else: continue
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(package.extractfile(member).read())
        count += 1
(target / 'README.txt').write_text(f'KaTeX {VERSION}\nSource: {URL}\nLicense: MIT (see LICENSE)\nSHA-512: {INTEGRITY}\nRestore: python scripts/fetch-blog-math.py\n', encoding='utf-8')
print(f'Vendored KaTeX {VERSION}: {count} files')
