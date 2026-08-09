"""FDE 实战：带工具调用的 LangChain Agent（可直接跑，需 pip install langchain langchain-openai python-dotenv）"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()
llm = ChatOpenAI(base_url="https://openrouter.ai/api/v1",
                 api_key=os.getenv("OPENROUTER_API_KEY"),
                 model=os.getenv("OPENROUTER_MODEL", "openrouter/free"))

PRICES = {"智能水杯": 299, "无线耳机": 499, "运动手环": 199, "智能手表": 899}

@tool
def get_product_price(name: str) -> int:
    """返回指定产品的价格（元）"""
    return PRICES.get(name, -1)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是智能客服，能用工具查价格并算差价。"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])
agent = create_tool_calling_agent(llm, [get_product_price], prompt)
exe = AgentExecutor(agent=agent, tools=[get_product_price], verbose=True)
print(exe.invoke({"input": "智能手表比运动手环贵多少？"})["output"])
