import json
import re
import threading
import httpx
import numpy as np
from .config import OLLAMA, MODEL, EMBED_MODEL, API_BASE, API_KEY

# Serialize GPU work on an 8GB laptop; avoid loading embedding/generation models concurrently.
MODEL_LOCK = threading.RLock()


class ModelUnavailable(RuntimeError):
    pass


def status():
    try:
        response = httpx.get(f'{OLLAMA}/api/tags', timeout=3)
        response.raise_for_status()
        names = [item['name'] for item in response.json().get('models', [])]
        return {'available': MODEL in names or bool(API_BASE), 'model': MODEL,
                'embedding_available': EMBED_MODEL in names, 'embedding_model': EMBED_MODEL,
                'models': names, 'provider': 'compatible' if API_BASE else 'ollama'}
    except (httpx.HTTPError, ValueError):
        return {'available': bool(API_BASE), 'model': MODEL, 'embedding_available': False,
                'embedding_model': EMBED_MODEL, 'models': [], 'provider': 'compatible' if API_BASE else 'ollama'}


def clean_content(text):
    # Do not expose model reasoning as the final answer.
    return re.sub(r'<think>.*?</think>', '', text, flags=re.S).strip()


def generate(system, prompt, max_tokens=1600, json_mode=False):
    try:
        with MODEL_LOCK:
            if API_BASE:
                headers = {'Authorization': f'Bearer {API_KEY}'} if API_KEY else {}
                payload = {'model': MODEL, 'messages': [{'role':'system','content':system},
                           {'role':'user','content':prompt}], 'temperature':0.15, 'max_tokens':max_tokens}
                if json_mode:
                    payload['response_format'] = {'type':'json_object'}
                response = httpx.post(f'{API_BASE}/chat/completions', headers=headers, json=payload, timeout=240)
                response.raise_for_status()
                text = response.json()['choices'][0]['message']['content']
            else:
                # Ollama's Qwen3 template needs thinking enabled to separate its
                # reasoning from the final content field. Disabling it on the
                # installed model emitted untagged reasoning as the answer.
                thinking = MODEL.lower().startswith('qwen3')
                payload = {'model': MODEL, 'messages':[{'role':'system','content':system},
                           {'role':'user','content':prompt}], 'stream':False, 'think':thinking,
                           'options':{'temperature':0.15, 'num_ctx':8192,
                                      'num_predict':max(4096,max_tokens+2048) if thinking else max_tokens}, 'keep_alive':'5m'}
                if json_mode:
                    payload['format'] = 'json'
                response = httpx.post(f'{OLLAMA}/api/chat', json=payload, timeout=300)
                response.raise_for_status()
                result = response.json()
                text = result['message']['content']
                if result.get('done_reason') == 'length':
                    raise ModelUnavailable('模型输出达到长度上限，未将不完整回答作为结果。请缩短问题或选择更少文献后重试。')
        text = clean_content(text)
        if not text:
            raise ModelUnavailable('模型未返回可用正文，请减少输入长度后重试。')
        return text
    except (httpx.HTTPError, KeyError, ValueError) as error:
        raise ModelUnavailable(f'本地模型调用失败：{type(error).__name__}。请检查 Ollama 是否已启动及模型是否可用。') from error


def embeddings(texts):
    if not texts:
        return np.empty((0, 0), dtype=np.float32)
    with MODEL_LOCK:
        response = httpx.post(f'{OLLAMA}/api/embed', json={'model':EMBED_MODEL, 'input':texts,
                              'truncate':True, 'keep_alive':'5m'}, timeout=180)
        response.raise_for_status()
    values = np.asarray(response.json()['embeddings'], dtype=np.float32)
    norms = np.linalg.norm(values, axis=1, keepdims=True)
    return values / np.maximum(norms, 1e-8)


def json_object(text):
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip())
    return json.loads(text)


def plan_tools(query, allow_external=False):
    """Ask the model to choose read-only tools using native function calling.

    Arguments are validated again by the dispatcher. No generated code is executed.
    """
    tools=[{'type':'function','function':{'name':'search_library',
        'description':'Search the local paper library for original evidence. Always call this for paper questions.',
        'parameters':{'type':'object','properties':{'query':{'type':'string'}},'required':['query']}}},
        {'type':'function','function':{'name':'citation_graph',
        'description':'Read the verified local citation graph when asked about relationships or influential papers.',
        'parameters':{'type':'object','properties':{}}}}]
    if allow_external:
        tools.append({'type':'function','function':{'name':'search_arxiv',
                      'description':'Search public arXiv metadata. Use a concise English research topic.',
                      'parameters':{'type':'object','properties':{'query':{'type':'string'}},'required':['query']}}})
    messages=[{'role':'system','content':'You plan a research task by selecting tools. Call search_library first. '
               'Optionally call citation_graph for citation relationships. Never invent tool results. Keep search terms concise.'},
              {'role':'user','content':query}]
    with MODEL_LOCK:
        if API_BASE:
            headers={'Authorization':f'Bearer {API_KEY}'} if API_KEY else {}
            response=httpx.post(API_BASE+'/chat/completions',headers=headers,
                                json={'model':MODEL,'messages':messages,'tools':tools,'max_tokens':400,'temperature':0},timeout=90)
            response.raise_for_status()
            calls=response.json()['choices'][0]['message'].get('tool_calls',[])
            return [{'name':c['function']['name'],'arguments':json.loads(c['function']['arguments'])} for c in calls]
        response=httpx.post(OLLAMA+'/api/chat',json={'model':MODEL,'messages':messages,'tools':tools,
                            'stream':False,'think':MODEL.lower().startswith('qwen3'),
                            'options':{'temperature':0,'num_ctx':4096,'num_predict':2200}},timeout=120)
        response.raise_for_status()
        return [c['function'] for c in response.json()['message'].get('tool_calls',[])]
