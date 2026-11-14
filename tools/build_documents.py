"""Build two reviewable competition documents from actual implementation evidence."""
import json
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.enums import TA_LEFT

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output'/'pdf'
OUT.mkdir(parents=True,exist_ok=True)
try:
    pdfmetrics.registerFont(TTFont('CN','C:/Windows/Fonts/msyh.ttc',subfontIndex=0))
except Exception:
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    registerFontFamily('CN',normal='STSong-Light')
    raise
INK=colors.HexColor('#183947');TEAL=colors.HexColor('#247b6b');MUTED=colors.HexColor('#78908f');LINE=colors.HexColor('#dae5e1')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyCN',fontName='CN',fontSize=10,leading=18,textColor=INK,spaceAfter=11))
styles.add(ParagraphStyle(name='H1CN',fontName='CN',fontSize=23,leading=34,textColor=INK,spaceAfter=18))
styles.add(ParagraphStyle(name='H2CN',fontName='CN',fontSize=14,leading=22,textColor=TEAL,spaceBefore=12,spaceAfter=10))
styles.add(ParagraphStyle(name='SmallCN',fontName='CN',fontSize=8,leading=13,textColor=MUTED,spaceAfter=8))
styles.add(ParagraphStyle(name='TableCN',fontName='CN',fontSize=8.4,leading=14,textColor=INK))


def p(text,style='BodyCN'):
    return Paragraph(escape(text).replace('\n','<br/>'),styles[style])


def table(rows,widths):
    data=[[p(str(cell),'TableCN') for cell in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9f2ec')),
                          ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),10),
                          ('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),9),
                          ('BOTTOMPADDING',(0,0),(-1,-1),9),('LINEBELOW',(0,0),(-1,-1),.4,LINE)]))
    return t


def screenshot(name,width=490,maxheight=325):
    path=ROOT/'artifacts'/'screenshots'/name
    if not path.exists():
        return Spacer(1,1)
    from PIL import Image as PILImage
    with PILImage.open(path) as im:
        w,h=im.size
    scale=min(width/w,maxheight/h)
    return Image(str(path),width=w*scale,height=h*scale,hAlign='CENTER')


def footer(canvas,doc):
    canvas.saveState()
    canvas.setFillColor(TEAL);canvas.rect(45,797,30,3,fill=1,stroke=0)
    canvas.setFont('CN',8);canvas.setFillColor(MUTED)
    canvas.drawString(45,810,'知研 / SCHOLAR WORKBENCH')
    canvas.setStrokeColor(LINE);canvas.line(45,46,550,46)
    canvas.drawString(45,31,'本地验收稿 · 2026.11.14 · 参赛身份与最终提交由本人确认')
    canvas.drawRightString(550,31,f'{doc.page:02d}')
    canvas.restoreState()


def build(track):
    name='AI创新应用挑战赛' if track=='innovation' else 'AI大模型创新应用挑战赛'
    story=[]
    def page(title,*items):
        if story:story.append(PageBreak())
        story.extend([p(title,'H1CN'),*items])
    page('知研\n让每个洞察，都有出处。',Spacer(1,15),p(name+' · 技术说明与验证记录','H2CN'),
         p('本地优先科研文献工作台。把 PDF 导入、原文阅读、证据问答、论文发现、引用图谱和写作辅助放在同一工作流中。'),
         screenshot('library.png',maxheight=340),Spacer(1,15),
         p('交付性质：本地可运行版本 / 未提交赛事\n参赛人、学校、组别及指导教师：待本人填写\n使用说明：本材料仅陈述已实现或明确标注的能力，不构成官方评测通过证明。','SmallCN'))
    page('01 / 问题与产品路径',p('科研阅读中常见的摩擦，是文献散落、问题与证据脱节、检索结果难以接入阅读、图表和写作成果难复现。知研以“文献 -> 内容块 -> 原文位置 -> 引用证据”为统一数据主线。'),
         table([['使用阶段','用户操作','系统产出'],['收集','上传 PDF 或从 arXiv 导入','本地文件、结构化段落、元数据'],['阅读','浏览原文、选择段落、查看译文','页码与坐标定位、缓存译文'],['理解','提出问题、选定文献范围','检索证据、模型回答、引用校验'],['连接','查看引用关系和局域排序','真实库内引用图、PageRank'],['表达','生成草稿、上传 CSV','有来源草稿、SVG 图与 Python 脚本']],[66,154,285]),
         Spacer(1,18),p('产品约束','H2CN'),p('用户本次选择先做本地版，没有云模型 API 或部署服务器。应用默认监听 127.0.0.1；论文文件与 SQLite 数据保存在项目 data 目录。arXiv 检索、首次依赖安装和模型下载需要网络。'))
    page('02 / 六个模块与完成范围',table([
         ['模块','当前实现','边界'],['文献管理','批量 PDF、OCR、分块、标题/作者/版本识别、重复提示','复杂版式与作者元数据需核对'],
         ['知识问答','BM25 + BGE-M3 向量检索、原文坐标、引用编号校验','编号有效不等于论断必然正确'],
         ['阅读翻译','原始页面、段落定位、划选翻译、双向比例滚动、全文任务与缓存','比例滚动不是严格逐句排版对齐'],
         ['发现推荐','arXiv 搜索、下载入库、兴趣保存、关键词关联度','当前按用户操作刷新，未实现无人值守周期追踪'],
         ['引用图谱','库内引用匹配、有向图、局域 PageRank','作者年制与跨页引用仍可能漏匹配'],
         ['写作绘图','综述、框架、方向、翻译、结构图代码；CSV 柱/折线图','LaTeX 公式可靠转写、复杂三维图仍待完善']],[72,225,208]),
         Spacer(1,18),p('这六个模块已经有真实服务与界面，但当前版本不应被描述为完整通过全部官方功能项。图表、公式、引用与生成内容都保留核对入口。','SmallCN'))
    page('03 / 系统架构与数据契约',table([
         ['层次','技术与职责'],['Web 界面','React + Vite；文献库、阅读器、问答、发现、图谱、写作；桌面与移动端布局'],
         ['应用服务','FastAPI；上传、分页读取、检索、生成、图谱、CSV、后台翻译任务'],
         ['文档处理','PyMuPDF 逐页解析与渲染；RapidOCR 处理扫描页；结构化表格按页识别'],
         ['本地存储','SQLite WAL；文献、内容块、向量、参考文献、译文、写作草稿、任务状态'],
         ['模型服务','Ollama；本地生成模型与 BGE-M3；模型请求串行锁避免同一进程争抢 GPU'],
         ['外部资源','仅通过受限 arXiv 检索与下载接口访问公开论文']],[95,410]),
         Spacer(1,18),p('关键数据契约','H2CN'),p('每个内容块包含稳定数据库 ID、文献 ID、页码、阅读顺序、文本、矩形坐标、类型和章节。问答结果引用这些内容块，而不是让模型自行编造页码。向量保存对应模型名，只有模型和维度匹配的向量参与检索。'),
         p('上传使用 SHA-256 检查完全重复文件；同一 arXiv 编号、正文重合度和已建索引时的语义相似度提供版本提示。用户决定保留两个版本或移除另一个版本。'))
    page('04 / 文档解析与阅读',p('解析采用逐页读取，页面图像也按需生成，不一次性把整本书渲染到浏览器。标准 PDF 保留字符文本与块坐标；文字不足的页面进入 OCR。双栏采用启发式阅读顺序，标题树和参考文献也由可审查规则提取。'),
         screenshot('沉浸阅读.png',maxheight=340),
         p('真实测试','H2CN'),p('作者官网公开版本《Understanding Deep Learning》：541 页，解析完成后形成 11,272 个内容块，并成功读取末页 11 个内容块。另使用 Attention Is All You Need 的 v1/v7 版本完成重复识别，正文词项重合度约 0.812。'),
         p('OCR 自动化测试使用由文本页生成的扫描样例，证明图像页处理链路可运行。它不代表所有扫描质量、数学公式和复杂表格均已达到官方标准。','SmallCN'))
    page('05 / 有来源的问答与智能体',p('检索先计算关键词相关度，再对已建立索引的内容块使用 BGE-M3 语义相似度，采用倒数排名融合组织候选证据。指定多篇文献时优先保证候选覆盖各篇文献。'),
         table([['步骤','控制措施'],['检索','返回原文段落及页码坐标；无证据时不强行生成结论'],['生成','系统规则把论文内容视为不可信数据，限制依据与输出引用'],['引用编号','外层证据编号与论文原有参考编号分开，避免错用原文编号'],['校验','越界或缺失引用的草稿不作为可信回答；写作可重试一次'],['工具调用','模型提出受限工具调用；仅允许本地检索、图谱与条件开放的 arXiv 搜索'],['边界','不执行模型生成代码；工具参数重新检查；规划失败回退固定检索流程']],[78,427]),
         Spacer(1,16),p('实测案例','H2CN'),p('对英文 Transformer 论文用中文询问 GPU 和训练时长，检索定位到具体原文。已验证的一次 DeepSeek-R1 8B 回答区分了 base 模型 12 小时、big 模型 3.5 天，均为 8 块 P100，并附原文来源。端到端约 52 秒；这是本机单次实测，不是性能基准。'))
    page('06 / 连接与表达',screenshot('引用图谱.png',maxheight=255),p('图谱只展示本地库中已解析和匹配的真实引用边。孤立节点仍可见，页面明确说明未连线不等于没有学术关系；PageRank 仅描述当前局域库。'),
         screenshot('chart.png',maxheight=245),p('CSV 绘图验证了数值列、缺失和非有限数值处理。支持柱状图与折线图，可导出 SVG 和 Python 复现脚本；预览最多 50 行，脚本读取原 CSV。图注描述数据来源，不编造统计显著性。','SmallCN'))
    if track=='innovation':
        page('07 / AI 协同与意图控制',p('真实起点','H2CN'),p('用户提出从零开发、双赛共用一套系统，并明确选择本地可运行版本。助手据此建立独立项目、保存阶段性 Git 提交，并以真实论文测试推进修复。'),
             table([['迭代','观察到的问题','实际处理'],['文献解析','arXiv 竖排边栏字号大，被误判为标题','排除窄竖排与 arXiv 标签，合并同字号标题行'],['证据生成','模型误用原论文参考文献编号','区分外层证据编号与原文参考编号，保留校验失败记录'],['交互','异步翻译和翻页可能出现陈旧结果','请求有效性保护、内容块 ID 对齐、问答会话保留'],['模型接入','短 token 上限可能只产生推理而无正文','对真实输出实测，按模型服务响应处理最终正文与工具规划']],[65,204,236]),
             Spacer(1,16),p('过程证据','H2CN'),p('artifacts/process-evidence 保存当前会话公开消息节选及实施工具调用。它不包含系统指令和内部推理，也不伪造三次独立用户 Prompt。是否满足组委会要求的至少三个完整核心 Prompt 链，仍需参赛人结合完整会话导出核对。'))
    else:
        page('07 / 技术深度与创新取舍',p('本地科研工作流','H2CN'),p('选择统一的文献证据数据模型，使问答、阅读、图谱和写作共享来源。对有限显存的个人电脑，优先使用现有本地模型与串行请求；界面把等待、失败和依据核查显式化。'),
             p('可审查的创新点','H2CN'),table([['设计','可观察的价值'],['位置级证据闭环','从生成引用直接进入原始页与对应内容块，降低核对成本'],['模型与原文编号分离','解决科研文献自带编号与 RAG 引用编号混淆的实际问题'],['本地多模块共享','同一份文献解析结果复用于问答、译文缓存、引用网络与写作'],['低门槛复现','无需付费 API 即可运行已配置模型；源码、环境模板与测试齐备']],[125,380]),
             Spacer(1,16),p('未主张的成果','H2CN'),p('未训练新基础模型、未实现 LoRA 优化、未报告大规模评测领先性。当前实现不应宣称彻底消除幻觉，亦不把局域 PageRank 解释为全学术领域影响力。'))
    page('08 / 验证证据与已知缺口',table([
         ['检查','结果 / 范围'],['后端自动化','18 项通过：解析坐标、重复与版本、检索与引用、OCR、120 页样例、CSV、URL 与来源限制、非法 PDF、删除、翻译取消续传、结构与 BibTeX、模型最终正文与截断'],
         ['真实文献','3 篇论文 + v7 版本 + 541 页书籍；末页读取、版本提示均完成'],['浏览器','7 个页面无运行错误，390px 手机宽度无横向溢出；CSV 上传及绘图通过'],
         ['模型实测','默认 Qwen3 4B 的跨语言问答、翻译、写作均已通过；另有真实原生 search_library 工具调用记录。单次延迟不是性能基准'],
         ['外部检索','arXiv 在线检索已返回真实结果；网络不可用时显示错误而非模拟结果'],
         ['仍待完善','严格公式 LaTeX 转写、复杂版式精度、作者年制引用全覆盖、自动周期追踪、复杂三维图及更大测试集'],
         ['外部交付','当前没有公网评审地址；未上传 GitHub/Gitee；未填写个人身份或提交比赛']],[93,412]),
         Spacer(1,16),p('测试文件位置','H2CN'),p('tests/test_workbench.py；artifacts/browser-qa.json；artifacts/live-model-validation.json；artifacts/writing-validation.json；artifacts/real-document-validation.json。记录中保留历史失败及修复后结果，不能将 HTTP 成功等同于内容正确。','SmallCN'))
    commits=subprocess.check_output(['git','log','--oneline','-6'],cwd=ROOT,text=True,encoding='utf-8')
    page('09 / 复现、运行与提交',p('本机运行','H2CN'),p('已安装依赖与模型的本机：双击 start.cmd，浏览器访问 http://127.0.0.1:8765。程序仅监听回环地址。首次在新电脑配置时，运行 setup.ps1，并在 Ollama 中准备生成模型及 bge-m3；下载时间取决于网络，不能保证首次下载在十分钟内结束。'),
         p('复现检查','H2CN'),p('运行 .venv\\Scripts\\python.exe -m pytest tests -q；运行 npm run build。Dockerfile 与 compose.yaml 是部署准备文件，本次 Windows 本机验收不等于 Docker 镜像或公网环境已经验证。'),
         p('阶段提交摘录','H2CN'),p(commits,'SmallCN'),
         p('赛道材料核对','H2CN'),p('两项均需可审查代码仓库、5-8 分钟 1080p MP4 与不超过 30 页技术 PDF。创新应用赛还要求开发 Prompt 链与至少两分钟 AI 协同过程展示；大模型赛要求评审可公网访问的在线地址。当前两套材料按不同侧重点组织，不能据此推定同源作品双赛参评已获组委会许可。'),
         p('规则来源：boxuegu.com/matchTrack/detail/?id=10039 与 ?id=10040。核验日期：2026-11-14。官网时间表存在冲突，应以个人中心与组委会最新通知确认最终截止时间。','SmallCN'))
    path=OUT/(name+'-知研技术说明-本地验收稿.pdf')
    doc=SimpleDocTemplate(str(path),pagesize=(595.28,841.89),rightMargin=45,leftMargin=45,topMargin=63,bottomMargin=63,title=name+' 知研技术说明',author='Scholar Workbench project')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(path)

if __name__=='__main__':
    build('innovation');build('llm')
