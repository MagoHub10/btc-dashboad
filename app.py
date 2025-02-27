import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ✅ Fetch Bitcoin OHLC Data for Candlestick Chart
@st.cache_data(ttl=1800)
def get_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc"
    params = {'vs_currency': 'usd', 'days': 365}  # Last Year of Data

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index("timestamp", inplace=True)
        return df
    except requests.exceptions.RequestException:
        return None

# ✅ Fetch RSI & EMA from AlphaVantage API
@st.cache_data(ttl=1800)
def get_technical_indicators():
    API_KEY = "0RZD71ZFRAWYN55E"
    base_url = "https://www.alphavantage.co/query"

    # Fetch RSI
    rsi_url = f"{base_url}?function=RSI&symbol=BTCUSD&interval=daily&time_period=14&series_type=close&apikey={API_KEY}"
    rsi_response = requests.get(rsi_url).json()
    rsi_data = rsi_response.get("Technical Analysis: RSI", {})

    # Fetch EMA for different time frames
    ema_urls = {
        "EMA_7": f"{base_url}?function=EMA&symbol=BTCUSD&interval=daily&time_period=7&series_type=close&apikey={API_KEY}",
        "EMA_30": f"{base_url}?function=EMA&symbol=BTCUSD&interval=daily&time_period=30&series_type=close&apikey={API_KEY}",
        "EMA_60": f"{base_url}?function=EMA&symbol=BTCUSD&interval=daily&time_period=60&series_type=close&apikey={API_KEY}",
        "EMA_200": f"{base_url}?function=EMA&symbol=BTCUSD&interval=daily&time_period=200&series_type=close&apikey={API_KEY}"
    }

    ema_data = {}
    for key, url in ema_urls.items():
        response = requests.get(url).json()
        ema_data[key] = response.get("Technical Analysis: EMA", {})

    return {"RSI": rsi_data, **ema_data}

# ✅ AI API (DeepSeek-Chat)
API_KEY = "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"
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"

@st.cache_data(ttl=600)
def generate_ai_insights(selected_kpis):
    crypto_df = get_crypto_data()
    indicators = get_technical_indicators()

    if crypto_df is None or not indicators:
        return "❌ Error fetching data."

    latest_price = crypto_df["close"].iloc[-1]
    latest_rsi = list(indicators["RSI"].values())[0]
    latest_ema = {key: list(value.values())[0] for key, value in indicators.items() if key != "RSI"}

    kpi_summary = f"RSI: {latest_rsi}\n" + "\n".join([f"{k}: {v}" for k, v in latest_ema.items()])
    
    prompt = f"""
    You are an experienced crypto market advisor. Analyze the Bitcoin trend based on the latest data.

    🔹 **Latest BTC Price:** ${latest_price:,.2f}
    🔹 **Key Indicators:**
    {kpi_summary}

    1️⃣ Identify the market trend (bullish, bearish, neutral).
    2️⃣ Find key support and resistance levels.
    3️⃣ Provide trading recommendations based on the data.

    🚨 **Rules:**  
    - Avoid generating random information.  
    - Keep the response structured like a market report.  
    - Provide realistic insights with recommended actions.  
    """

    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})

    if response.status_code != 200:
        return f"❌ AI API Error: HTTP {response.status_code}"

    return response.json()[0]['generated_text']

# ✅ Streamlit Dashboard UI
st.set_page_config(layout="wide")
st.title("📊 Bitcoin Market Dashboard with AI Insights")

# ✅ Sidebar for KPI Selection
st.sidebar.header("🔹 Select KPIs to Display")
kpi_options = ["RSI", "EMA_7", "EMA_30", "EMA_60", "EMA_200"]
selected_kpis = st.sidebar.multiselect("Choose indicators:", kpi_options, default=["RSI", "EMA_30", "EMA_200"])

st.sidebar.subheader("📌 Selected KPIs")
st.sidebar.write(", ".join(selected_kpis))

# ✅ AI Insights Section
st.subheader("🤖 AI Market Insights")
insights_placeholder = st.empty()
with st.spinner("Generating insights..."):
    insights = generate_ai_insights(selected_kpis)
insights_placeholder.write(insights)

# ✅ Show Candlestick Chart with Selected KPIs
st.subheader("📈 Bitcoin Candlestick Chart with Technical Indicators")
crypto_df = get_crypto_data()
indicators = get_technical_indicators()

if crypto_df is not None:
    fig = go.Figure()

    # ✅ Candlestick Chart
    fig.add_trace(go.Candlestick(
        x=crypto_df.index,
        open=crypto_df['open'],
        high=crypto_df['high'],
        low=crypto_df['low'],
        close=crypto_df['close'],
        increasing_line_color='green',
        decreasing_line_color='red',
        name="BTC Price"
    ))

    # ✅ Overlay Selected KPIs as Lines
    for kpi in selected_kpis:
        if kpi in indicators and indicators[kpi]:
            kpi_dates = pd.to_datetime(list(indicators[kpi].keys()))  # Convert to datetime
            kpi_values = list(indicators[kpi].values())
            fig.add_trace(go.Scatter(x=kpi_dates, y=kpi_values, mode='lines', name=kpi))

    fig.update_layout(
        title="Bitcoin Candlestick Chart with Technical Indicators",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig)
else:
    st.error("❌ Error fetching Bitcoin price data.")
