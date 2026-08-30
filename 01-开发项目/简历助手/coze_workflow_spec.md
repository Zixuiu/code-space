# 简历匹配打分工作流（Coze / 扣子）构建说明

本文件补齐「简历助手」所需的全部 Coze 配置。两种用法任选其一：
- **A. 云平台 UI 搭建（推荐，所有套餐可用）**：照下面步骤在 coze.cn 画布里拼 3 个节点，把提示词复制进去即可。
- **B. coze-studio 自托管导入**：用同目录 `resume-matcher.workflow.yaml`（按官方 DSL 写），在自托管 coze-studio 里导入。

---

## A. 在扣子云平台搭建（约 2 分钟）

1. 进入 **扣子** → 你的工作空间 → **资源库** → **工作流** → **新建工作流**，名称填 `简历匹配打分助手`。
2. **开始节点**：添加两个输入参数
   - `job_requirements`（文本 / String，必选）—— 描述：岗位要求
   - `resume_text`（文本 / String，必选）—— 描述：简历纯文本
3. 拖一个 **大模型节点**，连线 `开始 → 大模型`：
   - 模型：豆包·工具调用（或任意支持稳定输出的模型）
   - 温度：`0.2`
   - **输入**：添加 `job_requirements`、`resume_text`，分别「引用」开始节点对应的输出
   - **系统提示词**：直接复制 `coze_workflow_prompt.txt` 全文粘贴（含 `{{job_requirements}}` `{{resume_text}}` 变量）
4. 拖一个 **结束节点**，连线 `大模型 → 结束`：
   - 返回方式：**返回变量**
   - 添加输出变量 `result`（文本 / String），引用大模型节点的输出
5. **试运行**：`job_requirements` 填一段岗位要求，`resume_text` 填一段简历文本，确认输出是合规 JSON（含 score / level / gap_points 等）。
6. 点击 **发布**。发布后从浏览器地址栏 `workflow_id=` 后面复制那串数字。
7. 把该 `workflow_id` 和你的个人访问令牌填进 `简历助手/config.json`。

### 个人访问令牌（PAT）
左下角头像 → **API** → **授权** → **个人访问令牌** → 新建，勾选「工作流执行」权限。令牌以 `pat_` 开头，只显示一次，妥善保存。

---

## 本地应用如何调用它

`简历助手/coze_api.py` 通过 `POST {coze_api_base}/v1/workflow/run` 调用：
- Header：`Authorization: Bearer <PAT>`、`Content-Type: application/json`
- Body：`{"workflow_id": "...", "parameters": {"job_requirements": "...", "resume_text": "..."}}`
- 返回 `data` 为 JSON 字符串，本地解析成结构化结果用于打分报告。

> 说明：Coze 云平台读不到你电脑本地文件夹，所以「扫描简历 PDF 文件夹」这一步必须由本地 `简历助手.bat` 完成，再把文本传给 Coze 工作流。这正是本套方案的分层设计。

---

## B. coze-studio 自托管（可选）

`resume-matcher.workflow.yaml` 是官方工作流 DSL（schema_version 1.0.0）。在自托管 coze-studio 中通过「导入」载入即可；导入后需把开始节点两个参数、大模型系统提示词（同 prompt 文件）核对一遍，并发布得到 workflow_id。
（注：扣子云平台的「工作流导入」为付费功能；免费套餐请用上面的 A 方案手动搭建。）

---

## C. 源码核验（基于本地 coze-studio 仓库）

我对照了本地拉下来的 coze-studio 源码，确认以下事实，保证本工作流资产与官方实现一致：

- **运行接口**（两种部署通用）：`backend/api/router/coze/api.go:533` 注册 `POST /v1/workflow/run` → `OpenAPIRunFlow`；
  同文件 `:535` 还有 `/v1/workflow/stream_run`。**自托管 coze-studio 与 coze.cn 云用的是同一路径**。
  → 本地应用 `coze_api.py` 里只要把 `config.json` 的 `coze_api_base` 改成你自托管地址（如 `http://127.0.0.1:8888`），
  其余不用改即可打本地实例。
- **节点类型**（画布内部用数字，见 `frontend/.../sdk/__tests__/__mock_data__/canvas-schema.ts`）：
  `1`=开始、`3`=大模型、`2`=结束、`5`=代码。导出 DSL（YAML）用 `start/llm/end` 关键词。
- **提示词变量语法**：大模型节点系统提示词里用 `{{job_requirements}}` / `{{resume_text}}` 引用开始节点输出；
  `llmParam.responseFormat = 2` 表示 JSON 结构化输出。
- **入参/出参**：开始节点两个 `string` 输出（`job_requirements`、`resume_text`）；大模型节点输出 `output`(string)；
  结束节点 `returnVariables` 返回 `result`。

### 本目录下的两份工作流资产
- `resume-matcher.workflow.yaml`：**导出 DSL 格式**（schema_version 1.0.0），按官方文档的导入标准编写，
  可用于「导出/导入」ZIP 包导入（云平台付费功能 / 自托管均可用）。
- `resume-matcher.canvas.json`：**画布内部格式**（与源码 `canvas-schema.ts` 完全一致），
  用于通过 `workflow_api/save` 等内部接口直接注入自托管实例，或二次开发/自动化生成工作流。
  注意：它不是 ZIP 导入格式，别拿去走「导入」按钮。

### 想 100% 本地跑（不依赖 coze.cn）
如果你用本地 coze-studio 自托管，整条链路可完全离线：
1. 按 coze-studio 官方文档 `docker compose up` 起后端 + 前端（依赖 PostgreSQL / Redis / Elasticsearch / MinIO / ETCD 等）。
2. 在本地前端里用 A 方案搭好工作流并发布，或用 `resume-matcher.canvas.json` 通过 `workflow_api/save` 注入。
3. `config.json` 的 `coze_api_base` 改成自托管 API 地址、`coze_api_token` 用自托管的鉴权令牌，
   本地 `简历助手.bat` 即可完全本地调用，简历数据不出本机。
