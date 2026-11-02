// 只读取当前渲染结果；设计副本由原生编辑器保存，不回写 React 源码。
export async function capturePage(exclude) {
  await document.fonts.ready;
  const properties=('display position box-sizing width height min-width max-width min-height max-height margin-top margin-right margin-bottom margin-left padding-top padding-right padding-bottom padding-left top right bottom left z-index overflow overflow-x overflow-y opacity visibility color background-color background-image background-size background-position background-repeat border-top border-right border-bottom border-left border-radius box-shadow outline font-family font-size font-weight font-style line-height letter-spacing text-align text-decoration text-transform white-space word-break overflow-wrap vertical-align flex-direction flex-wrap flex-grow flex-shrink flex-basis justify-content align-items align-content align-self order gap row-gap column-gap grid-template-columns grid-template-rows grid-column grid-row object-fit object-position transform transform-origin clip-path fill stroke stroke-width stroke-linecap stroke-linejoin filter').split(' ');
  const attrs=['viewBox','d','fill','fill-rule','clip-rule','stroke','stroke-width','stroke-linecap','stroke-linejoin','stroke-dasharray','stroke-dashoffset','x','y','x1','y1','x2','y2','cx','cy','r','rx','ry','width','height','points','transform','preserveAspectRatio','xmlns','offset','stop-color','stop-opacity','gradientUnits','gradientTransform','id','aria-label','title'];
  properties.push('grid-template-areas','grid-auto-flow','grid-auto-columns','grid-auto-rows','justify-items','justify-self','list-style-type','list-style-position','list-style-image','font-stretch','font-feature-settings','font-variation-settings','fill-opacity','stroke-opacity','stop-color','stop-opacity','translate','rotate','scale','mask-image','mask-size','mask-position','mask-repeat');
  let count=0;
  function node(el) {
    if(el===exclude||['SCRIPT','STYLE','LINK','META','TEMPLATE','NOSCRIPT','IFRAME','OBJECT','EMBED'].includes(el.tagName))return null;
    const cs=getComputedStyle(el);
    if(cs.display==='none'||cs.visibility==='hidden'||el.hidden)return null;
    if(++count>3000)throw new Error('当前页面元素过多，请收起无关区域后再添加。');
    const style={};for(const p of properties){const v=cs.getPropertyValue(p);if(v)style[p]=v;}
    // 固定控件在设计稿内定位；不跟随编辑器窗口。
    if(style.position==='fixed'){const r=el.getBoundingClientRect();Object.assign(style,{position:'absolute',left:r.left+scrollX+'px',top:r.top+scrollY+'px',right:'auto',bottom:'auto'});}
    const attributes={};for(const a of attrs)if(el.hasAttribute(a))attributes[a]=el.getAttribute(a);
    if(el.tagName==='IMG'){attributes.src=el.currentSrc||el.src;attributes.alt=el.alt;}
    const children=[];
    function pseudo(which){const ps=getComputedStyle(el,which),content=ps.content;if(!content||['none','normal'].includes(content)||ps.display==='none')return null;const style={};for(const p of properties){const v=ps.getPropertyValue(p);if(v)style[p]=v;}return {tag:'span',style,attributes:{},children:[content.replace(/^["']|["']$/g,'')]};}
    const before=pseudo('::before');if(before)children.push(before);
    for(const c of el.childNodes){if(c.nodeType===Node.TEXT_NODE)children.push(c.textContent);else if(c.nodeType===Node.ELEMENT_NODE){const next=node(c);if(next)children.push(next);}}
    const after=pseudo('::after');if(after)children.push(after);
    let tag=el.localName;
    if(['input','textarea','select'].includes(tag)){
      children.splice(0,children.length,tag==='select'?el.selectedOptions?.[0]?.textContent??'':el.type==='password'?'••••••':el.value||el.placeholder||'');tag='div';
    }
    if(['canvas','video','audio'].includes(tag)){children.splice(0,children.length,'媒体预览');tag='div';}
    return {tag,style,attributes,children};
  }
  const loaded=[...document.fonts].filter(f=>f.status==='loaded'),fonts=[],warnings=[],seen=new Set();
  const sources=[];
  function rules(sheet){try{for(const r of sheet.cssRules){if(r.type===5)sources.push({style:r.style,base:sheet.href||location.href});else if(r.styleSheet)rules(r.styleSheet);else if(r.cssRules)rules(r);}}catch{}}
  for(const sheet of document.styleSheets)rules(sheet);
  for(const {style,base} of sources){
    const family=style.getPropertyValue('font-family').replace(/^["']|["']$/g,''),weight=style.getPropertyValue('font-weight')||'400',fontStyle=style.getPropertyValue('font-style')||'normal';
    const key=family+'|'+weight+'|'+fontStyle;
    if(seen.has(key)||!loaded.some(f=>f.family.replace(/^["']|["']$/g,'')===family&&f.weight===weight&&f.style===fontStyle))continue;
    seen.add(key);if(fonts.length>=12)break;
    const match=style.getPropertyValue('src').match(/url\(\s*["']?([^"')]+)["']?\s*\)/);if(!match)continue;
    try{
      const response=await fetch(new URL(match[1],base));if(!response.ok)throw new Error();const bytes=new Uint8Array(await response.arrayBuffer());if(bytes.length>1500000)throw new Error();
      let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));
      fonts.push({family,weight,style:fontStyle,base64:btoa(binary)});
    }catch{warnings.push('字体未导入：'+family+' '+fontStyle);}
  }
  const background=getComputedStyle(document.body).backgroundColor;
  return {title:document.querySelector('main h1,#main h1,h1')?.textContent.trim()||document.title,route:location.pathname+location.search+location.hash,origin:location.origin,language:document.documentElement.lang||'en',theme:document.documentElement.dataset.colorScheme||'light',width:innerWidth,height:Math.min(8000,Math.max(innerHeight,document.documentElement.scrollHeight)),background,nodes:[...document.body.children].map(node).filter(Boolean),fonts,warnings};
}
