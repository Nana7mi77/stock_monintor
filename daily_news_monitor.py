import datetime
import time
import os
import requests
import json
from duckduckgo_search import DDGS

# Target Companies
TARGETS = [
    "三花智控",
    "长飞光纤",
    "宏和科技",
    "阳光电源"
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

def get_company_info(name):
    """
    Agentic search: We search for both stock data and news generally.
    """
    # 1. Broad Search for Company Today
    query = f"{name} 股价 新闻 最新"
    results = search_web(query, max_results=8)
    
    return {
        "name": name,
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
        context_str += f"=== Company: {item['name']} ===\n"
        context_str += "Raw Search Results:\n"
        for res in item['search_results']:
            context_str += f"- Title: {res.get('title')}\n  Snippet: {res.get('body')}\n  Link: {res.get('href')}\n"
        context_str += "\n"

    system_prompt = """
    You are an intelligent financial assistant. 
    You have been provided with raw web search results for specific companies.
    
    Your Task:
    Generate a concise "Daily News Monitor Report" in Simplified Chinese.
    
    For each company:
    1. **Identify Stock Info**: Extract the most recent stock price and change percentage if available in the snippets. If not found, explicitly say "未检索到最新股价".
    2. **Summarize News**: Identify key financial news or announcements. If the search results are generic or old, say "暂无今日重大新闻".
    3. **Provide Links**: Use the links provided in the raw data to reference your sources.
    
    Output Format:
    # 上市公司每日新闻监测日报 [Date]
    
    ## [Company Name]
    **市场表现**: [Price / Change or "未检索到"]
    **最新动态**:
    - [News Summary] ([Source Title](Source Link))
    ...
    
    If no relevant info is found for a company, state it clearly.
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
    print("Starting Intelligent News Monitor (Agentic Search Mode)...", flush=True)
    
    # 1. Collect Data via Web Search
    raw_data = []
    for name in TARGETS:
        data = get_company_info(name)
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

