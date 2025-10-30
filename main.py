import requests
import ipaddress
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os
import re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba

# --- 调试设置 ---
# 将此IP设置为您想单独测试的IP地址。如果设为None，则运行完整扫描。
DEBUG_IP = '221.238.245.2' 
# DEBUG_IP = None # 正式运行时请使用此行

# --- 核心更新：增强版请求头 ---
# 模拟一个非常常见的 Windows + Chrome 浏览器环境
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# (其余代码与之前的调试版本完全相同)

data = []
ip_ranges = ['221.238.245.0/24', '60.29.153.0/24', '111.33.76.0/23', '117.131.219.0/24']

def get_data(response, output_folder):
    soup = BeautifulSoup(response.content, 'html.parser')
    ip_address = response.url.split('=')[-1]
    
    if DEBUG_IP and ip_address == DEBUG_IP:
        debug_html_path = os.path.join(output_folder, f'debug_{ip_address}.html')
        with open(debug_html_path, 'wb') as f: f.write(response.content)
        print(f"DEBUG: Saved HTML content for {ip_address} to {debug_html_path}")

    data_table = soup.find('table')
    if not data_table:
        print(f"INFO: No <table> found on page for IP {ip_address}. Skipping.")
        return

    rows = data_table.find_all('tr')
    if len(rows) <= 1:
        print(f"INFO: Data table for IP {ip_address} is empty. Skipping.")
        return

    print(f"SUCCESS: Found {len(rows) - 1} data rows for IP {ip_address}.")
    for tr in rows:
        tds = tr.find_all('td')
        if len(tds) == 5:
            data.append([ip_address, tds[0].text.strip(), tds[1].text.strip(), tds[2].text.strip(), tds[3].text.strip()])
        elif len(tds) > 0:
            print(f"WARNING: Skipping row for IP {ip_address} because it has {len(tds)} columns instead of 5.")

def get_response(ip_list, output_folder):
    for ip in ip_list:
        url = f'https://iknowwhatyoudownload.com/en/peer/?ip={ip}'
        try:
            print(f"Requesting data for IP: {ip}...")
            # 使用新的headers
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code == 200:
                get_data(response, output_folder)
            else:
                print(f"ERROR: Received status code {response.status_code} for IP {ip}. Skipping.")
        
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Could not connect to {url}: {e}")
            pass

def analyze_and_save(df, output_folder):
    if df.empty:
        print("DataFrame is empty, skipping analysis.")
        return
    # ... (此处省略未改变的分析代码)
    print("\nAnalyzing download categories...")
    category_counts = df['Category'].value_counts()
    category_counts.to_csv(os.path.join(output_folder, 'category_analysis.csv'))
    plt.figure(figsize=(12, 8)); category_counts.plot(kind='barh'); plt.title('Download Category Distribution'); plt.tight_layout(); plt.savefig(os.path.join(output_folder, 'category_distribution.png')); plt.close()
    print("Category analysis saved.")
    print("\nGenerating word cloud...")
    text = " ".join(df['Name'].dropna()); word_list = jieba.cut(text, cut_all=False); text_jieba = " ".join(word_list)
    try:
        wordcloud = WordCloud(width=1200, height=800, background_color='white', font_path='/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc').generate(text_jieba)
        wordcloud.to_file(os.path.join(output_folder, 'content_wordcloud.png'))
        print("Word cloud saved.")
    except Exception as e: print(f"Could not generate word cloud (might be a font issue): {e}")
    print("\nAnalyzing for NSFW content...")
    nsfw_keywords = ['adult', 'porn', 'xxx', 'sex', 'hentai', 'jav', 'av']; nsf_pattern = '|'.join(nsfw_keywords)
    df['is_nsfw'] = df['Name'].str.contains(nsf_pattern, case=False, na=False) | df['Category'].str.contains(nsf_pattern, case=False, na=False)
    nsfw_count = df['is_nsfw'].sum(); total_count = len(df); nsfw_percentage = (nsfw_count / total_count * 100) if total_count > 0 else 0
    with open(os.path.join(output_folder, 'nsfw_analysis.txt'), 'w') as f: f.write(f"NSFW Analysis Report\n-----------------\nTotal Items: {total_count}\nNSFW Items: {nsfw_count}\nNSFW Percentage: {nsfw_percentage:.2f}%\n")
    if nsfw_count > 0: df[df['is_nsfw']].to_csv(os.path.join(output_folder, 'nsfw_items.csv'), index=False); print(f"NSFW analysis saved. {nsfw_count} items flagged.")
    else: print("No NSFW content detected.")

if __name__ == '__main__':
    now = datetime.datetime.utcnow()
    date_folder = now.strftime('%Y-%m-%d')
    os.makedirs(date_folder, exist_ok=True)
    
    target_ips = []
    if DEBUG_IP:
        print(f"--- RUNNING IN DEBUG MODE FOR IP: {DEBUG_IP} ---")
        target_ips = [DEBUG_IP]
    else:
        print("--- RUNNING IN FULL SCAN MODE ---")
        for ip_range in ip_ranges:
            network = ipaddress.ip_network(ip_range)
            for ip in network.hosts(): target_ips.append(str(ip))

    get_response(target_ips, date_folder)

    if not data:
        print("\nFINAL RESULT: No data was scraped. Check logs for warnings and errors.")
        with open(os.path.join(date_folder, 'NO_DATA_SCRAPED.md'), 'w') as f: f.write(f"# No data was scraped on {date_folder}\n\nCheck the action logs for details.\n")
        if DEBUG_IP: print(f"\nACTION REQUIRED: Please check the generated file 'debug_{DEBUG_IP}.html' in the '{date_folder}' directory to see what the script received from the server.")
        exit()
        
    df = pd.DataFrame(data, columns=['IP_Address', 'First_Seen', 'Last_Seen', 'Category', 'Name'])
    raw_data_path = os.path.join(date_folder, 'data.csv')
    df.to_csv(raw_data_path, index=False)
    print(f"\nRaw data saved to {raw_data_path}")

    analyze_and_save(df, date_folder)
    print("\nScript finished successfully.")