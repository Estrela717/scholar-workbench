import {chromium} from 'playwright';
import {mkdir,writeFile} from 'node:fs/promises';
await mkdir('artifacts/screenshots',{recursive:true});
const browser=await chromium.launch({channel:'msedge',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:5173/',{waitUntil:'networkidle'});
await page.getByRole('heading',{name:'把文献，变成知识。'}).waitFor();
await page.screenshot({path:'artifacts/screenshots/library.png',fullPage:true});
for(const label of ['沉浸阅读','文献问答','发现论文','引用图谱','写作工坊','工作台设置']){
  await page.locator('aside.sidebar').getByRole('button',{name:label,exact:true}).click();
  await page.waitForTimeout(700);
  await page.screenshot({path:`artifacts/screenshots/${label}.png`,fullPage:true});
}
await page.locator('aside.sidebar').getByRole('button',{name:'写作工坊',exact:true}).click();
await page.getByRole('button',{name:'数据可视化',exact:true}).click();
await page.locator('input[type=file]').first().setInputFiles({name:'metrics.csv',mimeType:'text/csv',buffer:Buffer.from('Model,Score\nBaseline,72\nRAG,85\nHybrid,91\n')});
await page.getByText('已读取 3 行、2 列。').waitFor();
await page.screenshot({path:'artifacts/screenshots/chart.png',fullPage:true});
const mobile=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
await mobile.goto('http://127.0.0.1:5173/',{waitUntil:'networkidle'});
await mobile.screenshot({path:'artifacts/screenshots/mobile.png',fullPage:true});
const overflow=await mobile.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth);
await writeFile('artifacts/browser-qa.json',JSON.stringify({errors,mobileOverflow:overflow,checkedAt:new Date().toISOString()},null,2));
console.log(JSON.stringify({errors,mobileOverflow:overflow}));
await browser.close();
if(errors.length||overflow)process.exitCode=1;
