const {chromium}=require('playwright');const D=__dirname;
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
 await p.goto('file://'+D+'/title.html');await p.evaluate(()=>Promise.all([document.fonts.load('700 120px P','A')]));
 const ids=['t0','t1','t2'];
 for(const id of ids){await p.evaluate(([id,ids])=>{for(const x of ids)document.getElementById(x).classList.toggle('hide',x!==id)},[id,ids]);
   await p.waitForTimeout(80);await p.screenshot({path:`${D}/title_${id}.png`,omitBackground:true});}
 await p.evaluate(ids=>{for(const x of ids)document.getElementById(x).classList.remove('hide')},ids);
 await p.screenshot({path:`${D}/title_full.png`,omitBackground:true});await b.close()})();
