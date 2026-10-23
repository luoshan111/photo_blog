const vertex = `attribute vec2 position; varying vec2 uv; void main(){uv=position*.5+.5;gl_Position=vec4(position,0.,1.);}`;
const fragment = `precision highp float;
varying vec2 uv; uniform vec2 resolution; uniform vec2 imageSize; uniform vec2 pointer;
uniform float progress; uniform float time; uniform float scene; uniform sampler2D picture;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1.,0.)),f.x),mix(hash(i+vec2(0.,1.)),hash(i+vec2(1.)),f.x),f.y);}
float fbm(vec2 p){float v=0.,a=.5;for(int i=0;i<5;i++){v+=a*noise(p);p=mat2(.8,-.6,.6,.8)*p*2.03+17.1;a*=.5;}return v;}
float rect(vec2 p,vec2 lo,vec2 hi){vec2 a=smoothstep(lo,lo+.002,p),b=1.-smoothstep(hi-.002,hi,p);return a.x*a.y*b.x*b.y;}
vec3 photo(vec2 p,float aspect){float ia=imageSize.x/imageSize.y;vec2 scale=vec2(min(aspect/ia,1.),min(ia/aspect,1.));return texture2D(picture,clamp((p-.5)*scale+.5,.001,.999)).rgb;}
float ease(float p){return p*p*(3.-2.*p);}
void main(){
 float a=resolution.x/resolution.y,p=ease(progress);vec3 ink=vec3(.075,.087,.079),paper=vec3(.87,.86,.80);vec3 color=ink;
 float grain=hash(gl_FragCoord.xy+floor(time*20.))-.5;
 if(scene<.5){
   vec2 lo=vec2(.12,.16),hi=vec2(.90,.84);if(a<1.){lo=vec2(.055,.18);hi=vec2(.945,.83);}
   vec2 q=(uv-lo)/(hi-lo);float mask=rect(uv,lo,hi);vec3 rgb=photo(q,a*(hi.x-lo.x)/(hi.y-lo.y));float l=dot(rgb,vec3(.2126,.7152,.0722));
   float field=fbm(q*4.+vec2(.0,time*.018))*.7+q.x*.18+q.y*.12;
   float threshold=mix(-.15,1.16,p);float reveal=1.-smoothstep(threshold-.055,threshold+.055,field);
   float edge=exp(-abs(field-threshold)*55.)*(1.-smoothstep(.82,1.,p));
   vec3 silver=mix(vec3(l*.64),rgb,smoothstep(.22,.94,p));
   color=mix(ink+vec3(fbm(uv*8.)*.018),silver,mask*reveal);color+=mask*edge*paper*.28;
   color+=grain*.032*(1.-p);color*=mix(.62,1.,smoothstep(.05,.85,uv.x));
 }else if(scene<1.5){
   vec2 lo=vec2(.39,.12),hi=vec2(.95,.90);vec2 center=vec2(.69,.51);if(a<1.){lo=vec2(.08,.12);hi=vec2(.96,.77);center=vec2(.64,.37);}
   vec2 dvec=(uv-center)*vec2(a,1.);float d=length(dvec);float radius=mix(.015,1.35,p);float rim=exp(-abs(d-radius)*85.);
   vec2 direction=dvec/max(d,.001);vec2 bend=direction*.065*exp(-abs(d-radius)*17.)*(1.-p);
   bend+=(pointer-.5)*.016*(1.-p);
   vec2 q=(uv-lo)/(hi-lo);float pa=a*(hi.x-lo.x)/(hi.y-lo.y);
   vec3 rgb=photo(q+bend,pa);float split=.006*rim*(1.-p);
   rgb.r=photo(q+bend+vec2(split,0.),pa).r;rgb.b=photo(q+bend-vec2(split,0.),pa).b;
   float window=1.-smoothstep(radius-.015,radius+.015,d);float mask=rect(uv,lo,hi);
   color=mix(ink,rgb*.88,window*mask);color+=rim*vec3(.72,.70,.62)*mask*(1.-smoothstep(.65,1.,p))*.65;
   color+=pow(max(0.,1.-abs(d-radius)*8.),5.)*.04*(1.-p)*mask;
 }else{
   vec3 rgb=photo(uv,a);float l=dot(rgb,vec3(.2126,.7152,.0722));
   float height=l*1.25+fbm(vec2(uv.x*7.,uv.y*3.))*.20;
   float line=pow(max(0.,cos((uv.y*44.+height*2.6)*6.28318)),25.);
   float dots=pow(max(0.,cos(uv.x*160.*a)*cos(uv.y*150.)),18.);
   vec3 drawing=ink+paper*line*(.2+l*.55)+paper*dots*.07;
   float field=1.-uv.y+noise(uv*8.)*.10;float reveal=1.-smoothstep(p*1.2-.035,p*1.2+.035,field);
   color=mix(drawing,rgb*.78,reveal);float edge=exp(-abs(field-p*1.2)*95.)*(1.-smoothstep(.85,1.,p));color+=edge*paper*.09;
   color*=mix(.26,1.,smoothstep(.0,.8,uv.x));
 }
 color=max(color,vec3(0.));gl_FragColor=vec4(color,1.);
}`;

export class ShaderRenderer {
  constructor(canvas) { this.canvas=canvas;this.gl=null;this.disposed=false;this.resources=[]; }
  async init(url) {
    const gl=this.canvas.getContext('webgl',{alpha:false,antialias:false,powerPreference:'low-power'});
    if(!gl)return false;this.gl=gl;
    this.canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();this.lost=true;});
    const compile=(type,source)=>{const shader=gl.createShader(type);this.resources.push(['shader',shader]);gl.shaderSource(shader,source);gl.compileShader(shader);if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS))throw Error('Shader compilation failed');return shader;};
    const program=gl.createProgram();this.resources.push(['program',program]);this.program=program;
    gl.attachShader(program,compile(gl.VERTEX_SHADER,vertex));gl.attachShader(program,compile(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);
    if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('Shader link failed');gl.useProgram(program);
    const buffer=gl.createBuffer();this.resources.push(['buffer',buffer]);gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
    const position=gl.getAttribLocation(program,'position');gl.enableVertexAttribArray(position);gl.vertexAttribPointer(position,2,gl.FLOAT,false,0,0);
    this.uniforms={};for(const key of ['resolution','imageSize','pointer','progress','time','scene','picture'])this.uniforms[key]=gl.getUniformLocation(program,key);
    const image=new Image();image.src=url;await image.decode();if(this.disposed)return false;
    const texture=gl.createTexture();this.resources.push(['texture',texture]);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,texture);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGB,gl.RGB,gl.UNSIGNED_BYTE,image);gl.uniform1i(this.uniforms.picture,0);gl.uniform2f(this.uniforms.imageSize,image.naturalWidth,image.naturalHeight);
    this.ready=true;return true;
  }
  draw(scene,progress,time) {
    if(!this.ready||this.disposed)return;if(this.lost)throw Error('Graphics context lost');
    const gl=this.gl,canvas=this.canvas,r=canvas.getBoundingClientRect();
    const ratio=Math.min(devicePixelRatio||1,navigator.hardwareConcurrency<=4?1:1.25);
    const width=Math.max(1,Math.round(r.width*ratio)),height=Math.max(1,Math.round(r.height*ratio));
    if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height;}
    gl.viewport(0,0,width,height);gl.useProgram(this.program);
    gl.uniform2f(this.uniforms.resolution,width,height);gl.uniform2f(this.uniforms.pointer,.5,.5);gl.uniform1f(this.uniforms.progress,progress);gl.uniform1f(this.uniforms.time,time);gl.uniform1f(this.uniforms.scene,scene);gl.drawArrays(gl.TRIANGLES,0,6);
  }
  destroy() {
    if(this.disposed)return;this.disposed=true;const gl=this.gl;if(!gl)return;
    for(const [type,value] of this.resources){if(type==='shader')gl.deleteShader(value);if(type==='program')gl.deleteProgram(value);if(type==='buffer')gl.deleteBuffer(value);if(type==='texture')gl.deleteTexture(value);}
    this.resources=[];gl.getExtension('WEBGL_lose_context')?.loseContext();
  }
}
