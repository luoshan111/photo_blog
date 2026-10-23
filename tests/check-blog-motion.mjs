// Run against scripts/serve.py and a local Chromium CDP endpoint on port 9333.
// Uses Node's built-in fetch/WebSocket; no browser automation package required.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const pages=await(await fetch('http://127.0.0.1:9333/json/list')).json();
const ws=new WebSocket(pages.find(page=>page.type==='page').webSocketDebuggerUrl);
await new Promise(resolve=>ws.onopen=resolve);
let sequence=0;
const pending=new Map(),errors=[],checks={};
ws.onmessage=event=>{
  const message=JSON.parse(event.data);
  if(message.id){const task=pending.get(message.id);pending.delete(message.id);message.error?task.reject(message.error):task.resolve(message.result);}
  if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails.text);
};
const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function evaluate(expression){
  const result=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
  if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function wait(expression,timeout=5000){
  const start=Date.now();
  while(Date.now()-start<timeout){if(await evaluate(expression))return true;await pause(30);}
  return false;
}
async function visit(path){await call('Page.navigate',{url:'http://127.0.0.1:4173'+path});await pause(80);}
async function screenshot(name){const result=await call('Page.captureScreenshot',{format:'png'});await fs.writeFile(`docs/blog-motion-${name}.png`,Buffer.from(result.data,'base64'));}
try{
  await call('Page.enable');await call('Runtime.enable');await call('Network.enable');
  await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
  await visit('/photography/');await wait('!document.getElementById("site-motion")');
  await evaluate('document.querySelector("a[href=\'/blog/\']").click()');
  checks.entry=await wait('!!document.querySelector("#site-motion.blog.has-shader")');
  checks.locked=await evaluate('document.querySelector("main").inert && document.documentElement.classList.contains("motion-lock")');
  await pause(250);await screenshot('desktop');
  checks.finished=await wait('!document.getElementById("site-motion")');
  checks.released=await evaluate('!document.querySelector("main").inert && !document.documentElement.classList.contains("motion-lock") && document.activeElement===document.querySelector("main h1")');
  await call('Page.reload');await pause(400);
  checks.noReplayOnReload=await evaluate('!document.getElementById("site-motion")');
  await evaluate('document.querySelector("[data-motion-replay=blog]").click()');
  checks.replay=await wait('!!document.querySelector("#site-motion.blog.has-shader")');
  await evaluate(`(async()=>{
    const {PixelRenderer}=await import('/assets/blog/motion/renderer.js');
    window.__pixelDraw=PixelRenderer.prototype.draw;
    PixelRenderer.prototype.draw=function(scene,p,time){window.__pixelDraw.call(this,scene,.55,time)};
  })()`);
  await pause(60);await screenshot('reveal');
  await evaluate(`(async()=>{const {PixelRenderer}=await import('/assets/blog/motion/renderer.js');PixelRenderer.prototype.draw=window.__pixelDraw;delete window.__pixelDraw;})()`);
  await wait('!document.getElementById("site-motion")');
  // Verify actual shader alpha: opaque at the start, mixed midway, transparent at end.
  checks.shaderPixels=await evaluate(`(async()=>{
    const {PixelRenderer}=await import('/assets/blog/motion/renderer.js');
    const canvas=document.createElement('canvas');canvas.style.cssText='position:fixed;width:320px;height:200px;left:-500px';document.body.append(canvas);
    const renderer=new PixelRenderer(canvas);renderer.init();
    function sample(p){renderer.draw(0,p);const gl=renderer.gl;const pixels=new Uint8Array(canvas.width*canvas.height*4);gl.readPixels(0,0,canvas.width,canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
      let clear=0,opaque=0,gray=true;for(let i=0;i<pixels.length;i+=4){if(pixels[i+3]===0)clear++;if(pixels[i+3]===255)opaque++;if(pixels[i]!==pixels[i+1]||pixels[i]!==pixels[i+2])gray=false;}return {clear,opaque,gray};}
    const start=sample(0),middle=sample(.55),end=sample(1),total=canvas.width*canvas.height;
    renderer.destroy();canvas.remove();return start.opaque===total && middle.clear>total*.1 && middle.opaque>total*.1 && end.clear===total && start.gray&&middle.gray&&end.gray;
  })()`);
  await evaluate('document.querySelector("a[href=\'/blog/search/\']").click()');await pause(350);
  checks.internalSearchDirect=await evaluate('location.pathname==="/blog/search/"&&!document.getElementById("site-motion")');
  await evaluate('document.querySelector("a[href=\'/blog/\']").click()');await pause(350);
  checks.internalHomeDirect=await evaluate('location.pathname==="/blog/"&&!document.getElementById("site-motion")');
  await visit('/photography/');await wait('!document.getElementById("site-motion")');
  await evaluate('document.querySelector("a[href=\'/blog/\']").click()');await wait('!!document.querySelector("#site-motion.blog")');
  await evaluate('document.querySelector(".motion-skip").click()');
  checks.skip=await wait('!document.getElementById("site-motion")&&!document.querySelector("main").inert');
  await call('Emulation.setDeviceMetricsOverride',{width:375,height:812,deviceScaleFactor:1,mobile:true});
  await visit('/blog/');checks.mobile=await wait('!!document.querySelector("#site-motion.blog.has-shader")');await pause(300);await screenshot('mobile');
  checks.mobileLayout=await evaluate('document.documentElement.scrollWidth<=innerWidth && document.querySelector(".motion-heading").getBoundingClientRect().right<=innerWidth');
  await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
  checks.escape=await wait('!document.getElementById("site-motion")');
  await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'reduce'}]});
  await visit('/blog/');await pause(350);
  checks.reduced=await evaluate('!document.getElementById("site-motion")&&!document.documentElement.classList.contains("motion-starting")');
  await call('Emulation.setEmulatedMedia',{features:[{name:'prefers-reduced-motion',value:'no-preference'}]});
  const injection=await call('Page.addScriptToEvaluateOnNewDocument',{source:`const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){return type==='webgl'?null:original.call(this,type,...args)}`});
  await visit('/blog/');await pause(800);
  checks.noGL=await evaluate('!document.getElementById("site-motion")&&!document.querySelector("main").inert&&!document.documentElement.classList.contains("motion-starting")');
  await call('Page.removeScriptToEvaluateOnNewDocument',{identifier:injection.identifier});
  await call('Network.setBlockedURLs',{urls:['*assets/blog/motion/renderer.js']});await visit('/blog/');await pause(1000);
  checks.rendererFailure=await evaluate('!document.getElementById("site-motion")&&!document.querySelector("main").inert&&!document.documentElement.classList.contains("motion-starting")');
  await call('Network.setBlockedURLs',{urls:[]});
  assert.deepEqual(errors,[]);for(const [name,value]of Object.entries(checks))assert.equal(value,true,name);
  console.log(JSON.stringify({checks,errors},null,2));
}finally{await call('Browser.close');ws.close();}
