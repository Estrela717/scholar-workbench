"""Combine recorded browser video with clearly disclosed synthesized narration."""
import json,subprocess,wave,sys,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
FFMPEG=Path('D:/Software/miniconda/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe')
OUT=ROOT/'output'/'videos';OUT.mkdir(parents=True,exist_ok=True)
for track in sys.argv[1:] or ('innovation','llm'):
    folder=ROOT/'artifacts'/'video-raw'/track
    manifest=json.loads((folder/'timeline.json').read_text(encoding='utf8'))
    info=subprocess.run([str(FFMPEG),'-hide_banner','-i',str(folder/'screen.webm')],capture_output=True,text=True,encoding='utf8',errors='replace').stderr
    hours,minutes,seconds=map(float,re.search(r'Duration: (\d+):(\d+):([\d.]+)',info).groups())
    duration=hours*3600+minutes*60+seconds
    overhead=max(0,duration-sum(c['seconds'] for c in manifest['timeline']))
    lead=min(1.5,overhead)
    gap=(overhead-lead)/max(1,len(manifest['timeline'])-1)
    audio=folder/'narration.wav'
    with wave.open(str(audio),'wb') as result:
        for chapter in manifest['timeline']:
            with wave.open(str(folder/'audio'/f'{chapter["index"]:02d}.wav'),'rb') as source:
                if chapter['index']==0:
                    result.setparams(source.getparams())
                    result.writeframes(b'\0'*round(lead*source.getframerate())*source.getnchannels()*source.getsampwidth())
                frames=source.getnframes();rate=source.getframerate()
                result.writeframes(source.readframes(frames))
                chapter_gap=gap if chapter['index']<len(manifest['timeline'])-1 else 0
                padding=max(0,round((chapter['seconds']+chapter_gap)*rate)-frames)
                result.writeframes(b'\0'*padding*source.getnchannels()*source.getsampwidth())
    title='AI创新应用挑战赛' if track=='innovation' else 'AI大模型创新应用挑战赛'
    target=OUT/(title+'-知研本地演示与复盘.mp4')
    subprocess.run([str(FFMPEG),'-hide_banner','-loglevel','error','-y','-i',str(folder/'screen.webm'),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-r','25','-c:a','aac','-b:a','128k','-af','apad','-shortest','-movflags','+faststart',str(target)],check=True)
    print(target)
