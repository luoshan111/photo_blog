"""Publish only Markdown-referenced blog images, preserving transparency."""
import hashlib
import html
import shutil
from pathlib import Path
from urllib.parse import unquote, urlsplit
from PIL import Image, ImageOps


def image_resolver(site, post):
    module = Path(__file__).resolve().parent
    cache = {}

    def resolve(url, alt, title):
        attrs = f' alt="{html.escape(alt, quote=True)}" loading="lazy" decoding="async"'
        if title: attrs += f' title="{html.escape(title, quote=True)}"'
        parsed = urlsplit(url)
        if parsed.scheme in ('https', 'http') and parsed.netloc:
            return f'<img src="{html.escape(url, quote=True)}"{attrs} referrerpolicy="no-referrer">'
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
            raise ValueError(f'{post["file"]}: 不支持的图片地址 {url}')
        source = (post['file'].parent / unquote(parsed.path)).resolve()
        if not source.is_relative_to(module) or source.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.avif'):
            raise ValueError(f'{post["file"]}: 配图必须是博客模块目录内的图片：{url}')
        if not source.is_file(): raise ValueError(f'{post["file"]}: 配图不存在：{url}')
        if source not in cache:
            digest = hashlib.sha256(source.read_bytes()).hexdigest()[:16]
            key = f'assets/blog/images/{post["slug"]}/{digest}'
            with Image.open(source) as original:
                if getattr(original, 'is_animated', False):
                    dest = site.out / (key + source.suffix.lower())
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
                    cache[source] = (f'/{dest.relative_to(site.out).as_posix()}', '', original.width, original.height)
                else:
                    image = ImageOps.exif_transpose(original)
                    image = image.convert('RGBA' if 'A' in image.getbands() or 'transparency' in image.info else 'RGB')
                    width, height = image.size
                    candidates = []
                    for size in sorted({min(width, n) for n in (640, 1280, 1920)}):
                        resized = image.resize((size, max(1, round(height*size/width))), Image.Resampling.LANCZOS)
                        dest = site.out / f'{key}-{resized.width}.webp'
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        resized.save(dest, 'WEBP', quality=88)
                        candidates.append((dest, resized.width))
                    main = min(candidates, key=lambda row: abs(row[1]-1280))[0]
                    srcset = ', '.join(f'/{path.relative_to(site.out).as_posix()} {size}w' for path, size in candidates)
                    cache[source] = (f'/{main.relative_to(site.out).as_posix()}', srcset, width, height)
        src, srcset, width, height = cache[source]
        responsive = f' srcset="{srcset}" sizes="(max-width: 650px) 90vw, 760px"' if srcset else ''
        return f'<img src="{src}"{responsive} width="{width}" height="{height}"{attrs}>'

    return resolve
