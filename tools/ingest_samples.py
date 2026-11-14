from pathlib import Path
import json
import time
import httpx

base='http://127.0.0.1:8765/api'
with httpx.Client(timeout=240) as client:
    for file in sorted(Path('data/samples').glob('*.pdf')):
        with file.open('rb') as stream:
            result=client.post(base+'/documents',files={'file':(file.name,stream,'application/pdf')}).raise_for_status().json()
        print(json.dumps({'file':file.name,'id':result['document']['id'],'duplicate':result['duplicate']},ensure_ascii=False),flush=True)
    for _ in range(120):
        docs=client.get(base+'/documents').json()
        if all(d['status'] in ('ready','error') for d in docs):
            print(json.dumps([{'title':d['title'],'status':d['status'],'pages':d['page_count'],'error':d['error']} for d in docs],ensure_ascii=False),flush=True)
            break
        time.sleep(2)
