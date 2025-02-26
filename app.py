import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# ✅ Fetch Bitcoin OHLC Data for Candlestick Chart
@st.cache_data(ttl=1800)
def get_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc"
    params = {'vs_currency': 'usd', 'days': 365}  # Fetch Last Year Data

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index("timestamp", inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching Bitcoin data: {e}")
        return None

# ✅ Fetch RSI & EMA from AlphaVantage API
@st.cache_data(ttl=1800)
def get_technical_indicators():
    API_KEY = "0RZD71ZFRAWYN55E"  # Replace with your Alpha Vantage API key
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

# ✅ AI Insights Function (Using a Free LLM)
def generate_ai_insights(selected_kpis):
    crypto_df = get_crypto_data()
    indicators = get_technical_indicators()

    if crypto_df is None or not indicators:
        return "❌ Error fetching data."

    latest_price = crypto_df["close"].iloc[-1]
    
    # Extract latest KPI values correctly
    latest_rsi = list(indicators["RSI"].values())[0] if "RSI" in indicators and indicators["RSI"] else "N/A"
    latest_ema = {key: list(value.values())[0] for key, value in indicators.items() if key != "RSI" and key in selected_kpis}

    # Properly format KPI summary
    kpi_summary = f"RSI: {latest_rsi}\n" + "\n".join([f"{k}: {v}" for k, v in latest_ema.items()])

    prompt = f"""
    You are a professional crypto market analyst. Based on the latest Bitcoin market data:

    🔹 **Latest BTC Price:** ${latest_price:,.2f}
    🔹 **Key Indicators:**
    {kpi_summary}

    1️⃣ **Market Trend Analysis:** Identify if Bitcoin is bullish, bearish, or neutral.
    2️⃣ **Support & Resistance Levels:** Identify critical levels.
    3️⃣ **Trading Strategy:** Provide recommendations for long and short positions.

    🚨 **Rules:**  
    - Use professional financial terminology.
    - Structure insights in a clear market report.
    - No random or irrelevant information.

    **Generate your professional market analysis below:**
    """

    # Use a free LLM API (e.g., OpenAssistant or GPT-Neo)
    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct",
            headers={"Authorization": "Bearer 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"},
            json={"inputs": prompt}
        )
        if response.status_code == 200:
            return response.json()[0]['generated_text']
        else:
            return f"❌ AI API Error: HTTP {response.status_code}"
    except Exception as e:
        return f"❌ Error generating insights: {e}"

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
if st.button("Generate Insights"):
    with st.spinner("Generating insights..."):
        insights = generate_ai_insights(selected_kpis)
        insights_placeholder.write(insights)

# ✅ Show Candlestick Chart with KPI Trendlines
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

    # ✅ Overlay KPI Trendlines
    # ✅ Overlay KPI Trendlines
for kpi in selected_kpis:
    if kpi in indicators and indicators[kpi]:
        kpi_dates = pd.to_datetime(list(indicators[kpi].keys()))  # Convert to datetime
        kpi_values = [float(list(v.values())[0]) for v in indicators[kpi].values()]  # Extract and convert values to float
        fig.add_trace(go.Scatter(x=kpi_dates, y=kpi_values, mode='lines', name=f"{kpi} Trend"))

    fig.update_layout(
        title="Bitcoin Candlestick Chart with Technical Indicators",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=False
    )

    st.plotly_chart(fig)
else:
    st.error("❌ Error fetching Bitcoin price data.")
