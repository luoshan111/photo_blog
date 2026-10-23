// Runs in <head> to avoid a flash of the destination before its entrance.
(() => {
  const script = document.currentScript;
  const settings = {
    intro: Math.min(8, Math.max(1, Number(script.dataset.intro) || 4)),
    photography: Math.min(3, Math.max(.3, Number(script.dataset.photography) || .9)),
    blog: Math.min(3, Math.max(.3, Number(script.dataset.blog) || 1.6)),
    contact: Math.min(3, Math.max(.3, Number(script.dataset.contact) || 1.1)),
    image: script.dataset.image,
  };
  window.__siteMotionSettings = settings;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const type = performance.getEntriesByType('navigation')[0]?.type;
  if (type === 'back_forward') return;
  const path = location.pathname.replace(/index\.html$/, '');
  let initial = null;
  if (path === '/' && location.hash === '#contact') initial = 'contact';
  else if (path === '/') {
    // If storage is unavailable, keep the site immediately usable.
    try { if (!sessionStorage.getItem('personal-site:intro:v1')) initial = 'intro'; } catch {}
  } else if (path === '/photography/' || path === '/photography') {
    let fromPhotography = false;
    try { fromPhotography = new URL(document.referrer).pathname.startsWith('/photography'); } catch {}
    if (type !== 'reload' && !fromPhotography) initial = 'photography';
  } else if (path === '/blog/' || path === '/blog') {
    let fromBlog = false;
    try { fromBlog = new URL(document.referrer).pathname.startsWith('/blog'); } catch {}
    if (type !== 'reload' && !fromBlog) initial = 'blog';
  }
  if (!initial) return;
  window.__siteMotionInitial = initial;
  const style = document.createElement('style');
  style.textContent = `html.motion-starting{background:${initial==='blog'?'#090909':'#171a18'}}html.motion-starting body>:not(#site-motion){visibility:hidden}#site-motion{visibility:visible}`;
  document.head.append(style);
  document.documentElement.classList.add('motion-starting');
  // Fail open even if the module, image or graphics initialization never finishes.
  window.__siteMotionBootTimer = setTimeout(() => {
    window.__siteMotionExpired = true;
    document.documentElement.classList.remove('motion-starting');
  }, 1600);
})();
