from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import ipaddress
import datetime
import time

# --- Selenium 设置 ---
chrome_options = Options()
# 在 GitHub Actions 环境中必须使用无头模式和 no-sandbox
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

# 初始化 WebDriver
# Selenium 会自动在系统 PATH 中找到 chromedriver
service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)
# --- Selenium 设置结束 ---

# 定义存储数据的变量
data = []
# 定义要查询的IP网段
ip_ranges = ['221.238.245.0/24', '60.29.153.0/24', '111.33.76.0/23', '117.131.219.0/24']

# 提取数据并存储到pandas变量中 (此函数无需修改)
def get_data(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    rows_found = 0
    for tr in soup.select("table.table-striped tbody tr"): # 更精确的选择器
        tds = tr.find_all('td')
        if len(tds) == 5:
            date1 = tds[0].text.strip()
            date2 = tds[1].text.strip()
            category = tds[2].text.strip()
            name = tds[3].text.strip()
            data.append([date1, date2, category, name])
            rows_found += 1
    if rows_found > 0:
        print(f"Found {rows_found} data rows.")

# 遍历IP网段，生成所有IP地址，并发送请求并读取返回包
def get_response(ip_ranges):
    for ip_range in ip_ranges:
        print(f"Processing IP range: {ip_range}")
        network = ipaddress.ip_network(ip_range)
        for ip in network.hosts():
            url = 'https://iknowwhatyoudownload.com/en/peer/?ip=' + str(ip)
            try:
                print(f"Scraping IP: {ip}")
                # 使用 Selenium 打开页面
                driver.get(url)
                
                # 等待页面加载，Cloudflare可能会在这里执行JS挑战
                # 根据网络情况，可能需要调整等待时间
                time.sleep(5) # 等待5秒让JS执行完毕
                
                # 获取页面源代码并解析
                page_source = driver.page_source

                # 检查是否被成功加载或被拦截
                if "Just a moment..." in page_source or "Checking your browser" in page_source:
                    print(f"Cloudflare challenge failed for {ip}. Waiting longer...")
                    time.sleep(10) # 如果被拦截，再多等10秒
                    page_source = driver.page_source

                if "No data found for this IP" not in page_source:
                     get_data(page_source)
                else:
                    print("No data on site for this IP.")

            except Exception as e:
                print(f"An error occurred for IP {ip}: {e}")
                pass

if __name__ == '__main__':
    try:
        # 发送请求并读取返回包
        get_response(ip_ranges)
    finally:
        # 确保无论如何都关闭浏览器驱动
        driver.quit()

    # 创建pandas变量
    df = pd.DataFrame(data, columns=['Date1', 'Date2', 'Category', 'Name'])

    # 打印最终结果
    print("\n--- Final DataFrame ---")
    if df.empty:
        print("No data was scraped.")
    else:
        print(df)
    print("-----------------------\n")

    # 获取当前时间
    now = datetime.datetime.now()
    # 生成文件名
    filename = now.strftime('%Y-%m-%d') + '_data.csv'

    # 保存数据到CSV文件中
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")
