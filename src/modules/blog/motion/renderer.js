// Transparent WebGL pixels reveal the actual blog DOM underneath the canvas.
const vertex = `attribute vec2 position;
void main(){gl_Position=vec4(position,0.,1.);}`;
const fragment = `precision highp float;
uniform vec2 resolution;
uniform float progress;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){
  // Keep square pixels at every viewport size; flashes stay small and local.
  float size=max(12.,floor(resolution.x/86.));
  vec2 position=vec2(gl_FragCoord.x,resolution.y-gl_FragCoord.y);
  vec2 cell=floor(position/size);
  vec2 cells=ceil(resolution/size);
  vec2 uv=(cell+.5)/cells;
  float seed=hash(cell);
  float cluster=hash(floor(cell/vec2(6.,3.)));
  float field=uv.x*.31+uv.y*.69+(seed-.5)*.15+(cluster-.5)*.10;
  float sweep=mix(-.24,1.28,smoothstep(.10,1.,progress));
  float distance=field-sweep;
  float cover=smoothstep(-.045,.025,distance);
  float edge=exp(-abs(distance)*37.);
  float tile=step(.91,seed)*.10+step(.73,cluster)*.024;
  float seam=step(.8,mod(position.x,size))*step(.8,mod(position.y,size));
  float tone=.027+tile+seam*.012;
  // Thin silver trails travel along a few pixel rows ahead of the reveal front.
  float row=hash(vec2(cell.y,19.));
  float streak=step(.88,row)*exp(-abs(distance-.042)*24.);
  float core=step(.965,seed)*exp(-abs(distance)*12.);
  tone+=edge*(.12+seed*.26)+streak*.62+core*.24;
  // Each sparse light has one staggered pulse, a square core and a short silver ray.
  // The progress timeline makes pause/resume deterministic without extra timers.
  vec2 lightCell=floor(cell/vec2(7.,5.));
  float lightSeed=hash(lightCell+vec2(51.,13.));
  vec2 lightCenter=(lightCell*vec2(7.,5.)+vec2(1.5+lightSeed*4.,1.5+hash(lightCell+9.)*2.))*size;
  vec2 delta=position-lightCenter;
  float age=progress-(.035+lightSeed*.66);
  float pulse=smoothstep(0.,.014,age)*(1.-smoothstep(.035,.115,age));
  float point=1.-smoothstep(1.,2.,max(abs(delta.x),abs(delta.y)));
  float ray=exp(-abs(delta.x)/(size*.65))*exp(-abs(delta.y)/.65);
  float crossRay=exp(-abs(delta.y)/(size*.28))*exp(-abs(delta.x)/.65);
  float halo=exp(-length(delta)/(size*.32))*.16;
  float glint=step(.38,lightSeed)*pulse*(point+ray*.65+crossRay*.3+halo);
  glint*=smoothstep(.015,.09,distance)*(1.-smoothstep(.8,.95,progress));
  tone+=glint;
  float alpha=max(cover,(edge*.7+streak*.5)*(1.-smoothstep(.91,1.,progress)));
  alpha*=1.-smoothstep(.94,1.,progress);
  gl_FragColor=vec4(vec3(min(tone,.96)),clamp(alpha,0.,1.));
}`;

export class PixelRenderer {
  constructor(canvas){this.canvas=canvas;this.resources=[];this.disposed=false;}
  init(){
    const gl=this.canvas.getContext('webgl',{alpha:true,premultipliedAlpha:false,antialias:false,powerPreference:'low-power'});
    if(!gl)return false;
    this.gl=gl;
    this.canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();this.lost=true;});
    const compile=(type,source)=>{
      const shader=gl.createShader(type);this.resources.push(['shader',shader]);
      gl.shaderSource(shader,source);gl.compileShader(shader);
      if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS))throw Error('Pixel shader compilation failed');
      return shader;
    };
    const program=gl.createProgram();this.resources.push(['program',program]);this.program=program;
    gl.attachShader(program,compile(gl.VERTEX_SHADER,vertex));
    gl.attachShader(program,compile(gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);
    if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('Pixel shader link failed');
    gl.useProgram(program);
    const buffer=gl.createBuffer();this.resources.push(['buffer',buffer]);
    gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
    gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
    const position=gl.getAttribLocation(program,'position');
    gl.enableVertexAttribArray(position);gl.vertexAttribPointer(position,2,gl.FLOAT,false,0,0);
    this.resolution=gl.getUniformLocation(program,'resolution');
    this.progress=gl.getUniformLocation(program,'progress');
    this.ready=true;return true;
  }
  draw(scene,progress){
    if(!this.ready||this.disposed)return;
    if(this.lost)throw Error('Graphics context lost');
    const gl=this.gl,canvas=this.canvas,rect=canvas.getBoundingClientRect();
    const ratio=Math.min(devicePixelRatio||1,1.25);
    const width=Math.max(1,Math.round(rect.width*ratio)),height=Math.max(1,Math.round(rect.height*ratio));
    if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height;}
    gl.viewport(0,0,width,height);gl.useProgram(this.program);
    gl.uniform2f(this.resolution,width,height);gl.uniform1f(this.progress,progress);
    gl.drawArrays(gl.TRIANGLES,0,6);
  }
  destroy(){
    if(this.disposed)return;this.disposed=true;
    const gl=this.gl;if(!gl)return;
    for(const [type,value] of this.resources){
      if(type==='shader')gl.deleteShader(value);
      if(type==='program')gl.deleteProgram(value);
      if(type==='buffer')gl.deleteBuffer(value);
    }
    this.resources=[];gl.getExtension('WEBGL_lose_context')?.loseContext();
  }
}
