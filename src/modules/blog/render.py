import json
import re
from html import unescape
from build import ROOT, esc, slug, inside
from datetime import date
from markdown import render as markdown
from content import read_post
from images import image_resolver

def render(site):
    content=ROOT/'src/modules/blog/content/posts';posts=[];seen=set()
    for file in sorted(content.rglob('*.md')):
        post=read_post(file)
        if (post.get('draft',True) or not post.get('published',False)) and not site.preview: continue
        post['slug']=slug(post['slug']);date.fromisoformat(post['date'])
        if post['slug'] in seen: raise ValueError('Duplicate post slug')
        seen.add(post['slug']);post['html'],post['toc']=markdown(post['source'],image_resolver(site,post));posts.append(post)
    posts.sort(key=lambda p:(p['date'],p['slug']),reverse=True)
    def tax_link(t,kind): return f'<a href="/blog/{kind}/{slug(t["slug"])}/">{esc(t["name"])}</a>'
    def cards(selected):
        return ''.join(f'<article class="post-card"><div class="meta"><time datetime="{p["date"]}">{p["date"]}</time> · {tax_link(p["category"],"categories")}'+(' · 演示文章' if p.get('demo') else '')+(' · 草稿预览' if p.get('draft') or not p.get('published') else '')+f'</div><h2><a href="/blog/posts/{p["slug"]}/">{esc(p["title"])}</a></h2><p>{esc(p["description"])}</p><div class="tags">'+''.join(tax_link(t,'tags') for t in p['tags'])+'</div></article>' for p in selected) or '<p>暂无公开文章。</p>'
    categories={p['category']['slug']:p['category'] for p in posts};tags={t['slug']:t for p in posts for t in p['tags']}
    nav='<nav class="taxonomy" aria-label="博客导航"><a href="/blog/">全部文章</a>'+''.join(tax_link(t,'categories') for t in categories.values())+'<a href="/blog/search/">搜索</a><a href="/blog/archives/">归档</a></nav>'
    body='<div class="page-intro"><h1>编程、实践与复盘。</h1><p>技术博客 / 记录问题、方法与取舍</p></div>'+nav+cards(posts)
    site.save_page('/blog/',site.page('技术博客','编程实践、软件设计与项目复盘','/blog/',body))
    # Index is derived from the same publish-filtered collection as public pages.
    index=[{'title':p['title'],'description':p['description'],'date':p['date'],'category':p['category']['name'],'tags':[t['name'] for t in p['tags']],'body':' '.join(unescape(re.sub(r'<[^>]+>',' ',p['html'])).split()),'url':f'/blog/posts/{p["slug"]}/'} for p in posts]
    site.write('assets/blog/search-index.json',json.dumps(index,ensure_ascii=False))
    search='<div class="page-intro"><h1>搜索文章</h1><p>搜索标题、摘要、分类、标签与正文，多个关键词用空格分隔。</p></div>'+nav+'''<form class="search-form" role="search"><label for="query">关键词</label><div class="search-controls"><input id="query" name="q" type="search" maxlength="200" placeholder="例如：模块 或 JavaScript" autocomplete="off"><button type="submit">搜索</button></div></form><p id="search-status" class="meta" role="status">输入关键词开始搜索。</p><div id="search-results" aria-busy="false"></div><noscript><p>搜索需要启用 JavaScript，你也可以通过<a href="/blog/archives/">文章归档</a>浏览内容。</p></noscript>'''
    site.save_page('/blog/search/',site.page('搜索文章','搜索技术博客的标题和正文','/blog/search/',search,extra='<script type="module" src="/assets/blog/main.js"></script>'))
    years=sorted({p['date'][:4] for p in posts},reverse=True)
    archive='<div class="page-intro"><h1>文章归档</h1><p>按年月回顾技术文章。</p></div>'+nav
    for year in years:
        yearly=[p for p in posts if p['date'].startswith(year)]
        archive+=f'<section class="archive-year"><h2>{year} <span class="meta">{len(yearly)} 篇</span></h2>'
        for month in sorted({p['date'][5:7] for p in yearly},reverse=True):
            monthly=[p for p in yearly if p['date'][5:7]==month]
            archive+=f'<section class="archive-month"><h3>{int(month)} 月</h3><ul>'+''.join(f'<li><time datetime="{p["date"]}">{p["date"]}</time><a href="/blog/posts/{p["slug"]}/">{esc(p["title"])}</a></li>' for p in monthly)+'</ul></section>'
        archive+='</section>'
    if not posts: archive+='<p>暂无公开文章，发布后会按年月显示在这里。</p>'
    site.save_page('/blog/archives/',site.page('文章归档','按年月浏览技术文章','/blog/archives/',archive))
    for kind,terms in [('categories',categories),('tags',tags)]:
        for key,term in terms.items():
            selected=[p for p in posts if (p['category']['slug']==key if kind=='categories' else any(t['slug']==key for t in p['tags']))]
            route=f'/blog/{kind}/{slug(key)}/';body=f'<div class="page-intro"><a href="/blog/">← 技术博客</a><h1>{esc(term["name"])}</h1><p>'+('分类' if kind=='categories' else '标签')+'</p></div>'+nav+cards(selected)
            site.save_page(route,site.page(term['name'],'浏览相关技术文章',route,body))
    for p in posts:
        toc='<details class="toc" open><summary>文章目录</summary><nav aria-label="文章目录">'+''.join(f'<a href="#{anchor}" class="level-{level}">{esc(title)}</a>' for anchor,title,level in p['toc'])+'</nav></details>' if p['toc'] else ''
        route=f'/blog/posts/{p["slug"]}/'
        body=f'<article class="reading"><a href="/blog/">← 技术博客</a><div class="article-head"><p class="meta">{p["date"]} · {tax_link(p["category"],"categories")}'+(' · 演示文章' if p.get('demo') else '')+(' · 草稿预览' if p.get('draft') or not p.get('published') else '')+f'</p><h1>{esc(p["title"])}</h1><p class="lede">{esc(p["description"])}</p><div class="tags">'+''.join(tax_link(t,'tags') for t in p['tags'])+'</div></div>'+toc+f'<div class="prose">{p["html"]}</div></article>'
        extra='<link rel="stylesheet" href="/assets/blog/highlight.css"><script type="module" src="/assets/blog/main.js"></script>'
        if 'data-math' in p['html']:
            extra+='<link rel="stylesheet" href="/assets/blog/vendor/katex/katex.min.css"><script type="module" src="/assets/blog/math.js"></script>'
        site.save_page(route,site.page(p['title'],p['description'],route,body,extra=extra))
    from pygments.formatters import HtmlFormatter
    site.write('assets/blog/highlight.css',HtmlFormatter(style='default').get_style_defs('.code-block'))
