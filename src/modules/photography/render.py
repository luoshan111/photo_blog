import json
from build import ROOT, esc, slug, inside

def render(site):
    from_source=ROOT/'src/modules/photography'
    albums=json.loads((from_source/'content/albums.json').read_text(encoding='utf-8'))
    cards=[];seen=set()
    for album in albums:
        if not album.get('published',False) and not site.preview: continue
        name=slug(album['slug'])
        if name in seen: raise ValueError('Duplicate album slug')
        seen.add(name)
        photos=[p for p in album['photos'] if p.get('published',False) or site.preview]
        if not photos: continue
        route=f'/photography/albums/{name}/';gallery=[];viewer=[]
        for index, photo in enumerate(photos):
            key=f'photography/{name}/{slug(photo["id"])}'
            img=site.image(inside(from_source,photo['file']),key,photo['alt'],index==0)
            caption=' · '.join(str(photo[k]) for k in ['title','date','location','caption'] if photo.get(k))
            gallery.append(f'<figure><button class="photo" data-photo="{index}" aria-label="放大{esc(photo.get("title", "照片"))}">{img}</button><figcaption>{esc(caption)}</figcaption></figure>')
            viewer.append({'src':f'/assets/{key}-1920.webp','alt':photo['alt'],'caption':caption})
        payload=json.dumps(viewer,ensure_ascii=False).replace('<','\\u003c')
        body=f'<div class="page-intro"><a href="/photography/">← 全部相册</a><h1>{esc(album["title"])}</h1><p>{esc(album["description"])}</p></div><div class="photo-grid">'+''.join(gallery)+'</div>'
        body+='''<dialog id="viewer" aria-label="全屏照片"><div class="viewer-head"><span id="photo-caption"></span><button id="close" autofocus>关闭 ×</button></div><div class="viewer-image"><img id="full-photo" alt=""><p id="image-error" hidden>照片未能加载，请关闭后重试。</p></div><div class="viewer-controls"><button id="previous">← 上一张</button><span id="photo-position" aria-live="polite"></span><button id="next">下一张 →</button></div></dialog>'''+f'<script type="application/json" id="photos">{payload}</script>'
        site.save_page(route,site.page(album['title'],album['description'],route,body,'photography','<script type="module" src="/assets/photography/main.js"></script>'))
        cover=photos[0];img=site.image(inside(from_source,cover['file']),f'photography/{name}/{slug(cover["id"])}',cover['alt'])
        cards.append(f'<a class="album" href="{route}">{img}<div><h2>{esc(album["title"])}</h2><span aria-hidden="true">↗</span></div><p>{esc(album["description"])}</p></a>')
    body='<div class="page-intro"><h1>把目光留下。</h1><p>摄影作品 / 相册与系列</p><p class="credit">'+esc(site.config['photoCredit'])+'</p></div><div class="albums">'+(''.join(cards) or '<p>还没有公开相册，新的作品会出现在这里。</p>')+'</div>'
    site.save_page('/photography/',site.page('摄影作品','浏览相册与摄影系列','/photography/',body,'photography'))
