import yfinance as yf
import datetime
import time

# Target Companies
TARGETS = [
    {"name": "三花智控", "code": "002050.SZ"},
    {"name": "长飞光纤", "code": "6869.HK"},
    {"name": "宏和科技", "code": "603256.SS"},
    {"name": "阳光电源", "code": "300274.SZ"}
]

def get_stock_data(symbol):
    print(f"Fetching data for {symbol}...", flush=True)
    try:
        ticker = yf.Ticker(symbol)
        
        # Fetch history for price (most reliable for current/last close)
        # period='1d' might return empty if market just opened or closed, so use '5d' and take last
        try:
            hist = ticker.history(period="5d")
            
            if hist.empty:
                price = "N/A"
                change_percent = "N/A"
            else:
                last_quote = hist.iloc[-1]
                prev_quote = hist.iloc[-2] if len(hist) > 1 else last_quote # Fallback if only 1 day
                
                price = f"{last_quote['Close']:.2f}"
                
                if len(hist) > 1:
                    change = (last_quote['Close'] - prev_quote['Close']) / prev_quote['Close'] * 100
                    change_percent = f"{change:+.2f}%"
                else:
                    change_percent = "N/A"
        except Exception as e:
            print(f"  Price fetch failed: {e}")
            price = "N/A"
            change_percent = "N/A"

        # Fetch News
        try:
            news = ticker.news
        except Exception as e:
            print(f"  News fetch failed: {e}")
            news = []
        
        return {
            "price": price,
            "change_percent": change_percent,
            "news": news
        }

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def generate_report():
    today = datetime.date.today().strftime("%Y-%m-%d")
    report_content = f"# 上市公司每日新闻监测日报\n\n**日期**: {today}\n\n"
    
    has_news_today = False
    
    for company in TARGETS:
        data = get_stock_data(company['code'])
        
        if not data:
            report_content += f"## {company['name']} ({company['code']})\n* 数据获取失败\n\n"
            continue
            
        report_content += f"## {company['name']} ({company['code']})\n"
        
        # Market Data
        price_display = data['price']
        change_display = data['change_percent']
        report_content += f"**市场表现**: 收盘价 {price_display} | 涨跌幅 {change_display}\n\n"
        
        # News
        # yfinance news items usually have 'title', 'link', 'providerPublishTime'
        current_news = []
        if data['news']:
            for item in data['news']:
                # Check date if possible, but YF news can be mixed. 
                # We'll just take the top 3 most recent.
                current_news.append(item)
                
            if current_news:
                report_content += "**最新动态**:\n"
                for news in current_news[:3]: # Top 3
                    title = news.get('title', 'No Title')
                    link = news.get('link', '#')
                    # publisher = news.get('publisher', 'Unknown')
                    # pub_time = datetime.datetime.fromtimestamp(news.get('providerPublishTime', 0)).strftime('%Y-%m-%d')
                    
                    report_content += f"*   [{title}]({link})\n"
                has_news_today = True
            else:
                report_content += "**最新动态**: 暂无今日重大新闻，仅记录市场表现。\n"
        else:
            report_content += "**最新动态**: 暂无今日重大新闻，仅记录市场表现。\n"
        
        report_content += "\n---\n\n"
        
    if not has_news_today:
        report_content += "\n*注：今日监测范围内未发现重大新闻，以上主要为市场行情记录。*\n"

    return report_content

if __name__ == "__main__":
    print("开始执行新闻监测任务 (使用 yfinance)...", flush=True)
    report = generate_report()
    
    print("\n" + "="*30 + " 监测日报 " + "="*30 + "\n")
    print(report)
    
    filename = f"daily_report_{datetime.date.today().strftime('%Y%m%d')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n日报已保存至: {filename}")
