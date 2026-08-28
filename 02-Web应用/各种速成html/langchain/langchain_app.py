"""
LangChain 智能客服实战系统（真实调用大模型）
==========================================
- 模型：通过 OpenRouter 调用（默认 openrouter/free，可在 .env 修改）
- 架构：ChatOpenAI + ConversationBufferMemory（记忆）
        + @tool get_product_price（工具） + AgentExecutor（Agent）
- 运行：pip install -r requirements.txt  ->  python langchain_app.py

说明：免费模型对「工具调用」支持不一定稳定，因此系统提示词里也内置了
价格表作为兜底——即便模型不调用工具，也能靠上下文正确回答价格问题。
"""

import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, SystemMessage

# Windows + Python 3.8 默认 stdout 编码可能是 ascii，强制 utf-8，避免中文打印触发 ascii 报错
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")

# 产品知识库（与教程一致）
PRODUCTS = {
    "智能水杯": {"price": 299, "info": "智能水杯是我们的热门产品，内置温度传感器与蓝牙模块，可通过手机 APP 管理饮水数据。",
                "features": "主要功能：① 实时温度显示 ② 智能饮水提醒 ③ APP 数据同步 ④ 长效续航。"},
    "无线耳机": {"price": 499, "info": "无线耳机主打主动降噪与长续航，适合通勤与运动场景。",
                "features": "主要功能：① 主动降噪 ② 30 小时续航 ③ 低延迟游戏模式 ④ 双设备连接。"},
    "运动手环": {"price": 199, "info": "运动手环轻巧防水，是入门级健康追踪的好帮手。",
                "features": "主要功能：① 心率监测 ② 睡眠分析 ③ 50 米防水 ④ 14 天超长续航。"},
    "智能手表": {"price": 899, "info": "智能手表为旗舰款，支持独立通话与精准定位。",
                "features": "主要功能：① AMOLED 高清屏 ② GPS 定位 ③ 血氧检测 ④ 独立通话。"},
}

# ========== 真正的 Tool：查询价格 ==========
@tool
def get_product_price(product_name: str) -> str:
    """查询产品价格。输入产品名称（如『智能水杯』），返回该产品的精确价格。
    当用户询问某款产品的价格、报价或两款产品的差价时，都应调用本工具。"""
    for key in PRODUCTS:
        if key in product_name:
            return f"{key} 的价格是 ¥{PRODUCTS[key]['price']}"
    return f"抱歉，未找到「{product_name}」的价格信息。可用产品：{'、'.join(PRODUCTS.keys())}。"


# ========== 大模型（OpenRouter 是 OpenAI 兼容接口） ==========
llm = ChatOpenAI(
    model=MODEL,
    api_key=API_KEY,
    base_url="https://openrouter.ai/api/v1",
    temperature=0,
    max_tokens=600,
    default_headers={
        "HTTP-Referer": "https://langchain-demo.local",
        "X-Title": "LangChain Customer Service Demo",
    },
)

SYSTEM_PROMPT = """你是一个电子产品的智能客服助手，服务一家电子产品公司。
请用简体中文、友好专业的语气回答用户关于【产品功能】和【价格】的问题。
已知产品与价格（如工具不可用，也可据此回答）：
- 智能水杯 ¥299
- 无线耳机 ¥499
- 运动手环 ¥199
- 智能手表 ¥899
当用户问到价格时，优先调用 get_product_price 工具获取精确价格再作答；
涉及两款产品比价时，分别调用工具后计算差价。
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

agent = create_tool_calling_agent(llm=llm, tools=[get_product_price], prompt=prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=[get_product_price],
    memory=memory,
    verbose=False,  # Python 3.8 + langchain 0.2.17 下 verbose=True 会触发 StdOutCallbackHandler 回调 AttributeError bug；升级到 Python 3.11 后可改回 True 看思考链
    handle_parsing_errors=True,
    max_iterations=5,
)


def fallback_reply(user_input: str) -> str:
    """工具调用不可用时，直接用 LLM + 上下文兜底，保证仍能看到效果。"""
    history = memory.load_memory_variables({})["chat_history"]
    msgs = [SystemMessage(content=SYSTEM_PROMPT)] + list(history) + [HumanMessage(content=user_input)]
    try:
        return llm.invoke(msgs).content
    except Exception as e:
        return f"（调用大模型失败：{e}）"


def main():
    print("=" * 52)
    print("🦜 LangChain 智能客服系统（真实大模型）")
    print(f"   模型：{MODEL}  |  接口：OpenRouter")
    print("   输入消息开始对话；输入 exit / quit 退出。")
    print("=" * 52)
    while True:
        try:
            q = input("\n[用户] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            continue
        if q.lower() in ("exit", "quit", "q"):
            print("👋 再见！")
            break
        try:
            result = agent_executor.invoke({"input": q})
            print(f"\n[客服] {result['output']}")
        except Exception as e:
            print(f"\n[系统] Agent 工具调用异常，启用兜底回答：{e}")
            ans = fallback_reply(q)
            memory.save_context({"input": q}, {"output": ans})
            print(f"\n[客服] {ans}")


if __name__ == "__main__":
    main()
