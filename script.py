import requests
import ipaddress
from bs4 import BeautifulSoup
import pandas as pd
import datetime
# 定义请求头
headers = {
    'Host': 'iknowwhatyoudownload.com',
    'Cache-Control': 'max-age=0',
    'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Ubuntu"',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; ELE-L29) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Mobile Safari/537.36null',
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
        print(ip_range)
        network = ipaddress.ip_network(ip_range)
        for ip in network.hosts():
            url = 'https://iknowwhatyoudownload.com/en/peer/?ip=' + str(ip)
            try:
                response = requests.get(url, headers=headers)
                get_data(response)
            except requests.exceptions.ConnectionError:
                pass


if __name__ == '__main__':
    # 发送请求并读取返回包
    get_response(ip_ranges)

    # 创建pandas变量
    df = pd.DataFrame(data, columns=['Date1', 'Date2', 'Category', 'Name'])

    # 打印pandas变量
    print(df)

    # 获取当前时间
    now = datetime.datetime.now()
    # 生成文件名
    filename = now.strftime('%Y-%m-%d') + '_data.csv'

    # 保存数据到CSV文件中
    df.to_csv(filename, index=False)
