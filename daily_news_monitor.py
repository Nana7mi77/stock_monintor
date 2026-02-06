import datetime
import time
import os
import requests
import json

# Target Companies
TARGETS = [
    {"name": "三花智控", "site": "finance.sina.com.cn"},
    {"name": "长飞光纤", "site": "finance.sina.com.cn"},
    {"name": "宏和科技", "site": "finance.sina.com.cn"},
    {"name": "阳光电源", "site": "finance.sina.com.cn"}
]

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

def generate_report_for_company(target):
    """
    Ask DeepSeek directly to provide info (Simulating "Search itself" / Hallucination check).
    """
    name = target["name"]
    site = target["site"]
    today = datetime.date.today().strftime("%Y-%m-%d")

    system_prompt = """
    You are an intelligent financial assistant.
    The user wants you to act as if you can browse the specified website to get real-time information.
    
    Your Task:
    Provide a "Daily News Monitor Report" for the specified company.
    
    **Important Note**: 
    If you do not have real-time internet access, please use your internal knowledge to provide *general* information about where to find this data, 
    OR (if allowed by your capabilities) perform the search. 
    If you cannot access today's real-time data, please honestly state: "Due to lack of real-time internet access, I cannot provide today's specific data."
    
    However, if you DO have access (e.g. via specific model features), please provide:
    1. Latest Stock Price.
    2. Latest News Headlines.
    """

    user_prompt = f"""
    Target Company: {name}
    Preferred Source: {site}
    Date: {today}

    Please search for the latest stock price and news for {name} on {site} and summarize it.
    """

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

    print(f"Asking DeepSeek about {name}...", flush=True)
    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"DeepSeek API failed: {e}")
        return f"Error fetching info for {name}: {e}"

if __name__ == "__main__":
    print("Starting Intelligent News Monitor (Direct API Mode)...", flush=True)
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    final_report = f"# 上市公司每日新闻监测日报 {today}\n\n"
    
    if DEEPSEEK_API_KEY:
        for target in TARGETS:
            content = generate_report_for_company(target)
            final_report += f"## {target['name']}\n{content}\n\n---\n\n"
            time.sleep(1)
    else:
        final_report += "DEEPSEEK_API_KEY not set."

    print("\n" + "="*30 + " Generated Report " + "="*30 + "\n")
    print(final_report)
    
    # 3. Save to file
    filename = f"daily_report_{datetime.date.today().strftime('%Y%m%d')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_report)
    print(f"\nReport saved to: {filename}")
    
    # Email sending
    # email_subject = f"上市公司新闻日报 - {datetime.date.today().strftime('%Y-%m-%d')}"
    # send_email(email_subject, report)

