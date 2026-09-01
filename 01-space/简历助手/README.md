# 简历助手（Coze 驱动的简历匹配打分工具）

把岗位要求给进去，把简历 PDF 丢进文件夹，双击运行，自动产出按匹配度排名的打分报告（含匹配点 / 不匹配点 / 建议）。

## 一键运行
双击 **`简历助手.bat`**。首次会自动建虚拟环境并安装依赖（需要联网装 `pypdf`）。

## 使用步骤
1. 编辑 **`岗位要求.txt`**，粘贴你的岗位要求（越具体打分越准）。
2. 把要筛选的简历 PDF 放进 **`简历/`** 文件夹。
3. 双击 **`简历助手.bat`**。
4. 自动打开 **`简历匹配报告.html`**，按匹配度从高到低排列，红字标出不匹配/不足点。

## Coze 接入（推荐，专业评估）
没配置 Coze 时，应用会用「本地关键词重叠」做粗评（仅供演示）。
要获得专业匹配分析，接入 Coze：
1. 按 **`coze_workflow_spec.md`** 在扣子平台搭建并发布「简历匹配打分助手」工作流（约 2 分钟，提示词在 `coze_workflow_prompt.txt`）。
2. 申请个人访问令牌（PAT，`pat_` 开头，勾选工作流执行权限）。
3. 把 `workflow_id` 和 PAT 填进 **`config.json`** 的 `workflow_id` / `coze_api_token`。
4. 重新双击 `简历助手.bat`。

## 文件说明
- `run.py`：主程序（读岗位要求 + 扫 PDF + 调 Coze + 生成报告）
- `coze_api.py`：Coze 工作流调用 + 本地兜底打分
- `pdf_reader.py`：PDF 文本抽取
- `config.json`：Coze 地址 / 令牌 / 文件夹路径配置
- `coze_workflow_spec.md` / `coze_workflow_prompt.txt` / `resume-matcher.workflow.yaml`：补齐的 Coze 工作流资产
- `简历匹配报告.html`：运行产物

## 设计说明
Coze 云平台读不到你电脑的本地文件夹，因此「扫描简历 PDF」必须由本地应用完成，再把文本传给 Coze 工作流打分。这是这套方案的分层原因。
