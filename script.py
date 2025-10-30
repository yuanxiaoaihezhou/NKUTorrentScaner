import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import pandas as pd
import ipaddress
import datetime
import time
import traceback

# --- undetected-chromedriver 设置 ---
print("Setting up browser options...")
options = uc.ChromeOptions()
# 在 GitHub Actions 环境中必须使用无头模式
# undetected-chromedriver 会自动处理很多反检测选项，但这些在CI环境中是必须的
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")

print("Initializing undetected_chromedriver...")
# 使用 try-except 块来捕获驱动初始化时可能发生的错误
try:
    # use_subprocess=True 在 Linux/Docker 环境下更稳定
    driver = uc.Chrome(options=options, use_subprocess=True)
    print("Browser initialized successfully.")
except Exception as e:
    print("!!! Failed to initialize browser driver. Exiting. !!!")
    print(f"Error: {e}")
    print(traceback.format_exc())
    # 如果驱动都启动失败，直接退出
    exit()
# --- 设置结束 ---

# 定义存储数据的变量
data = []
# 定义要查询的IP网段
ip_ranges = ['221.238.245.0/24', '60.29.153.0/24', '111.33.76.0/23', '117.131.219.0/24']

# 提取数据并存储到pandas变量中
def get_data(page_source, ip):
    soup = BeautifulSoup(page_source, 'html.parser')
    rows_found = 0
    # 使用更精确的CSS选择器来定位数据行
    for tr in soup.select("table.table-striped tbody tr"):
        tds = tr.find_all('td')
        if len(tds) == 5:
            date1 = tds[0].text.strip()
            date2 = tds[1].text.strip()
            category = tds[2].text.strip()
            name = tds[3].text.strip()
            data.append([date1, date2, category, name])
            rows_found += 1
    if rows_found > 0:
        print(f"Success for IP {ip}: Found {rows_found} data rows.")
    else:
        # 如果页面有表格但没数据，也打印出来
        if soup.select_one("table.table-striped"):
             print(f"Warning for IP {ip}: Page has a table but no data rows were found.")

# 遍历IP网段
def get_response(ip_ranges):
    # 只处理第一个网段的少量IP用于测试，避免运行时间过长
    ip_to_test = []
    network = ipaddress.ip_network(ip_ranges[0])
    for i, ip in enumerate(network.hosts()):
        if i >= 10: # 先测试10个IP
            break
        ip_to_test.append(ip)

    for ip in ip_to_test:
        url = f'https://iknowwhatyoudownload.com/en/peer/?ip={ip}'
        print(f"\n--- Scraping IP: {ip} ---")
        try:
            driver.get(url)
            
            # 使用智能等待，而不是固定的 time.sleep
            print("Waiting for Cloudflare challenge (up to 30s)...")
            time.sleep(15) # 给一个初始的较长等待时间
            
            page_source = driver.page_source
            page_title = driver.title

            # 增加更详细的调试信息
            print(f"Page Title: {page_title}")
            print(f"Page Source Length: {len(page_source)}")

            # 检查是否仍然停留在挑战页面
            if "Just a moment..." in page_title or "challenge" in page_title.lower():
                print("!!! Still on Cloudflare challenge page. This method failed. !!!")
                # 打印页面内容以供分析
                print("Page source snippet:", page_source[:600])
                continue # 继续下一个IP

            if "No data found for this IP" not in page_source:
                 get_data(page_source, ip)
            else:
                print(f"Info for IP {ip}: Site reports no data.")

        except Exception as e:
            print(f"!!! An error occurred for IP {ip}: {e} !!!")
            print(traceback.format_exc())
            pass

if __name__ == '__main__':
    try:
        get_response(ip_ranges)
    finally:
        print("\nClosing browser driver...")
        driver.quit()
        print("Driver closed.")

    df = pd.DataFrame(data, columns=['Date1', 'Date2', 'Category', 'Name'])

    print("\n--- Final DataFrame ---")
    if df.empty:
        print("No data was scraped.")
    else:
        print(df)
    print("-----------------------\n")

    now = datetime.datetime.now()
    filename = now.strftime('%Y-%m-%d') + '_data.csv'

    df.to_csv(filename, index=False)
    print(f"Operation finished. Data saved to {filename}")