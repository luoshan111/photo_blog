"""Build a portable public site. Only explicit published content reaches the output."""
from pathlib import Path
import argparse
import html
import importlib.util
import json
import re
import shutil
import sys
from datetime import date
from urllib.parse import urlsplit
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src/modules/blog'))
from markdown import render as markdown

def esc(value): return html.escape(str(value), quote=True)
def slug(value):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value): raise ValueError(f'Invalid slug: {value}')
    return value
def inside(base, relative):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()): raise ValueError('Content path escapes module')
    return path

class Builder:
    def __init__(self, preview=False, output=None):
        self.preview = preview
        self.out = Path(output) if output else ROOT / ('.preview-dist' if preview else 'dist')
        if not self.out.is_absolute(): self.out = ROOT / self.out
        self.out = self.out.resolve()
        if self.out not in (ROOT / 'dist', ROOT / '.preview-dist'):
            raise ValueError('Build output must be dist or .preview-dist')
        self.config = json.loads((ROOT / 'site.json').read_text(encoding='utf-8'))
        self.url = self.config['url'].rstrip('/')
        if self.url and (urlsplit(self.url).scheme not in ('https', 'http') or not urlsplit(self.url).netloc):
            raise ValueError('site.url must be an absolute http(s) URL')
        self.routes = []
        self.images = {}
    def write(self, path, content):
        dest = self.out / path; dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding='utf-8')
    def save_page(self, route, page):
        self.write(route.strip('/') + '/index.html' if route != '/' else 'index.html', page)
        self.routes.append(route)
    def nav(self, active):
        links = [('/', '门户', 'portal')]
        for key in self.config.get('moduleOrder', ['photography','blog']):
            if key not in ('photography','blog'): continue
            name = self.config.get('moduleLabels',{}).get(key, key)
            if self.config['modules'].get(key): links.append((f'/{key}/', name, key))
        links.append(('/#contact', '联系', 'contact'))
        return ''.join(f'<a href="{href}"'+(' aria-current="page"' if active == key else '')+f'>{esc(name)}</a>' for href, name, key in links)
    def motion_tags(self):
        motion=self.config.get('motion',{})
        if not motion.get('enabled',True): return ''
        def seconds(key,default,maximum):
            value=motion.get(key,default)
            return min(maximum,max(.3,float(value)))
        return '<link rel="stylesheet" href="/assets/shared/motion/styles.css"><script src="/assets/shared/motion/boot.js" data-image="/assets/portal/cover-1280.webp"'+f' data-intro="{seconds("introSeconds",4,8)}" data-photography="{seconds("photographySeconds",.9,3)}" data-blog="{seconds("blogSeconds",1.6,3)}" data-contact="{seconds("contactSeconds",1.1,3)}"'+ '></script><script type="module" src="/assets/shared/motion/main.js"></script>'
    def meta(self, title, description, route, image='/assets/portal/cover-1280.webp'):
        tags = f'<meta name="description" content="{esc(description)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:type" content="website">'
        if self.url:
            tags += f'<link rel="canonical" href="{esc(self.url+route)}"><meta property="og:url" content="{esc(self.url+route)}"><meta property="og:image" content="{esc(self.url+image)}">'
        if self.preview: tags += '<meta name="robots" content="noindex,nofollow">'
        return tags
    def page(self, title, description, route, body, module='blog', extra=''):
        preview = '<div class="preview-banner">本地草稿预览 · 不用于公开发布</div>' if self.preview else ''
        replay = '<button type="button" class="motion-replay" data-motion-replay="blog" hidden>重播入场</button>' if module=='blog' and route=='/blog/' else ''
        return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · {esc(self.config['name'])}</title>{self.meta(title,description,route)}<link rel="stylesheet" href="/assets/shared/base.css"><link rel="stylesheet" href="/assets/{module}/styles.css">{extra}{self.motion_tags()}</head><body class="{module}">{preview}<a class="skip" href="#main">跳至内容</a><header><a class="brand" href="/">{esc(self.config['name'])}</a><nav aria-label="主导航">{self.nav(module)}</nav></header><main id="main">{body}</main><footer><a href="/">返回个人门户</a>{replay}<span>{esc(self.config['name'])} · 摄影与技术</span></footer></body></html>'''
    def image(self, source, key, alt, eager=False):
        if key not in self.images:
            with Image.open(source) as original:
                original = ImageOps.exif_transpose(original).convert('RGB')
                width, height = original.size
                for size in [640, 1280, 1920]:
                    image = original.copy(); image.thumbnail((size, size))
                    target = self.out / f'assets/{key}-{size}.webp'; target.parent.mkdir(parents=True, exist_ok=True)
                    image.save(target, 'WEBP', quality=85)
                self.images[key] = (width, height)
        width, height = self.images[key]
        # Browser width descriptors match actual output width, including portrait photographs.
        candidates = [(size, min(width, size, round(size*width/height))) for size in [640,1280,1920]]
        srcset = ', '.join(f'/assets/{key}-{size}.webp {actual}w' for size, actual in candidates)
        return f'<img src="/assets/{key}-1280.webp" srcset="{srcset}" sizes="(max-width: 650px) 92vw, 65vw" width="{width}" height="{height}" alt="{esc(alt)}" '+('fetchpriority="high"' if eager else 'loading="lazy"')+' decoding="async">'
    def build(self):
        # Output paths are fixed and checked above before any recursive deletion.
        if self.out.exists(): shutil.rmtree(self.out)
        self.out.mkdir()
        shutil.copytree(ROOT/'src/shared', self.out/'assets/shared', ignore=shutil.ignore_patterns('*.py','__pycache__'))
        for module in ['portal','photography','blog']:
            for file in ['styles.css','main.js','math.js','prose.css']:
                source=ROOT/f'src/modules/{module}/{file}'
                if source.exists():
                    target=self.out/f'assets/{module}/{file}';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
            motion_source=ROOT/f'src/modules/{module}/motion'
            if motion_source.is_dir():
                shutil.copytree(motion_source,self.out/f'assets/{module}/motion')
            vendor_source=ROOT/f'src/modules/{module}/vendor'
            if vendor_source.is_dir():
                shutil.copytree(vendor_source,self.out/f'assets/{module}/vendor')
        config = dict(self.config)
        config['modules']={key:{'enabled':value,'href':f'/{key}/'} for key,value in config['modules'].items()}
        config['cover']='/assets/portal/cover-1280.webp'
        self.write('assets/portal/config.js','export const portal = '+json.dumps(config,ensure_ascii=False)+';')
        source=(ROOT/'index.html').read_text(encoding='utf-8')
        source=re.sub(r'<meta name="description"[^>]+>','',source)
        source=source.replace('./src/modules/portal/','/assets/portal/').replace('./design-demos/gallery/index.html#photography','/photography/').replace('./design-demos/technical-blog/index.html','/blog/').replace('href="./"','href="/"')
        source=re.sub(r'<img id="cover"[^>]+>',self.image(inside(ROOT,self.config['cover']),'portal/cover',self.config['coverAlt'],True).replace('<img ','<img id="cover" '),source)
        for key, enabled in self.config['modules'].items():
            if not enabled:
                source=re.sub(r'<a\b[^>]*data-module="'+re.escape(key)+r'"[^>]*>.*?</a>','',source,flags=re.S)
        for key in ['photography','blog']:
            label = self.config.get('moduleLabels',{}).get(key, key)
            source=re.sub(r'(<a data-module="'+key+r'"[^>]+>).*?(</a>)',lambda m:m[1]+esc(label)+m[2],source)
            source=re.sub(r'(<a class="destination" data-module="'+key+r'".*?<h2>).*?(</h2><p>).*?(</p>)',lambda m:m[1]+esc(label)+m[2]+esc(self.config.get('moduleDescriptions',{}).get(key,'')).replace('\n','<br>')+m[3],source,flags=re.S)
        destination_section=re.search(r'<section class="destinations".*?</section>',source,re.S)
        if destination_section:
            items={m[1]:m[0] for m in re.finditer(r'<a class="destination" data-module="([^"]+)".*?</a>',destination_section[0],re.S)}
            ordered=''.join(items[key] for key in self.config.get('moduleOrder',['photography','blog']) if key in items)
            source=source.replace(destination_section[0],'<section class="destinations" aria-label="独立站点入口">'+ordered+'</section>')
        if self.config.get('avatar'):
            avatar=self.image(inside(ROOT,self.config['avatar']),'portal/avatar',self.config['name']+'的头像')
        source=source.replace('门户初版 · 站点入口暂连接已完成的预览页','摄影作品与技术博客 · 独立空间')
        source=re.sub(r'<nav aria-label="主导航">.*?</nav>','<nav aria-label="主导航">'+self.nav('portal')+'<a href="#about">关于</a></nav>',source,flags=re.S)
        for key, value in [('brand',config['name']),('description',config['description']),('bio',config['bio']),('cover-caption',config['coverCaption']),('footer-name',config['name']+' · 摄影与技术')]:
            source=re.sub(r'(<[^>]+id="'+key+r'"[^>]*>).*?(</[^>]+>)',lambda m:m[1]+esc(value).replace('\n','<br>')+m[2],source,flags=re.S)
        if self.config.get('avatar'):
            source=source.replace('<a class="brand" href="/" id="brand">','<a class="brand" href="/" id="brand">'+avatar.replace('<img ','<img class="avatar" '))
        source=source.replace('Unsplash 演示 · 非本人作品',esc(config['photoCredit']))
        source=re.sub(r'<title>.*?</title>','<title>'+esc(config['name'])+' · 摄影与技术</title>',source)
        source=source.replace('</head>',self.meta(config['name'],config['description'],'/')+self.motion_tags()+'</head>')
        if self.preview: source=source.replace('<body>','<body><div class="preview-banner">本地草稿预览 · 不用于公开发布</div>')
        self.save_page('/',source)
        if self.config['modules'].get('photography'): self.photography()
        if self.config['modules'].get('blog'): self.blog()
        body='<section class="page-intro"><h1>这个页面暂时不可用。</h1><p>内容可能已撤下，或该模块暂未开放。</p><a href="/">返回个人门户 →</a></section>'
        self.write('404.html',self.page('页面未找到','返回门户或浏览已开放的模块','/404/',body))
        if self.url and not self.preview:
            urls=''.join(f'<url><loc>{esc(self.url+route)}</loc></url>' for route in self.routes)
            self.write('sitemap.xml','<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+urls+'</urlset>')
        self.write('robots.txt','User-agent: *\n'+('Disallow: /\n' if self.preview else 'Allow: /\n')+(f'Sitemap: {self.url}/sitemap.xml\n' if self.url and not self.preview else ''))
        print(f'Built {len(self.routes)} pages → {self.out.name}'+(' (draft preview)' if self.preview else ' (public)'))
    def render_module(self, module):
        path = ROOT / f'src/modules/{module}/render.py'
        spec = importlib.util.spec_from_file_location(f'{module}_render', path)
        renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)
        renderer.render(self)
    def photography(self): self.render_module('photography')
    def blog(self): self.render_module('blog')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');args=parser.parse_args()
    Builder(args.preview).build()
