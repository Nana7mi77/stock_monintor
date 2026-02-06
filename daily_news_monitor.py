import yfinance as yf
import datetime
import time
import os
import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.header import Header

# Target Companies (Names only)
TARGETS = [
    "三花智控",
    "长飞光纤",
    "宏和科技",
    "阳光电源"
]

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

def search_stock_code(name):
    """
    Search for stock code by name using Yahoo Finance API.
    """
    print(f"Searching code for: {name}...", flush=True)
    try:
        url = "https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            "q": name,
            "quotesCount": 5,
            "newsCount": 0,
            "enableFuzzyQuery": False,
            "quotesQueryId": "tss_match_phrase_query"
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()
        
        if "quotes" in data and len(data["quotes"]) > 0:
            # Prefer equity/stock results
            for quote in data["quotes"]:
                if quote.get("quoteType") == "EQUITY":
                    symbol = quote["symbol"]
                    print(f"  Found: {symbol} ({quote.get('longname')})")
                    return symbol
            # Fallback to first result
            return data["quotes"][0]["symbol"]
        
        print(f"  No code found for {name}")
        return None
    except Exception as e:
        print(f"  Search error: {e}")
        return None

def get_stock_data_raw(name):
    """
    Get raw data for a company to feed into LLM.
    """
    symbol = search_stock_code(name)
    if not symbol:
        return {"name": name, "symbol": "Unknown", "error": "Stock code not found"}
    
    try:
        ticker = yf.Ticker(symbol)
        # Get price
        try:
            hist = ticker.history(period="5d")
            if not hist.empty:
                last_quote = hist.iloc[-1]
                price = last_quote['Close']
                prev_close = hist.iloc[-2]['Close'] if len(hist) > 1 else price
                change_pct = ((price - prev_close) / prev_close) * 100
                market_data = f"Price: {price:.2f}, Change: {change_pct:+.2f}%"
            else:
                market_data = "Market data unavailable"
        except Exception:
            market_data = "Market data unavailable"

        # Get news
        try:
            news_items = ticker.news
            news_summary = []
            if news_items:
                for item in news_items[:3]:
                    news_summary.append(f"- {item.get('title')} ({item.get('link')})")
            else:
                news_summary = ["No recent news found on Yahoo Finance."]
        except Exception:
            news_summary = ["Failed to fetch news."]
            
        return {
            "name": name,
            "symbol": symbol,
            "market_data": market_data,
            "news": news_summary
        }
    except Exception as e:
        return {"name": name, "symbol": symbol, "error": str(e)}

def generate_report_with_deepseek(raw_data_list):
    """
    Use DeepSeek to generate the final report.
    """
    if not DEEPSEEK_API_KEY:
        return "Error: DEEPSEEK_API_KEY not set. Cannot generate intelligent report."

    today = datetime.date.today().strftime("%Y-%m-%d")
    
    # Prepare prompt
    context_str = f"Date: {today}\n\nData:\n"
    for item in raw_data_list:
        context_str += f"Company: {item['name']} ({item['symbol']})\n"
        if 'error' in item:
            context_str += f"Status: Error - {item['error']}\n"
        else:
            context_str += f"Market: {item['market_data']}\n"
            context_str += "News:\n" + "\n".join(item['news']) + "\n"
        context_str += "---\n"

    system_prompt = """
    You are a professional financial news analyst. 
    Your task is to generate a daily summary report based on the provided raw data for several companies.
    
    Guidelines:
    1. **Title**: "上市公司每日新闻监测日报" + Date.
    2. **Structure**: One section per company.
    3. **Content**: 
       - Summarize market performance briefly.
       - Summarize the news headlines provided.
       - **CRITICAL**: If the data says "No code found", "Market data unavailable" AND "No recent news", you MUST explicitly state that you could not find relevant information for this company. Do NOT output a template with "N/A". Use natural language like "今日未检索到该公司的有效市场数据或新闻。" (No effective market data or news retrieved today).
       - If there is news, list it with links.
    4. **Tone**: Professional, objective, concise.
    5. **Language**: Simplified Chinese.
    """

    user_prompt = f"Here is the raw data for today:\n{context_str}\n\nPlease generate the report."

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    print("Calling DeepSeek API to generate report...", flush=True)
    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"DeepSeek API failed: {e}")
        return f"Report generation failed due to API error: {e}\n\nRaw Data:\n{context_str}"

def send_email(subject, content):
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    # Support multiple receivers split by comma
    receivers_str = os.environ.get("EMAIL_RECEIVER", "1261875597@qq.com,1669675380@qq.com")
    receivers = [r.strip() for r in receivers_str.split(',') if r.strip()]
    
    if not sender or not password:
        print("Skipping email: EMAIL_SENDER or EMAIL_PASSWORD environment variable not set.")
        return

    # Determine SMTP server based on sender domain
    smtp_server = "smtp.qq.com"
    smtp_port = 465 # SSL
    
    if "@163.com" in sender:
        smtp_server = "smtp.163.com"
    elif "@gmail.com" in sender:
        smtp_server = "smtp.gmail.com"
    
    try:
        message = MIMEText(content, 'markdown', 'utf-8')
        message['From'] = sender
        message['To'] = ", ".join(receivers)
        message['Subject'] = Header(subject, 'utf-8')

        print(f"Connecting to SMTP server {smtp_server}...")
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender, password)
        print("Logged in successfully.")
        
        server.sendmail(sender, receivers, message.as_string())
        server.quit()
        print(f"Email sent successfully to {', '.join(receivers)}!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    print("Starting Intelligent News Monitor...", flush=True)
    
    # 1. Collect Data
    raw_data = []
    for name in TARGETS:
        data = get_stock_data_raw(name)
        raw_data.append(data)
        time.sleep(1) # Rate limit politeness
        
    # 2. Generate Report via LLM
    if DEEPSEEK_API_KEY:
        report = generate_report_with_deepseek(raw_data)
    else:
        print("WARNING: DEEPSEEK_API_KEY not set. Using basic fallback report.")
        report = "# Monitor Report (Basic)\n\n"
        for item in raw_data:
            report += f"## {item['name']} ({item['symbol']})\n"
            report += f"{item.get('market_data', 'No Data')}\n"
            report += f"{item.get('news', ['No News'])[0]}\n\n"
            report += "Note: Configure DEEPSEEK_API_KEY for intelligent reporting.\n"

    print("\n" + "="*30 + " Generated Report " + "="*30 + "\n")
    print(report)
    
    # 3. Save and Send
    filename = f"daily_report_{datetime.date.today().strftime('%Y%m%d')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport saved to: {filename}")
    
    email_subject = f"上市公司新闻日报 - {datetime.date.today().strftime('%Y-%m-%d')}"
    send_email(email_subject, report)
