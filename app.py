import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# ✅ Load Bitcoin price data (Last 6 Months)
def get_crypto_data(crypto_id="bitcoin", days=180):
    url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
    params = {'vs_currency': 'usd', 'days': days, 'interval': 'daily'}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data['prices'], columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    else:
        st.error(f"❌ Error fetching data: {response.json()}")
        return pd.DataFrame()

# ✅ Fetch Current Bitcoin Price
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd"}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        return data["bitcoin"]["usd"]
    else:
        return None

# ✅ Calculate 7-Day Percentage Change
def get_weekly_change():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": "7"}
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()["prices"]
        start_price = data[0][1]  # Price 7 days ago
        current_price = data[-1][1]  # Latest price
        percentage_change = ((current_price - start_price) / start_price) * 100
        return round(percentage_change, 2)
    else:
        return None

# ✅ AI API (Hugging Face)
API_KEY = "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"  # Replace with your API Key
API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"

# ✅ AI Insights Function with Live BTC Data
def generate_ai_insights():
    btc_price = get_btc_price()
    weekly_change = get_weekly_change()

    if btc_price is None or weekly_change is None:
        return "❌ Unable to fetch Bitcoin price data. Please try again later."

    # Create AI prompt with real-time price data
    prompt = f"""
    Bitcoin's current price is **${btc_price:,.2f}**.
    Over the past 7 days, the price has changed by **{weekly_change:.2f}%**.

    Provide a financial market insight based on this data.
    Mention possible reasons for the trend and a short-term forecast.
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
st.title("📊 Bitcoin Dashboard with AI Insights")

# ✅ Load & Display BTC Data
crypto_df = get_crypto_data()

if crypto_df.empty:
    st.error("❌ No data available.")
else:
    st.subheader("🔹 Bitcoin Price Trend (Last 6 Months)")
    st.line_chart(crypto_df.set_index('timestamp')['price'])

    # 🔹 Show Real-Time BTC Price & Weekly Change
    btc_price = get_btc_price()
    weekly_change = get_weekly_change()
    
    if btc_price and weekly_change is not None:
        st.subheader(f"💰 Current Bitcoin Price: **${btc_price:,.2f}**")
        st.metric(label="📉 7-Day Change", value=f"{weekly_change:.2f}%", delta=weekly_change)

    # 🔹 AI Insights Section
    st.subheader("🤖 AI-Generated Insights on Bitcoin")

    if st.button("Generate Insights"):
        with st.spinner("Generating insights..."):
            insights = generate_ai_insights()
            st.write(insights)
