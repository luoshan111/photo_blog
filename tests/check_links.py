"""Check generated local links and images, plus the source-exposure boundary of the server."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import urllib.request
import urllib.error
ROOT=Path(__file__).resolve().parents[1];output=ROOT/'dist'
class Parser(HTMLParser):
    def __init__(self): super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        for key in ['href','src']:
            if attrs.get(key): self.links.append(attrs[key])
failures=[]
for file in output.rglob('*.html'):
    parser=Parser();parser.feed(file.read_text(encoding='utf-8'))
    for link in parser.links:
        url=urlsplit(link)
        if url.scheme or url.netloc or not url.path:continue
        target=output/unquote(url.path).lstrip('/') if url.path.startswith('/') else file.parent/unquote(url.path)
        if url.path.endswith('/'):target=target/'index.html'
        if not target.exists():failures.append((str(file.relative_to(output)),link))
for path in ['/src/modules/blog/content/posts/modules.md','/site.json','/does-not-exist','/blog/posts/test-draft/']:
    try: urllib.request.urlopen('http://127.0.0.1:4173'+path);failures.append(('unexpected public path',path))
    except urllib.error.HTTPError as e:
        if e.code!=404:failures.append(('wrong status',path))
if failures:raise SystemExit(str(failures))
print('All generated local links/assets exist; source and unknown paths return 404.')
