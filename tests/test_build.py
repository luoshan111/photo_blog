"""Integration checks for publishing boundaries, routes, metadata and Markdown safety."""
from pathlib import Path
import json
import sys
import unittest
import html
import re
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build import Builder, ROOT
sys.path.insert(0,str(ROOT/'src/modules/blog'))
from markdown import render

class BuildTests(unittest.TestCase):
    def test_motion_assets_and_switch(self):
        site=Builder()
        self.assertIn('/assets/shared/motion/boot.js',site.motion_tags())
        self.assertIn('data-contact="1.1"',site.motion_tags())
        self.assertIn('data-blog="1.6"',site.motion_tags())
        for name in ['boot.js','main.js','renderer.js','styles.css']:
            self.assertTrue((ROOT/'src/shared/motion'/name).exists())
        site.config['motion']={'enabled':False}
        self.assertEqual(site.motion_tags(),'')
    def test_public_output_and_metadata(self):
        site=Builder();site.url='https://example.com';site.build()
        self.assertTrue((site.out/'photography/albums/mountains/index.html').exists())
        self.assertTrue((site.out/'blog/categories/frontend/index.html').exists())
        self.assertTrue((site.out/'assets/blog/motion/renderer.js').exists())
        self.assertTrue((site.out/'assets/blog/motion/styles.css').exists())
        post=(site.out/'blog/posts/module-boundaries/index.html').read_text(encoding='utf-8')
        self.assertIn('href="#section-1"',post)
        self.assertIn('rel="canonical"',post)
        self.assertIn('https://example.com/blog/posts/module-boundaries/',(site.out/'sitemap.xml').read_text())
        self.assertFalse(list(site.out.rglob('*.jpg')))
        self.assertFalse(list(site.out.rglob('*.md')))
        self.assertNotIn('design-demos',(site.out/'index.html').read_text(encoding='utf-8'))
    def test_drafts_and_withdrawn_posts(self):
        folder=ROOT/'src/modules/blog/content/posts'
        fixtures=[]
        try:
            for kind in ['draft','withdrawn']:
                metadata={'slug':'test-'+kind,'title':'PRIVATE_'+kind,'description':'private','date':'2026-10-14','category':{'slug':'private-category','name':'private'},'tags':[{'slug':'private-tag','name':'private'}],'draft':kind=='draft','published':kind!='withdrawn'}
                for ext,data in [('json',json.dumps(metadata)),('md','## Private body\nSECRET_'+kind)]:
                    file=folder/f'test-{kind}.{ext}'
                    if file.exists(): raise RuntimeError('Refusing to overwrite test fixture')
                    file.write_text(data,encoding='utf-8');fixtures.append(file)
            public=Builder();public.build()
            all_html=''.join(p.read_text(encoding='utf-8') for p in public.out.rglob('*.html'))
            self.assertNotIn('PRIVATE_',all_html);self.assertNotIn('SECRET_',all_html)
            search_index=(public.out/'assets/blog/search-index.json').read_text(encoding='utf-8')
            self.assertNotIn('PRIVATE_',search_index);self.assertNotIn('SECRET_',search_index)
            self.assertNotIn('PRIVATE_',(public.out/'blog/archives/index.html').read_text(encoding='utf-8'))
            self.assertFalse((public.out/'blog/tags/private-tag/index.html').exists())
            preview=Builder(True);preview.build()
            self.assertTrue((preview.out/'blog/posts/test-draft/index.html').exists())
            self.assertTrue((preview.out/'blog/posts/test-withdrawn/index.html').exists())
            self.assertIn('noindex,nofollow',(preview.out/'blog/posts/test-draft/index.html').read_text(encoding='utf-8'))
        finally:
            for file in fixtures: file.unlink(missing_ok=True)
    def test_disabled_modules(self):
        site=Builder();site.config['modules']={'photography':False,'blog':False};site.build()
        self.assertFalse((site.out/'photography').exists());self.assertFalse((site.out/'blog').exists())
        home=(site.out/'index.html').read_text(encoding='utf-8')
        self.assertNotIn('href="/photography/"',home);self.assertNotIn('href="/blog/"',home)
    def test_unpublished_photographs(self):
        source=ROOT/'src/modules/photography/content/albums.json'
        original=source.read_text(encoding='utf-8')
        try:
            albums=json.loads(original);albums[0]['photos'][1]['published']=False;albums[1]['published']=False
            source.write_text(json.dumps(albums),encoding='utf-8')
            site=Builder();site.build()
            self.assertFalse((site.out/'photography/albums/coast/index.html').exists())
            self.assertFalse((site.out/'assets/photography/mountains/lake-1280.webp').exists())
            self.assertNotIn('水与山',(site.out/'photography/albums/mountains/index.html').read_text(encoding='utf-8'))
        finally: source.write_text(original,encoding='utf-8')
    def test_markdown_escaping(self):
        body,toc=render('## Heading\n<script>alert(1)</script>\n\n[bad](javascript:alert)\n\n```js\n<x>\n```')
        self.assertNotIn('<script>',body);self.assertNotIn('href="javascript:',body)
        self.assertIn('<x>',html.unescape(re.sub(r'<[^>]+>','',body)));self.assertEqual(len(toc),1)
    def test_highlight_preserves_code(self):
        from markdown import code_block
        for language in ['javascript','python','not-a-language']:
            source=['  <script>&"\'','    value = 1','']
            rendered=code_block(source,language)
            code=re.search(r'<code>(.*?)</code>',rendered,re.S)[1]
            self.assertEqual(html.unescape(re.sub(r'<[^>]+>','',code)),'\n'.join(source))
            self.assertNotIn('<script>',rendered)
    def test_search_and_archive(self):
        folder=ROOT/'src/modules/blog/content/posts';files=[]
        try:
            for key, day in [('old','2024-02-10'),('recent','2025-12-12')]:
                metadata={'slug':'test-'+key,'title':'Test '+key,'description':'description','date':day,'category':{'slug':'testing','name':'Testing'},'tags':[],'draft':False,'published':True}
                for ext,data in [('json',json.dumps(metadata)),('md','## Testing\nUniqueBodyTerm_'+key)]:
                    file=folder/f'archive-fixture-{key}.{ext}'
                    if file.exists(): raise RuntimeError('Refusing to overwrite fixture')
                    file.write_text(data,encoding='utf-8');files.append(file)
            site=Builder();site.build()
            archive=(site.out/'blog/archives/index.html').read_text(encoding='utf-8')
            self.assertLess(archive.index('2025 <'),archive.index('2024 <'))
            self.assertIn('2 月',archive);self.assertIn('12 月',archive)
            index=json.loads((site.out/'assets/blog/search-index.json').read_text(encoding='utf-8'))
            self.assertTrue(any('UniqueBodyTerm_old' in p['body'] for p in index))
            self.assertTrue((site.out/'blog/search/index.html').exists())
            post=(site.out/'blog/posts/async-recovery/index.html').read_text(encoding='utf-8')
            self.assertIn('<span class=',post);self.assertIn('/assets/blog/highlight.css',post)
        finally:
            for file in files:file.unlink(missing_ok=True)

if __name__=='__main__':
    try: unittest.main()
    finally: Builder().build()
