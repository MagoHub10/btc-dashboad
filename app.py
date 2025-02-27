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
        return df
    except requests.exceptions.RequestException:
        return None

# ✅ Calculate RSI (14-period)
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ✅ Calculate EMA for different periods
def calculate_ema(data, window):
    return data.ewm(span=window, adjust=False).mean()

# ✅ AI API (LLaMA 3)
API_KEY = "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"  # Replace with your actual API Key
API_URL = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B"

# ✅ Generate AI insights based on market data
def generate_ai_insights(selected_kpis):
    # Fetch historical BTC data
    crypto_df = get_crypto_data()
    if crypto_df is None:
        return "❌ Error fetching Bitcoin data."

    # Compute indicators
    crypto_df["RSI"] = calculate_rsi(crypto_df["price"])
    crypto_df["EMA_7"] = calculate_ema(crypto_df["price"], 7)
    crypto_df["EMA_30"] = calculate_ema(crypto_df["price"], 30)
    crypto_df["EMA_60"] = calculate_ema(crypto_df["price"], 60)
    crypto_df["EMA_200"] = calculate_ema(crypto_df["price"], 200)

    # Get latest BTC price and indicator values
    latest_price = crypto_df["price"].iloc[-1]
    latest_kpi_values = {kpi: crypto_df[kpi].iloc[-1] for kpi in selected_kpis}

    # Create prompt for AI
    kpi_summary = "\n".join([f"{kpi}: {latest_kpi_values[kpi]:,.2f}" for kpi in latest_kpi_values])
    prompt = f"""
    You are an expert cryptocurrency analyst. Based on the latest Bitcoin market data, generate a financial insight:

    🔹 **BTC Price:** ${latest_price:,.2f}
    {kpi_summary}

    Provide a professional summary of the current trend, potential market movement, and key indicators traders should monitor.
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

# ✅ KPI Selection Box
st.subheader("📌 Select KPIs to Analyze")
kpi_options = ["RSI", "EMA_7", "EMA_30", "EMA_60", "EMA_200"]
selected_kpis = st.multiselect("Choose indicators:", kpi_options, default=["RSI", "EMA_30", "EMA_200"])

# ✅ Generate AI insights automatically
st.subheader("🤖 AI-Generated Market Insights")
with st.spinner("Generating insights..."):
    insights = generate_ai_insights(selected_kpis)
    st.write(insights)

# ✅ Show Price Chart & Selected Indicators
crypto_df = get_crypto_data()
if crypto_df is not None:
    st.subheader("📈 Bitcoin Price Chart with Selected Indicators")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(crypto_df["timestamp"], crypto_df["price"], label="BTC Price", color="blue")

    # Plot selected indicators
    if "RSI" in selected_kpis:
        ax.plot(crypto_df["timestamp"], crypto_df["RSI"], label="RSI", linestyle="dashed", color="red")
    if "EMA_7" in selected_kpis:
        ax.plot(crypto_df["timestamp"], crypto_df["EMA_7"], label="EMA 7", linestyle="dotted", color="green")
    if "EMA_30" in selected_kpis:
        ax.plot(crypto_df["timestamp"], crypto_df["EMA_30"], label="EMA 30", linestyle="dotted", color="orange")
    if "EMA_60" in selected_kpis:
        ax.plot(crypto_df["timestamp"], crypto_df["EMA_60"], label="EMA 60", linestyle="dotted", color="purple")
    if "EMA_200" in selected_kpis:
        ax.plot(crypto_df["timestamp"], crypto_df["EMA_200"], label="EMA 200", linestyle="dotted", color="brown")

    ax.legend()
    st.pyplot(fig)
else:
    st.error("❌ Error fetching Bitcoin price data.")
