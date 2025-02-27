import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ✅ Fetch Bitcoin historical data
@st.cache_data(ttl=1800)
def get_crypto_data(crypto_id="bitcoin", days=180):
    url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
    params = {'vs_currency': 'usd', 'days': days, 'interval': 'daily'}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
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

# ✅ AI API (Mistral-7B or DeepSeek)
API_KEY = "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"
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"

# ✅ Generate AI insights based on market data
def generate_ai_insights(selected_kpis):
    crypto_df = get_crypto_data()
    if crypto_df is None:
        return "❌ Error fetching Bitcoin data."

    # Compute indicators
    crypto_df["RSI"] = calculate_rsi(crypto_df["price"])
    crypto_df["EMA_7"] = calculate_ema(crypto_df["price"], 7)
    crypto_df["EMA_30"] = calculate_ema(crypto_df["price"], 30)
    crypto_df["EMA_60"] = calculate_ema(crypto_df["price"], 60)
    crypto_df["EMA_200"] = calculate_ema(crypto_df["price"], 200)

    # Filter selected KPIs
    available_kpis = [kpi for kpi in selected_kpis if kpi in crypto_df.columns]

    if not available_kpis:
        return "⚠️ No valid KPIs selected."

    # Get latest values
    latest_price = crypto_df["price"].iloc[-1]
    latest_kpi_values = {kpi: crypto_df[kpi].iloc[-1] for kpi in available_kpis}

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

crypto_df = get_crypto_data()
if crypto_df is not None:
    st.subheader("📈 Bitcoin Price Chart with Selected Indicators")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(crypto_df.index, crypto_df["price"], label="BTC Price", color="blue")

    for kpi in selected_kpis:
        if kpi in crypto_df.columns:
            ax.plot(crypto_df.index, crypto_df[kpi], label=kpi, linestyle="dotted")

    ax.legend()
    st.pyplot(fig)
else:
    st.error("❌ Error fetching Bitcoin price data.")
