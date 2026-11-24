const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const C=JSON.parse(fs.readFileSync('/home/user/Mendaki/number_cards/cards.json'));
const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file:///home/user/Mendaki/number_cards/card.html');await p.evaluate(()=>Promise.all([document.fonts.load('800 64px P','Primary 1 → University'),document.fonts.load('500 28px P','a')]));
for(const c of C){await p.evaluate(c=>{document.getElementById('b').textContent=c.big;document.getElementById('s').textContent=c.small;const b=document.getElementById('b');let f=64;b.style.fontSize=f+'px';while(document.querySelector(".card").scrollWidth>780&&f>40){f-=2;b.style.fontSize=f+'px'}},c);
 await p.screenshot({path:`/home/user/Mendaki/number_cards/${c.id}.png`,omitBackground:true});}
await b.close()})();
