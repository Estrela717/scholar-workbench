# 自然配音与赛道文档制作

两段视频使用通用普通话神经语音 `zh-CN-XiaoxiaoNeural`，不是参赛者本人录音或声音克隆。画面保留“合成配音”提示。较原SAPI版本，讲稿改成更短的口语句子，使用正常句读与停顿；语速设置为-5%，响度目标-18 LUFS，峰值目标-1.5 dBTP。

文本到语音使用Microsoft Edge在线语音服务，用户已明确授权发送演示讲稿。此制作工具与科研助手的本地推理分离，不影响应用离线解析和模型问答。工具依赖单列在`tools/requirements-voice.txt`，不增加应用运行依赖。

1. `tools/narration_natural.json`保存两赛道各12段讲稿。
2. `tools/narrate_natural.py`生成语音，音频保存在被Git忽略的`artifacts/voice-natural`。
3. `tools/replace_narration.py`按录制章节分配音轨，检查每段不超过可用时间；原视频流直接复制，替换音轨并统一响度。
4. `tools/validate_media.py`验证1080p、时长、音视频编码与完整解码。

旧配音视频保留在`output/history/voice-sapi`，旧技术PDF保留在`output/history/before-track-revision`。交付入口只指向新版。生成工具依据：[edge-tts项目](https://github.com/rany2/edge-tts)、[Microsoft语音支持文档](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts)。

文档由`tools/submission_content.py`分别定义内容，`tools/build_submission_docs.py`生成PDF与可编辑原稿。页数、章节对应和30页上限自动校验；最终使用Poppler渲染逐页检查。
