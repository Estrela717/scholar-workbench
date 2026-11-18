"""Render authorized narration with a generic Microsoft neural Mandarin voice.

Only the text in narration_natural.json is sent to the speech service.
Audio stays in ignored artifacts/voice-natural; no keys are needed.
"""
import asyncio,json,os,subprocess,wave
from pathlib import Path
import edge_tts

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'artifacts/voice-natural';OUT.mkdir(exist_ok=True)
FFMPEG=os.environ.get('FFMPEG_EXE','D:/Software/miniconda/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe')
manifest=json.loads((ROOT/'tools/narration_natural.json').read_text('utf8'))

async def main():
    semaphore=asyncio.Semaphore(2)
    async def render(track,i,text):
        folder=OUT/track;folder.mkdir(exist_ok=True)
        mp3=folder/f'{i:02d}.mp3';wav=folder/f'{i:02d}.wav'
        async with semaphore:
            for attempt in range(3):
                try:
                    await edge_tts.Communicate(text,manifest['voice'],rate=manifest['rate'],proxy=os.environ.get('TTS_PROXY')).save(str(mp3))
                    break
                except Exception:
                    if attempt==2:raise
                    await asyncio.sleep(2*(attempt+1))
            subprocess.run([FFMPEG,'-v','error','-y','-i',str(mp3),'-ac','1','-ar','24000','-c:a','pcm_s16le',str(wav)],check=True)
            with wave.open(str(wav)) as w:seconds=w.getnframes()/w.getframerate()
            print(json.dumps({'track':track,'chapter':i+1,'seconds':round(seconds,2)},ensure_ascii=False),flush=True)
            return {'track':track,'index':i,'seconds':seconds,'text':text}
    rows=await asyncio.gather(*(render(track,i,text) for track in ('innovation','llm') for i,text in enumerate(manifest[track])))
    (OUT/'generation.json').write_text(json.dumps({'voice':manifest['voice'],'rate':manifest['rate'],'chapters':rows},ensure_ascii=False,indent=2),'utf8')

if __name__=='__main__':asyncio.run(main())
