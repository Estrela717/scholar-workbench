import json
import time
from pathlib import Path
import httpx

BASE='http://127.0.0.1:8765/api'
results={'checked_at':time.strftime('%Y-%m-%d %H:%M:%S'),'checks':[]}
out=Path('artifacts/live-model-validation.json')
out.parent.mkdir(exist_ok=True)


def check(name,path,data):
    started=time.time()
    try:
        response=httpx.post(BASE+path,json=data,timeout=480)
        result={'name':name,'http_status':response.status_code,'seconds':round(time.time()-started,2),'result':response.json()}
    except Exception as error:
        result={'name':name,'seconds':round(time.time()-started,2),'error':str(error)}
    results['checks'].append(result)
    out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'name':name,'seconds':result['seconds'],'status':result.get('http_status'),'error':result.get('error')},ensure_ascii=False),flush=True)


docs=httpx.get(BASE+'/documents').json()
attention=next(d['id'] for d in docs if d['arxiv_id']=='1706.03762v1')
check('Chinese question over English paper','/ask',{'query':'Transformer 的 base 和 big 模型分别使用多少块 GPU，训练了多久？请区分两种设置。','doc_ids':[attention]})
check('Academic paragraph translation','/translate',{'text':'The Transformer allows for significantly more parallelization and can reach a new state of the art in translation quality after being trained for as little as twelve hours on eight P100 GPUs.'})
check('Grounded literature outline','/write',{'kind':'outline','topic':'用三点概述 Transformer 的方法创新。每点必须引用原文，不超过300字。','doc_ids':[attention]})
