const photos = JSON.parse(document.getElementById('photos').textContent);
const dialog = document.getElementById('viewer');
const image = document.getElementById('full-photo');
const error = document.getElementById('image-error');
let index = 0;
let opener;
function show(next) {
  index = (next + photos.length) % photos.length;
  const photo = photos[index];
  image.hidden = false;
  error.hidden = true;
  image.src = photo.src;
  image.alt = photo.alt;
  document.getElementById('photo-caption').textContent = photo.caption;
  document.getElementById('photo-position').textContent = `${index + 1} / ${photos.length}`;
  for (const id of ['previous','next']) document.getElementById(id).disabled = photos.length < 2;
}
image.addEventListener('error', () => { image.hidden = true; error.hidden = false; });
document.querySelectorAll('[data-photo]').forEach(button => button.addEventListener('click', () => {
  opener = button;
  show(Number(button.dataset.photo));
  dialog.showModal();
  document.body.classList.add('viewer-open');
}));
document.getElementById('close').onclick = () => dialog.close();
document.getElementById('previous').onclick = () => show(index - 1);
document.getElementById('next').onclick = () => show(index + 1);
dialog.addEventListener('close', () => { document.body.classList.remove('viewer-open'); opener?.focus({preventScroll:true}); });
dialog.addEventListener('keydown', e => {
  if (['ArrowLeft','ArrowRight'].includes(e.key)) { e.preventDefault(); show(index + (e.key==='ArrowRight'?1:-1)); }
});
dialog.addEventListener('click', e => {
  if (e.target !== dialog) return;
  const rect = dialog.getBoundingClientRect();
  if (e.clientX<rect.left || e.clientX>rect.right || e.clientY<rect.top || e.clientY>rect.bottom) dialog.close();
});
let touch;
dialog.addEventListener('touchstart', e => { touch={x:e.changedTouches[0].clientX,y:e.changedTouches[0].clientY}; }, {passive:true});
dialog.addEventListener('touchend', e => {
  if (!touch) return;
  const dx=e.changedTouches[0].clientX-touch.x,dy=e.changedTouches[0].clientY-touch.y;
  if (Math.abs(dx)>50 && Math.abs(dx)>Math.abs(dy)) show(index+(dx<0?1:-1));
  touch=null;
}, {passive:true});
