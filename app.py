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
            return None
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching BTC price: {e}")
        return None

# ✅ Cache 7-day percentage change for 5 minutes
@st.cache_data(ttl=300)
def get_weekly_change():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": "7"}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()["prices"]
        start_price = data[0][1]  # Price 7 days ago
        current_price = data[-1][1]  # Latest price
        percentage_change = ((current_price - start_price) / start_price) * 100
        return round(percentage_change, 2)
    
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching weekly change: {e}")
        return None

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
        st.error(f"Error fetching historical data: {e}")
        return None

# ✅ AI API (Hugging Face)
API_KEY = "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"  # Replace with your API Key
API_URL = "API_URL = "https://api-inference.huggingface.co/models/google/gemma-7b"
# ✅ AI Insights Function with Live BTC Data
def generate_ai_insights(user_prompt):
    if not user_prompt:
        return "❌ Please enter a question to ask the AI."

    # Fetch live Bitcoin data
    btc_price = get_btc_price()
    weekly_change = get_weekly_change()

    # If API calls fail, return an error
    if btc_price is None or weekly_change is None:
        return "❌ Unable to fetch Bitcoin data. Please try again later."

    # **Better Prompt Engineering**
    full_prompt = f"""
    You are a professional cryptocurrency market analyst with expertise in Web3 and blockchain finance. 

    🔹 Current Bitcoin price: **${btc_price:,.2f}**
    🔹 7-day trend: **{weekly_change:.2f}%**

    Based on this data and historical trends, provide an **accurate, insightful** response to the user's question:

    **User Question:** {user_prompt}

    🔹 **Your response should be:**
    - Well-structured
    - Based on Bitcoin market trends
    - Avoid hallucinations or false information
    - Give investment indicators & risk factors

    **Keep your response clear and professional.**
    """

    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(API_URL, headers=headers, json={"inputs": full_prompt})

    if response.status_code != 200:
        return f"❌ AI API Error: HTTP {response.status_code}"

    try:
        return response.json()[0]['generated_text']
    except Exception as e:
        return f"❌ Error processing AI response: {e}"

# ✅ Streamlit Dashboard
st.title("📊 Bitcoin Dashboard with AI Insights")

# ✅ Load & Display BTC Data
crypto_df = get_crypto_data()

if crypto_df is None:
    st.error("❌ Error fetching historical Bitcoin data.")
else:
    st.subheader("🔹 Bitcoin Price Trend (Last 6 Months)")
    st.line_chart(crypto_df.set_index('timestamp')['price'])

# ✅ Show Real-Time BTC Price & Weekly Change
st.subheader("💰 Current Bitcoin Price")

btc_price = get_btc_price()
weekly_change = get_weekly_change()

if btc_price is None or weekly_change is None:
    st.warning("⚠️ Too many requests or API unavailable. Please wait a few minutes.")
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
