import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Minimal .env loading: never overwrite a process-provided value.
if (ROOT / '.env').exists():
    for line in (ROOT / '.env').read_text(encoding='utf-8-sig').splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
DATA = Path(os.environ.get('SCHOLAR_DATA_DIR', str(ROOT / 'data'))).resolve()
FILES = DATA / 'files'
EXPORTS = DATA / 'exports'
OLLAMA = os.environ.get('OLLAMA_URL', 'http://127.0.0.1:11434').rstrip('/')
MODEL = os.environ.get('LLM_MODEL', 'qwen3-vl:4b-instruct')
EMBED_MODEL = os.environ.get('EMBEDDING_MODEL', 'bge-m3:latest')
API_BASE = os.environ.get('LLM_BASE_URL', '').rstrip('/')
API_KEY = os.environ.get('LLM_API_KEY', '')
for folder in (DATA, FILES, EXPORTS):
    folder.mkdir(parents=True, exist_ok=True)
