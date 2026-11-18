import os
import tempfile
from pathlib import Path
test_root=Path(__file__).resolve().parent.parent/'.cache'/'tests'
test_root.mkdir(parents=True,exist_ok=True)
os.environ['SCHOLAR_DATA_DIR']=tempfile.mkdtemp(prefix='scholar-test-',dir=test_root)
import pymupdf as fitz
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app import llm
from app.db import connect

client=TestClient(app)


def make_pdf(title='Evidence Study',pages=2,scan=False,version='v1'):
    doc=fitz.open()
    for i in range(pages):
        page=doc.new_page()
        page.insert_text((60,70),title,fontsize=22)
        page.insert_text((60,105),'arXiv:1706.03762'+version,fontsize=10)
        page.insert_text((60,140),'1 Introduction',fontsize=15)
        page.insert_textbox(fitz.Rect(60,160,520,300),
            f'The experiment used eight GPUs. The accuracy was 91.2 percent. Page {i+1}. '
            'Our method uses attention for machine translation and source attribution. '*3,fontsize=11)
        if scan:
            pix=page.get_pixmap(matrix=fitz.Matrix(1.6,1.6))
            image=pix.tobytes('png')
            doc.delete_page(i)
            page=doc.new_page(pno=i)
            page.insert_image(page.rect,stream=image)
    data=doc.tobytes()
    doc.close()
    return data


@pytest.fixture(scope='module')
def uploaded():
    response=client.post('/api/documents',files={'file':('evidence.pdf',make_pdf(),'application/pdf')})
    assert response.status_code==200
    return response.json()['document']['id']


def test_parse_preserves_page_and_source_coordinates(uploaded):
    item=client.get('/api/documents/'+uploaded).json()
    assert item['status']=='ready',item
    assert item['page_count']==2
    page=client.get(f'/api/documents/{uploaded}/pages/2').json()
    chunks=page['chunks']
    assert any('eight GPUs' in c['text'] for c in chunks)
    assert all(len(c['bbox'])==4 and c['page']==2 for c in chunks)
    image=client.get(f'/api/documents/{uploaded}/pages/2/image')
    assert image.status_code==200 and image.content.startswith(b'\x89PNG')
    assert client.get(f'/api/documents/{uploaded}/pages/999').status_code==404


def test_identical_pdf_is_not_imported_twice(uploaded):
    original=client.get(f'/api/documents/{uploaded}/file').content
    result=client.post('/api/documents',files={'file':('renamed.pdf',original,'application/pdf')}).json()
    assert result['duplicate'] is True
    assert result['document']['id']==uploaded


def test_versions_have_duplicate_warning(uploaded):
    data=make_pdf(version='v7')
    result=client.post('/api/documents',files={'file':('version.pdf',data,'application/pdf')}).json()
    detail=client.get('/api/documents/'+result['document']['id']).json()
    assert any(d['id']==uploaded for d in detail['duplicates'])


def test_search_returns_original_evidence(uploaded):
    result=client.post('/api/search',json={'query':'eight GPUs','doc_ids':[uploaded]}).json()
    assert result['sources'] and result['mode']=='keyword'
    assert 'eight GPUs' in result['sources'][0]['text']
    assert result['sources'][0]['doc_id']==uploaded


def test_no_evidence_does_not_call_model(monkeypatch,uploaded):
    def should_not_run(*args,**kwargs):
        raise AssertionError('Model must not be called without evidence')
    monkeypatch.setattr(llm,'generate',should_not_run)
    result=client.post('/api/ask',json={'query':'zzzznonexistentterm','doc_ids':[uploaded]}).json()
    assert result['mode']=='no_evidence' and result['sources']==[]


def test_invalid_generated_citation_is_rejected(monkeypatch,uploaded):
    monkeypatch.setattr(llm,'generate',lambda *a,**k:'The accuracy is 99 percent [99].')
    result=client.post('/api/ask',json={'query':'accuracy','doc_ids':[uploaded]}).json()
    assert result['mode']=='citation_rejected'
    assert '99 percent' not in result['answer']


def test_valid_citation_keeps_sources(monkeypatch,uploaded):
    monkeypatch.setattr(llm,'generate',lambda *a,**k:'The experiment used eight GPUs [1].')
    result=client.post('/api/ask',json={'query':'GPUs','doc_ids':[uploaded]}).json()
    assert result['validated'] and result['sources']


def test_ocr_scanned_page():
    result=client.post('/api/documents',files={'file':('scanned.pdf',make_pdf(pages=1,scan=True),'application/pdf')}).json()
    detail=client.get('/api/documents/'+result['document']['id']).json()
    assert detail['status']=='ready',detail
    assert detail['warnings']
    page=client.get(f'/api/documents/{detail["id"]}/pages/1').json()
    assert any('experiment' in c['text'].lower() for c in page['chunks'])


def test_hundred_page_document():
    result=client.post('/api/documents',files={'file':('long.pdf',make_pdf(pages=120),'application/pdf')}).json()
    detail=client.get('/api/documents/'+result['document']['id']).json()
    assert detail['status']=='ready' and detail['page_count']==120
    page=client.get(f'/api/documents/{detail["id"]}/pages/120').json()
    assert any('Page 120' in c['text'] for c in page['chunks'])


def test_csv_rejects_nonfinite_columns():
    response=client.post('/api/csv',files={'file':('values.csv',b'Model,Score,Invalid\nA,5,nan\nB,-3,inf\n','text/csv')})
    assert response.status_code==200
    data=response.json()
    assert data['numeric']==['Score'] and data['count']==2


def test_remote_import_does_not_accept_urls():
    assert client.post('/api/discover/import',json={'arxiv_id':'http://127.0.0.1/private'}).status_code==400


def test_cross_origin_mutation_is_blocked():
    assert client.post('/api/ask',headers={'origin':'https://evil.example'},json={'query':'test'}).status_code==403


def test_non_pdf_rejected():
    assert client.post('/api/documents',files={'file':('bad.pdf',b'not-a-pdf','application/pdf')}).status_code==400


def test_delete_cascades_chunks():
    result=client.post('/api/documents',files={'file':('delete.pdf',make_pdf(title='Delete Study',pages=1),'application/pdf')}).json()
    doc_id=result['document']['id']
    assert client.delete('/api/documents/'+doc_id).status_code==200
    assert client.get('/api/documents/'+doc_id).status_code==404
    with connect() as db:
        assert db.execute('SELECT COUNT(*) FROM chunks WHERE doc_id=?',(doc_id,)).fetchone()[0]==0


def test_cancelled_translation_is_not_restarted(monkeypatch, uploaded):
    from app.jobs import translate_document
    with connect() as db:
        db.execute("INSERT OR REPLACE INTO translation_jobs(doc_id,status,total,updated_at) VALUES(?,'cancelled',2,'test')",(uploaded,))
    monkeypatch.setattr(llm,'generate',lambda *a,**k:pytest.fail('Cancelled job called model'))
    translate_document(uploaded)
    assert client.get(f'/api/documents/{uploaded}/translation').json()['status']=='cancelled'


def test_translation_resume_uses_cached_chunks(monkeypatch, uploaded):
    with connect() as db:
        ids=[row['id'] for row in db.execute('SELECT id FROM chunks WHERE doc_id=? ORDER BY ordinal',(uploaded,))]
        db.execute('INSERT OR REPLACE INTO translations(chunk_id,text,model,created_at) VALUES(?,?,?,?)',(ids[0],'cached text','test','test'))
    calls=[]
    def generate(*a,**k):
        calls.append(a)
        return 'translated test text'
    monkeypatch.setattr(llm,'generate',generate)
    assert client.post(f'/api/documents/{uploaded}/translation').status_code==200
    job=client.get(f'/api/documents/{uploaded}/translation').json()
    assert job['status']=='done' and job['completed']==len(ids)
    assert len(calls)==len(ids)-1
    with connect() as db:
        assert db.execute('SELECT text FROM translations WHERE chunk_id=?',(ids[0],)).fetchone()['text']=='cached text'


def test_structure_extraction_and_bibtex_are_real(uploaded):
    response=client.get(f'/api/documents/{uploaded}/pages/1/structures')
    assert response.status_code==200 and isinstance(response.json()['tables'],list)
    bib=client.get('/api/export/bibtex')
    assert bib.status_code==200 and 'Evidence Study' in bib.text and '1706.03762v1' in bib.text


def test_qwen_reasoning_is_separate_and_truncation_is_rejected(monkeypatch):
    captured=[]
    monkeypatch.setattr(llm,'MODEL','qwen3:4b')
    monkeypatch.setattr(llm,'API_BASE','')
    class Response:
        def raise_for_status(self):pass
        def json(self):
            return {'message':{'content':'Final answer','thinking':'private reasoning'},'done_reason':'stop'}
    def post(*a,**k):
        captured.append(k['json'])
        return Response()
    monkeypatch.setattr(llm.httpx,'post',post)
    assert llm.generate('system','prompt')=='Final answer'
    assert captured[0]['think'] is True and captured[0]['options']['num_predict']>=4096
    monkeypatch.setattr(Response,'json',lambda self:{'message':{'content':'Partial'},'done_reason':'length'})
    with pytest.raises(llm.ModelUnavailable,match='长度上限'):
        llm.generate('system','prompt')


def test_periodic_tracking_deduplicates_and_respects_pause(monkeypatch):
    from app import tracking
    calls=[]
    def search(topic,**kwargs):
        calls.append(topic)
        return [{'id':'1706.03762v1','title':'Attention','abstract':'test'}]
    monkeypatch.setattr(tracking,'arxiv_search',search)
    client.put('/api/tracking',json={'topic':'attention','interval_hours':1})
    assert tracking.refresh_due()['new']==1
    assert tracking.refresh_due()['topics']==0
    assert tracking.refresh_due(True)['new']==0
    client.put('/api/tracking',json={'topic':'attention','enabled':False})
    assert tracking.refresh_due(True)['topics']==0
    assert len(calls)==2


def test_tracking_network_failure_does_not_report_success(monkeypatch):
    from app import tracking
    def fail(*a,**k):raise RuntimeError('offline')
    monkeypatch.setattr(tracking,'arxiv_search',fail)
    client.put('/api/tracking',json={'topic':'fail topic'})
    assert tracking.refresh_due(True)['topics']==0
    row=next(t for t in tracking.snapshot()['topics'] if t['topic']=='fail topic')
    assert row['error']=='offline' and not row['last_run']


def test_formula_review_is_saved_against_real_chunk(uploaded):
    chunk=client.get(f'/api/documents/{uploaded}/pages/1').json()['chunks'][0]
    latex=r'E=mc^2'
    assert client.put('/api/formulas/'+str(chunk['id']),json={'latex':latex}).status_code==200
    result=client.get('/api/formulas/'+str(chunk['id'])).json()
    assert result['latex']==latex and result['reviewed']==1
    assert client.put('/api/formulas/99999999',json={'latex':latex}).status_code==404


def test_public_review_access_and_library_protection(monkeypatch):
    monkeypatch.setenv('PUBLIC_REVIEW_TOKEN','test-review-token')
    assert client.get('/api/documents').status_code==401
    assert client.get('/review').status_code==200
    headers={'Authorization':'Bearer test-review-token'}
    assert client.get('/api/documents',headers=headers).status_code==200
    assert client.delete('/api/documents/anything',headers=headers).status_code==403
    assert client.post('/api/ask',headers={**headers,'origin':'https://evil.example'},json={'query':'test'}).status_code==403


def test_note_edit_persists_without_mutating_sources():
    with connect() as db:
        db.execute("INSERT INTO notes(id,title,text,sources,created_at) VALUES('edit-test','title','old','[]','test')")
    assert client.put('/api/notes/edit-test',json={'text':'revised'}).status_code==200
    with connect() as db:
        r=db.execute("SELECT * FROM notes WHERE id='edit-test'").fetchone()
        assert r['text']=='revised' and r['sources']=='[]'
