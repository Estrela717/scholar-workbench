import json,re,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
FFMPEG='D:/Software/miniconda/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
out=ROOT/'output'/'videos';qa=out/'qa';qa.mkdir(exist_ok=True)
results=[]
for i,p in enumerate(out.glob('*.mp4')):
    info=subprocess.run([FFMPEG,'-hide_banner','-i',str(p)],capture_output=True,text=True,encoding='utf8',errors='replace').stderr
    match=re.search(r'Duration: (\d+):(\d+):([\d.]+)',info)
    h,m,s=map(float,match.groups());seconds=h*3600+m*60+s
    assert 300<=seconds<=480,seconds
    assert '1920x1080' in info and 'Audio: aac' in info and 'Video: h264' in info
    decoded=subprocess.run([FFMPEG,'-v','error','-i',str(p),'-f','null','-'],capture_output=True,text=True,encoding='utf8',errors='replace')
    assert decoded.returncode==0 and not decoded.stderr,decoded.stderr
    frames=[]
    for n,t in enumerate([8,seconds*.35,seconds*.65,seconds-15]):
        target=qa/f'video-{i}-{n}.png'
        subprocess.run([FFMPEG,'-v','error','-y','-ss',str(t),'-i',str(p),'-frames:v','1',str(target)],check=True)
        im=Image.open(target);im.thumbnail((960,540));frames.append(im.copy())
    sheet=Image.new('RGB',(1920,1080),'white')
    for n,im in enumerate(frames):sheet.paste(im,((n%2)*960,(n//2)*540))
    sheet.save(qa/f'contact-{i}.jpg',quality=90)
    results.append({'filename':p.name,'duration_seconds':seconds,'resolution':'1920x1080','video':'H.264','audio':'AAC / synthesized Mandarin','decode_errors':[],'bytes':p.stat().st_size})
(out/'视频技术验收.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(results,ensure_ascii=False,indent=2))
