import datetime
import time
import os
import requests
import json
from duckduckgo_search import DDGS

# Target Companies (Name + Preferred Source)
TARGETS = [
    {"name": "三花智控", "site": "finance.yahoo.com"},
    {"name": "长飞光纤", "site": "finance.yahoo.com"},
    {"name": "宏和科技", "site": "finance.yahoo.com"},
    {"name": "阳光电源", "site": "finance.yahoo.com"}
]

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

def search_web(query, max_results=5):
    """
    Search the web using DuckDuckGo.
    """
    print(f"Searching web for: {query}...", flush=True)
    try:
        results = DDGS().text(query, max_results=max_results)
        return results if results else []
    except Exception as e:
        print(f"  Search error: {e}")
        return []

def get_company_info(target):
    name = target["name"]
    site = target.get("site", "")
    
    # Construct queries
    # 1. Search for stock price/info specifically on the preferred site or generally
    stock_query = f"{name} stock price site:{site}" if site else f"{name} stock price"
    stock_results = search_web(stock_query, max_results=3)
    
    # 2. Search for recent news
    news_query = f"{name} latest news financial"
    news_results = search_web(news_query, max_results=5)
    
    return {
        "name": name,
        "stock_results": stock_results,
        "news_results": news_results
    }

def generate_report_with_deepseek(raw_data_list):
    """
    Use DeepSeek to analyze search results and generate the report.
    """
    if not DEEPSEEK_API_KEY:
        return "Error: DEEPSEEK_API_KEY not set."

    today = datetime.date.today().strftime("%Y-%m-%d")
    
    # Prepare prompt with raw search data
    context_str = f"Date: {today}\n\n"
    for item in raw_data_list:
        context_str += f"=== Company: {item['name']} ===\n"
        
        context_str += "Search Results (Stock Info):\n"
        for res in item['stock_results']:
            context_str += f"- Title: {res.get('title')}\n  Snippet: {res.get('body')}\n  Link: {res.get('href')}\n"
            
        context_str += "\nSearch Results (News):\n"
        for res in item['news_results']:
            context_str += f"- Title: {res.get('title')}\n  Snippet: {res.get('body')}\n  Link: {res.get('href')}\n"
        
        context_str += "\n"

    system_prompt = """
    You are an advanced financial analyst AI.
    Your task is to read the provided Web Search Results and compile a "Listed Company Daily News Monitor Report".
    
    Guidelines:
    1. **Title**: "上市公司每日新闻监测日报" + Date.
    2. **Structure**: One section per company.
    3. **Content Extraction**:
       - **Market Performance**: Try to find the latest stock price, symbol, and trend (change %) from the "Stock Info" search snippets. If you see a recent date and price, use it. If data is missing or ambiguous, say "暂未获取到最新股价".
       - **Latest News**: Summarize the most relevant and recent financial news from the "News" search snippets. Ignore irrelevant or old news.
       - **Links**: When citing news, provide the source link in Markdown format `[Title](Link)`.
    4. **Tone**: Professional, objective.
    5. **Language**: Simplified Chinese.
    6. **Handling Missing Data**: If the search results don't contain useful info, honestly state "未检索到相关有效信息" (No relevant information found).
    """

    user_prompt = f"Here is the raw search data:\n{context_str}\n\nPlease generate the report."

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
        return f"Report generation failed: {e}"

if __name__ == "__main__":
    print("Starting Intelligent News Monitor (Web Search Mode)...", flush=True)
    
    # 1. Collect Data via Web Search
    raw_data = []
    for target in TARGETS:
        data = get_company_info(target)
        raw_data.append(data)
        time.sleep(2) # Be polite to DDG
        
    # 2. Generate Report via LLM
    if DEEPSEEK_API_KEY:
        report = generate_report_with_deepseek(raw_data)
    else:
        report = "DEEPSEEK_API_KEY not set. Cannot analyze search results."

    print("\n" + "="*30 + " Generated Report " + "="*30 + "\n")
    print(report)
    
    # 3. Save to file (Email disabled as requested)
    filename = f"daily_report_{datetime.date.today().strftime('%Y%m%d')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport saved to: {filename}")
    
    # Email sending is temporarily disabled
    # email_subject = f"上市公司新闻日报 - {datetime.date.today().strftime('%Y-%m-%d')}"
    # send_email(email_subject, report)
