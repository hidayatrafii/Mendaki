const {chromium}=require('playwright');const D=__dirname;
const Q={q1:'What inspired you?',q2:'Most rewarding part?',q3:'A memorable moment?',q4:'Beyond academics?',q5:'Thinking of joining?'};
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
 await p.goto('file://'+D+'/lt.html');
 for(const [id,n,d,y] of [['lt_syaheer','Muhammad Syaheer Bin Noorhalim','','MAP Coach since 2011'],
                          ['lt_azyyati','Nur Azyyati Binte Ismail','','MAP Coach since 2015']]){
   await p.evaluate(([n,d,y])=>{document.getElementById('n').textContent=n;document.getElementById('d').textContent=d;document.getElementById('d').style.display=d?'block':'none';document.getElementById('y').textContent=y},[n,d,y]);
   await p.screenshot({path:`${D}/${id}.png`,omitBackground:true});}
 await p.goto('file://'+D+'/q.html');await p.evaluate(()=>Promise.all([document.fonts.load('800 50px P','A')]));
 for(const [id,t] of Object.entries(Q)){await p.evaluate(t=>{document.getElementById('t').textContent=t},t);
   await p.waitForTimeout(100);await p.screenshot({path:`${D}/${id}.png`,omitBackground:true});}
 await p.goto('file://'+D+'/card.html');await p.evaluate(()=>Promise.all([document.fonts.load('800 64px P','A'),document.fonts.load('500 28px P','a')]));
 for(const c of [{id:'end',top:'900px',big:'Be a MAP Coach',small:'Sign up now at mendaki.org.sg',logo:true}]){
   await p.evaluate(c=>{document.querySelector('.wrap').style.setProperty('--top',c.top);document.getElementById('b').textContent=c.big;document.getElementById('s').textContent=c.small;
     document.getElementById('logo').style.display=c.logo?'block':'none'},c);
   await p.waitForTimeout(150);await p.screenshot({path:`${D}/${c.id}.png`,omitBackground:true});}
 await b.close()})();
