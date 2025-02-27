import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ✅ Fetch Bitcoin OHLC data
@st.cache_data(ttl=1800)
def get_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc"
    params = {'vs_currency': 'usd', 'days': 180}

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

    # RSI
    rsi_url = f"{base_url}?function=RSI&symbol=BTCUSD&interval=daily&time_period=14&series_type=close&apikey={API_KEY}"
    rsi_response = requests.get(rsi_url).json()
    rsi = rsi_response.get("Technical Analysis: RSI", {})

    # EMA
    ema_urls = {
        "EMA_7": f"{base_url}?function=EMA&symbol=BTCUSD&interval=daily&time_period=7&series_type=close&apikey={API_KEY}",
        "EMA_30": f"{base_url}?function=EMA&symbol=BTCUSD&interval=daily&time_period=30&series_type=close&apikey={API_KEY}",
        "EMA_60": f"{base_url}?function=EMA&symbol=BTCUSD&interval=daily&time_period=60&series_type=close&apikey={API_KEY}",
        "EMA_200": f"{base_url}?function=EMA&symbol=BTCUSD&interval=daily&time_period=200&series_type=close&apikey={API_KEY}"
    }

    ema_values = {}
    for key, url in ema_urls.items():
        ema_response = requests.get(url).json()
        ema_data = ema_response.get("Technical Analysis: EMA", {})
        ema_values[key] = ema_data

    return {"RSI": rsi, **ema_values}

# ✅ AI API (DeepSeek-Chat)
API_KEY = "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"
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"

@st.cache_data(ttl=600)
def generate_ai_insights():
    crypto_df = get_crypto_data()
    indicators = get_technical_indicators()

    if crypto_df is None or not indicators:
        return "❌ Error fetching data."

    latest_price = crypto_df["close"].iloc[-1]
    latest_rsi = list(indicators["RSI"].values())[0]
    latest_ema = {key: list(value.values())[0] for key, value in indicators.items() if key != "RSI"}

    kpi_summary = f"RSI: {latest_rsi}\n" + "\n".join([f"{k}: {v}" for k, v in latest_ema.items()])
    
    prompt = f"""
    You are a professional financial analyst specializing in Bitcoin.

    🔹 **Latest BTC Price:** ${latest_price:,.2f}
    🔹 **Key Indicators:**
    {kpi_summary}

    1️⃣ Identify the market trend (bullish, bearish, neutral).
    2️⃣ Find key support and resistance levels.
    3️⃣ Suggest investment strategies based on the data.
    """

    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})

    return response.json()[0]['generated_text']

# ✅ Display Candlestick Chart Without Slicer
crypto_df = get_crypto_data()
fig = go.Figure(data=[go.Candlestick(
    x=crypto_df.index,
    open=crypto_df['open'],
    high=crypto_df['high'],
    low=crypto_df['low'],
    close=crypto_df['close'],
    increasing_line_color='green', decreasing_line_color='red'
)])

fig.update_layout(xaxis_rangeslider_visible=False)
st.plotly_chart(fig)
