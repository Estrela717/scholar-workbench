"""Verify the private reviewer login without logging its password."""
import json
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parent.parent
profile=json.loads((ROOT/'docs/participant.json').read_text('utf8'))
secret=json.loads((ROOT/'runtime/review-credentials.json').read_text('utf8'))['password']
base=profile['demo'].removesuffix('/review')
with httpx.Client(timeout=60,follow_redirects=True) as c:
    denied=c.get(base+'/api/documents')
    login=c.post(base+'/review',data={'password':secret})
    health=c.get(base+'/api/health')
    docs=c.get(base+'/api/documents')
    formula=c.get(base+'/api/formulas/2308')
    result={'url':base,'unauthenticated_status':denied.status_code,'login_status':login.status_code,'health':health.json(),'documents_status':docs.status_code,'document_count':len(docs.json()),'formula_status':formula.status_code,'formula_contains_final_V':formula.json().get('latex','').replace('\\end{equation}','').strip().endswith('V')}
    assert denied.status_code==401 and login.status_code==200 and docs.status_code==200
    assert result['document_count']==5 and result['formula_contains_final_V']
    result['validated']=True
(ROOT/'artifacts/public-access-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
print(json.dumps(result,ensure_ascii=False))
