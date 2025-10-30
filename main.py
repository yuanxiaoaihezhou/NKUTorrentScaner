import requests
import ipaddress
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os
import re
import matplotlib
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba # 用于中文分词

# 设置matplotlib后端，这在没有图形界面的服务器上是必需的
matplotlib.use('Agg')

# --- 1. 数据抓取部分 (与之前类似) ---

# 定义请求头
headers = {
    'Host': 'iknowwhatyoudownload.com',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'close',
}
data = []
ip_ranges = ['221.238.245.0/24', '60.29.153.0/24', '111.33.76.0/23', '117.131.219.0/24']

def get_data(response):
    soup = BeautifulSoup(response.content, 'html.parser')
    ip_address = response.url.split('=')[-1]
    for tr in soup.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) == 5:
            data.append([ip_address, tds[0].text.strip(), tds[1].text.strip(), tds[2].text.strip(), tds[3].text.strip()])

def get_response(ip_ranges):
    for ip_range in ip_ranges:
        print(f"Scanning IP range: {ip_range}")
        network = ipaddress.ip_network(ip_range)
        for ip in network.hosts():
            url = f'https://iknowwhatyoudownload.com/en/peer/?ip={ip}'
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    get_data(response)
            except requests.exceptions.RequestException as e:
                print(f"Could not connect to {url}: {e}")
                pass

# --- 2. 数据分析与可视化部分 ---

def analyze_and_save(df, output_folder):
    """对DataFrame进行分析并保存结果"""
    if df.empty:
        print("DataFrame is empty, skipping analysis.")
        return

    # --- 2.1 内容类别分析 ---
    print("\nAnalyzing download categories...")
    category_counts = df['Category'].value_counts()
    category_counts.to_csv(os.path.join(output_folder, 'category_analysis.csv'))
    
    # 绘制条形图
    plt.figure(figsize=(12, 8))
    category_counts.plot(kind='barh')
    plt.title('Download Category Distribution')
    plt.xlabel('Count')
    plt.ylabel('Category')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'category_distribution.png'))
    plt.close()
    print("Category analysis saved.")

    # --- 2.2 词云分析 ---
    print("\nGenerating word cloud...")
    text = " ".join(df['Name'].dropna())
    # 使用jieba进行中文分词
    word_list = jieba.cut(text, cut_all=False)
    text_jieba = " ".join(word_list)
    
    # 注意: GitHub Actions的运行环境可能没有中文字体。
    # 这里我们尝试使用一个常见的无衬线字体。如果词云出现方框，需要指定一个存在的中文字体路径。
    # 例如 font_path='/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
    try:
        wordcloud = WordCloud(width=1200, height=800, background_color='white', font_path=None).generate(text_jieba)
        wordcloud.to_file(os.path.join(output_folder, 'content_wordcloud.png'))
        print("Word cloud saved.")
    except Exception as e:
        print(f"Could not generate word cloud (might be a font issue): {e}")


    # --- 2.3 NSFW 内容分析 ---
    print("\nAnalyzing for NSFW content...")
    # 定义一个简单的NSFW关键词列表（您可以根据需要扩展）
    # 使用正则表达式的'|' (OR) 来匹配任何一个词
    nsfw_keywords = [
        'adult', 'porn', 'xxx', 'sex', 'hentai', 'jav', 'av' # 示例关键词
    ]
    nsfw_pattern = '|'.join(nsfw_keywords)
    
    # 在'Name'和'Category'列中搜索关键词，不区分大小写
    df['is_nsfw'] = df['Name'].str.contains(nsfw_pattern, case=False, na=False) | \
                    df['Category'].str.contains(nsfw_pattern, case=False, na=False)
    
    nsfw_count = df['is_nsfw'].sum()
    total_count = len(df)
    nsfw_percentage = (nsfw_count / total_count * 100) if total_count > 0 else 0
    
    # 创建分析报告
    nsfw_report = f"""NSFW Content Analysis Report
-----------------------------
Total Items Scanned: {total_count}
NSFW Items Detected: {nsfw_count}
NSFW Percentage: {nsfw_percentage:.2f}%
-----------------------------
"""
    
    # 保存报告到文件
    with open(os.path.join(output_folder, 'nsfw_analysis.txt'), 'w') as f:
        f.write(nsfw_report)
    
    # 将被标记为NSFW的项目单独保存到一个CSV中
    if nsfw_count > 0:
        nsfw_items = df[df['is_nsfw']]
        nsfw_items.to_csv(os.path.join(output_folder, 'nsfw_items.csv'), index=False)
        print(f"NSFW analysis saved. {nsfw_count} items flagged.")
    else:
        print("No NSFW content detected.")


# --- 3. 主程序执行部分 ---

if __name__ == '__main__':
    # 抓取数据
    get_response(ip_ranges)

    if not data:
        print("No data was scraped. Exiting.")
        # 即使没有数据，也创建一个空的报告文件夹和README，以便git可以提交
        now = datetime.datetime.utcnow()
        date_folder = now.strftime('%Y-%m-%d')
        os.makedirs(date_folder, exist_ok=True)
        with open(os.path.join(date_folder, 'README.md'), 'w') as f:
            f.write(f"# Data for {date_folder}\n\nNo data was scraped on this day.\n")
        exit()
        
    # 创建DataFrame
    df = pd.DataFrame(data, columns=['IP_Address', 'First_Seen', 'Last_Seen', 'Category', 'Name'])

    # --- 文件与文件夹设置 ---
    now = datetime.datetime.utcnow()
    date_folder = now.strftime('%Y-%m-%d')
    os.makedirs(date_folder, exist_ok=True)
    
    # 保存原始数据
    raw_data_path = os.path.join(date_folder, 'data.csv')
    df.to_csv(raw_data_path, index=False)
    print(f"\nRaw data saved to {raw_data_path}")

    # 执行分析
    analyze_and_save(df, date_folder)

    print("\nScript finished successfully.")