"""Package source, Git history and a readable local delivery index."""
import hashlib,json,subprocess,zipfile
from pathlib import Path
from html import escape

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output';OUT.mkdir(exist_ok=True)
source=OUT/'知研-源码与构建.zip'
subprocess.run(['git','archive','--format=zip','--prefix=scholar-workbench/','--output='+str(source),'HEAD'],cwd=ROOT,check=True)
with zipfile.ZipFile(source,'a',compression=zipfile.ZIP_DEFLATED) as archive:
    for p in (ROOT/'dist').rglob('*'):
        if p.is_file():archive.write(p,'scholar-workbench/'+p.relative_to(ROOT).as_posix())
bundle=OUT/'知研-完整Git历史.bundle'
subprocess.run(['git','bundle','create',str(bundle),'--all'],cwd=ROOT,check=True)
files=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file() and (p.suffix in ('.pdf','.mp4','.zip','.bundle')):
        files.append({'path':p.relative_to(OUT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()})
(OUT/'交付文件校验.json').write_text(json.dumps({'date':'2026-11-14','git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':files},ensure_ascii=False,indent=2),encoding='utf8')
cards=[]
for title in ('AI创新应用挑战赛','AI大模型创新应用挑战赛'):
    pdf=f'pdf/{title}-知研技术说明-本地验收稿.pdf'
    video=f'videos/{title}-知研本地演示与复盘.mp4'
    cards.append(f'<section><span class="tag">{title}</span><h2>{"开发过程与产品创新" if "大模型" not in title else "科研工作流与模型工程"}</h2><p>10 页技术说明 · 1920 × 1080 实操演示 · 合成普通话配音</p><a href="{pdf}">打开技术 PDF ↗</a><a href="{video}">打开演示 MP4 ↗</a><video controls preload="metadata" src="{video}"></video></section>')
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>知研 · 本地交付导航</title><style>*{box-sizing:border-box}body{margin:0;background:#f1f5f1;color:#173b44;font:16px/1.75 system-ui,'Microsoft YaHei'}main{max-width:1180px;margin:60px auto;padding:0 28px}.eyebrow{letter-spacing:3px;color:#2b7d6b;font-size:12px}h1{font-size:44px;margin:12px 0}h2{font-size:24px;line-height:1.4}p{color:#55706c}a{color:#267a67;text-decoration:none;display:inline-block;margin:8px 20px 8px 0}a:hover{text-decoration:underline}.hero{padding:36px 42px;border-radius:24px;background:#163b47;color:white}.hero p{color:#c8dbd5}.hero a{background:#eff7ef;color:#245d4e;padding:12px 22px;border-radius:9px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin:28px 0}section{background:white;padding:30px;border:1px solid #dfe8e0;border-radius:20px}.tag{font-size:13px;color:#6b8d80}video{width:100%;margin-top:20px;border-radius:10px;background:#183b47}.limits{border-left:4px solid #c29c59;padding:10px 24px;background:#fffaf0;border-radius:8px}code{background:#e5ece6;padding:3px 6px;border-radius:5px;font-size:13px}footer{margin:30px 0;color:#79918a;font-size:13px}@media(max-width:800px){.grid{grid-template-columns:1fr}h1{font-size:32px}.hero{padding:25px}}</style><main><div class="eyebrow">SCHOLAR WORKBENCH / LOCAL DELIVERY / 2026.11.14</div><h1>知研，让每个洞察都有出处。</h1><p>这是一套本地科研助手，以及面向两个赛道分别整理的可审阅材料。没有代填个人信息，也没有提交比赛。</p><div class="hero"><h2>先打开应用，体验真实工作流</h2><p>模型与依赖已在这台电脑准备好。如果服务未启动，请双击上一级项目目录中的 start.cmd。</p><a href="http://127.0.0.1:8765" target="_blank">打开知研工作台 ↗</a><a href="../README.md">阅读启动说明 ↗</a></div><div class="grid">'''+''.join(cards)+'''</div><section><h2>代码、历史与验证</h2><p>源码包包含构建后的界面，未捆绑依赖环境、模型权重或论文 PDF。完整历史可通过 Git bundle 还原；运行与安装说明在 README。</p><a href="知研-源码与构建.zip">源码与构建 ZIP ↗</a><a href="知研-完整Git历史.bundle">完整 Git 历史 ↗</a><a href="../docs/validation.md">查看真实验收记录 ↗</a><a href="交付文件校验.json">SHA-256 文件校验 ↗</a><p>18 项后端测试通过；7 个界面无浏览器错误；390px 手机宽度无溢出；真实 541 页教材、版本检测与默认模型问答已有记录。</p></section><div class="limits"><h2>正式提交前仍有事项</h2><p>当前版本没有公网评审地址和远程代码仓库。可靠公式转写、无人值守周期追踪、复杂三维图与更广泛评测仍待完善。创新赛的完整 Prompt 链与协同展示形式、同源作品双赛参评规则需要核对。视频中的开发部分明确为真实记录复盘，不是当时的实时录屏。</p><a href="../docs/submission-checklist.md">查看双赛提交核对表 ↗</a></div><footer>所有结果按实际验证范围陈述。演示数值不是模型性能实验。生成回答和写作草稿应回到原文核对。</footer></main></html>'''
(OUT/'交付导航.html').write_text(html,encoding='utf8')
delivery=OUT/'知研-双赛道本地交付包.zip'
with zipfile.ZipFile(delivery,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    with zipfile.ZipFile(source) as original:
        for name in original.namelist():archive.writestr(name,original.read(name))
    for p in OUT.rglob('*'):
        if p.is_file() and p!=delivery and p!=source and 'qa' not in p.relative_to(OUT).parts:
            if p.suffix in ('.pdf','.mp4','.bundle','.html','.json'):
                archive.write(p,'scholar-workbench/output/'+p.relative_to(OUT).as_posix())
print(json.dumps({'source_zip':source.stat().st_size,'git_bundle':bundle.stat().st_size,'delivery_zip':delivery.stat().st_size,'files':len(files)},ensure_ascii=False))
