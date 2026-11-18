"""Render distinct competition reports and editable sources; enforce page limits."""
import json,re
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate,PageBreak,Spacer,Flowable
from reportlab.lib import colors
from build_documents import p,table,screenshot,INK,TEAL,MUTED,LINE
from submission_content import innovation,llm
import pymupdf
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output/submission-2026-11-18';OUT.mkdir(parents=True,exist_ok=True)
class Flow(Flowable):
    def __init__(self,labels):
        super().__init__();self.labels=labels;self.width=505;self.height=65
    def draw(self):
        c=self.canv;w=91;gap=12
        for i,label in enumerate(self.labels):
            x=i*(w+gap);c.setFillColor(colors.HexColor('#e9f2ec'));c.setStrokeColor(LINE)
            c.roundRect(x,13,w,42,5,stroke=1,fill=1)
            c.setFillColor(INK);c.setFont('CN',8.4);c.drawCentredString(x+w/2,30,label)
            if i<len(self.labels)-1:
                c.setStrokeColor(TEAL);c.line(x+w+2,34,x+w+gap-2,34)
                c.line(x+w+gap-5,37,x+w+gap-2,34);c.line(x+w+gap-5,31,x+w+gap-2,34)
def footer(c,doc):
    c.saveState();c.setFont('CN',8);c.setFillColor(MUTED)
    c.drawString(45,810,'知研 / SCHOLAR WORKBENCH / 2026.11.18')
    c.setStrokeColor(LINE);c.line(45,46,550,46)
    c.drawString(45,31,'曲珈莹 · 云南大学 · 人工智能2025级 · A组')
    c.drawRightString(550,31,f'{doc.page:02d}');c.restoreState()
results={}
for key,name,chapters in [('innovation','AI创新应用挑战赛',innovation()),('llm','AI大模型创新应用挑战赛',llm())]:
    story=[];md=['# 知研 · '+name,'','按2026-11-18官网公开规则编写，具体证据见章节末。']
    for i,chapter in enumerate(chapters):
        if i:story.append(PageBreak())
        story.append(p(chapter['title'],'H1CN'));md+=['','## '+chapter['title'],'']
        for block in chapter['blocks']:
            kind=block[0]
            if kind in ('p','h','evidence','code'):
                style={'p':'BodyCN','h':'H2CN','evidence':'SmallCN','code':'TableCN'}[kind]
                if kind=='code':
                    story.extend([Spacer(1,7),table([[block[1]]],[505]),Spacer(1,12)])
                    md+=['```text',block[1],'```','']
                else:
                    story.append(p(block[1],style));md += [('### ' if kind=='h' else '')+block[1],'']
            elif kind=='table':
                rows,widths=block[1:];story.extend([table(rows,widths or [505/len(rows[0])]*len(rows[0])),Spacer(1,12)])
                for n,row in enumerate(rows):
                    md.append('| '+' | '.join(str(x).replace('|','/') for x in row)+' |')
                    if n==0:md.append('| '+' | '.join('---' for _ in row)+' |')
                md.append('')
            elif kind=='image':
                story.extend([screenshot(block[1],maxheight=block[2]),Spacer(1,12)])
                md+=['截图证据：artifacts/screenshots/'+block[1],'']
            elif kind=='flow':
                story.extend([Flow(block[1]),Spacer(1,12)]);md+=[' → '.join(block[1]),'']
    target=OUT/f'曲珈莹-{name}-技术文档.pdf'
    SimpleDocTemplate(str(target),pagesize=(595.28,841.89),leftMargin=45,rightMargin=45,topMargin=63,bottomMargin=63,title=name+' 知研技术文档',author='曲珈莹').build(story,onFirstPage=footer,onLaterPages=footer)
    document=pymupdf.open(target)
    assert len(document)==len(chapters),(name,'unexpected page overflow',len(document),len(chapters))
    assert len(document)<=30
    for i,chapter in enumerate(chapters):
        normalize=lambda s:re.sub(r'\s+','',s)
        assert normalize(chapter['title']) in normalize(document[i].get_text()),(name,i,chapter['title'])
    (ROOT/'docs'/f'{key}-technical-report.md').write_text('\n'.join(md),'utf8')
    results[key]={'title':name,'pages':len(document),'sections':[x['title'] for x in chapters],'file':target.name}
(OUT/'文档赛道对应校验.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),'utf8')
print(json.dumps(results,ensure_ascii=False,indent=2))
