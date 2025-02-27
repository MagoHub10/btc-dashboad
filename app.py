import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ✅ Fetch Bitcoin OHLC data (for candlestick charts)
@st.cache_data(ttl=1800)
def get_crypto_data(crypto_id="bitcoin", days=180):
    url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/ohlc"
    params = {'vs_currency': 'usd', 'days': days}

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

# ✅ Calculate RSI (14-period)
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)

# ✅ Calculate EMA for different periods
def calculate_ema(data, window):
    return data.ewm(span=window, adjust=False).mean().fillna(data)

# ✅ AI API (DeepSeek-Chat or OpenChat-7B)
API_KEY = "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"
API_URL = "https://api-inference.huggingface.co/models/deepseek-ai/deepseek-chat"

# ✅ Generate AI insights based on market data
@st.cache_data(ttl=600)  # Cache for 10 minutes
def generate_ai_insights(selected_kpis):
    crypto_df = get_crypto_data()
    if crypto_df is None:
        return "❌ Error fetching Bitcoin data."

    # Compute indicators only if selected
    if "RSI" in selected_kpis:
        crypto_df["RSI"] = calculate_rsi(crypto_df["close"])
    if "EMA_7" in selected_kpis:
        crypto_df["EMA_7"] = calculate_ema(crypto_df["close"], 7)
    if "EMA_30" in selected_kpis:
        crypto_df["EMA_30"] = calculate_ema(crypto_df["close"], 30)
    if "EMA_60" in selected_kpis:
        crypto_df["EMA_60"] = calculate_ema(crypto_df["close"], 60)
    if "EMA_200" in selected_kpis:
        crypto_df["EMA_200"] = calculate_ema(crypto_df["close"], 200)

    # Get latest values
    latest_price = crypto_df["close"].iloc[-1]
    latest_kpi_values = {kpi: crypto_df[kpi].iloc[-1] for kpi in selected_kpis if kpi in crypto_df.columns}

    # Create AI prompt
    kpi_summary = "\n".join([f"{kpi}: {latest_kpi_values[kpi]:,.2f}" for kpi in latest_kpi_values])
    prompt = f"""
    You are a professional financial analyst specializing in Bitcoin.

    🔹 **Latest BTC Price:** ${latest_price:,.2f}
    🔹 **Key Indicators:**
    {kpi_summary}

    1️⃣ Identify the market trend (bullish, bearish, neutral).
    2️⃣ Find key support and resistance levels.
    3️⃣ Suggest investment strategies based on the data.

    🚨 **Rules:**  
    - Do **not** generate random words.  
    - Keep it **short & professional**.  
    - Provide **realistic** trading insights.  
    """

    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(API_URL, headers=headers, json={"inputs": prompt})

    if response.status_code == 503:
        return "⚠️ AI Service is temporarily unavailable. Please try again later."
    if response.status_code != 200:
        return f"❌ AI API Error: HTTP {response.status_code}"

    try:
        return response.json()[0]['generated_text']
    except Exception:
        return "❌ Error processing AI response."

# ✅ Streamlit Dashboard
st.title("📊 Bitcoin Market Dashboard with AI Insights")

st.subheader("📌 Select KPIs to Analyze")
kpi_options = ["RSI", "EMA_7", "EMA_30", "EMA_60", "EMA_200"]
selected_kpis = st.multiselect("Choose indicators:", kpi_options, default=["RSI", "EMA_30", "EMA_200"])

st.subheader("🤖 AI-Generated Market Insights")
with st.spinner("Generating insights..."):
    insights = generate_ai_insights(selected_kpis)
    st.write(insights)

# ✅ Show Candlestick Chart with Selected Indicators
crypto_df = get_crypto_data()
if crypto_df is not None:
    st.subheader("📈 Bitcoin Candlestick Chart with Selected Indicators")

    fig = go.Figure()

    # ✅ Add Candlestick Chart
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

    # ✅ Add Selected Indicators
    for kpi in selected_kpis:
        if kpi in crypto_df.columns:
            fig.add_trace(go.Scatter(x=crypto_df.index, y=crypto_df[kpi], mode='lines', name=kpi))

    fig.update_layout(title="Bitcoin Candlestick Chart with Technical Indicators", xaxis_title="Date", yaxis_title="Price (USD)")
    st.plotly_chart(fig)
else:
    st.error("❌ Error fetching Bitcoin price data.")
