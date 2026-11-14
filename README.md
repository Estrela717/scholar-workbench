# 知研 · Scholar Workbench

本地优先的科研文献工作台，将 PDF 管理、原文阅读、证据问答、论文发现、引用图谱和写作放在同一流程中。当前为 **2026-11-14 本地验收版本**，不是已完成报名或通过官方评测的声明。

本项目从零独立开发，为传智杯 AI 创新应用挑战赛和 AI 大模型创新应用挑战赛共用。两个赛道共用代码，分别准备过程与技术说明；同源作品能否双赛参评仍需依据组委会确认。

## 在这台电脑上启动

1. 保持已安装的 Ollama 运行。
2. 双击项目目录中的 `start.cmd`。
3. 浏览器打开 **http://127.0.0.1:8765**。如果已经能打开，无需重复启动。

本机依赖、模型和示例文献已准备好，无需 API 密钥。保持启动窗口运行，按 Ctrl+C 停止。默认生成模型 `qwen3:4b`，语义向量模型 `bge-m3:latest`；模型权重由 Ollama 管理，不在源码包内。

## 十分钟体验

1. **文献库**：查看 Attention、BERT、RAG 与长篇教材，或批量上传 PDF。
2. **沉浸阅读**：选择 Attention，浏览原始页、段落、目录和参考文献；图表面板支持表格数据导出。
3. **文献问答**：选中 Attention，询问“Transformer 的 base 和 big 模型分别使用多少块 GPU，训练了多久？”。打开检索记录，点击引用核对原文。
4. **发现论文**：用英文主题检索 arXiv，查看摘要或导入 PDF，此步骤需要网络。
5. **引用图谱**：查看真实库内引用及局域排序。
6. **写作工坊**：选择论文生成草稿，或上传 CSV 导出 SVG 与 Python 绘图代码。

十分钟指依赖与模型已就绪后的体验。首次下载和文献索引可能更久；未建语义索引时仍可使用关键词检索。

## 新 Windows 电脑配置

需要 Python 3.13、Node.js 22+、uv、Ollama。建议至少 16GB 内存。本机实际验证为 Windows、32GB、RTX 5060 Laptop 8GB、Python 3.13.5、Node 24.11；其他硬件未计时验证。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
ollama pull qwen3:4b
ollama pull bge-m3
.\start.cmd
```

可选配置见 `.env.example`，不用修改即可连接本机 Ollama。兼容 API 为预留接入，本次没有付费接口可供验证。密钥不要提交 Git。

## 实现范围

| 模块 | 实现 | 边界 |
|---|---|---|
| 文献管理 | 批量 PDF、扫描 OCR、元数据、精确重复与版本提示 | 复杂版式、元数据与 OCR 需要校对 |
| 检索问答 | BM25 + BGE-M3、排名融合、文献范围、位置级证据与编号校验 | 引用有效不代表论断必然正确 |
| 智能体 | 原生工具规划、白名单与参数复核、最多 3 次工具建议、失败回退 | 有界的一轮规划执行 |
| 阅读翻译 | 原文与段落、定位、参考跳转、比例滚动、划选翻译、缓存与全文暂停续传 | 非严格逐句排版对齐；长文翻译耗时较久 |
| 发现推荐 | arXiv 检索入库、研究兴趣、关键词关联度 | 需要网络；当前手动刷新 |
| 图谱 | 库内引用匹配、关系箭头、PageRank | 可能漏匹配；排序只对局域库有效 |
| 写作绘图 | 草稿与导出、结构图代码、PDF 表格、CSV 柱/折线图、SVG 和 Python | Mermaid 当前输出代码；公式不是可靠 LaTeX；未做复杂三维图 |

## 数据与运行

- `data/library.sqlite3` 保存文献、文本块、向量、引用、译文、草稿与任务状态。
- `data/files/` 保存原始 PDF，数据不提交 Git；样例来源见 `docs/sample-sources.md`。
- `GET /api/export/bibtex` 导出已识别元数据，正式引用前核对作者、年份与版本。
- 本地解析和推理无需联网；arXiv 搜索和下载访问公开网络。服务只监听 `127.0.0.1`。
- 全文翻译可停止与继续，重启后未完成任务标为可继续。模型工作在同一服务进程中串行执行。

备份时先停止服务，再复制整个 `data` 目录。源码包不包含个人数据、依赖环境和模型权重。

## 开发与验证

```powershell
# 后端
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8765
# 另一终端启动开发界面
npm run dev
# 自动化检查
.\.venv\Scripts\python.exe -m pytest tests -q
npm run build
# 需要 Edge 与运行中的开发服务
node tools/browser_qa.mjs
```

最新验收为 **18 项后端测试通过**，7 个界面无浏览器运行错误，390px 手机宽度无横向溢出。真实测试涵盖 541 页教材、Attention v1/v7、默认 Qwen3 4B 问答、翻译与写作。详见 `docs/validation.md`。

测试中的模型替身只验证确定性控制流；真实模型输出另外记录。`artifacts/` 保留历史失败，不能将其混称为最终成功结果。

## 目录与参赛材料

`app/` 后端；`src/` 界面；`tests/` 行为测试；`docs/` 开发与验收；`artifacts/` 真实记录；`tools/` 检查和制作脚本；`output/pdf/` 两套技术说明；`output/videos/` 两套演示与复盘。

Dockerfile 和 compose.yaml 是部署准备文件，尚未在 Docker / 公网验收。用户明确先做本地版，当前没有公网评审地址、远程仓库、个人参赛信息或赛事提交。

PDF 与视频是可审阅的本地材料。创新赛原始 Prompt 链与两分钟协同过程要求需结合完整真实对话核对，开发片段明确为真实记录复盘，不冒充当时实时录屏。大模型赛公网地址尚未提供，详见 `docs/submission-checklist.md`。
