import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime

# ✅ Cache BTC price for 5 minutes (300 seconds)
@st.cache_data(ttl=300)
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "usd"}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if "bitcoin" in data and "usd" in data["bitcoin"]:
            return data["bitcoin"]["usd"]
        else:
            return "⚠️ API response format error"
    
    except requests.exceptions.RequestException as e:
        return f"❌ API Request Error: {e}"

# ✅ Cache 7-day percentage change for 5 minutes
@st.cache_data(ttl=300)
def get_weekly_change():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": "7"}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()["prices"]
        start_price = data[0][1]
        current_price = data[-1][1]
        percentage_change = ((current_price - start_price) / start_price) * 100
        return round(percentage_change, 2)
    
    except requests.exceptions.RequestException as e:
        return f"❌ API Request Error: {e}"

# ✅ Cache BTC historical data for 30 minutes
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
    except requests.exceptions.RequestException as e:
        return f"❌ Error fetching price data: {e}"

# ✅ AI API (Hugging Face)
API_KEY = "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"  # Replace with your API Key
API_URL = "https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"

# ✅ AI Insights Function with User Input
def generate_ai_insights(user_prompt):
    if not user_prompt:
        return "❌ Please enter a question to ask the AI."

    # Add real-time BTC price & change for context
    btc_price = get_btc_price()
    weekly_change = get_weekly_change()

    if isinstance(btc_price, str) and "❌" in btc_price:
        return btc_price  # Return error message if API fails
    if isinstance(weekly_change, str) and "❌" in weekly_change:
        return weekly_change  # Return error message if API fails

    # Append real BTC data to user question
    prompt = f"""
    Bitcoin's current price is **${btc_price:,.2f}**.
    Over the past 7 days, the price has changed by **{weekly_change:.2f}%**.

    User question: {user_prompt}
    
    You are an expert of Crypto and WEB3 which gives financial advises about trends and what happened in the industry, use all the knowledge you have to provide insightful suggestions on kpis and trends to monitor to succeed in the industry
    Open always your response politely and be professional as much as possible.
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

if isinstance(crypto_df, str) and "❌" in crypto_df:
    st.error(crypto_df)  # Display API error in UI
else:
    st.subheader("🔹 Bitcoin Price Trend (Last 6 Months)")
    st.line_chart(crypto_df.set_index('timestamp')['price'])

# ✅ Show Real-Time BTC Price & Weekly Change
st.subheader("💰 Current Bitcoin Price")

btc_price = get_btc_price()
weekly_change = get_weekly_change()

if isinstance(btc_price, str) and "❌" in btc_price:
    st.warning("⚠️ Too many requests! Data is temporarily unavailable. Please wait a few minutes.")
    st.error(btc_price)
elif isinstance(weekly_change, str) and "❌" in weekly_change:
    st.warning("⚠️ Too many requests! Data is temporarily unavailable. Please wait a few minutes.")
    st.error(weekly_change)
else:
    st.metric(label="📊 Bitcoin Price", value=f"${btc_price:,.2f}")
    st.metric(label="📉 7-Day Change", value=f"{weekly_change:.2f}%", delta=weekly_change)

# ✅ AI Insights Section with User Input
st.subheader("🤖 Ask AI About Bitcoin")

user_question = st.text_area("Enter your question about Bitcoin:", "")
if st.button("Generate AI Insights"):
    with st.spinner("Generating insights..."):
        insights = generate_ai_insights(user_question)
        st.write(insights)
