import { ShaderRenderer } from './renderer.js';

const settings = window.__siteMotionSettings;
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
const definitions = {
  intro: { shader: 2, title: '世界，\n被重新看见。', caption: '摄影师 / 程序员', duration: settings?.intro || 4 },
  photography: { shader: 0, title: '留住，片刻。', caption: '摄影作品 / 相册与系列', duration: settings?.photography || .9 },
  blog: { shader: 0, title: 'CODE\n& NOTES_', caption: '技术博客 / 把思考写进代码', duration: settings?.blog || 1.6 },
  contact: { shader: 1, title: '看见，\n然后交谈。', caption: '联系 / 让想法相遇', duration: settings?.contact || 1.1 },
};
let active = null;
const releaseBoot = () => {
  clearTimeout(window.__siteMotionBootTimer);
  document.documentElement.classList.remove('motion-starting');
};
function focusTarget(target) {
  if (!target) return;
  const temporary = !target.hasAttribute('tabindex');
  if (temporary) target.setAttribute('tabindex','-1');
  target.focus({ preventScroll:true });
  if (temporary) target.addEventListener('blur',()=>target.removeAttribute('tabindex'),{once:true});
}
function showContact() {
  const target=document.getElementById('contact');
  if (!target) return;
  if(location.hash!=='#contact')history.pushState(null,'','#contact');
  target.scrollIntoView({behavior:'instant',block:'start'});
  focusTarget(target.querySelector('h2') || target);
}

async function run(kind, after = null) {
  if (!settings || reduced.matches) { releaseBoot();after?.();return; }
  if (active) return;
  const definition=definitions[kind];
  const overlay=document.createElement('div');
  overlay.id='site-motion';overlay.className=kind;
  overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-labelledby','motion-heading');
  const poster=document.createElement('img');poster.className='motion-poster';if(kind!=='blog')poster.src=settings.image;poster.alt='';poster.setAttribute('aria-hidden','true');
  const canvas=document.createElement('canvas');canvas.setAttribute('aria-hidden','true');
  const top=document.createElement('div');top.className='motion-top';
  const name=document.createElement('span');name.className='motion-name';name.textContent=document.querySelector('.brand')?.textContent || '个人站';
  const skip=document.createElement('button');skip.className='motion-skip';skip.type='button';skip.textContent='跳过动画';top.append(name,skip);
  const heading=document.createElement('h2');heading.id='motion-heading';heading.className='motion-heading';heading.textContent=definition.title;
  const caption=document.createElement('p');caption.className='motion-caption';caption.textContent=definition.caption;
  const progress=document.createElement('div');progress.className='motion-progress';progress.setAttribute('aria-hidden','true');progress.append(document.createElement('span'));
  overlay.append(poster,canvas,top,heading,caption,progress);
  const originalFocus=document.activeElement;
  const inertNodes=[...document.body.children].filter(node=>node instanceof HTMLElement && !['SCRIPT','STYLE'].includes(node.tagName));
  const previousInert=inertNodes.map(node=>node.inert);
  inertNodes.forEach(node=>node.inert=true);
  document.body.append(overlay);document.body.classList.add('motion-running');document.documentElement.classList.add('motion-lock');
  releaseBoot();skip.focus({preventScroll:true});
  const state={overlay,renderer:null,frame:0,finished:false,timer:null,started:0,elapsed:0};active=state;
  if (kind==='intro') { try { sessionStorage.setItem('personal-site:intro:v1','seen'); } catch {} }
  function finish() {
    if(state.finished)return;state.finished=true;
    cancelAnimationFrame(state.frame);clearTimeout(state.timer);
    overlay.classList.add('is-leaving');
    // The destination is made ready underneath the final Shader frame.
    inertNodes.forEach((node,i)=>node.inert=previousInert[i]);
    document.body.classList.remove('motion-running');
    document.documentElement.classList.remove('motion-lock');
    if(after)after();else if(kind==='contact')showContact();else if(kind==='photography')focusTarget(document.querySelector('main h1'));
    else if(originalFocus instanceof HTMLElement&&originalFocus!==document.body)originalFocus.focus({preventScroll:true});
    else focusTarget(document.querySelector('main h1'));
    overlay.removeAttribute('aria-modal');overlay.setAttribute('aria-hidden','true');
    setTimeout(()=>{state.renderer?.destroy();overlay.remove();if(active===state)active=null;},240);
  }
  state.finish=finish;
  skip.onclick=finish;
  overlay.addEventListener('keydown',event=>{
    if(event.key==='Escape'){event.preventDefault();finish();}
    if(event.key==='Tab'){event.preventDefault();skip.focus();}
  });
  // A stalled image/driver must never trap the visitor behind an overlay.
  state.timer=setTimeout(finish,Math.max(2200,definition.duration*1000+1800));
  try {
    const Renderer=kind==='blog' ? (await import('../../blog/motion/renderer.js')).PixelRenderer : ShaderRenderer;
    if(state.finished)return;
    const renderer=new Renderer(canvas);
    state.renderer=renderer;
    const ready=await Promise.race([renderer.init(settings.image),new Promise(resolve=>setTimeout(()=>resolve(false),900))]);
    if(state.finished)return;
    if(ready)overlay.classList.add('has-shader');
    else { renderer.destroy();state.renderer=null; }
  } catch { state.renderer?.destroy();state.renderer=null; }
  if(state.finished)return;
  const playbackSeconds=state.renderer?definition.duration:Math.min(.2,definition.duration);
  function frame(now) {
    if(state.finished)return;
    if(!state.started)state.started=now;
    const seconds=state.elapsed+(now-state.started)/1000;
    const p=Math.min(1,seconds/playbackSeconds);
    try { state.renderer?.draw(definition.shader,p,seconds); } catch { finish();return; }
    progress.firstElementChild.style.transform=`scaleX(${p})`;
    if(kind==='blog'){
      // The real document shows through the transparent pixels, not a captured image.
      const opacity=String(1-Math.min(1,Math.max(0,(p-.16)/.23)));
      heading.style.opacity=opacity;caption.style.opacity=opacity;name.style.opacity=opacity;
      progress.style.opacity=String(1-Math.min(1,Math.max(0,(p-.65)/.25)));
      skip.style.opacity=String(1-Math.min(1,Math.max(0,(p-.8)/.2)));
    }else heading.style.opacity=String(Math.min(1,.12+p*4));
    if(!state.renderer)poster.style.opacity=String(.14+.5*p);
    if(p>=1){finish();return;}
    state.frame=requestAnimationFrame(frame);
  }
  state.frame=requestAnimationFrame(frame);
  state.resume=()=>{state.started=0;state.frame=requestAnimationFrame(frame);};
  state.pause=()=>{if(state.started)state.elapsed+=(performance.now()-state.started)/1000;state.started=0;cancelAnimationFrame(state.frame);};
}

document.addEventListener('click',event=>{
  if(!settings||reduced.matches||event.defaultPrevented||event.button!==0||event.ctrlKey||event.metaKey||event.shiftKey||event.altKey)return;
  const link=event.target instanceof Element?event.target.closest('a[href]'):null;
  if(!link||link.hasAttribute('download')||(link.target&&link.target!=='_self'))return;
  const url=new URL(link.href,location.href);
  if(url.origin!==location.origin||url.hash!=='#contact')return;
  if(url.pathname===location.pathname || (url.pathname==='/'&&document.getElementById('contact'))){
    event.preventDefault();run('contact',showContact);
  }
});
for(const button of document.querySelectorAll('[data-motion-replay]')){
  button.hidden=!settings||reduced.matches;
  button.addEventListener('click',()=>run(button.dataset.motionReplay==='blog'?'blog':'intro'));
  reduced.addEventListener('change',()=>{button.hidden=!settings||reduced.matches;});
}
document.addEventListener('visibilitychange',()=>{
  if(!active||active.finished)return;
  if(document.hidden)active.pause?.();else active.resume?.();
});
reduced.addEventListener('change',()=>{if(reduced.matches)active?.finish();releaseBoot();});
addEventListener('pageshow',event=>{if(event.persisted){active?.finish();releaseBoot();}});
if(window.__siteMotionInitial&&!window.__siteMotionExpired)run(window.__siteMotionInitial);
else releaseBoot();
