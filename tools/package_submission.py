"""Build the private dated handoff from committed source and verified media."""
import hashlib,json,shutil,subprocess,zipfile
from pathlib import Path
from html import escape

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output/submission-2026-11-18';OUT.mkdir(parents=True,exist_ok=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
source=OUT/'知研-源码与构建.zip'
subprocess.run(['git','archive','--format=zip','--prefix=scholar-workbench/','--output='+str(source),'HEAD'],cwd=ROOT,check=True)
with zipfile.ZipFile(source,'a',compression=zipfile.ZIP_DEFLATED) as z:
    for p in (ROOT/'dist').rglob('*'):
        if p.is_file():z.write(p,'scholar-workbench/'+p.relative_to(ROOT).as_posix())
bundle=OUT/'知研-完整Git历史.bundle'
subprocess.run(['git','bundle','create',str(bundle),'--all'],cwd=ROOT,check=True)
for track in ('AI创新应用挑战赛','AI大模型创新应用挑战赛'):
    shutil.copyfile(ROOT/'output/videos'/f'{track}-知研本地演示与复盘.mp4',OUT/f'曲珈莹-{track}-演示.mp4')
for filename,title in [('submission-2026-11-18.md','双赛提交说明.md'),('defense-guide.md','答辩准备.md'),('online-review.md','评审运行与恢复.md'),('sample-sources.md','样例来源.md'),('validation.md','实际验收记录.md')]:
    shutil.copyfile(ROOT/'docs'/filename,OUT/title)
shutil.copyfile(ROOT/'output/videos/视频技术验收.json',OUT/'视频技术验收.json')
evidence=OUT/'真实开发过程.zip'
with zipfile.ZipFile(evidence,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in (ROOT/'artifacts/process-evidence').iterdir():
        if p.is_file():z.write(p,p.name)
    for p in (ROOT/'artifacts').glob('*.json'):z.write(p,'验收记录/'+p.name)
profile=json.loads((ROOT/'docs/participant.json').read_text('utf8'))
cards=[]
for track in ('AI创新应用挑战赛','AI大模型创新应用挑战赛'):
    pdf=f'曲珈莹-{track}-技术文档.pdf';mp4=f'曲珈莹-{track}-演示.mp4'
    cards.append(f'<section><span>{track}</span><h2>{"意图控制与真实协同开发" if "大模型" not in track else "科研流程与模型工程"}</h2><p>12 页技术 PDF · 1080p 实操视频 · 明示合成普通话配音</p><a href="{pdf}">技术文档 PDF ↗</a><a href="{mp4}">演示 MP4 ↗</a><video controls preload="metadata" src="{mp4}"></video></section>')
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>曲珈莹 · 知研双赛交付</title><style>*{box-sizing:border-box}body{margin:0;background:#f1f5f1;color:#183b44;font:16px/1.8 system-ui,'Microsoft YaHei'}main{max-width:1180px;margin:50px auto;padding:0 28px}h1{font-size:42px}h2{font-size:23px}p{color:#56736d}a{color:#267a67;text-decoration:none;display:inline-block;margin:8px 22px 8px 0}a:hover{text-decoration:underline}.hero{padding:30px;border-radius:20px;background:#183b44;color:white}.hero p{color:#d0e3da}.hero a{background:white;padding:8px 20px;border-radius:8px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:25px 0}section{background:white;border:1px solid #dfe7e1;padding:28px;border-radius:20px}section span{color:#68917e;font-size:13px}video{width:100%;margin-top:20px;border-radius:10px}.limits{padding:20px 28px;border-left:4px solid #c49f65;background:#fffaf0;margin:25px 0}footer{font-size:12px;color:#6d8980}code{word-break:break-all}@media(max-width:800px){.grid{grid-template-columns:1fr}h1{font-size:30px}}</style><main><small>SCHOLAR WORKBENCH / 2026.11.18</small><h1>知研，让每个洞察都有出处。</h1><p>曲珈莹 · 云南大学 · 人工智能 / 2025 级 · A 组 · 指导教师：无</p><div class="hero"><h2>打开应用，核对真实工作流</h2><p>本机模型和样例已就绪。普通工作台使用 start.cmd；公开评审是带口令的独立实例。</p><a href="http://127.0.0.1:8765">本地工作台 ↗</a>'''+f'<a href="{escape(profile["demo"])}">HTTPS 评审入口 ↗</a><a href="{escape(profile["repository"])}">GitHub 源码 ↗</a>'+'''</div><div class="grid">'''+''.join(cards)+'''</div><section><h2>代码、过程与复现</h2><a href="知研-源码与构建.zip">源码与界面构建 ZIP ↗</a><a href="知研-完整Git历史.bundle">完整 Git 历史 ↗</a><a href="真实开发过程.zip">公开对话、三条功能链与验收证据 ↗</a><a href="答辩准备.md">答辩准备 ↗</a><a href="双赛提交说明.md">提交说明 ↗</a><a href="实际验收记录.md">实际验收 ↗</a><a href="样例来源.md">样例来源 ↗</a><p>源码包不含模型权重、依赖环境或完整论文 PDF。Git bundle 可用 git clone 恢复。三条功能链来自同一真实会话，不伪造独立用户逐轮 Prompt。</p></section><div class="limits"><h2>提交和访问状态</h2><p>工程与材料已准备，尚未在赛事个人中心上传。临时公网依赖本机、Ollama 和隧道持续运行；重启隧道可能更换域名。原始 Prompt 链评分、协同复盘形式和同源双赛资格仍须按主办方要求确认。</p><a href="评审访问信息-勿提交到公开仓库.txt">私有评审口令说明 ↗</a><a href="评审运行与恢复.md">恢复公网访问 ↗</a><p>本交付包内有私有评审口令，只交给本人及评审；不要整体上传到公开 Git 仓库。</p></div><footer>23 项后端测试通过；七页界面检查、五类图表、真实长书及模型修复记录已留存。测试替身与真实模型结果分别记录。<br>源码版本：<code>'''+head+'''</code> · <a href="交付文件校验.json">SHA-256 校验 ↗</a></footer></main></html>'''
(OUT/'交付导航.html').write_text(html,'utf8')
items=[]
for p in sorted(OUT.iterdir()):
    if p.is_file() and p.name not in ('交付文件校验.json','曲珈莹-知研双赛完整交付包.zip'):
        with p.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        items.append({'path':p.name,'bytes':p.stat().st_size,'sha256':digest})
(OUT/'交付文件校验.json').write_text(json.dumps({'date':'2026-11-18','git_commit':head,'contains_private_reviewer_credentials':True,'files':items},ensure_ascii=False,indent=2),'utf8')
delivery=OUT/'曲珈莹-知研双赛完整交付包.zip'
with zipfile.ZipFile(delivery,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.iterdir()):
        if p.is_file() and p!=delivery:z.write(p,'知研双赛交付/'+p.name)
for p in (source,evidence,delivery):
    with zipfile.ZipFile(p) as z:assert z.testzip() is None,p
subprocess.run(['git','bundle','verify',str(bundle)],cwd=ROOT,check=True)
# Redirect the earlier delivery index to the current folder without deleting history.
(ROOT/'output/交付导航.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=submission-2026-11-18/交付导航.html"><a href="submission-2026-11-18/交付导航.html">打开 11 月 18 日最终交付</a>','utf8')
print(json.dumps({'commit':head,'files':len(items),'delivery_bytes':delivery.stat().st_size,'zip_integrity':True},ensure_ascii=False))
