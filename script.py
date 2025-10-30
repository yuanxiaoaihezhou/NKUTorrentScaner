import requests
import ipaddress
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time # 引入 time 模块

# 定义请求头
headers = {
    'Host': 'iknowwhatyoudownload.com',
    'Cache-Control': 'max-age=0',
    'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Ubuntu"',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36', # 更换为更常见的桌面User-Agent
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-User': '?1',
    'Sec-Fetch-Dest': 'document',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'close',
}
# 定义存储数据的变量
data = []
# 定义要查询的IP网段
ip_ranges = ['221.238.245.0/24', '60.29.153.0/24', '111.33.76.0/23', '117.131.219.0/24']

# 提取数据并存储到pandas变量中
def get_data(response):
    soup = BeautifulSoup(response.content, 'html.parser')

    # 检查是否有 "No data found for this IP" 这样的提示
    if "No data found" in response.text:
        print("Debug: Page indicates no data found.")
        return

    found_rows = 0
    for tr in soup.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) == 5:
            date1 = tds[0].text.strip()
            date2 = tds[1].text.strip()
            category = tds[2].text.strip()
            name = tds[3].text.strip()
            data.append([date1, date2, category, name])
            found_rows += 1
    
    if found_rows > 0:
        print(f"Debug: Found {found_rows} data rows.")
    else:
        # 如果没有找到任何数据行，这很可能说明页面结构不是我们预期的
        print("Debug: No rows with 5 <td> elements found. The page structure might have changed or it's an anti-bot page.")


# 遍历IP网段，生成所有IP地址，并发送请求并读取返回包
def get_response(ip_ranges):
    # 添加一个变量来控制只调试第一个IP
    first_ip_debugged = False
    for ip_range in ip_ranges:
        print(ip_range)
        network = ipaddress.ip_network(ip_range)
        for ip in network.hosts():
            url = 'https://iknowwhatyoudownload.com/en/peer/?ip=' + str(ip)
            try:
                response = requests.get(url, headers=headers)
                
                # --- 新增的调试代码 ---
                if not first_ip_debugged:
                    print(f"--- Debugging First IP: {ip} ---")
                    print(f"Status Code: {response.status_code}")
                    print("Response Text (first 500 chars):")
                    print(response.text[:500])
                    print("--- End Debugging ---")
                    first_ip_debugged = True
                # --- 调试代码结束 ---

                get_data(response)
                # 在请求之间增加一个小的随机延迟，模仿人类行为
                time.sleep(0.5)

            except requests.exceptions.ConnectionError as e:
                print(f"Connection error for {ip}: {e}")
                pass


if __name__ == '__main__':
    # 发送请求并读取返回包
    get_response(ip_ranges)

    # 创建pandas变量
    df = pd.DataFrame(data, columns=['Date1', 'Date2', 'Category', 'Name'])

    # 打印pandas变量
    print("Final DataFrame:")
    print(df)

    # 获取当前时间
    now = datetime.datetime.now()
    # 生成文件名
    filename = now.strftime('%Y-%m-%d') + '_data.csv'

    # 保存数据到CSV文件中
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")