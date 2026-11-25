const {chromium}=require('playwright');const D=__dirname;
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
 await p.goto('file://'+D+'/end.html');await p.evaluate(()=>Promise.all([document.fonts.load('800 84px P','A'),document.fonts.load('600 58px P','A')]));
 const ids=['bg','l1','url','ul','l3'];
 for(const id of ids){await p.evaluate(([id,ids])=>{for(const x of ids)document.getElementById(x).classList.toggle('hide',x!==id)},[id,ids]);
   await p.waitForTimeout(80);await p.screenshot({path:`${D}/end_${id}.png`,omitBackground:true});}
 await p.evaluate(ids=>{for(const x of ids)document.getElementById(x).classList.remove('hide')},ids);
 await p.screenshot({path:`${D}/end_full.png`,omitBackground:true});
 await b.close()})();
