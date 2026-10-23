import { portal } from './config.js';

const brand = document.getElementById('brand');
if (!brand.querySelector('.avatar')) brand.textContent = portal.name;
document.getElementById('footer-name').textContent = `${portal.name} · 摄影与技术`;
document.title = `${portal.name} · 摄影与技术`;
for (const key of ['description', 'bio']) document.getElementById(key).textContent = portal[key];
const cover = document.getElementById('cover');
cover.src = portal.cover;
cover.alt = portal.coverAlt;
document.getElementById('cover-caption').textContent = portal.coverCaption;
function showFallback() {
  cover.hidden = true;
  cover.nextElementSibling.hidden = false;
}
cover.addEventListener('error', showFallback);
if (cover.complete && cover.naturalWidth === 0) showFallback();
for (const link of document.querySelectorAll('[data-module]')) {
  const module = portal.modules[link.dataset.module];
  link.hidden = !module?.enabled;
  if (module?.enabled) link.href = module.href;
}
const contacts = document.getElementById('contact-links');
for (const contact of portal.contacts) {
  let url;
  try { url = new URL(contact.href); } catch { continue; }
  if (!['https:', 'mailto:'].includes(url.protocol)) continue;
  const link = document.createElement('a');
  link.textContent = contact.label;
  link.href = url.href;
  contacts.append(link);
}
document.getElementById('contact-empty').hidden = contacts.children.length > 0;
