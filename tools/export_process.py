"""Export this task's public messages and implementation calls, never hidden reasoning.

The source session path is explicitly scoped to the user's current conversation.
This is an excerpt, not a claim of a complete original conversation export.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
SOURCE=Path('C:/Users/Estrela/.codex/sessions/2026/11/14/rollout-2026-11-14T12-28-11-01a1d850-1eef-7b51-81cf-35a9329cc46c.jsonl')
OUT=ROOT/'artifacts'/'process-evidence'
OUT.mkdir(parents=True,exist_ok=True)
started=False
messages=[]
events=[]
for line in SOURCE.open(encoding='utf-8'):
    record=json.loads(line)
    if record.get('type')!='response_item':
        continue
    payload=record.get('payload',{})
    kind=payload.get('type')
    if kind=='message' and payload.get('role') in ('user','assistant'):
        if payload.get('role')=='assistant' and payload.get('channel',payload.get('phase')) not in ('commentary','final','final_answer'):
            continue
        text='\n'.join(c.get('text','') for c in payload.get('content',[]) if c.get('type') in ('input_text','output_text','text'))
        # Never copy internal metadata, reasoning records, system or developer messages.
        if payload.get('role')=='user' and '从零开始。两个都做' in text:
            started=True
        if started and text and not text.lstrip().startswith('<environment_context>'):
            messages.append({'timestamp':record.get('timestamp'),'role':payload['role'],'text':text})
    elif started and kind in ('custom_tool_call','function_call'):
        value=payload.get('input',payload.get('arguments',''))
        events.append({'timestamp':record.get('timestamp'),'type':kind,'name':payload.get('name'),
                       'call_id':payload.get('call_id'),'input':value})

notice=('本文件来自本次真实会话，仅包含从用户确认从零开发开始的公开用户/助手消息。'
        '系统指令、开发者指令、内部推理与二进制工具结果不包含在内。工具调用另存 JSONL。'
        '这份节选不是伪造的三次用户 Prompt，也不替代组委会可能要求的完整原始对话导出。')
lines=['# 真实开发会话节选',notice]
for message in messages:
    lines.extend(['',f'## {message["timestamp"]} / {message["role"]}','',message['text']])
(OUT/'public-dialogue.md').write_text('\n'.join(lines),encoding='utf-8')
(OUT/'implementation-calls.jsonl').write_text('\n'.join(json.dumps(e,ensure_ascii=False) for e in events),encoding='utf-8')
(OUT/'README.md').write_text('# 过程证据说明\n\n'+notice+'\n\n可结合 Git 细粒度提交历史、真实测试结果和修复前后截图审查开发演进。\n',encoding='utf-8')
print(json.dumps({'messages':len(messages),'implementation_calls':len(events),'directory':str(OUT)},ensure_ascii=False))
