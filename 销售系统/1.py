import streamlit as st
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# ================= 1. 模拟数据生成 =================
def generate_customer_data(n=200):
    np.random.seed(42)
    data = {
        '客户ID': [f'C{1000+i}' for i in range(n)],
        '最近购买天数': np.random.randint(1, 365, n),
        '购买频次': np.random.randint(1, 20, n),
        '平均消费金额': np.random.uniform(100, 10000, n).round(2),
        '网站浏览时长(分)': np.random.randint(1, 120, n),
        '是否成交': np.random.choice([0, 1], n, p=[0.6, 0.4])
    }
    return pd.DataFrame(data)

def generate_sales_pipeline():
    return pd.DataFrame({
        '客户名称': ['科技A公司', '制造B集团', '零售C企业', '教育D机构', '医疗E中心'],
        '阶段': ['线索', '沟通', '报价', '谈判', '成交'],
        '预计金额(万)': [50, 120, 80, 200, 150],
        '赢单概率(%)': [10, 30, 60, 80, 100]
    })

# ================= 2. 页面布局与路由 =================
st.set_page_config(page_title="智能销售系统", layout="wide")
st.title("🚀 智能销售系统")

menu = ["📊 销售流程看板", "🤖 AI 客户分析", "🎭 常见销售场景", "📚 销售知识库"]
choice = st.sidebar.selectbox("选择功能模块", menu)

# ================= 3. 功能模块实现 =================

if choice == "📊 销售流程看板":
    st.header("销售流程管理")
    st.markdown("管理从线索到成交的全生命周期，提升转化率。")
    
    pipeline_data = generate_sales_pipeline()
    
    # 漏斗分析
    st.subheader("销售漏斗预测")
    stages = ['线索', '沟通', '报价', '谈判', '成交']
    stage_values = [pipeline_data[pipeline_data['阶段']==s]['预计金额(万)'].sum() for s in stages]
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.dataframe(pipeline_data, use_container_width=True)
    with col2:
        fig, ax = plt.subplots()
        ax.barh(stages[::-1], stage_values[::-1], color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
        ax.set_xlabel('预计金额 (万)')
        ax.set_title('各阶段金额池')
        st.pyplot(fig)

    st.markdown("### 操作面板")
    with st.form("add_lead"):
        st.write("新增销售线索")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            new_comp = st.text_input("客户名称")
        with col_b:
            new_amt = st.number_input("预计金额(万)", min_value=0)
        with col_c:
            new_stage = st.selectbox("当前阶段", stages)
        submitted = st.form_submit_button("提交线索")
        if submitted:
            st.success(f"线索 {new_comp} 已成功录入！")

elif choice == "🤖 AI 客户分析":
    st.header("AI 客户分析引擎")
    st.markdown("利用机器学习对客户进行分群，识别高价值客户与潜在流失风险。")
    
    df = generate_customer_data()
    
    st.subheader("客户数据概览")
    st.dataframe(df.head(10), use_container_width=True)
    
    st.subheader("AI 客户分群 (K-Means 聚类)")
    feature_cols = ['最近购买天数', '购买频次', '平均消费金额']
    X = df[feature_cols]
    
    # 模型训练
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['客户群体'] = kmeans.fit_predict(X)
    
    # 群体定义映射 (根据聚类中心动态定义，此处简化)
    cluster_map = {0: '高价值沉睡客户', 1: '低价值活跃客户', 2: '高价值活跃客户'}
    df['客户标签'] = df['客户群体'].map(cluster_map)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.write("### 客户分群结果")
        st.dataframe(df[['客户ID', '最近购买天数', '购买频次', '平均消费金额', '客户标签']].head(20), use_container_width=True)
        
    with col2:
        st.write("### 群体分布可视化")
        fig, ax = plt.subplots()
        scatter = ax.scatter(df['购买频次'], df['平均消费金额'], c=df['客户群体'], cmap='viridis')
        ax.set_xlabel('购买频次')
        ax.set_ylabel('平均消费金额')
        ax.set_title('客户分群散点图')
        st.pyplot(fig)
        
    st.info("💡 **AI建议**：针对'高价值沉睡客户'，建议立即触发挽回营销活动；针对'低价值活跃客户'，建议进行交叉销售提升客单价。")

elif choice == "🎭 常见销售场景":
    st.header("常见销售场景与应对策略")
    
    scenarios = {
        "价格异议": {
            "场景描述": "客户表示你们的产品比竞品贵，要求降价。",
            "应对策略": "1. 价值重塑：不要单纯比价格，对比总体拥有成本(TCO)和隐性成本。\n2. 分解成本：将价格分解到每天/每个使用人次，凸显性价比。\n3. 让步条件：如果必须降价，要求交换条件（如：预付款、增购模块）。",
            "话术模板": "王总，我理解您对预算的关注。单纯看报价，我们确实高一些。但如果算上我们系统为您节省的20%运维时间和后续0成本的升级服务，三年下来您的总成本其实是更低的。如果您这边能确认本周签约，我可以帮您申请一个VIP培训名额作为补偿，您看如何？"
        },
        "竞品比较": {
            "场景描述": "客户正在考虑竞争对手的产品，并询问你们的差异。",
            "应对策略": "1. 承认竞品：不要恶意贬低竞品，展现自信。\n2. 突出差异化：强调我们在核心功能、服务响应速度或行业深耕上的优势。\n3. 提供证明：提供同行业成功案例作为背书。",
            "话术模板": "X公司的确是个优秀的同行。不过，在您所在的制造行业，我们有超过50家的成功实施经验，这是他们目前不具备的。我们的算法更贴合车间的实际情况，您要不要看看我们给同行业Y公司做的数据对比？"
        },
        "决策拖延": {
            "场景描述": "客户对产品认可，但一直拖延不做最终决定。",
            "应对策略": "1. 制造紧迫感：限时优惠、库存紧张、政策变动等。\n2. 挖掘真实原因：是否预算未批、内部有分歧？\n3. 描绘痛点：拖延上线每天造成的损失量化。",
            "话术模板": "李总，早一天上线系统，您部门每天就能少加2个小时的班处理手工报表。另外，本月底我们的老客户续费补贴政策就截止了，下个月恢复原价差了将近2万块。咱们是不是可以把流程往前推一推？"
        }
    }
    
    selected_scenario = st.selectbox("请选择销售场景", list(scenarios.keys()))
    
    if selected_scenario:
        info = scenarios[selected_scenario]
        st.subheader(f"🎯 {selected_scenario}")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**场景描述**")
            st.info(info['场景描述'])
            st.markdown("**应对策略**")
            st.warning(info['应对策略'])
        with col2:
            st.markdown("**参考话术**")
            st.success(info['话术模板'])

elif choice == "📚 销售知识库":
    st.header("销售知识库")
    
    tab1, tab2, tab3 = st.tabs(["📖 产品知识", "🗣️ 话术库", "❓ 常见Q&A"])
    
    with tab1:
        st.subheader("产品核心卖点")
        products = {
            "智能CRM标准版": "面向中小企业，涵盖客户管理、跟进记录、基础报表。",
            "智能CRM专业版": "面向中大型企业，包含AI客户画像、销售预测、自动化工作流。",
            "智能CRM旗舰版": "面向集团企业，支持定制化开发、私有化部署、BI大屏看板。"
        }
        for prod, desc in products.items():
            with st.expander(f"📦 {prod}"):
                st.write(desc)
                
    with tab2:
        st.subheader("开场白话术")
        opening_lines = [
            "您好，王总。我是[公司名]的小张。了解到贵司最近在扩张业务线，想跟您探讨一下如何提升新团队的成单效率，您现在方便接听电话吗？",
            "李总您好，关注到贵司公众号发布了新品，恭喜！我们专门为新品发布提供了一套营销转化方案，想给您发一份案例参考，可以加个微信吗？"
        ]
        for i, line in enumerate(opening_lines):
            st.text_area(f"话术 {i+1}", value=line, height=100, key=f"opening_{i}")
            
    with tab3:
        st.subheader("客户常见问题解答")
        qa_data = pd.DataFrame({
            '问题': ['系统实施周期多长？', '数据安全如何保障？', '是否支持移动端？'],
            '标准答案': ['标准版1周上线，专业版根据定制需求一般2-4周。', '我们采用阿里云/腾讯云金融级加密，且支持私有化部署。', '支持，我们提供完整的APP和微信小程序端。']
        })
        st.table(qa_data)
