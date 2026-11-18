import {chromium} from 'playwright';
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import path from 'node:path';

const track=process.argv[2]||'innovation';
const root=process.cwd(),out=path.join(root,'artifacts','video-raw',track);
await mkdir(out,{recursive:true});
const chapters=JSON.parse(await readFile('tools/video_manifest.json','utf8'))[track];
const audioDurations=JSON.parse(await readFile(path.join(out,'audio-durations.json'),'utf8'));
const base=process.env.DEMO_URL||'http://127.0.0.1:8767/';
const attention='60d4185358b54b60a2e4c2a3282319f9', book='cb6634f45cd04076bf3b07d6c975308f';
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1,recordVideo:{dir:out,size:{width:1920,height:1080}}});
const page=await context.newPage();
page.setDefaultTimeout(20000);
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const timeline=[];
const escape=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
let inCard=false;
async function app(){if(inCard||page.url()!==base){await page.goto(base,{waitUntil:'networkidle'});inCard=false;} }
async function nav(name){await app();await page.locator('aside.sidebar').getByRole('button',{name:new RegExp('^'+name)}).click();await page.waitForTimeout(800);}
async function caption(title){await page.evaluate(title=>{let el=document.querySelector('#demo-caption');if(!el){el=document.createElement('div');el.id='demo-caption';el.style.cssText='position:fixed;z-index:99999;left:280px;right:24px;bottom:12px;padding:14px 22px;border-radius:10px;background:#142f3ff2;color:white;font:19px Microsoft YaHei;pointer-events:none;box-shadow:0 8px 30px #0002;display:flex;justify-content:space-between';document.body.append(el);}el.replaceChildren();const a=document.createElement('span');a.textContent=title;const b=document.createElement('span');b.textContent='本地实操与记录复盘 · 合成配音';b.style.cssText='font-size:14px;opacity:.7';el.append(a,b);},title);}
async function card(title,lead,blocks){
  inCard=true;
  await page.setContent(`<html lang="zh-CN"><meta charset="utf-8"><style>*{box-sizing:border-box}body{margin:0;background:#edf3ef;color:#163c46;font-family:'Microsoft YaHei';padding:88px 104px}.eyebrow{color:#2d8273;letter-spacing:4px;font-size:18px}h1{font-size:48px;margin:20px 0 24px;font-weight:650}p{font-size:25px;line-height:1.8;max-width:1500px;color:#52716f}.grid{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin-top:34px}section{padding:30px;border-radius:20px;background:white;border:1px solid #dce6df}h2{font-size:24px;margin:0 0 20px;color:#247868}pre{white-space:pre-wrap;word-break:break-word;line-height:1.7;font:19px/1.75 Consolas,'Microsoft YaHei';max-height:490px;overflow:hidden;margin:0}.foot{position:fixed;bottom:35px;font-size:16px;color:#78908b}</style><body><div class="eyebrow">SCHOLAR WORKBENCH / ${track==='innovation'?'DEVELOPMENT EVIDENCE':'LOCAL RESEARCH AGENT'}</div><h1>${escape(title)}</h1><p>${escape(lead)}</p><div class="grid">${blocks.map(([h,c])=>`<section><h2>${escape(h)}</h2><pre>${escape(c)}</pre></section>`).join('')}</div><div class="foot">基于真实源码和运行记录的复盘页面 · 非伪造实时对话 · 2026.11.18</div></body></html>`);
}
async function readSnippet(file,needle,count=17){const s=(await readFile(file,'utf8')).split('\n');const i=Math.max(0,s.findIndex(x=>x.includes(needle)));return s.slice(i,i+count).join('\n');}
async function reader(id=attention,p=1){await nav('沉浸阅读');await page.locator('.reader-controls select').selectOption(id);await page.waitForTimeout(1000);await page.getByRole('spinbutton',{name:'页码'}).fill(String(p));await page.waitForTimeout(1200);await page.getByRole('button',{name:'对照阅读',exact:true}).click();}
const actions={
  home:async()=>{await app();},
  library:async()=>{await nav('文献库');await page.locator('main').evaluate(el=>el.scrollTop=0);},
  'process-intent':async()=>card('01 / 将用户意图变成开发约束','真实用户要求决定实现范围；过程记录与源码保存为可审查的项目文件。',[
    ['公开用户指令','“从零开始。两个都做，全部由你来完成，今天能不能做完”\n\n“都没有，先做本地可运行版”\n\n来源：当前真实会话公开用户消息节选。'],
    ['真实阶段提交',execFileSync('git',['log','--oneline','-6'],{encoding:'utf8'})]]),
  'process-data':async()=>card('02 / 先约定数据，再连接六个模块','页码、坐标和稳定内容块 ID 是科研助手可追溯性的基础。',[
    ['数据库真实定义',await readSnippet('app/db.py','CREATE TABLE IF NOT EXISTS chunks',16)],
    ['从模型到产品','用户意图 → 本地优先的研究工作流\n\nPDF 原文 → 页码与块坐标 → 混合检索\n\n证据编号 → 生成回答 → 引用校验\n\n同一来源贯穿阅读、问答和写作。']]),
  'process-parser':async()=>card('03 / 真实文献暴露问题，修复规则','同篇论文版本、双栏论文和 541 页教材，直接推动解析迭代。',[
    ['解析源码片段',await readSnippet('app/parser.py','title_candidates',18)],
    ['实际观察与处理','问题：arXiv 竖排侧栏干扰标题。\n处理：排除竖排标签，合并标题行。\n\n问题：参考条目跨文本块被截断。\n处理：按编号重新组织引用条目。\n\n验证：v1 / v7 内容重合约 0.812；\n教材 541 页，11,272 个内容块。']]),
  'process-citations':async()=>card('04 / 让模型结果接受检查','保留失败记录，改进编号边界；最终回答和模型推理使用不同字段。',[
    ['模型响应处理',await readSnippet('app/llm.py','result = response.json()',12)],
    ['已验证的修复','原论文 [33] ≠ 检索证据 [33]\n\n送入模型前区分两种引用编号。\n越界、缺失引用不直接作为可信答案。\n\n默认使用 Qwen 视觉指令模型。\n兼容思考模型时仅读取最终 content。\n长度截断时明确报错，允许重试。']]),
  'process-tests':async()=>card('05 / 验收围绕实际失败风险','自动化结果、浏览器结果与真实模型输出分别保存，不混淆验证范围。',[
    ['后端与浏览器','pytest：23 passed\n\n扫描 OCR、版本检测、120 页解析\n证据坐标、错误引用拒绝\n翻译取消与缓存续传\n模型推理分离与截断检查\n\n浏览器：7 个页面，运行错误 0\n390px 手机布局：横向溢出 false'],
    ['真实模型验收','Qwen 本地模型 + BGE-M3 / 本机运行\n\n英文论文 → 中文问题 → 原文证据\nbase：8 块 P100 / 12 小时\nbig：8 块 P100 / 3.5 天\n\n段落翻译与三点方法概述均已实测。\n编号有效仍需核对具体论断。']]),
  architecture:async()=>card('可追溯的本地科研助手','围绕文献证据组织应用；模型负责规划和表达，服务负责执行与校验。',[
    ['数据与模型路径','PDF → PyMuPDF / 扫描 OCR\n       ↓\nSQLite：文本 + 页码 + 坐标\n       ↓\nBM25 + BGE-M3 → 排名融合\n       ↓\nQwen 本地模型 → 证据编号校验\n       ↓\n回答 / 阅读定位 / 写作草稿'],
    ['工具执行边界','原生 Function Calling\n\n允许：本地文献检索、引用图谱\n条件开放：公开 arXiv 检索\n\n参数重新检查；最多 3 次工具建议。\n无有效规划时回退固定检索。\n不执行任意生成代码。\n论文内容作为数据，不作为指令。']]),
  book:async()=>reader(book,541),
  reader:async()=>{await reader();await page.getByRole('button',{name:'目录',exact:true}).click();await page.waitForTimeout(2500);await page.getByRole('button',{name:'对照阅读',exact:true}).click();},
  search:async()=>{await nav('文献问答');await page.getByLabel('仅检索原文').check();await page.locator('.doc-chips button').filter({hasText:'Attention Is All You Need'}).last().click();await page.locator('.composer textarea').fill('eight P100 GPUs training hours');const pending=page.waitForResponse(r=>r.url().endsWith('/api/search'),{timeout:150000});await page.locator('.send-button').click();await pending;await page.locator('.source-list button').first().waitFor();},
  ask:async()=>{await nav('文献问答');await page.locator('.doc-chips button').filter({hasText:'Attention Is All You Need'}).last().click();await page.getByLabel('智能体工具调用').check();await page.locator('.composer textarea').fill('Transformer 的 base 和 big 模型分别使用多少块 GPU，训练了多久？');const pending=page.waitForResponse(r=>r.url().endsWith('/api/ask'),{timeout:240000});await page.locator('.send-button').click();const response=await pending;const result=await response.json();await writeFile(path.join(out,'recorded-answer.json'),JSON.stringify(result,null,2));if(!response.ok()||!result.validated)throw new Error('Live recorded answer did not validate');await page.locator('.assistant-answer').last().waitFor();await page.locator('details.trace summary').click();await page.waitForTimeout(5000);},
  source:async()=>{await page.locator('.assistant-answer .citation').first().click();await page.waitForTimeout(2000);await page.locator('.reader-title').waitFor();},
  structures:async()=>{await reader(attention,3);await page.getByRole('button',{name:'图表与公式',exact:true}).click();await page.locator('.formula-render .katex').waitFor();await page.locator('.formula-render').first().scrollIntoViewIfNeeded();},
  discover:async()=>{await nav('发现论文');await page.getByPlaceholder('输入研究主题、论文标题或关键词（英文更准确）').fill('retrieval augmented generation');const response=page.waitForResponse(r=>r.url().includes('/api/discover?'),{timeout:100000});await page.locator('form').getByRole('button').click();const r=await response;await writeFile(path.join(out,'recorded-discovery.json'),JSON.stringify(await r.json(),null,2));await page.waitForTimeout(1000);},
  graph:async()=>nav('引用图谱'),
  writing:async()=>{await nav('引用图谱');await page.waitForTimeout(4000);await nav('写作工坊');await page.locator('.saved-notes button').first().click();await page.waitForTimeout(1000);},
  chart:async()=>{await nav('写作工坊');await page.getByRole('button',{name:'数据可视化',exact:true}).click();await page.locator('input[type=file]').first().setInputFiles({name:'demo-example.csv',mimeType:'text/csv',buffer:Buffer.from('X,Y,Z\n1,72,180\n2,81,220\n3,91,240\n')});await page.getByText('已读取 3 行、3 列。').waitFor();await page.waitForTimeout(3500);await page.getByLabel('图表类型',{exact:true}).selectOption('radar');await page.waitForTimeout(4000);await page.getByLabel('图表类型',{exact:true}).selectOption('scatter3d');await page.waitForTimeout(2000);},
  ending:async()=>card('本地版本交付 · 真实边界','已实现的能力附源码与验证证据；正式参赛材料仍需满足各赛道的外部要求。',[
    ['本次交付','本地应用与一键启动脚本\nPython / Node 依赖锁文件\n真实 Git 阶段历史\n23 项后端测试与浏览器检查\n两套技术 PDF\n两套 1080p 演示与配音脚本'],
    ['评审与提交注意事项','临时公网入口需电脑持续在线\n公开 GitHub 仓库已推送\n公式、周期追踪与三维图已补充\n\n参赛身份已填写，最终提交未执行\n原始功能链与意图控制按真实记录展示\n同源作品双赛参评的官方确认']])
};
let video;
try{
  await page.goto(base,{waitUntil:'networkidle'});
  for(let i=0;i<chapters.length;i++){
    const c=chapters[i],start=Date.now();
    await actions[c.action]();await caption(c.title);
    const minimum=process.env.DEMO_FAST ? 1 : Math.max(28,audioDurations[i]+2);
    await page.waitForTimeout(Math.max(1000,minimum*1000-(Date.now()-start)));
    const seconds=(Date.now()-start)/1000;
    timeline.push({...c,seconds,index:i});
    await page.screenshot({path:path.join(out,`chapter-${String(i).padStart(2,'0')}.png`)});
    await writeFile(path.join(out,'timeline.json'),JSON.stringify({track,timeline,errors},null,2));
    console.log(JSON.stringify({track,chapter:i+1,seconds,title:c.title}));
  }
  video=page.video();await context.close();
  await video.saveAs(path.join(out,'screen.webm'));
  console.log(JSON.stringify({track,complete:true,total:timeline.reduce((n,c)=>n+c.seconds,0),errors}));
}finally{await browser.close();}
if(errors.length)process.exitCode=1;
