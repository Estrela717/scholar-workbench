"""Combine recorded browser video with clearly disclosed synthesized narration."""
import json,subprocess,wave,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
FFMPEG=Path('D:/Software/miniconda/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe')
OUT=ROOT/'output'/'videos';OUT.mkdir(parents=True,exist_ok=True)
for track in sys.argv[1:] or ('innovation','llm'):
    folder=ROOT/'artifacts'/'video-raw'/track
    manifest=json.loads((folder/'timeline.json').read_text(encoding='utf8'))
    audio=folder/'narration.wav'
    with wave.open(str(audio),'wb') as result:
        for chapter in manifest['timeline']:
            with wave.open(str(folder/'audio'/f'{chapter["index"]:02d}.wav'),'rb') as source:
                if chapter['index']==0:result.setparams(source.getparams())
                frames=source.getnframes();rate=source.getframerate()
                result.writeframes(source.readframes(frames))
                padding=max(0,round(chapter['seconds']*rate)-frames)
                result.writeframes(b'\0'*padding*source.getnchannels()*source.getsampwidth())
    title='AI创新应用挑战赛' if track=='innovation' else 'AI大模型创新应用挑战赛'
    target=OUT/(title+'-知研本地演示与复盘.mp4')
    subprocess.run([str(FFMPEG),'-y','-i',str(folder/'screen.webm'),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-r','25','-c:a','aac','-b:a','128k','-af','apad','-shortest','-movflags','+faststart',str(target)],check=True)
    print(target)
