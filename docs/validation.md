# 本地验收记录

日期：2026-11-14。Windows、Python 3.13.5、Node 24.11、32GB 内存、RTX 5060 Laptop 8GB。以下是实际开发验收，不是官方评测。

| 检查 | 结果 | 证据与限制 |
|---|---|---|
| 后端自动化 | 18 passed，15.61s | tests/test_workbench.py；一条测试客户端弃用提示，不影响结果 |
| 前端构建 | 通过 | npm run build |
| 浏览器 | 7 个页面 errors=[] | artifacts/browser-qa.json；真实 Edge 无头浏览器 |
| 手机布局 | 390 × 844 无横向溢出 | mobileOverflow=false，不代表全部设备 |
| CSV | 3 行、2 列，柱/折线图 | 示例数据仅验证功能，不是性能实验 |
| 论文索引 | 3 篇、1,397 个向量 | Attention v1、BERT、RAG；BGE-M3 |
| 版本识别 | Attention v1/v7 提示重复 | real-document-validation.json；词项重合约 0.812 |
| 真实长书 | 541 页、11,272 块，末页 11 块 | 作者公开 UDL；未建整本书语义索引 |
| OCR | 扫描样例成功识别 | 合成扫描页验证，不代表全部扫描质量 |
| PDF 表格 | Attention 第 6 页识别 4 列 | 原表多行被合并为 2 行，仍需校正 |
| 引用图 | 5 节点、5 条匹配边 | 真实库内引用，可能漏匹配 |
| arXiv | 实际在线检索成功 | 网络不可用时显示错误，不返回模拟结果 |
| DeepSeek 8B | 问答正确区分训练设置 | live-model-validation.json 也保留首次写作 HTTP 400 |
| 默认 Qwen3 4B | 问答、翻译、三点草稿均 200 | qwen-e2e-validation.json：57.27s、21.73s、48.49s，单次观察 |
| 原生工具规划 | search_library 调用 | native-plan-final.json；22.38s；失败回退固定检索 |
| 全文翻译续传 | 自动化通过 | 模型替身验证状态与缓存；没有整书真实翻译实验 |
| 两套视频 | 353.16s / 410.20s，1920×1080 | H.264/AAC；完整解码无错误，浏览器可加载；合成普通话配音 |
| 两套 PDF | 各 10 页 | 已渲染与抽查版面，无页数超限 |
| 正式地址 | 7 页检查通过 | http://127.0.0.1:8765；修复 Windows JavaScript MIME 后再次检查 |

## 自动化覆盖

解析坐标页码、完全重复文件、版本提示、原文检索、无证据不调用模型、错误引用拒绝、正确引用保留、扫描 OCR、120 页合成文档、CSV 非有限数值、只接受 arXiv 编号的远程导入、跨站来源限制、非法 PDF、删除级联、翻译取消、缓存续传、结构与 BibTeX、最终正文与截断处理。

模型替身验证确定性的控制流，不构成真实模型准确率。真实输出另外保存。写作即使引用有效也可能概括不够精确，例如多头注意力的三点总结仍需润色。

## 未完成的赛道项

- 可靠公式 LaTeX 转写、复杂版式全覆盖、作者年制引用完整关联。
- 无人值守周期追踪、复杂三维图和更丰富科研绘图。
- 公网评审地址、远程公开仓库、Docker 环境验证。
- 更大规模评测和对照实验；没有消融结论、准确率领先性或 LoRA 成果。
- 个人信息、原始 Prompt 链合规核对、同源双赛确认与最终提交。

`live-model-validation.json` 与早期 `qwen-agent-validation.json` 保留历史失败。默认生成模型以 `qwen-e2e-validation.json` 为准，最终规划以 `native-plan-final.json` 为准。本机录屏实际 API 回答及时间记录位于 `artifacts/video-raw`。
