"""Author the dated submission PDFs from verified implementation records."""
import json,subprocess
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,PageBreak,Spacer
from build_documents import p,table,screenshot,INK,TEAL,MUTED,LINE

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output/submission-2026-11-18';OUT.mkdir(parents=True,exist_ok=True)
profile=json.loads((ROOT/'docs/participant.json').read_text(encoding='utf8'))
def footer(c,doc):
    c.saveState();c.setFont('CN',8);c.setFillColor(MUTED);c.drawString(45,810,'知研 / SCHOLAR WORKBENCH / 2026.11.18')
    c.setStrokeColor(LINE);c.line(45,46,550,46);c.drawString(45,31,'曲珈莹 · 云南大学 · 人工智能 2025 级 · A 组');c.drawRightString(550,31,str(doc.page));c.restoreState()
for track in ['AI创新应用挑战赛','AI大模型创新应用挑战赛']:
    story=[]
    def page(title,*items):
        if story:story.append(PageBreak())
        story.extend([p(title,'H1CN'),*items])
    page('知研\n让每个洞察，都有出处。',p(track+' · 技术文档','H2CN'),p('参赛人：曲珈莹\n学校：云南大学\n专业 / 年级：人工智能 / 2025 级\n参赛组别：A 组\n指导教师：无'),screenshot('library.png',maxheight=280),p('本文件按真实实现与验收记录整理。生成内容仍应核对原文；材料准备不等于赛事已经提交。','SmallCN'))
    page('01 / 场景与产品价值',p('科研工作中，文献收集、原文阅读、知识问答、引用关系与写作往往分散。知研用统一的页码和内容块坐标连接这些环节，让生成结论能直接返回原始证据。'),table([['环节','具体行为','可检查产出'],['收集','批量导入、版本提示、论文检索','原始 PDF、解析状态、元数据'],['理解','双栏阅读、译文、问题检索','页码、原文坐标、译文缓存'],['研究','周期追踪、引用网络、方法比较','更新收件箱、真实图谱、来源'],['表达','结构图、草稿、CSV 图表','可编辑文字、SVG、LaTeX、Python / TikZ']],[65,190,250]),Spacer(1,20),p('选型约束','H2CN'),p('以个人电脑为主要运行环境，优先使用本地开源模型。公开评审通过隔离实例和临时 HTTPS 隧道接入，模型运算仍在本机进行。'))
    page('02 / 六类功能与边界',table([['模块','实现','需要核对的边界'],['文献解析','文本、扫描 OCR、长书、版本、结构与公式转写','复杂版式和公式不是零错误'],['知识问答','BM25 + BGE-M3、均衡多文证据、来源跳转','编号校验不是逻辑蕴含验证'],['阅读翻译','原始页、段落、引用跳转、缓存续传、Markdown','比例滚动不等于逐句精排'],['论文发现','检索入库、后台周期、去重、反馈与代码线索','代码线索不代表仓库复现已成功'],['引用图谱','真实本地匹配边、PageRank、领域综述与方向','局域指标；未建立全球引用库'],['写作绘图','草稿编辑、Mermaid、五类图、Python / TikZ','没有自动统计显著性结论']],[70,230,205]),Spacer(1,18),p('共同数据主线','H2CN'),p('文献 ID → 内容块 ID → 页码与 bbox → 检索证据 → 引用编号 → 原文核查。不同模块使用同一来源，而非各自产生互不对应的文本。'))
    page('03 / 架构与工程',table([['层次','技术与职责'],['界面','React / Vite、KaTeX、Mermaid、Plotly；大型绘图库按需加载'],['服务','FastAPI；文件、检索、生成、追踪、译文、草稿与导出'],['文档','PyMuPDF + RapidOCR；按页解析与渲染，坐标始终保留'],['数据库','SQLite WAL；文献、文本、向量、引用、公式、译文、追踪状态'],['模型','Ollama 本地模型；BGE-M3 语义向量；Qwen 视觉指令模型用于公式和补充问答'],['外部','arXiv 公共接口；GitHub 仓库；带口令的 HTTPS 临时评审入口']],[90,415]),p('请求边界','H2CN'),p('模型提出的工具调用只在白名单中执行，最多处理三条建议。论文内容作为数据，不执行其中的命令。拒绝任意远程 PDF URL，仅接纳合法 arXiv 编号。评审实例使用独立公开样例库，口令不进入公开仓库。'))
    page('04 / 文档与公式',p('真实长书 Understanding Deep Learning 共 541 页，解析出 11,272 个块，并成功读取末页。Attention v1/v7 版本完成正文与版本提示；已有语义索引时还计算向量相似度。'),screenshot('formula-final.png',maxheight=300),p('公式转写的真实修复','H2CN'),p('第一次只裁剪公式主块，遗漏了单独文字块中的末尾 V。修复为合并同一公式带相邻短块后，视觉模型识别出完整的 softmax(QK^T / sqrt(d_k))V。用户可查看原图、修改 LaTeX、渲染并保存校对。'),p('证据：formula-first-crop-failure.json 与 formula-live-validation.json。保留失败结果，不能将“能渲染”直接解释为转写正确。','SmallCN'))
    page('05 / 检索与多文推理',p('检索融合精确词项与语义向量。多文问题以文献分组轮转候选，优先正文段落，避免一篇文献只入选图题而另一篇占据几乎全部上下文。'),table([['问题','控制措施'],['原论文编号与证据编号混用','送入模型前明确区分两种编号'],['证据不足','不强行生成；返回原文并解释不足'],['生成越界引用','拒绝作为有效回答，写作可重试一次'],['比较对象漂移','要求围绕用户指定对象；均衡多篇正文证据'],['模型输出被截断','不把不完整推理或正文当作最终结果']],[160,345]),p('已完成实测','H2CN'),p('单篇问答区分 Transformer base / big 的 8 块 P100、12 小时 / 3.5 天，引用定位到第 7 页。跨篇实验保留了推理截断、对象漂移与证据均衡修复记录，最终结果以 artifacts/multi-paper-balanced-validation.json 为准。'))
    page('06 / 周期追踪与图谱',p('服务启动后每 30 秒检查到期主题。数据库保存 next_run，关闭浏览器不影响执行；进程停止时任务暂停，重启后补查。查询失败后退避 15 分钟，topic + arXiv ID 唯一键避免重复入箱。真实运行已取回 12 条追踪结果。'),p('推荐可解释','H2CN'),p('结合本地关键词关联度、摘要中的代码线索与用户喜欢 / 不喜欢反馈排序。明确区别“摘要提及代码”与“代码仓库已实际复现”。'),screenshot('引用图谱.png',maxheight=260),p('Future Work 按时间与证据判断：只有后续全文证据明确支持已经解决，才可排除旧方向；否则标为待查证，不能声称已自动证明某问题仍未解决。','SmallCN'))
    page('07 / 写作与科研图表',p('草稿可编辑并保存，保留引用；Mermaid 方法图在受限模式渲染并可导出 SVG。CSV 支持柱状、折线、散点、雷达和三维散点图，使用全部有效行，提供图像与 Python / 适用 TikZ 代码。'),screenshot('chart-scatter3d.png',maxheight=280),screenshot('chart-radar.png',maxheight=230),p('示例数值仅验证产品功能。雷达图不自动归一化；不同量纲必须先由研究者处理。三维 WebGL 图导出 PNG，二维图可导出 SVG。','SmallCN'))
    if track=='AI创新应用挑战赛':
        page('08 / AI 协同与三条迭代链',p('真实用户先提出从零开发、双赛共用，随后指定本地运行，并在 11 月 18 日要求补齐所有内容。助手根据约束自主拆分工作、生成代码和修复。'),table([['功能链','真实失败与修复','证据'],['来源与模型校验','混用参考编号、推理截断 → 编号分离与最终正文处理','调用原文、失败 JSON、Git'],['公式转写','漏掉独立文字块 V → 同带相邻块合并','首轮与修复后转写 JSON'],['追踪与绘图','持久化周期、去重与恢复 → 五类真实浏览器检查','追踪结果、测试和截图']],[120,245,140]),p('真实性说明','H2CN'),p('三条链是同一会话按功能索引的真实实施链，共享用户总指令，不能伪称三次独立用户逐轮提问。完整公开用户/助手文本与实施调用已导出，系统指令和内部推理不包含在内。视频展示真实记录复盘，清楚标注合成配音。'))
    else:
        page('08 / 技术贡献与取舍',p('统一的来源位置模型','H2CN'),p('将解析、阅读、问答、翻译、图谱和写作连接到可追溯内容块，减少跨模块证据不一致。'),p('可审查的模型工程','H2CN'),p('将推理正文分离、编号校验、工具白名单、公式原图校对和跨文均衡候选作为独立控制环节，保留失败而非只展示成功样例。'),p('个人电脑上的多模态科研流程','H2CN'),p('采用现有本地模型完成文本与视觉任务，串行锁限制单进程模型并发；没有主张训练新基础模型、LoRA 增益或大规模评测领先性。'),p('可解释的自动化','H2CN'),p('追踪状态、失败退避、未读结果和推荐理由对用户可见。Future Work 的“已解决”必须有后续证据，不把未知状态包装为确定结论。'))
    page('09 / 验收与复现证据',table([['验证','结果与范围'],['后端','23 项通过，覆盖取消、续传、去重、来源、访问控制与草稿'],['浏览器','七页无运行错误；手机宽度无溢出；五类图表逐一渲染'],['真实 PDF','5 篇/版本，共 606 页；其中长书 541 页'],['公式','首轮裁剪缺因子；修复后完整公式，前端 KaTeX 可渲染'],['追踪','真实 arXiv 返回 12 条，保存到本地未读收件箱'],['公网','外部 HTTPS 登录成功，认证后读到独立样例库 5 篇'],['代码','公开仓库保留历史，合并远程初始化提交，没有强推覆盖']],[95,410]),p('检查位置','H2CN'),p('tests/test_workbench.py；artifacts/advanced-browser-validation.json；tracking-live-validation.json；formula-live-validation.json；public-access-validation.json；多文问答修复记录。测试替身只验证控制流，真实模型记录另存。','SmallCN'))
    page('10 / 部署与运行',p('公开源码','H2CN'),p(profile['repository']),p('在线评审入口','H2CN'),p(profile['demo']),p('口令通过单独的“评审访问信息”文件交付，不发布到源码仓库。此地址是临时隧道，依赖电脑、Ollama、评审服务和隧道持续运行；没有持久在线 SLA，重启隧道可能改变域名。'),p('本地复现','H2CN'),p('Windows：运行 setup.ps1；准备 qwen3:4b、bge-m3 和 qwen3-vl:4b-instruct；双击 start.cmd。依赖与模型已准备后可快速复现，首次下载耗时取决于网络，不能保证十分钟。'),p('Dockerfile 与 compose.yaml 已提供。当前宿主 Docker 引擎未启动，未把它们记为已完成 Docker 运行验证。','SmallCN'))
    page('11 / 过程、提交与责任边界',p('参赛者与 AI 贡献','H2CN'),p('参赛者提出需求与约束、提供身份与仓库；AI 生成实现、执行测试、诊断修复和制作材料。参赛者应在答辩前理解核心源码及设计，不能将助手自主决策伪称本人逐轮 Prompt。'),p('交付清单','H2CN'),p('完整代码与 Git 历史、环境模板与锁文件、两份技术 PDF、两段 1080p MP4、真实对话与三条功能链、验收记录、答辩准备、评审访问说明。'),p('正式提交状态','H2CN'),p('已准备材料，未登录赛事个人中心上传。官网说明省赛提交入口在缴费后个人中心显示。同源作品双赛参评未取得组委会明确确认，不能推定获准。'),p('规则核验：2026-11-18，官方赛道 10039 / 10040。页面仍显示省赛提交截止为 2026-11-18，同时存在后续阶段日期表述冲突，应以个人中心和组委会通知为准。','SmallCN'))
    target=OUT/f'曲珈莹-{track}-技术文档.pdf'
    SimpleDocTemplate(str(target),pagesize=(595.28,841.89),leftMargin=45,rightMargin=45,topMargin=63,bottomMargin=63,title=track+' 知研技术文档',author='曲珈莹').build(story,onFirstPage=footer,onLaterPages=footer)
    print(target)
