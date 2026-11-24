const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file:///home/user/Mendaki/cover/cover.html');await p.evaluate(()=>Promise.all([document.fonts.load('800 60px P','$'),document.fonts.load('600 40px P','a'),document.fonts.load('500 30px P','a')]));
await p.screenshot({path:'/home/user/Mendaki/cover/MENDAKI_ReadyForSchool_cover_1080x1920.png'});
await p.addStyleTag({content:'body::after{content:"";position:absolute;left:0;right:0;top:285px;height:1350px;outline:6px dashed red}'});
await p.screenshot({path:'/home/user/Mendaki/cover/crop_check.png'});await b.close()})();
