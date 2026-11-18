"""Optional password protection for an isolated reviewer instance."""
import os,secrets
from fastapi.responses import HTMLResponse,JSONResponse,RedirectResponse

async def protect(request,call_next):
    token=os.environ.get('PUBLIC_REVIEW_TOKEN','')
    if not token:return await call_next(request)
    if request.url.path=='/review':
        if request.method=='POST':
            form=await request.form()
            if secrets.compare_digest(str(form.get('password','')),token):
                response=RedirectResponse('/',status_code=303)
                response.set_cookie('scholar_review',token,httponly=True,secure=True,samesite='strict',max_age=86400)
                response.headers['Referrer-Policy']='no-referrer'
                return response
        return HTMLResponse('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>知研评审入口</title><body style="background:#eef3ef;color:#183b44;font:18px system-ui;max-width:560px;margin:12vh auto;padding:24px"><h1>知研 · 评审入口</h1><p>曲珈莹 · 云南大学 · A 组</p><form method="post"><label>评审口令 <input type="password" name="password" required autocomplete="current-password" style="padding:12px"></label><button style="padding:12px">进入工作台</button></form><p>演示数据独立保存；模型在作者电脑运行。</p></body></html>')
    supplied=request.cookies.get('scholar_review','')
    bearer=request.headers.get('authorization','').removeprefix('Bearer ')
    if not(secrets.compare_digest(supplied,token) or secrets.compare_digest(bearer,token)):
        return JSONResponse({'detail':'请先进入评审登录页'},status_code=401) if request.url.path.startswith('/api/') else RedirectResponse('/review')
    # Keep the public sample library intact. Generation and CSV evaluation remain available.
    if request.method=='DELETE' or (request.method=='POST' and (request.url.path=='/api/documents' or request.url.path.endswith(('/parse','/index','/resolve-duplicate')) or request.url.path=='/api/discover/import')):
        return JSONResponse({'detail':'公共评审实例保护示例库；完整导入、索引与删除可在本地复现'},status_code=403)
    response=await call_next(request)
    response.headers['Cache-Control']='no-store'
    return response
