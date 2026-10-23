// Requires the local preview on 4173 and a Chromium CDP endpoint on 9333.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const pages=await(await fetch('http://127.0.0.1:9333/json/list')).json();
const socket=new WebSocket(pages.find(page=>page.type==='page').webSocketDebuggerUrl);
await new Promise(resolve=>socket.onopen=resolve);
const pending=new Map(),errors=[],failures=[],requests=[];
let sequence=0;
socket.onmessage=event=>{
  const message=JSON.parse(event.data);
  if(message.id){const task=pending.get(message.id);pending.delete(message.id);message.error?task.reject(message.error):task.resolve(message.result);}
  if(message.method==='Runtime.exceptionThrown')errors.push(message.params.exceptionDetails.text);
  if(message.method==='Network.requestWillBeSent')requests.push(message.params.request.url);
  if(message.method==='Network.loadingFailed'&&!message.params.canceled)failures.push(message.params.errorText);
};
const call=(method,params={})=>new Promise((resolve,reject)=>{const id=++sequence;pending.set(id,{resolve,reject});socket.send(JSON.stringify({id,method,params}));});
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function evaluate(expression){const result=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));return result.result.value;}
async function wait(expression){for(let i=0;i<100;i++){if(await evaluate(expression))return true;await pause(50);}return false;}
async function screenshot(name){const result=await call('Page.captureScreenshot',{format:'png'});await fs.writeFile(`docs/blog-markdown-${name}.png`,Buffer.from(result.data,'base64'));}
const checks={};
try{
  await call('Page.enable');await call('Runtime.enable');await call('Network.enable');
  await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false});
  await call('Page.navigate',{url:'http://127.0.0.1:4173/blog/posts/markdown-guide/'});
  checks.formulas=await wait('document.querySelectorAll(".prose [data-math] .katex").length===6');
  checks.noFormulaErrors=await evaluate('!document.querySelector(".katex-error")');
  await evaluate('document.fonts.ready');
  checks.mathFonts=await evaluate('document.fonts.check("16px KaTeX_Main") && document.fonts.check("16px KaTeX_Math")');
  checks.image=await evaluate('(async()=>{const img=document.querySelector(".prose img");img.loading="eager";await img.decode();return img.naturalWidth>0&&img.alt.length>0&&!!img.srcset;})()');
  checks.table=await evaluate('document.querySelectorAll(".prose table tbody tr").length===4 && getComputedStyle(document.querySelector(".prose table th:last-child")).textAlign==="right"');
  checks.codeLiteral=await evaluate('document.querySelector(".code-block code").textContent.includes("$E = mc^2$")&&!document.querySelector(".code-block [data-math]")&&!document.querySelector(".code-block img")');
  await evaluate('document.querySelector(".prose img").scrollIntoView({block:"start",behavior:"instant"})');await pause(100);await screenshot('desktop');
  const widths={};
  for(const width of [320,375,414,768,1440]){
    await call('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<650});
    await pause(80);
    widths[width]=await evaluate('document.documentElement.scrollWidth<=innerWidth && [...document.querySelectorAll(".prose img,.math-display,.table-scroll")].every(node=>node.getBoundingClientRect().width<=innerWidth)');
    if(width===375){
      checks.mobileTableScroll=await evaluate('document.querySelector(".table-scroll").scrollWidth>document.querySelector(".table-scroll").clientWidth');
      checks.mobileFormulaScroll=await evaluate(`(async()=>{
        const {renderMath}=await import('/assets/blog/math.js');
        const formula=document.createElement('div');formula.className='math-display';formula.textContent=Array.from({length:40},(_,i)=>'x_{'+i+'}').join('+');
        document.querySelector('.prose').append(formula);renderMath(formula);
        const scrolls=formula.scrollWidth>formula.clientWidth&&document.documentElement.scrollWidth<=innerWidth;
        formula.remove();return scrolls;
      })()`);
      await evaluate('document.querySelector(".table-scroll").scrollIntoView({block:"start",behavior:"instant"})');await screenshot('mobile');
    }
  }
  checks.responsive=Object.values(widths).every(Boolean);
  checks.badMathContained=await evaluate(String.raw`(async()=>{
    const {renderMath}=await import('/assets/blog/math.js');
    const bad=document.createElement('span');bad.className='math-inline';bad.textContent='\\frac{1}{';document.querySelector('.prose').append(bad);renderMath(bad);
    const invalid=bad.classList.contains('math-error')&&!!bad.querySelector('.katex-error');
    bad.textContent='\\href{javascript:alert(1)}{click}';renderMath(bad);const safe=!bad.querySelector('a');bad.remove();return invalid&&safe;
  })()`);
  checks.localResources=requests.filter(url=>url.startsWith('http')).every(url=>new URL(url).hostname==='127.0.0.1');
  checks.fontsRequested=requests.some(url=>url.includes('/vendor/katex/fonts/'));
  await call('Page.navigate',{url:'http://127.0.0.1:4173/blog/posts/module-boundaries/'});await wait('!!document.querySelector(".prose")');
  checks.plainArticle=await evaluate(`!document.querySelector('script[src*="/math.js"]')&&!document.querySelector('link[href*=katex]')`);
  assert.deepEqual(errors,[]);assert.deepEqual(failures,[]);
  for(const [name,value]of Object.entries(checks))assert.equal(value,true,name);
  console.log(JSON.stringify({checks,widths,errors,failures},null,2));
}finally{await call('Browser.close');socket.close();}
