#!/usr/bin/env node
/* 同步字庫：從「墨龍飛天」的 index.html 讀 THEMES，轉成本遊戲的字庫（含注音），寫回 index.html。
   用法：node tools/sync-bank.js /路徑/el-dragon-de-tinta/index.html
   （只動 index.html 裡 BANK:START ～ BANK:END 之間的內容；不連 Firebase） */
const fs=require('fs');
const src=process.argv[2];
if(!src){console.error('請給墨龍飛天 index.html 的路徑');process.exit(1);}
// 拼音 → 注音
const INI={b:'ㄅ',p:'ㄆ',m:'ㄇ',f:'ㄈ',d:'ㄉ',t:'ㄊ',n:'ㄋ',l:'ㄌ',g:'ㄍ',k:'ㄎ',h:'ㄏ',j:'ㄐ',q:'ㄑ',x:'ㄒ',zh:'ㄓ',ch:'ㄔ',sh:'ㄕ',r:'ㄖ',z:'ㄗ',c:'ㄘ',s:'ㄙ'};
const FIN={a:'ㄚ',o:'ㄛ',e:'ㄜ',ai:'ㄞ',ei:'ㄟ',ao:'ㄠ',ou:'ㄡ',an:'ㄢ',en:'ㄣ',ang:'ㄤ',eng:'ㄥ',er:'ㄦ',
 i:'ㄧ',ia:'ㄧㄚ',io:'ㄧㄛ',ie:'ㄧㄝ',iao:'ㄧㄠ',iu:'ㄧㄡ',ian:'ㄧㄢ',in:'ㄧㄣ',iang:'ㄧㄤ',ing:'ㄧㄥ',iong:'ㄩㄥ',
 u:'ㄨ',ua:'ㄨㄚ',uo:'ㄨㄛ',uai:'ㄨㄞ',ui:'ㄨㄟ',uan:'ㄨㄢ',un:'ㄨㄣ',uang:'ㄨㄤ',ong:'ㄨㄥ',
 'ü':'ㄩ','üe':'ㄩㄝ','üan':'ㄩㄢ','ün':'ㄩㄣ'};
const TONE={'ā':['a',1],'á':['a',2],'ǎ':['a',3],'à':['a',4],'ē':['e',1],'é':['e',2],'ě':['e',3],'è':['e',4],
 'ī':['i',1],'í':['i',2],'ǐ':['i',3],'ì':['i',4],'ō':['o',1],'ó':['o',2],'ǒ':['o',3],'ò':['o',4],
 'ū':['u',1],'ú':['u',2],'ǔ':['u',3],'ù':['u',4],'ǖ':['ü',1],'ǘ':['ü',2],'ǚ':['ü',3],'ǜ':['ü',4]};
const MARK=['','','ˊ','ˇ','ˋ'];
function split(py){
  const V='aeiouüāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ';
  const re=new RegExp('(?:zh|ch|sh|[bpmfdtnlgkhjqxrzcsyw])?['+V+']+(?:ng|n(?![' + V + ']))?','g');
  return py.match(re)||[];
}
function syl2zy(s){
  if(/^[eēéěè]r$/.test(s)){const t={e:5,'ē':1,'é':2,'ě':3,'è':4}[s[0]];return (t===5?'˙':'')+'ㄦ'+(t>1&&t<5?MARK[t]:'');}
  let tone=5,b='';
  for(const c of s){ if(TONE[c]){b+=TONE[c][0];tone=TONE[c][1];} else b+=c; }
  let ini='';
  for(const k of ['zh','ch','sh']) if(b.startsWith(k)){ini=k;break;}
  if(!ini&&INI[b[0]])ini=b[0];
  let fin=b.slice(ini.length);
  if(['j','q','x'].includes(ini)&&fin.startsWith('u'))fin='ü'+fin.slice(1);
  if(['zh','ch','sh','r','z','c','s'].includes(ini)&&fin==='i')return (tone===5?'˙':'')+INI[ini]+(tone>1&&tone<5?MARK[tone]:'');
  if(ini===''){ // 零聲母：yi wu yu 等
    const map={yi:'i',yin:'in',ying:'ing',ya:'ia',yo:'io',ye:'ie',yao:'iao',you:'iu',yan:'ian',yang:'iang',yong:'iong',
      wu:'u',wa:'ua',wo:'uo',wai:'uai',wei:'ui',wan:'uan',wen:'un',wang:'uang',weng:'ong',
      yu:'ü',yue:'üe',yuan:'üan',yun:'ün'};
    fin=map[b]||b;
  }
  const z=(INI[ini]||'')+(FIN[fin]||('?'+fin));
  if(tone===5)return '˙'+z; if(tone===1)return z; return z+MARK[tone];
}
const zy=py=>{const parts=/^[eēéěè]r$/.test(py)?[py]:split(py);return parts.map(syl2zy).join('');};
const s=fs.readFileSync(src,'utf8');
const a=s.indexOf('const THEMES = [');
const b=s.indexOf('\n];',a)+3;
const T=eval(s.slice(a+'const THEMES = '.length,b).replace(/;\s*$/,''));
const seen=new Set(),out=[];
T.forEach(t=>t.words.forEach(w=>{
  if(seen.has(w[0]))return;seen.add(w[0]);
  const z=zy(w[2]);if(/\?/.test(z))throw new Error('注音失敗 '+w[0]+' '+w[2]+' '+z);
  out.push({zh:w[0],sc:w[1],py:w[2],zy:z,es:w[3],en:w[4]});
}));
const body='/* BANK:START（由 tools/sync-bank.js 產生，請勿手改） */\nconst BANK=[\n'+
  out.map(o=>' '+JSON.stringify(o).replace(/"(\w+)":/g,'$1:').replace(/'/g,"\\'").replace(/"/g,"'")).join(',\n')+'\n];\n/* BANK:END */';
const f=__dirname+'/../index.html';
let h=fs.readFileSync(f,'utf8');
if(h.includes('/* BANK:START')) h=h.replace(/\/\* BANK:START[\s\S]*?\/\* BANK:END \*\//,()=>body);
else h=h.replace(/const BANK=\[[\s\S]*?\n\];/,()=>body);
fs.writeFileSync(f,h);
console.log('字庫',out.length,'詞');
