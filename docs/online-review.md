# 评审入口的运行与恢复

当前地址及状态见 `submission-2026-11-18.md`。评审口令保存在被 Git 忽略的 `runtime/review-credentials.json`，另附私有访问说明。请勿把口令写入公开 issue、README 或 commit。

本机组成：Ollama 11434，个人工作台 8765，独立样例评审实例 8766，cloudflared HTTPS 隧道。个人数据目录 `data` 与评审数据目录 `data-judge` 分离。公网请求需要口令，评审模式禁止增删库内 PDF 和重建索引；仍允许问答、翻译、草稿、图表和追踪。

1. 保持电脑唤醒、Ollama 与网络可用。
2. 双击 `start-online.cmd`。脚本使用隐藏窗口启动后台服务；如果评审服务和隧道已经运行，不重复启动。
3. 从 `runtime/cloudflared.log` 最后一段读取 `https://...trycloudflare.com` 地址，在末尾加 `/review`。
4. 重新启动隧道可能更换域名。务必同时更新赛事平台地址和评审访问说明，并从外网验证口令登录。
5. 普通本地应用使用 `start.cmd`，不需要评审口令。

这台机器已经准备 cloudflared。新机器可从 [Cloudflare 官方发布页](https://github.com/cloudflare/cloudflared/releases) 下载 Windows amd64 程序放入 `.cache/cloudflared.exe`，先完成模型、依赖、样例准备；`prepare_review.py` 当前按本项目验收样例 ID 创建独立副本，应先核对样例存在，不能在任意个人文献库上盲目执行。

终止公开访问可在任务管理器结束本项目的 cloudflared.exe。不要随意结束其他应用的同名进程。隧道关闭后本地 8765 仍可使用。

临时隧道不保证跨日在线，也不是稳定服务器。若主办方要求长期可访问，需要另行准备持久托管环境与有效域名，迁移后复测。
