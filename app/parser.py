import hashlib
import json
import re
import threading
import unicodedata
from collections import Counter
from pathlib import Path
import pymupdf as fitz
import numpy as np
from .config import FILES, EMBED_MODEL
from .db import connect, document, record
from . import llm

PARSE_LOCK = threading.Lock()
OCR_LOCK = threading.Lock()
_ocr = None


def tokens(text):
    latin = re.findall(r'[a-z0-9]+', text.lower())
    chinese = re.findall(r'[\u4e00-\u9fff]+', text)
    return latin + [s[i:i+2] for s in chinese for i in range(max(1,len(s)-1))]


def ocr_blocks(page):
    global _ocr
    with OCR_LOCK:
        if _ocr is None:
            from rapidocr_onnxruntime import RapidOCR
            _ocr = RapidOCR(intra_op_num_threads=2, inter_op_num_threads=2)
        scale = 1.7
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        pixels = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height,pix.width,pix.n)
        result, _ = _ocr(pixels)
    blocks = []
    for points, text, confidence in (result or []):
        if float(confidence) < 0.45:
            continue
        xs, ys = zip(*points)
        blocks.append({'text':text,'bbox':[min(xs)/scale,min(ys)/scale,max(xs)/scale,max(ys)/scale],
                       'kind':'ocr','size':10})
    return blocks


def page_blocks(page):
    blocks = []
    for block in page.get_text('dict')['blocks']:
        if block['type'] != 0:
            continue
        lines, sizes = [], []
        for line in block['lines']:
            lines.append(''.join(span['text'] for span in line['spans']))
            sizes.extend(span['size'] for span in line['spans'] if span['text'].strip())
        text = unicodedata.normalize('NFKC','\n'.join(lines).strip())
        text = re.sub(r'(?<=\w)-\n(?=\w)', '', text)
        if text:
            blocks.append({'text':text,'bbox':list(block['bbox']),'kind':'paragraph',
                           'size':max(sizes) if sizes else 10})
    if sum(len(b['text']) for b in blocks) < 40:
        blocks = ocr_blocks(page)
    # Split two-column reading bands at full-width blocks, then read left/right columns.
    width = page.rect.width
    full = sorted([b for b in blocks if b['bbox'][0] < width*.35 and b['bbox'][2] > width*.65],
                  key=lambda b:b['bbox'][1])
    narrow = [b for b in blocks if b not in full]
    ordered = []
    for separator in full + [None]:
        end = separator['bbox'][1] if separator else float('inf')
        band = [b for b in narrow if b['bbox'][1] < end]
        narrow = [b for b in narrow if b['bbox'][1] >= end]
        left = [b for b in band if b['bbox'][0] < width*.48]
        right = [b for b in band if b['bbox'][0] >= width*.48]
        ordered.extend(sorted(left,key=lambda b:b['bbox'][1]))
        ordered.extend(sorted(right,key=lambda b:b['bbox'][1]))
        if separator:
            ordered.append(separator)
    return ordered


def split_text(text, limit=1600):
    if len(text) <= limit:
        return [text]
    parts = []
    while len(text) > limit:
        pos = max(text.rfind('\n',0,limit),text.rfind('. ',0,limit),text.rfind('。',0,limit))
        if pos < limit//2:
            pos = limit
        parts.append(text[:pos+1].strip())
        text = text[pos+1:]
    if text.strip():
        parts.append(text.strip())
    return parts


def update_document(doc_id, **values):
    with connect() as db:
        db.execute('UPDATE documents SET '+','.join(f'{key}=?' for key in values)+' WHERE id=?',
                   (*values.values(),doc_id))


def parse_document(doc_id):
    # One CPU/OCR parsing job at a time, keeping large books bounded in memory.
    with PARSE_LOCK:
        try:
            _parse_document(doc_id)
        except Exception as error:
            update_document(doc_id,status='error',error=f'{type(error).__name__}: {str(error)[:250]}')
            record('error', f'文献解析失败：{doc_id}')


def _parse_document(doc_id):
    item = document(doc_id)
    if not item:
        return
    update_document(doc_id,status='parsing',progress=0,error='')
    with connect() as db:
        db.execute('DELETE FROM paper_references WHERE doc_id=?',(doc_id,))
        db.execute('DELETE FROM chunks WHERE doc_id=?',(doc_id,))
    pdf = fitz.open(FILES / f'{doc_id}.pdf')
    if pdf.needs_pass:
        raise ValueError('文件已加密，请先提供可阅读的 PDF')
    count = len(pdf)
    update_document(doc_id,page_count=count)
    heading, ordinal, reference_mode = '', 0, False
    headings, warnings, page_sizes, first_blocks, first_text = [], [], [], [], ''
    figures = []
    for page_index in range(count):
        page = pdf[page_index]
        page_sizes.append([page.rect.width,page.rect.height])
        blocks = page_blocks(page)
        if any(b['kind']=='ocr' for b in blocks):
            warnings.append(f'第 {page_index+1} 页使用 OCR，公式和表格结构需人工核对')
        if not blocks:
            warnings.append(f'第 {page_index+1} 页未识别到正文')
        if page_index == 0:
            first_blocks = blocks
            first_text = '\n'.join(b['text'] for b in blocks)
        sizes = [b['size'] for b in blocks if len(b['text'])>60]
        normal_size = float(np.median(sizes)) if sizes else 10
        entries = []
        for block in blocks:
            text = block['text']
            compact = ' '.join(text.split())
            kind = block['kind']
            if len(compact)<180 and (block['size']>normal_size*1.16 or re.match(r'^\d+(?:\.\d+){0,2}\s+[A-Z\u4e00-\u9fff]',compact)
                                      or compact.lower() in ('abstract','references','bibliography','conclusion','摘要','参考文献')):
                kind='heading'
                heading=compact
                headings.append({'title':compact,'page':page_index+1,'bbox':block['bbox']})
            if compact.lower() in ('references','bibliography','参考文献'):
                reference_mode=True
            elif kind=='heading' and re.match(r'^(appendix|[A-Z]\s|附录)',compact,re.I):
                reference_mode=False
            elif re.match(r'^(Table|Figure|Fig\.|表\s*\d|图\s*\d)\s*\d*',compact,re.I):
                kind='caption'
            if reference_mode and kind!='heading':
                kind='reference'
            for part in split_text(text):
                entries.append((doc_id,page_index+1,ordinal,part,json.dumps(block['bbox']),kind,heading))
                ordinal+=1
        with connect() as db:
            db.executemany('INSERT INTO chunks(doc_id,page,ordinal,text,bbox,kind,heading) VALUES(?,?,?,?,?,?,?)',entries)
        # Keep figure positions, not all decoded images, in metadata.
        for image in page.get_image_info():
            if len(figures)<300:
                figures.append({'page':page_index+1,'bbox':list(image['bbox'])})
        update_document(doc_id,progress=round((page_index+1)/max(count,1)*90),chunk_count=ordinal)
    metadata = pdf.metadata or {}
    pdf.close()
    title_candidates = [b for b in first_blocks if len(' '.join(b['text'].split()))>12
                        and b['bbox'][1]<350 and b['bbox'][2]-b['bbox'][0]>80
                        and not re.match(r'^arxiv\s*:',b['text'],re.I)]
    largest=max((b['size'] for b in title_candidates),default=10)
    title_parts=sorted([b for b in title_candidates if b['size']>=largest-.4],key=lambda b:b['bbox'][1])
    inferred_title=' '.join(b['text'] for b in title_parts if b['bbox'][1]<title_parts[0]['bbox'][1]+90) if title_parts else item['filename']
    title = metadata.get('title','').strip()
    if len(title)<10 or title.lower().endswith('.pdf'):
        title=' '.join(inferred_title.split())[:300]
    authors=metadata.get('author','')[:500]
    if not authors and title_parts:
        title_bottom=max(b['bbox'][3] for b in title_parts)
        abstract_y=min((b['bbox'][1] for b in first_blocks if b['text'].strip().lower()=='abstract'),default=350)
        names=[]
        for block in sorted(first_blocks,key=lambda b:(b['bbox'][1],b['bbox'][0])):
            if block['bbox'][1]<title_bottom or block['bbox'][1]>=abstract_y:
                continue
            for line in block['text'].splitlines():
                if re.search(r'@|arxiv|google|university|research|institute|laboratory|facebook|^\{|^\d',line,re.I):
                    continue
                clean=re.sub(r'[†‡∗⋆*0-9]+','',line).strip(' ,; ')
                if 5<len(clean)<200 and len(clean.split())>=2:
                    names.append(clean)
        authors=', '.join(names)[:500]
    arxiv_match=re.search(r'(?:arXiv[:\s]*)?(\d{4}\.\d{4,5})(v\d+)?',first_text+' '+item['filename'])
    arxiv_id=''.join(x or '' for x in arxiv_match.groups()) if arxiv_match else ''
    doi_match=re.search(r'10\.\d{4,9}/[^\s<>]+',first_text)
    abstract_match=re.search(r'\bAbstract\b\s*[:—-]?\s*(.{60,3000}?)(?:\n\s*1\s|\nIntroduction|\nKeywords|$)',first_text,re.S|re.I)
    abstract=' '.join(abstract_match.group(1).split())[:2000] if abstract_match else ''
    year_match=re.search(r'\b(20[0-2]\d|19\d{2})\b(?!\.\d)',first_text)
    year=('20'+arxiv_id[:2]) if arxiv_id else (year_match.group(0) if year_match else '')
    update_document(doc_id,title=title,authors=authors,abstract=abstract,arxiv_id=arxiv_id,
                    doi=doi_match.group(0) if doi_match else '',year=year,
                    warnings=json.dumps(warnings,ensure_ascii=False),
                    metadata=json.dumps({'headings':headings,'page_sizes':page_sizes,'figures':figures},ensure_ascii=False),
                    status='ready',progress=100)
    extract_references(doc_id)
    link_references()
    record('import',f'已解析《{title}》，{count} 页 / {ordinal} 个内容块')


def extract_references(doc_id):
    with connect() as db:
        rows=db.execute("SELECT * FROM chunks WHERE doc_id=? AND kind='reference' ORDER BY ordinal",(doc_id,)).fetchall()
        numbered=any(re.match(r'^\[\d{1,3}\]',row['text'].strip()) for row in rows)
        entries=[]
        if numbered:
            current=None
            for row in rows:
                for part in re.split(r'(?=\[\d{1,3}\]\s)',row['text']):
                    part=part.strip()
                    if len(part)<4:
                        continue
                    match=re.match(r'^\[(\d+)\]',part)
                    if match:
                        if current:
                            entries.append(current)
                        current={'label':match.group(1),'text':part,'page':row['page'],'chunk_id':row['id']}
                    elif current:
                        current['text']+='\n'+part
            if current:
                entries.append(current)
        else:
            entries=[{'label':str(i+1),'text':row['text'],'page':row['page'],'chunk_id':row['id']}
                     for i,row in enumerate(rows) if len(row['text'])>=25]
        for entry in entries:
            db.execute('INSERT INTO paper_references(doc_id,label,text,page,chunk_id) VALUES(?,?,?,?,?)',
                       (doc_id,entry['label'],entry['text'],entry['page'],entry['chunk_id']))


def link_references():
    with connect() as db:
        papers=db.execute("SELECT id,title,arxiv_id,doi FROM documents WHERE status='ready'").fetchall()
        refs=db.execute('SELECT id,doc_id,text FROM paper_references').fetchall()
        for ref in refs:
            target=None
            text=' '.join(ref['text'].lower().split())
            normalized_text=re.sub(r'[^a-z0-9]+','',text)
            for paper in papers:
                if paper['id']==ref['doc_id']:
                    continue
                title=' '.join(paper['title'].lower().split())
                arxiv=re.sub(r'v\d+$','',paper['arxiv_id'])
                normalized_title=re.sub(r'[^a-z0-9]+','',title)
                if (len(normalized_title)>15 and normalized_title in normalized_text) or (arxiv and arxiv in text) or (paper['doi'] and paper['doi'].lower() in text):
                    target=paper['id']
                    break
            db.execute('UPDATE paper_references SET target_doc_id=? WHERE id=?',(target,ref['id']))


def index_document(doc_id):
    item=document(doc_id)
    if not item or item['status'] not in ('ready','indexing'):
        return
    try:
        update_document(doc_id,status='indexing',progress=0,error='')
        with connect() as db:
            rows=db.execute('SELECT id,text FROM chunks WHERE doc_id=? ORDER BY ordinal',(doc_id,)).fetchall()
        for start in range(0,len(rows),12):
            batch=rows[start:start+12]
            values=llm.embeddings([row['text'] for row in batch])
            with connect() as db:
                for row,value in zip(batch,values):
                    db.execute('UPDATE chunks SET embedding=?,embedding_model=? WHERE id=?',
                               (value.astype(np.float32).tobytes(),EMBED_MODEL,row['id']))
            update_document(doc_id,progress=round(min(start+12,len(rows))/max(len(rows),1)*100))
        record('index',f'已建立《{item["title"]}》的语义索引')
    except Exception as error:
        update_document(doc_id,error=f'语义索引未完成，可继续关键词检索：{type(error).__name__}')
    finally:
        update_document(doc_id,status='ready',progress=100)


def duplicates(doc_id):
    item=document(doc_id)
    if not item:
        return []
    with connect() as db:
        docs=db.execute("SELECT id,title,arxiv_id FROM documents WHERE id!=? AND status='ready'",(doc_id,)).fetchall()
        own=' '.join(r['text'] for r in db.execute('SELECT text FROM chunks WHERE doc_id=? ORDER BY ordinal LIMIT 100',(doc_id,)))
        own_tokens=set(tokens(own))
        def centroid(identifier):
            values=[np.frombuffer(r['embedding'],dtype=np.float32) for r in db.execute(
                'SELECT embedding FROM chunks WHERE doc_id=? AND embedding IS NOT NULL AND embedding_model=? ORDER BY ordinal LIMIT 80',
                (identifier,EMBED_MODEL))]
            if not values or len({v.size for v in values})!=1:
                return None
            mean=np.mean(values,axis=0)
            return mean/max(np.linalg.norm(mean),1e-8)
        own_vector=centroid(doc_id)
        matches=[]
        for other in docs:
            text=' '.join(r['text'] for r in db.execute('SELECT text FROM chunks WHERE doc_id=? ORDER BY ordinal LIMIT 100',(other['id'],)))
            other_tokens=set(tokens(text))
            similarity=len(own_tokens&other_tokens)/max(len(own_tokens|other_tokens),1)
            other_vector=centroid(other['id']) if own_vector is not None else None
            semantic=float(own_vector @ other_vector) if other_vector is not None and own_vector.size==other_vector.size else None
            same_arxiv=bool(item['arxiv_id']) and re.sub(r'v\d+$','',item['arxiv_id'])==re.sub(r'v\d+$','',other['arxiv_id'])
            if same_arxiv or similarity>0.7 or (semantic is not None and semantic>.95 and similarity>.35):
                matches.append({'id':other['id'],'title':other['title'],'score':round(similarity,3),
                                'semantic_score':round(semantic,3) if semantic is not None else None,
                                'reason':'同一 arXiv 论文的版本' if same_arxiv else ('语义与正文内容高度相似' if semantic is not None and semantic>.95 else '正文词项高度重合'),
                                'arxiv_id':other['arxiv_id']})
    return matches
