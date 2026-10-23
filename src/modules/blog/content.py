"""Read Markdown with YAML metadata, retaining existing JSON sidecars."""
import json
import re
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / '.local-deps'))
import yaml


def read_post(file):
    text = file.read_text(encoding='utf-8-sig')
    if text.startswith('---\n'):
        match = re.search(r'^---[ \t]*$', text[4:], re.M)
        if not match: raise ValueError(f'{file}: Markdown 文件开头的 YAML 信息缺少结束 ---')
        metadata = yaml.safe_load(text[4:4+match.start()])
        body = text[4+match.end():].lstrip('\n')
    elif file.with_suffix('.json').exists():
        metadata = json.loads(file.with_suffix('.json').read_text(encoding='utf-8-sig'))
        body = text
    else:
        raise ValueError(f'{file}: 请在 Markdown 开头添加 --- 包围的文章信息')
    if not isinstance(metadata, dict): raise ValueError(f'{file}: 文章信息必须是字段列表')
    post = dict(metadata)
    for key in ['title', 'slug', 'date']:
        if not post.get(key): raise ValueError(f'{file}: 缺少 {key}')
    post['date'] = str(post['date'])
    date.fromisoformat(post['date'])
    post.setdefault('description', '')
    post.setdefault('category', {'slug': 'notes', 'name': '技术笔记'})
    post.setdefault('tags', [])
    post.setdefault('draft', True)
    post.setdefault('published', True)
    for key in ['draft', 'published']:
        if not isinstance(post[key], bool): raise ValueError(f'{file}: {key} 必须是 true 或 false')
    for key in ['title', 'description']:
        if not isinstance(post[key], str): raise ValueError(f'{file}: {key} 必须是文字')
    if not isinstance(post['tags'], list): raise ValueError(f'{file}: tags 必须是列表，可填 []')
    for term in [{'slug': post['slug'], 'name': post['title']}, post['category'], *post['tags']]:
        if not isinstance(term, dict) or not isinstance(term.get('name'), str) or not isinstance(term.get('slug'), str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', term['slug']):
            raise ValueError(f'{file}: 文章、分类和标签需要名称，slug 仅支持小写英文、数字和连字符')
    post['source'] = body
    post['file'] = file
    return post
