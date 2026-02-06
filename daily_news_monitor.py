import datetime
import time
import os
import requests
import json
from duckduckgo_search import DDGS

# Target Companies
TARGETS = [
    {"name": "三花智控", "site": "finance.sina.com.cn"},
    {"name": "长飞光纤", "site": "finance.sina.com.cn"},
    {"name": "宏和科技", "site": "finance.sina.com.cn"},
    {"name": "阳光电源", "site": "finance.sina.com.cn"}
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
    """
    Site-specific search: We search for stock data and news on the specified site.
    """
    name = target["name"]
    site = target["site"]
    
    # 1. Site-Specific Search
    # Query: site:finance.sina.com.cn 三花智控 股价 新闻
    query = f"site:{site} {name} 股价 新闻"
    results = search_web(query, max_results=8)
    
    return {
        "name": name,
        "site": site,
        "search_results": results
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
        context_str += f"=== Company: {item['name']} (Source: {item['site']}) ===\n"
        context_str += "Raw Search Results:\n"
        for res in item['search_results']:
            context_str += f"- Title: {res.get('title')}\n  Snippet: {res.get('body')}\n  Link: {res.get('href')}\n"
        context_str += "\n"

    system_prompt = """
    You are an intelligent financial analyst.
    You have been provided with raw web search results from specific financial websites (e.g., Sina Finance).
    
    Your Task:
    Generate a concise "Daily News Monitor Report" in Simplified Chinese.
    
    For each company:
    1. **Identify Stock Info**: Extract the most recent stock price and trend from the search snippets. If not found, say "未检索到最新股价".
    2. **Summarize News**: Identify key financial news. Since the search is site-specific, prioritize the most relevant headlines.
    3. **Provide Links**: Use the links provided in the raw data.
    
    Output Format:
    # 上市公司每日新闻监测日报 [Date]
    
    ## [Company Name]
    **数据来源**: [Site]
    **市场表现**: [Price / Change or "未检索到"]
    **最新动态**:
    - [News Summary] ([Source Title](Source Link))
    ...
    """

    user_prompt = f"Here is the search data:\n{context_str}\n\nPlease generate the report."

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
    print("Starting Intelligent News Monitor (Site-Specific Search Mode)...", flush=True)
    
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
    
    # 3. Save to file
    filename = f"daily_report_{datetime.date.today().strftime('%Y%m%d')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport saved to: {filename}")
    
    # Email sending
    # email_subject = f"上市公司新闻日报 - {datetime.date.today().strftime('%Y-%m-%d')}"
    # send_email(email_subject, report)

