import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
        try:
            response = requests.get(url).json()
            if "Technical Analysis: EMA" in response:
                ema_data[key] = response["Technical Analysis: EMA"]
            else:
                st.warning(f"No EMA data found for {key}")
        except Exception as e:
            st.error(f"Error fetching {key} EMA data: {e}")

    return {"RSI": rsi_data, **ema_data}

# ✅ AI Insights Function (Using OpenAssistant)
def generate_ai_insights(selected_kpis):
    crypto_df = get_crypto_data()
    indicators = get_technical_indicators()

    if crypto_df is None or not indicators:
        return "❌ Error fetching data."

    latest_price = crypto_df["close"].iloc[-1]
    
    # Extract latest KPI values correctly
    latest_rsi = list(indicators["RSI"].values())[0] if "RSI" in indicators and indicators["RSI"] else "N/A"
    latest_ema = {}
    for key, value in indicators.items():
        if key != "RSI" and key in selected_kpis and value:
            try:
                latest_ema[key] = float(list(value.values())[0]) if value else "N/A"
            except (ValueError, TypeError):
                latest_ema[key] = "N/A"

    # Properly format KPI summary
    kpi_summary = f"RSI: {latest_rsi}\n" + "\n".join([f"{k}: {v}" for k, v in latest_ema.items()])

    # Structured prompt for LLM
    prompt = f"""
    You are a professional crypto market analyst. Based on the latest Bitcoin market data:

    🔹 **Latest BTC Price:** ${latest_price:,.2f}
    🔹 **Key Indicators:**
    {kpi_summary}

    Provide a professional market analysis with the following structure:
    1️⃣ **Market Trend Analysis:** Identify if Bitcoin is bullish, bearish, or neutral.
    2️⃣ **Support & Resistance Levels:** Identify critical levels.
    3️⃣ **Trading Strategy:** Provide recommendations for long and short positions.

    Rules:
    - Use professional financial terminology.
    - Do not include the prompt in your response.
    - Keep the response concise and structured.
    """

    # Use OpenAssistant
API URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
headers = {"Authorization": "Bearer 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"}
    payload = {"inputs": prompt}

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
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
    # Create subplots: 2 rows, 1 column
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])

    # ✅ Candlestick Chart (Row 1)
    fig.add_trace(go.Candlestick(
        x=crypto_df.index,
        open=crypto_df['open'],
        high=crypto_df['high'],
        low=crypto_df['low'],
        close=crypto_df['close'],
        increasing_line_color='green',
        decreasing_line_color='red',
        name="BTC Price"
    ), row=1, col=1)

    # ✅ Overlay KPI Trendlines (Row 1)
    for kpi in selected_kpis:
        if kpi in indicators and indicators[kpi] and kpi != "RSI":
            kpi_dates = pd.to_datetime(list(indicators[kpi].keys()))  # Convert to datetime
            kpi_values = [float(list(v.values())[0]) for v in indicators[kpi].values()]  # Extract and convert values to float
            fig.add_trace(go.Scatter(x=kpi_dates, y=kpi_values, mode='lines', name=f"{kpi} Trend"), row=1, col=1)

    # ✅ RSI Chart (Row 2)
    if "RSI" in selected_kpis and indicators["RSI"]:
        rsi_dates = pd.to_datetime(list(indicators["RSI"].keys()))
        rsi_values = [float(list(v.values())[0]) for v in indicators["RSI"].values()]
        fig.add_trace(go.Scatter(x=rsi_dates, y=rsi_values, mode='lines', line=dict(color='blue'), name="RSI"), row=2, col=1)
        
        # Add horizontal lines for overbought (70) and oversold (30)
        fig.add_hline(y=70, line=dict(color='purple', dash='dash'), row=2, col=1)
        fig.add_hline(y=30, line=dict(color='purple', dash='dash'), row=2, col=1)

    # Update layout
    fig.update_layout(
        title="Bitcoin Candlestick Chart with Technical Indicators",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=False,
        showlegend=True
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("❌ Error fetching Bitcoin price data.")
