const {chromium}=require('playwright');const D=__dirname;
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
 await p.goto('file://'+D+'/lt.html');
 for(const [id,n,d,y] of [['lt_syaheer','Muhammad Syaheer Bin Noorhalim','Department Head, IT Infrastructure and Operations','MAP Coach since 2011'],
                          ['lt_azyyati','Nur Azyyati Binte Ismail','Freelance Visual Arts Trainer','MAP Coach since 2015']]){
   await p.evaluate(([n,d,y])=>{document.getElementById('n').textContent=n;document.getElementById('d').textContent=d;document.getElementById('y').textContent=y},[n,d,y]);
   await p.screenshot({path:`${D}/${id}.png`,omitBackground:true});}
 await p.goto('file://'+D+'/card.html');await p.evaluate(()=>Promise.all([document.fonts.load('800 64px P','A'),document.fonts.load('500 28px P','a')]));
 for(const c of [{id:'hook',top:'395px',big:'Meet our MAP Coaches',small:'MENDAKI Achievement Programme (MAP)',logo:false},
                 {id:'end',top:'900px',big:'Be a MAP Coach',small:'Sign up now at mendaki.org.sg',logo:true}]){
   await p.evaluate(c=>{document.querySelector('.wrap').style.setProperty('--top',c.top);document.getElementById('b').textContent=c.big;document.getElementById('s').textContent=c.small;
     document.getElementById('logo').style.display=c.logo?'block':'none';const b=document.getElementById('b');let f=64;b.style.fontSize=f+'px';
     while(document.querySelector('.card').scrollWidth>820&&f>40){f-=2;b.style.fontSize=f+'px'}},c);
   await p.waitForTimeout(150);await p.screenshot({path:`${D}/${c.id}.png`,omitBackground:true});}
 await b.close()})();
