"""Resume an Ollama pull with compact progress instead of terminal animation."""
import json
import time
import httpx

last=0
with httpx.stream('POST','http://127.0.0.1:11434/api/pull',json={'model':'qwen3:4b','stream':True},timeout=600) as response:
    response.raise_for_status()
    for line in response.iter_lines():
        if not line:
            continue
        data=json.loads(line)
        if data.get('error'):
            raise RuntimeError(data['error'])
        if time.time()-last>20 or data.get('status')=='success':
            print(json.dumps(data),flush=True)
            last=time.time()
