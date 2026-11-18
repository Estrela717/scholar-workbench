"""Fit neural narration to recorded chapters; keep the existing video stream."""
import json,re,subprocess,wave,shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'artifacts/voice-natural'
FFMPEG='D:/Software/miniconda/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
backup=ROOT/'output/history/voice-sapi';backup.mkdir(parents=True,exist_ok=True)
report=[]
for track,title in [('innovation','AI创新应用挑战赛'),('llm','AI大模型创新应用挑战赛')]:
    video=ROOT/'output/videos'/f'{title}-知研本地演示与复盘.mp4'
    original=backup/video.name
    if not original.exists():shutil.copy2(video,original)
    info=subprocess.run([FFMPEG,'-hide_banner','-i',str(original)],capture_output=True,text=True,encoding='utf8',errors='replace').stderr
    h,m,s=map(float,re.search(r'Duration: (\d+):(\d+):([\d.]+)',info).groups());duration=h*3600+m*60+s
    chapters=json.loads((ROOT/f'artifacts/video-raw/{track}/timeline.json').read_text('utf8'))['timeline']
    overhead=max(0,duration-sum(x['seconds'] for x in chapters));lead=min(1.5,overhead);gap=(overhead-lead)/(len(chapters)-1)
    rate=24000;data=np.zeros(round(duration*rate),dtype=np.int16);offset=lead;segments=[]
    for i,c in enumerate(chapters):
        with wave.open(str(BASE/track/f'{i:02d}.wav')) as w:
            assert (w.getframerate(),w.getnchannels(),w.getsampwidth())==(rate,1,2)
            samples=np.frombuffer(w.readframes(w.getnframes()),np.int16)
        seconds=len(samples)/rate;available=c['seconds']+(gap if i<len(chapters)-1 else 0)
        assert seconds<available-.7,(track,i,seconds,available)
        start=round(offset*rate);data[start:start+len(samples)]=samples
        segments.append({'chapter':i+1,'starts_at':round(offset,3),'speech_seconds':round(seconds,3),'available_seconds':round(available,3),'overlap':False})
        offset+=available
    wav=BASE/track/'narration.wav'
    with wave.open(str(wav),'wb') as w:w.setparams((1,2,rate,0,'NONE','not compressed'));w.writeframes(data.tobytes())
    target=BASE/track/'natural-voice.mp4'
    subprocess.run([FFMPEG,'-v','error','-y','-i',str(original),'-i',str(wav),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k','-af','loudnorm=I=-18:TP=-1.5:LRA=9','-t',str(duration),'-movflags','+faststart',str(target)],check=True)
    decoded=subprocess.run([FFMPEG,'-v','error','-i',str(target),'-f','null','-'],capture_output=True,text=True)
    assert decoded.returncode==0 and not decoded.stderr,decoded.stderr
    shutil.copy2(target,video)
    report.append({'track':track,'duration_seconds':duration,'voice':'zh-CN-XiaoxiaoNeural','synthesized':True,'video_stream':'copied without re-encoding','decode_errors':[],'chapters':segments})
(ROOT/'artifacts/natural-voice-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf8')
print(json.dumps([{'track':r['track'],'duration':r['duration_seconds'],'chapters':len(r['chapters'])} for r in report]))
