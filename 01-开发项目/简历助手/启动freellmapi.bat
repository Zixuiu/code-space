@echo off
cd /d D:\codespace\05-开源项目\freellmapi
if not exist node_modules (
  echo 首次启动，正在安装依赖（约几分钟，请耐心等待）...
  call npm install
)
echo 正在启动 FreeLLMAPI 网关（开发模式）...
start "FreeLLMAPI" cmd /k "npm run dev"
echo.
echo ============================================================
echo  [OK] 网关已在后台窗口启动，接下来只做一次：
echo    1) 浏览器打开 http://localhost:5173  （管理后台）
echo    2) 在 Keys / Provider 页粘贴至少一家【免费】key
echo       推荐：Google AI Studio 的 Gemini（免绑卡，额度最大方）
echo       备选：Groq / Mistral / OpenRouter / 智谱 / Kimi（均免费）
echo    3) 复制 Keys 页生成的统一密钥  freellmapi-xxxx
echo    4) 粘贴到 config.json 的 llm.api_key（config.json 与本 bat 同目录）
echo    5) 双击“简历助手-免费LLM.bat”即可免费真 LLM 打分
echo.
echo  想确认网关是否就绪：浏览器访问 http://localhost:3001/v1/models
echo ============================================================
echo.
pause
