import cloudscraper
import ipaddress
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time

# 使用 cloudscraper 创建一个 scraper 实例，它会自动处理 Cloudflare 质询
scraper = cloudscraper.create_scraper()

# 定义请求头 (User-Agent 依然重要)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}
# 定义存储数据的变量
data = []
# 定义要查询的IP网段
ip_ranges = ['221.238.245.0/24', '60.29.153.0/24', '111.33.76.0/23', '117.131.219.0/24']

# 提取数据并存储到pandas变量中 (此函数无需修改)
def get_data(response):
    soup = BeautifulSoup(response.content, 'html.parser')

    for tr in soup.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) == 5:
            date1 = tds[0].text.strip()
            date2 = tds[1].text.strip()
            category = tds[2].text.strip()
            name = tds[3].text.strip()
            data.append([date1, date2, category, name])

# 遍历IP网段，生成所有IP地址，并发送请求并读取返回包
def get_response(ip_ranges):
    for ip_range in ip_ranges:
        print(f"Processing IP range: {ip_range}")
        network = ipaddress.ip_network(ip_range)
        for ip in network.hosts():
            url = 'https://iknowwhatyoudownload.com/en/peer/?ip=' + str(ip)
            try:
                # 使用 scraper.get() 代替 requests.get()
                response = scraper.get(url, headers=headers)
                
                # 检查状态码是否为200 (OK)
                if response.status_code == 200:
                    get_data(response)
                else:
                    # 如果状态码不是200，打印出来方便排查
                    print(f"Failed for IP {ip}, Status Code: {response.status_code}")

                # 在请求之间增加一个小的延迟
                time.sleep(0.5)

            except Exception as e:
                # 捕获 cloudscraper 可能抛出的异常
                print(f"An error occurred for IP {ip}: {e}")
                pass


if __name__ == '__main__':
    # 发送请求并读取返回包
    get_response(ip_ranges)

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
