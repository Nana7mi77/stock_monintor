import requests
import json
import sys
import traceback

print("Script started.", flush=True)

# Configuration
API_KEY = "sk-5799952aa25543bfae084566075b795f"
BASE_URL = "https://api.deepseek.com/chat/completions"

def generate_workflow():
    print("Function generate_workflow started.", flush=True)
    # Context based on the previous task
    experience_description = """
    最近的任务是为一个金融分析场景创建一个每日新闻监测流程。
    具体经验如下：
    1.  **目标对象**：需要监测特定的上市公司列表（例如：三花智控 002050.SZ、长飞光纤 6869.HK、宏和科技 603256.SS、阳光电源 300274.SZ）。
    2.  **数据来源**：使用权威财经网站（如 Yahoo Finance）作为主要信息源。
    3.  **检索策略**：
        *   使用“公司英文名”或“股票代码”作为关键词进行搜索。
        *   使用日期关键词（如 "February 6 2026" 或 "Today"）来过滤即时新闻。
    4.  **信息筛选**：
        *   优先寻找公司公告、重大业务进展、财报发布等实质性新闻。
        *   排除过期资讯或无关的通用市场综述。
    5.  **兜底机制**：如果当日无重大新闻，则记录当天的股价表现（涨跌幅、收盘价）作为替代信息。
    6.  **输出格式**：形成一份结构化的日报，包含“新闻动态”和“市场表现”两部分。
    """

    prompt = f"""
    请根据上述的“背景经验”，总结并生成一个标准化的《上市公司每日新闻监测工作流程》。
    
    要求：
    1.  **流程清晰**：分步骤描述，从输入关注列表到输出最终报告。
    2.  **实用性强**：步骤应具体可执行，适合人工操作或指导自动化脚本开发。
    3.  **包含关键点**：涵盖多关键词检索、时间过滤、信息验证和无新闻时的处理方案。
    4.  **输出风格**：专业、简洁。

    背景经验：
    {experience_description}
    """

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are an expert business process analyst."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    print("Sending request to DeepSeek API...", flush=True)
    
    try:
        # Increase timeout just in case
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=120)
        print(f"Response status code: {response.status_code}", flush=True)
        
        response.raise_for_status()
        
        result = response.json()
        print("Response JSON parsed successfully.", flush=True)
        
        content = result['choices'][0]['message']['content']
        
        print("Content extracted.", flush=True)
        
        # Write to file
        with open("workflow.md", "w", encoding="utf-8") as f:
            f.write(content)
        print("workflow.md written.", flush=True)
        
        # Print content to console so user can see it
        print("\n" + "="*20 + " Generated Workflow " + "="*20 + "\n", flush=True)
        print(content, flush=True)
        print("\n" + "="*50, flush=True)
        
    except Exception as e:
        print(f"An error occurred: {e}", flush=True)
        traceback.print_exc()
        if 'response' in locals():
            print(f"Response content: {response.text}", flush=True)

if __name__ == "__main__":
    generate_workflow()
