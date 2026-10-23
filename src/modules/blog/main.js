const form = document.querySelector('.search-form');
if (form) {
  const input = document.getElementById('query');
  const results = document.getElementById('search-results');
  const status = document.getElementById('search-status');
  let indexPromise, version = 0, timer;
  const normalize = text => text.normalize('NFKC').toLocaleLowerCase('zh-CN');
  function element(tag, text, className) {
    const node = document.createElement(tag);
    node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  async function search() {
    const current = ++version;
    const query = input.value.trim().slice(0, 200);
    const url = new URL(location.href);
    query ? url.searchParams.set('q', query) : url.searchParams.delete('q');
    history.replaceState(null, '', url);
    results.replaceChildren();
    results.setAttribute('aria-busy', 'false');
    if (!query) { status.textContent = '输入关键词开始搜索。'; return; }
    status.textContent = '正在搜索…';
    results.setAttribute('aria-busy', 'true');
    try {
      indexPromise ||= fetch('/assets/blog/search-index.json').then(response => {
        if (!response.ok) throw new Error('index');
        return response.json();
      }).catch(error => { indexPromise = null; throw error; });
      const index = await indexPromise;
      if (current !== version) return;
      const tokens = normalize(query).split(/\s+/u);
      const matches = index.map(post => {
        const title = normalize(post.title);
        const text = normalize([post.title, post.description, post.category, ...post.tags, post.body].join(' '));
        return { post, match: tokens.every(token => text.includes(token)), score: tokens.reduce((n, token) => n + (title.includes(token) ? 3 : 0), 0) };
      }).filter(row => row.match).sort((a,b) => b.score-a.score || b.post.date.localeCompare(a.post.date));
      status.textContent = matches.length ? `找到 ${matches.length} 篇文章。` : '没有找到相关文章，试试更短的关键词。';
      for (const {post} of matches) {
        const card = element('article', '', 'post-card');
        card.append(element('div', `${post.date} · ${post.category}`, 'meta'));
        const heading = document.createElement('h2');
        const link = element('a', post.title);
        link.href = post.url;
        heading.append(link);
        card.append(heading);
        const body = post.body.replace(/\s+/g, ' ');
        const found = Math.max(0, normalize(body).indexOf(tokens[0]));
        const start = Math.max(0, found-35);
        card.append(element('p', (start ? '…' : '') + body.slice(start,start+160) + (body.length>start+160?'…':'')));
        results.append(card);
      }
    } catch {
      if (current === version) status.textContent = '搜索资料未能加载，请再次搜索，或通过归档浏览文章。';
    } finally {
      if (current === version) results.setAttribute('aria-busy', 'false');
    }
  }
  form.addEventListener('submit', e => { e.preventDefault(); clearTimeout(timer); search(); });
  input.addEventListener('input', () => { ++version; clearTimeout(timer); timer = setTimeout(search, 200); });
  input.value = (new URL(location.href).searchParams.get('q') || '').slice(0,200);
  if (input.value) search();
}

for (const block of document.querySelectorAll('.code-block')) {
  const button = document.createElement('button');
  button.type = 'button'; button.textContent = '复制代码';
  const status = document.createElement('span');
  status.setAttribute('role','status'); status.className = 'copy-status';
  block.querySelector('.code-tools').append(status,button);
  button.addEventListener('click', async () => {
    button.disabled = true;
    try {
      await navigator.clipboard.writeText(block.querySelector('code').textContent);
      status.textContent = '已复制';
    } catch {
      const range = document.createRange(); range.selectNodeContents(block.querySelector('code'));
      const selection = getSelection(); selection.removeAllRanges(); selection.addRange(range);
      status.textContent = '已选中，请手动复制';
    } finally { button.disabled = false; }
  });
}
