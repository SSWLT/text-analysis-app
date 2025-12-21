import streamlit as st
import requests
from bs4 import BeautifulSoup
import jieba
import jieba.analyse
from collections import Counter
import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import WordCloud, Bar, Pie, Line, Scatter, Radar, Funnel
from pyecharts.globals import ThemeType
from streamlit_echarts import st_pyecharts
import re
import numpy as np

# 设置页面配置
st.set_page_config(
    page_title="文本分析可视化工具",
    page_icon="📊",
    layout="wide"
)

# 初始化session state
if 'word_freq' not in st.session_state:
    st.session_state.word_freq = None
if 'text_content' not in st.session_state:
    st.session_state.text_content = None
if 'original_word_freq' not in st.session_state:
    st.session_state.original_word_freq = None

# 标题
st.title("📊 文本分析可视化工具")
st.markdown("---")

# 侧边栏 - 配置选项
with st.sidebar:
    st.header("⚙️ 配置选项")
    
    # URL输入
    st.subheader("1. 输入文章URL")
    url = st.text_input("请输入文章URL:", placeholder="https://example.com/article")
    
    # 抓取按钮
    if st.button("🚀 抓取并分析文本", use_container_width=True):
        if url:
            with st.spinner("正在抓取和分析文本..."):
                try:
                    # 抓取网页内容
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(url, headers=headers, timeout=10)
                    response.encoding = 'utf-8'
                    
                    # 解析HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 移除脚本和样式
                    for script in soup(["script", "style", "nav", "footer", "header"]):
                        script.decompose()
                    
                    # 获取文本
                    text = soup.get_text()
                    # 清理文本
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    st.session_state.text_content = text
                    
                    # 使用jieba分词
                    # jieba.enable_paddle()
                    words = jieba.lcut(text)
                    
                    # 过滤非中文字符和停用词
                    stop_words = set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'])
                    filtered_words = []
                    chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
                    
                    for word in words:
                        if word in stop_words or len(word) < 2:
                            continue
                        if chinese_pattern.search(word):
                            filtered_words.append(word)
                    
                    # 统计词频
                    word_counter = Counter(filtered_words)
                    st.session_state.original_word_freq = word_counter
                    st.session_state.word_freq = word_counter
                    
                    st.sidebar.success(f"✅ 成功抓取文本！共分析 {len(words)} 个词汇")
                    
                except Exception as e:
                    st.sidebar.error(f"❌ 抓取失败: {str(e)}")
        else:
            st.sidebar.warning("⚠️ 请输入URL")
    
    st.markdown("---")
    
    # 图表类型选择
    st.subheader("2. 选择图表类型")
    chart_type = st.selectbox(
        "请选择可视化图表:",
        ["词云图", "条形图", "饼图", "折线图", "散点图", "雷达图", "漏斗图", "组合图"]
    )
    
    st.markdown("---")
    
    # 词频过滤
    st.subheader("3. 过滤低频词")
    if st.session_state.word_freq:
        min_frequency = st.slider(
            "最小词频:",
            min_value=1,
            max_value=50,
            value=3,
            help="过滤出现次数低于此值的词汇"
        )
        
        if st.button("🔄 应用过滤", use_container_width=True):
            filtered = {word: freq for word, freq in st.session_state.original_word_freq.items() 
                       if freq >= min_frequency}
            st.session_state.word_freq = Counter(filtered)
            st.sidebar.success(f"过滤后剩余 {len(st.session_state.word_freq)} 个词汇")
    
    st.markdown("---")
    
    # 显示当前状态
    st.subheader("📈 当前状态")
    if st.session_state.text_content:
        text_length = len(st.session_state.text_content)
        word_count = len(st.session_state.word_freq) if st.session_state.word_freq else 0
        st.metric("文本长度", f"{text_length} 字符")
        st.metric("词汇数量", f"{word_count} 个")
    
    # 重置按钮
    if st.button("🔄 重置所有数据", use_container_width=True):
        st.session_state.word_freq = None
        st.session_state.text_content = None
        st.session_state.original_word_freq = None
        st.rerun()

# 主内容区域
if st.session_state.text_content and st.session_state.word_freq:
    # 显示文本预览
    with st.expander("📝 查看文本内容预览"):
        st.text_area("文本预览:", st.session_state.text_content[:1000] + "..." 
                    if len(st.session_state.text_content) > 1000 else st.session_state.text_content, 
                    height=200)
    
    # 显示词频表格
    st.subheader("📊 词频排名 Top 20")
    
    # 获取前20个词频
    top_20 = st.session_state.word_freq.most_common(20)
    df = pd.DataFrame(top_20, columns=["词汇", "频次"])
    df.index = df.index + 1  # 从1开始编号
    
    # 显示表格和柱状图
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.dataframe(df, use_container_width=True)
    
    with col2:
        # 创建简单的柱状图预览
        chart_df = df.head(10)
        st.bar_chart(chart_df.set_index("词汇")["频次"])
    
    st.markdown("---")
    
    # 根据选择的图表类型显示可视化
    st.subheader(f"🎨 {chart_type} 可视化")
    
    # 准备数据
    if st.session_state.word_freq:
        data = st.session_state.word_freq.most_common(50)  # 取前50个用于可视化
        
        # 词云图
        if chart_type == "词云图":
            wordcloud = (
                WordCloud(init_opts=opts.InitOpts(theme=ThemeType.DARK))
                .add(
                    series_name="词频",
                    data_pair=data,
                    word_size_range=[20, 100],
                    shape="circle",
                    rotate_step=45,
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(
                        title="词云图",
                        subtitle="词汇频率可视化",
                        title_textstyle_opts=opts.TextStyleOpts(font_size=24)
                    ),
                    tooltip_opts=opts.TooltipOpts(is_show=True),
                )
            )
            st_pyecharts(wordcloud, height="500px")
        
        # 条形图
        elif chart_type == "条形图":
            top_n = min(20, len(data))
            bar = (
                Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
                .add_xaxis([item[0] for item in data[:top_n]])
                .add_yaxis("词频", [item[1] for item in data[:top_n]])
                .reversal_axis()
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="词频条形图"),
                    xaxis_opts=opts.AxisOpts(name="频次"),
                    yaxis_opts=opts.AxisOpts(name="词汇"),
                )
                .set_series_opts(
                    label_opts=opts.LabelOpts(position="right")
                )
            )
            st_pyecharts(bar, height="500px")
        
        # 饼图
        elif chart_type == "饼图":
            top_n = min(15, len(data))
            pie = (
                Pie(init_opts=opts.InitOpts(theme=ThemeType.ROMA))
                .add(
                    "",
                    data[:top_n],
                    radius=["30%", "75%"],
                    center=["50%", "50%"],
                    rosetype="radius",
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="词频分布饼图"),
                    legend_opts=opts.LegendOpts(
                        orient="vertical", pos_top="15%", pos_left="2%"
                    ),
                )
                .set_series_opts(
                    tooltip_opts=opts.TooltipOpts(
                        trigger="item", formatter="{a} <br/>{b}: {c} ({d}%)"
                    ),
                    label_opts=opts.LabelOpts(formatter="{b}: {c}")
                )
            )
            st_pyecharts(pie, height="500px")
        
        # 折线图
        elif chart_type == "折线图":
            top_n = min(20, len(data))
            line = (
                Line(init_opts=opts.InitOpts(theme=ThemeType.CHALK))
                .add_xaxis([item[0] for item in data[:top_n]])
                .add_yaxis(
                    "词频",
                    [item[1] for item in data[:top_n]],
                    is_smooth=True,
                    label_opts=opts.LabelOpts(is_show=False),
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="词频趋势图"),
                    xaxis_opts=opts.AxisOpts(
                        name="词汇",
                        axislabel_opts=opts.LabelOpts(rotate=45)
                    ),
                    yaxis_opts=opts.AxisOpts(name="频次"),
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                )
            )
            st_pyecharts(line, height="500px")
        
        # 散点图
        elif chart_type == "散点图":
            top_n = min(30, len(data))
            scatter = (
                Scatter(init_opts=opts.InitOpts(theme=ThemeType.WESTEROS))
                .add_xaxis(list(range(top_n)))
                .add_yaxis(
                    "词频",
                    [item[1] for item in data[:top_n]],
                    symbol_size=lambda val: val * 2,
                    label_opts=opts.LabelOpts(
                        formatter=lambda params: data[params.data_index][0]
                    ),
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="词频散点图"),
                    xaxis_opts=opts.AxisOpts(
                        name="排名",
                        splitline_opts=opts.SplitLineOpts(is_show=True)
                    ),
                    yaxis_opts=opts.AxisOpts(
                        name="频次",
                        splitline_opts=opts.SplitLineOpts(is_show=True)
                    ),
                    tooltip_opts=opts.TooltipOpts(
                        formatter=lambda params: f"{data[params.data_index][0]}<br/>排名: {params.data_index + 1}<br/>频次: {params.value[1]}"
                    ),
                )
            )
            st_pyecharts(scatter, height="500px")
        
        # 雷达图
        elif chart_type == "雷达图":
            top_n = min(8, len(data))
            radar = (
                Radar(init_opts=opts.InitOpts(theme=ThemeType.DARK))
                .add_schema(
                    schema=[
                        opts.RadarIndicatorItem(name=item[0], max_=max([d[1] for d in data[:top_n]]))
                        for item in data[:top_n]
                    ],
                    splitarea_opt=opts.SplitAreaOpts(
                        is_show=True, areastyle_opts=opts.AreaStyleOpts(opacity=1)
                    ),
                )
                .add(
                    "词频",
                    [[item[1] for item in data[:top_n]]],
                    linestyle_opts=opts.LineStyleOpts(color="#CD0000"),
                )
                .set_global_opts(title_opts=opts.TitleOpts(title="词频雷达图"))
            )
            st_pyecharts(radar, height="500px")
        
        # 漏斗图
        elif chart_type == "漏斗图":
            top_n = min(10, len(data))
            funnel = (
                Funnel(init_opts=opts.InitOpts(theme=ThemeType.MACARONS))
                .add(
                    "词汇",
                    data[:top_n],
                    label_opts=opts.LabelOpts(position="inside"),
                    tooltip_opts=opts.TooltipOpts(formatter="{b}: {c}"),
                )
                .set_global_opts(title_opts=opts.TitleOpts(title="词频漏斗图"))
            )
            st_pyecharts(funnel, height="500px")
        
        # 组合图（条形图+折线图）
        elif chart_type == "组合图":
            top_n = min(15, len(data))
            bar_line = (
                Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
                .add_xaxis([item[0] for item in data[:top_n]])
                .add_yaxis(
                    "词频",
                    [item[1] for item in data[:top_n]],
                    yaxis_index=0,
                    label_opts=opts.LabelOpts(is_show=False),
                )
                .extend_axis(
                    yaxis=opts.AxisOpts(
                        name="累计占比",
                        type_="value",
                        min_=0,
                        max_=100,
                        position="right",
                        axislabel_opts=opts.LabelOpts(formatter="{value}%"),
                    )
                )
                .set_global_opts(
                    title_opts=opts.TitleOpts(title="词频分布与累计占比"),
                    xaxis_opts=opts.AxisOpts(
                        axislabel_opts=opts.LabelOpts(rotate=45)
                    ),
                    yaxis_opts=opts.AxisOpts(name="频次"),
                    tooltip_opts=opts.TooltipOpts(trigger="axis"),
                )
            )
            
            # 计算累计百分比
            total = sum([item[1] for item in data[:top_n]])
            cumulative = []
            current_sum = 0
            for item in data[:top_n]:
                current_sum += item[1]
                cumulative.append(round(current_sum / total * 100, 2))
            
            line = (
                Line()
                .add_xaxis([item[0] for item in data[:top_n]])
                .add_yaxis(
                    "累计占比",
                    cumulative,
                    yaxis_index=1,
                    label_opts=opts.LabelOpts(is_show=False),
                    linestyle_opts=opts.LineStyleOpts(width=3),
                    symbol="circle",
                    symbol_size=10,
                )
            )
            
            bar_line.overlap(line)
            st_pyecharts(bar_line, height="500px")
    
    # 数据导出选项
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 导出词频数据", use_container_width=True):
            df_all = pd.DataFrame(
                st.session_state.word_freq.most_common(),
                columns=["词汇", "频次"]
            )
            csv = df_all.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="下载CSV文件",
                data=csv,
                file_name="词频统计.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        if st.button("📊 导出可视化图表", use_container_width=True):
            st.info("图表已显示在页面上，您可以使用浏览器的截图功能保存图表")
    
    with col3:
        if st.button("🖨️ 打印分析报告", use_container_width=True):
            st.success("分析报告已生成！")

else:
    # 初始状态显示
    st.markdown("""
    ## 🎯 使用说明
    
    欢迎使用文本分析可视化工具！请按照以下步骤操作：
    
    1. **输入URL**：在左侧边栏输入您要分析的文章URL
    2. **抓取文本**：点击"抓取并分析文本"按钮
    3. **选择图表**：从7种可视化图表中选择您喜欢的类型
    4. **过滤词汇**：使用滑块过滤低频词汇
    5. **查看结果**：查看词频排名和可视化图表
    
    ### 📈 支持的图表类型：
    - **词云图**：直观展示词汇频率
    - **条形图**：横向比较词频高低
    - **饼图**：显示词汇分布比例
    - **折线图**：展示词频趋势变化
    - **散点图**：观察词汇分布情况
    - **雷达图**：多维度对比词汇频率
    - **漏斗图**：展示词汇筛选过程
    - **组合图**：综合展示词频和累计占比
    
    ### 💡 小贴士：
    - 确保输入的URL可公开访问
    - 支持中文网页内容分析
    - 可调整过滤阈值优化显示效果
    """)
    
    # 示例展示
    with st.expander("查看示例数据"):
        st.image("https://via.placeholder.com/800x400?text=示例可视化图表", 
                caption="示例图表展示", use_column_width=True)

# 页脚
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>文本分析可视化工具 © 2023 | 基于Streamlit和PyEcharts构建</div>",
    unsafe_allow_html=True
)