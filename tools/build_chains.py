"""Index three real feature histories without inventing participant prompts."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'artifacts/process-evidence'
events=[json.loads(x) for x in (OUT/'implementation-calls.jsonl').read_text(encoding='utf8').splitlines()]
chains=[('01-来源与模型校验',['app/research.py','引用编号','qwen-final-validation','recorded-agent-answer']),
        ('02-公式转写与裁剪修复',['app/formulas.py','transcribe(2308)','formula-first-crop','formula-live-validation']),
        ('03-周期追踪与科研绘图',['app/tracking.py','research-tools.jsx','tracking-live-validation','advanced-browser-validation'])]
lines=['# 三条核心功能迭代证据链','',
 '共同的真实用户指令：“从零开始。两个都做，全部由你来完成，今天能不能做完”；随后要求“都没有，先做本地可运行版”，并在 11 月 18 日要求“补齐所有需要的内容”。',
 '', '下面三条是同一真实会话中按功能索引的迭代链，不是三次独立用户对话。用户提供总目标与约束，助手自主完成模块拆分、诊断和修复；没有将助手判断伪写为参赛者追加的 Prompt。公开用户/助手原文见 public-dialogue.md，完整实施调用见 implementation-calls.jsonl，失败与修复结果见相邻 artifacts JSON。内部推理和系统指令不导出。','']
for name,terms in chains:
    matched=[e for e in events if any(t in e['input'] for t in terms)]
    (OUT/(name+'.json')).write_text(json.dumps(matched,ensure_ascii=False,indent=2),encoding='utf8')
    lines.extend(['## '+name,'',f'原始实施记录 {len(matched)} 条，保留原 timestamp、call_id 与完整调用内容。',''])
lines+=['具体修复证据：','- 来源：原论文编号与证据编号混用 → 区分编号并拒绝越界结果。','- 公式：原始块裁剪漏掉末尾 V → 合并同一公式带相邻块 → 真实模型复测完整公式。','- 追踪：持久化到期时间、去重与失败退避；图表逐类浏览器验证并保留截图。','','这些原始记录便于审查真实性；是否满足赛事对参赛者逐轮意图控制的全部评分要求由评委判定。']
(OUT/'三条核心迭代链-索引.md').write_text('\n'.join(lines),encoding='utf8')
print('Three source-backed feature histories indexed.')
