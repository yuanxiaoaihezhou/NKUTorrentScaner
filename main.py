import time
import pandas as pd
import datetime
import os
from bs4 import BeautifulSoup
import ipaddress

# 导入Selenium相关库
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import jieba

# --- 调试设置 ---
DEBUG_IP = '221.238.245.2'
# DEBUG_IP = None # 正式运行时请使用此行

# --- Selenium 设置 ---
def setup_driver():
    """配置并返回一个无头Chrome浏览器实例"""
    chrome_options = Options()
    # 无头模式：在后台运行浏览器，没有UI界面
    chrome_options.add_argument("--headless")
    # 禁用GPU加速，在服务器环境中是必需的
    chrome_options.add_argument("--disable-gpu")
    # 解决在Linux root环境下运行的问题
    chrome_options.add_argument("--no-sandbox")
    # 禁用/dev/shm使用，防止内存不足问题
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 设置一个常规的User-Agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    
    # 使用webdriver-manager自动下载并配置ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("Selenium WebDriver for Chrome is set up.")
    return driver

# --- 数据抓取与解析 (使用Selenium) ---
data = []

def get_data_from_page(page_source, ip_address):
    """从页面源代码中解析数据"""
    soup = BeautifulSoup(page_source, 'html.parser')
    data_table = soup.find('table')
    if not data_table:
        print(f"INFO: No <table> found for IP {ip_address}.")
        return
    
    rows = data_table.find_all('tr')
    if len(rows) <= 1:
        print(f"INFO: Data table for IP {ip_address} is empty.")
        return

    print(f"SUCCESS: Found {len(rows) - 1} data rows for IP {ip_address}.")
    for tr in rows:
        tds = tr.find_all('td')
        if len(tds) == 5:
            data.append([ip_address, tds[0].text.strip(), tds[1].text.strip(), tds[2].text.strip(), tds[3].text.strip()])

def get_response_with_selenium(driver, ip_list):
    """使用Selenium遍历IP并抓取数据"""
    for ip in ip_list:
        url = f'https://iknowwhatyoudownload.com/en/peer/?ip={ip}'
        print(f"Requesting data for IP: {ip} using Selenium...")
        try:
            driver.get(url)
            # 等待几秒钟，让页面上的JS挑战（如果存在）完成
            time.sleep(5) 
            
            # 检查是否被Cloudflare等拦截
            if "checking your browser" in driver.title.lower() or "just a moment" in driver.page_source.lower():
                print(f"WARNING: Detected a JS challenge for IP {ip}. Waiting longer...")
                time.sleep(10) # 再多等10秒

            # 获取最终的页面源代码并解析
            get_data_from_page(driver.page_source, ip)
            
        except Exception as e:
            print(f"ERROR: An error occurred with Selenium for IP {ip}: {e}")
            # 出现错误时，截个图保存下来，方便调试
            driver.save_screenshot(os.path.join(date_folder, f'error_{ip}.png'))


# (analyze_and_save 函数保持不变, 此处省略)
def analyze_and_save(df, output_folder):
    if df.empty: print("DataFrame is empty, skipping analysis."); return
    print("\nAnalyzing download categories..."); category_counts = df['Category'].value_counts(); category_counts.to_csv(os.path.join(output_folder, 'category_analysis.csv')); plt.figure(figsize=(12, 8)); category_counts.plot(kind='barh'); plt.title('Download Category Distribution'); plt.tight_layout(); plt.savefig(os.path.join(output_folder, 'category_distribution.png')); plt.close(); print("Category analysis saved.")
    print("\nGenerating word cloud..."); text = " ".join(df['Name'].dropna()); word_list = jieba.cut(text, cut_all=False); text_jieba = " ".join(word_list)
    try: wordcloud = WordCloud(width=1200, height=800, background_color='white', font_path=None).generate(text_jieba); wordcloud.to_file(os.path.join(output_folder, 'content_wordcloud.png')); print("Word cloud saved.")
    except Exception as e: print(f"Could not generate word cloud (might be a font issue): {e}")
    print("\nAnalyzing for NSFW content..."); nsfw_keywords = ['adult', 'porn', 'xxx', 'sex', 'hentai', 'jav', 'av']; nsfw_pattern = '|'.join(nsfw_keywords); df['is_nsfw'] = df['Name'].str.contains(nsfw_pattern, case=False, na=False) | df['Category'].str.contains(nsfw_pattern, case=False, na=False); nsfw_count = df['is_nsfw'].sum(); total_count = len(df); nsfw_percentage = (nsfw_count / total_count * 100) if total_count > 0 else 0;
    with open(os.path.join(output_folder, 'nsfw_analysis.txt'), 'w') as f: f.write(f"NSFW Analysis Report\n-----------------\nTotal Items: {total_count}\nNSFW Items: {nsfw_count}\nNSFW Percentage: {nsfw_percentage:.2f}%\n");
    if nsfw_count > 0: df[df['is_nsfw']].to_csv(os.path.join(output_folder, 'nsfw_items.csv'), index=False); print(f"NSFW analysis saved. {nsfw_count} items flagged.");
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
        for ip_range in ['221.238.245.0/24', '60.29.153.0/24', '111.33.76.0/23', '117.131.219.0/24']:
            network = ipaddress.ip_network(ip_range)
            for ip in network.hosts(): target_ips.append(str(ip))

    # 初始化浏览器驱动
    driver = setup_driver()
    
    # 执行抓取
    get_response_with_selenium(driver, target_ips)
    
    # 关闭浏览器
    driver.quit()

    if not data:
        print("\nFINAL RESULT: No data was scraped.")
        with open(os.path.join(date_folder, 'NO_DATA_SCRAPED.md'), 'w') as f: f.write(f"# No data was scraped on {date_folder}\n")
        exit()
        
    df = pd.DataFrame(data, columns=['IP_Address', 'First_Seen', 'Last_Seen', 'Category', 'Name'])
    df.to_csv(os.path.join(date_folder, 'data.csv'), index=False)
    print(f"\nRaw data saved to {os.path.join(date_folder, 'data.csv')}")

    analyze_and_save(df, date_folder)
    print("\nScript finished successfully.")
