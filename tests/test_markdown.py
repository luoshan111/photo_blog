"""Markdown publishing tests: one-file posts, tables, math and referenced images."""
import html
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build import Builder, ROOT
from markdown import render
from content import read_post
from images import image_resolver
from PIL import Image


def metadata(key, draft=False):
    return {'slug': key, 'title': key, 'date': '2026-10-23', 'draft': draft,
            'published': True, 'category': {'slug': 'frontend', 'name': '前端开发'}, 'tags': []}


class MarkdownTests(unittest.TestCase):
    def test_tables_images_math_and_code_boundaries(self):
        source = r'''## A **heading**

![diagram](images/test.png "caption")

| Name | Formula |
| :--- | ---: |
| **mean** | $\frac{1}{N}$ |
| `<script>` | 3 |

Inline $x^2$ and `![literal](missing.png) $raw$`.

$$
\begin{bmatrix}1 & 2 \\ 3 & 4\end{bmatrix}
$$

```python
formula = "$not_math$"
picture = "![literal](missing.png)"
```

## A **heading**
'''
        resolved = []
        def image(url, alt, title):
            resolved.append((url, alt, title));return '<img src="/test.webp" alt="diagram">'
        body, toc = render(source, image)
        self.assertEqual(resolved, [('images/test.png', 'diagram', 'caption')])
        self.assertIn('<table>', body);self.assertIn('text-align:right', body)
        self.assertIn('&lt;script&gt;', body);self.assertNotIn('<script>', body)
        self.assertEqual(body.count('data-math'), 3)
        self.assertIn('class="math-display"', body)
        code = re.search(r'<pre[^>]*><code>(.*?)</code>', body, re.S)[1]
        self.assertIn('$not_math$', html.unescape(re.sub('<[^>]+>', '', code)))
        self.assertEqual(toc, [('section-1', 'A heading', 2), ('section-2', 'A heading', 2)])

    def test_common_markdown_and_unsafe_html(self):
        body, _ = render('1. First\n2. Second\n\n> **quote**\n\n~~gone~~\n\n<script>alert(1)</script>\n\n![bad](javascript:alert)\n\n[bad](data:text/html,test)\n\nCost \\$100 and `$x$`.')
        self.assertIn('<ol>', body);self.assertIn('<blockquote>', body);self.assertIn('<s>gone</s>', body)
        self.assertNotIn('<script>', body);self.assertNotIn('<img', body);self.assertNotIn('href="data:', body)
        self.assertNotIn('data-math', body)

    def test_one_file_metadata_and_defaults(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'tests', prefix='.markdown-') as folder:
            file = Path(folder)/'post.md'
            file.write_text('---\nslug: first\ntitle: First\ndate: 2026-10-23\n---\n## Body\n', encoding='utf-8')
            post = read_post(file)
            self.assertEqual(post['date'], '2026-10-23');self.assertEqual(post['source'], '## Body\n')
            self.assertTrue(post['draft']);self.assertEqual(post['tags'], [])
            file.write_text('---\nslug: first\ntitle: First\ndate: 2026-10-23\ndraft: "false"\n---\nBody', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'draft'): read_post(file)

    def test_missing_and_escaping_images(self):
        post = {'slug': 'test', 'file': ROOT/'src/modules/blog/content/posts/test.md'}
        resolve = image_resolver(Builder(), post)
        for path in ['images/not-present.png', '../../../../../site.json', '%2e%2e/%2e%2e/%2e%2e/%2e%2e/private.png']:
            with self.subTest(path=path), self.assertRaises(ValueError): resolve(path, 'alt', '')
        remote = resolve('https://example.com/image.png', '"><script>', '"caption')
        self.assertNotIn('<script>', remote);self.assertIn('referrerpolicy="no-referrer"', remote)

    def test_images_follow_frontmatter_publish_state(self):
        folder = ROOT/'src/modules/blog/content/posts'
        created = []
        try:
            for name, draft in [('test-markdown-public', False), ('test-markdown-private', True)]:
                image = folder/(name+'.png')
                file = folder/(name+'.md')
                if image.exists() or file.exists(): raise RuntimeError('Fixture already exists')
                created.extend([image, file])
                Image.new('RGBA', (900, 300), (20 if draft else 150, 100, 50, 120)).save(image)
                text = '---\n'+json.dumps(metadata(name,draft))+'\n---\n## Test\n\n![alpha]('+name+'.png)\n\n| A | B |\n| --- | --- |\n| x | $x^2$ |\n\n$$x+y$$\n'
                file.write_text(text, encoding='utf-8')
            unused = folder/'test-markdown-unused.png'
            if unused.exists(): raise RuntimeError('Fixture already exists')
            created.append(unused);Image.new('RGB',(10,10)).save(unused)
            public = Builder();public.build()
            self.assertTrue((public.out/'blog/posts/test-markdown-public/index.html').exists())
            self.assertFalse((public.out/'blog/posts/test-markdown-private').exists())
            self.assertFalse((public.out/'assets/blog/images/test-markdown-private').exists())
            for image in (public.out/'assets/blog/images/test-markdown-public').glob('*.webp'):
                with Image.open(image) as decoded: self.assertIn('A', decoded.getbands())
            self.assertFalse(list(public.out.rglob('*.png')))
            self.assertFalse(list(public.out.rglob('*.md')))
            body = (public.out/'blog/posts/test-markdown-public/index.html').read_text(encoding='utf-8')
            self.assertIn('/assets/blog/math.js', body);self.assertIn('<table>', body)
            self.assertIn('srcset=', body);self.assertIn('width="900" height="300"', body)
            index = (public.out/'assets/blog/search-index.json').read_text(encoding='utf-8')
            self.assertIn('test-markdown-public', index);self.assertNotIn('test-markdown-private', index)
            preview = Builder(True);preview.build()
            self.assertTrue((preview.out/'assets/blog/images/test-markdown-private').is_dir())
        finally:
            for file in created: file.unlink(missing_ok=True)


if __name__ == '__main__':
    try: unittest.main()
    finally: Builder().build()
