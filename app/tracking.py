"""Durable, in-app periodic research tracking. No external messages are sent."""
import json,threading,time
from .db import connect,now,record
from .research import arxiv_search

RUN_LOCK=threading.Lock()

def refresh_due(force=False):
    if not RUN_LOCK.acquire(blocking=False):
        return {'busy':True,'topics':0,'new':0}
    checked=added=0
    try:
        with connect() as db:
            topics=[dict(x) for x in db.execute('SELECT * FROM tracking_topics WHERE enabled=1 AND (next_run<=? OR ?)',(time.time(),int(force)))]
        for item in topics:
            # Persist the lease before accessing the network; avoid tight retries.
            with connect() as db:
                db.execute('UPDATE tracking_topics SET next_run=? WHERE topic=?',(time.time()+item['interval_hours']*3600,item['topic']))
            try:
                results=arxiv_search(item['topic'],limit=12,newest=True)
                count=0
                with connect() as db:
                    for result in results:
                        count+=db.execute('INSERT OR IGNORE INTO discoveries(topic,arxiv_id,payload,found_at) VALUES(?,?,?,?)',
                            (item['topic'],result['id'],json.dumps(result,ensure_ascii=False),now())).rowcount
                    db.execute("UPDATE tracking_topics SET last_run=?,error='' WHERE topic=?",(now(),item['topic']))
                added+=count;checked+=1
                if count:record('discover',f'自动追踪 {item["topic"]}：发现 {count} 篇新记录')
            except Exception as error:
                with connect() as db:
                    db.execute('UPDATE tracking_topics SET error=?,next_run=? WHERE topic=?',
                        (str(error)[:240],time.time()+900,item['topic']))
        return {'busy':False,'topics':checked,'new':added}
    finally:RUN_LOCK.release()

def loop(stop):
    while not stop.wait(30):
        refresh_due()

def snapshot():
    with connect() as db:
        topics=[dict(r) for r in db.execute('SELECT * FROM tracking_topics ORDER BY topic')]
        rows=db.execute('SELECT * FROM discoveries ORDER BY found_at DESC LIMIT 150').fetchall()
    return {'topics':topics,'results':[{**json.loads(r['payload']),'topic':r['topic'],'found_at':r['found_at'],'is_new':bool(r['is_new'])} for r in rows]}
