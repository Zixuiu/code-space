# 用 FreeLLMAPI 给简历助手接上「免费真 LLM」

之前纠结的 Coze / PAT / 付费 key 全都不需要了。FreeLLMAPI 是一个**本地网关**，
把各家大模型的「免费额度」聚合成一个 OpenAI 兼容端点。简历助手已经内置 OpenAI
兼容调用，只要指向它，就能**零费用、真 LLM 读简历、数据不出机**。

## 一、FreeLLMAPI 的「免费额度」到底是什么

FreeLLMAPI 自己**不发**额度，它只做「聚合 + 路由」：

- 你去各家注册**免费** API Key（都不用绑卡）：Google AI Studio(Gemini)、Groq、
  Mistral、OpenRouter、GitHub Models、智谱、Kimi……
- 把这些 key 粘进 FreeLLMAPI 网页后台 → 它生成**一个统一密钥** `freellmapi-xxxx`
- 你所有程序只打 `http://localhost:3001/v1`，带这个统一 key，`model="auto"`，
  由它自动选当前最优可用模型 + 限流自动 failover（最多重试 20 次）

所以「免费」= 各家免费档的聚合；FreeLLMAPI 负责统一和兜底。

## 二、一次性准备（只需做一次）

1. 双击 `启动freellmapi.bat`
   - 首次会自动 `npm install`（几分钟）
   - 然后弹出后台窗口跑 `npm run dev`，并打开 http://localhost:5173
2. 在后台里添加至少一家 provider 的免费 key（推荐 Gemini，额度最大方）
3. 复制 Keys 页的统一密钥 `freellmapi-xxxx`
4. 打开 `config.json`，把 `llm.api_key` 改成那个统一密钥
   - `llm.base_url` 已默认为 `http://localhost:3001/v1`、`model` 为 `auto`，不用动

## 三、日常使用（每次都只需一步）

把 PDF 简历丢进 `简历/` → 编辑 `岗位要求.txt` → **双击 `简历助手-免费LLM.bat`**
→ 自动起网关 + 跑打分 + 打开带排名/差距高亮的 `简历匹配报告.html`。

## 四、性能与限制（实话）

- 免费模型多为 Gemini-Flash / Llama-3.3-70B / DeepSeek 档，做「简历匹配打分」完全够用；
  比付费 GPT/Claude 略弱，但远强于本地启发式规则。
- 免费档有速率限制（如 Gemini 10 rpm），FreeLLMAPI 会自动换可用模型；简历很多时
  可能稍慢，属正常。
- 只支持文本 + tool call，不支持图片/embedding（简历是 PDF 文本，不受影响）。
- 网关必须保持运行（那个后台窗口别关）。关了简历助手会自动回退到本地启发式并提示。

## 五、不想用 FreeLLMAPI 也行

`config.json` 的 `llm` 段换成任意 OpenAI 兼容服务即可：
- 本机 Ollama（零账号零费用）：`base_url=http://localhost:11434/v1`、`api_key` 随便填、
  `model=qwen2.5:7b`（需先 `ollama pull`）
- 付费 DeepSeek：`base_url=https://api.deepseek.com/v1`、`api_key=sk-xxx`、`model=deepseek-chat`

Coze 云工作流的资产（`coze_workflow_*.md` / `resume-matcher.*`）现在用不到了，留着无害。
