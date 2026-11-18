"""Create an isolated, password-protected public sample workspace."""
import json,secrets,sqlite3,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
target=ROOT/'data-judge';target.mkdir(exist_ok=True);(target/'files').mkdir(exist_ok=True)
selected=['60d4185358b54b60a2e4c2a3282319f9','1797e6341fa44b17850e410df2e97df8','08a2c1b5811d4371894da6f15eed25d6','cb6634f45cd04076bf3b07d6c975308f','33fa7f7868ae455590421ac491c51c20']
with sqlite3.connect(ROOT/'data/library.sqlite3') as source,sqlite3.connect(target/'library.sqlite3') as dest:
    source.backup(dest);dest.execute('PRAGMA foreign_keys=ON')
    dest.execute('DELETE FROM documents WHERE id NOT IN ('+','.join('?'*len(selected))+')',selected)
    for table in ('notes','activity','settings','translation_jobs','tracking_topics','discoveries'):dest.execute('DELETE FROM '+table)
for key in selected:shutil.copyfile(ROOT/'data/files'/f'{key}.pdf',target/'files'/f'{key}.pdf')
runtime=ROOT/'runtime';runtime.mkdir(exist_ok=True)
credentials=runtime/'review-credentials.json'
if not credentials.exists():credentials.write_text(json.dumps({'password':secrets.token_urlsafe(18)},ensure_ascii=False),encoding='utf8')
print('Isolated reviewer dataset prepared; credentials remain in ignored runtime directory.')
