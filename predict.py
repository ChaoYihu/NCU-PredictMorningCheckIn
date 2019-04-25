'''
Powered by ChaoYihu. All Rights Reserved.
本代码仅用于判断某一日的早点到概率,模型包含降水量 历史天气预测.
代码地址仅限新建区!
优先判断日期,如果为休息日或者法定节假日,则早点到概率直接改为0%;如果为正常工作日或者调课,再进行权重计算.
预测权重值:
当日5:00-8:00降水量:80%
(降水量是指从天空降落到地面上的液态或固态（经融化后）水，未经蒸发、渗透、流失，而在水平面上积聚的深度。单位为mm)
近5年同日天气:20%
    其中,每年总占比为4%
    天晴或者多云或者阴 4%
    雨(大中小雷暴)或者雪(大中小) 0%
'''
import requests
from bs4 import BeautifulSoup
import time


def jsl():
    headers = {'User-Agent': 'Mozilla/5.0'}
    pagetext = requests.get(url='http://www.nmc.cn/publish/forecast/AJX/xinjian.html', headers=headers)
    pagetext.encoding = pagetext.apparent_encoding
    soup = BeautifulSoup(pagetext.text, 'html.parser')
    timelist = []
    time = soup.find('div', attrs={'class': 'hour3'}).findChildren('div', attrs={'style': 'font-size: 12px;'})
    jslist = []
    js = soup.find('div', attrs={'class': 'row js'}).findChildren('div')[1:]
    for i in range(0, len(time)):
        timelist.append(str(time[i])[30:-6].strip().split('日')[-1])
        jslist.append(str(js[i])[5:-6].strip().replace('无降水', '0').replace('mm', ''))
    jsl_dict = {}
    for i in range(0, len(js)):
        jsl_dict[timelist[i]] = jslist[i]
    return jsl_dict


def date_judge(date):  # date字符串类型
    # date为8位,示例:19990513,此API仅支持2017年之后的日期
    # 正常工作日对应结果为 0, 法定节假日对应结果为 1, 节假日调休补班对应的结果为 2，休息日对应结果为 3
    while True:
        response = requests.get(url='http://api.goseek.cn/Tools/holiday?date=' + date)
        result = dict(response.json())
        if 'data' in result.keys():
            return result['data']


def history_weather(date):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        pagetext = requests.get(url='https://m.tianqi.com/lishi/xinjian/' + date[:6] + '.html', headers=headers)
        pagetext.encoding = pagetext.apparent_encoding
        soup = BeautifulSoup(pagetext.text, 'html.parser')
        title = '新建' + date[:4] + '年' + date[4:6] + '/' + date[6:8] + '历史天气'
        weather = soup.find('a', attrs={'title': title}).findChildren(attrs={'class': 'txt1'})[0].string
        temp = str(soup.find('a', attrs={'title': title}).findChildren(attrs={'class': 'txt2'})[0]).replace(
            '<dd class="txt2">', '').replace('<b>', '').replace('</b>', '').replace('</dd>', '')
        return (weather, temp)  # 返回一个tuple,第一个元素为天气情况,第二个元素为温度
    except AttributeError:
        return '未找到日期为' + date + '的历史天气数据'


def get_date():  # 本函数用于获取需要判断早点到的日期.具体方法为,如果为当天的凌晨5点前,返回当天日期,如果是当天凌晨5点后,返回下一天日期.
    time_variable = time.strftime("%Y%m%d %H:%M:%S", time.localtime())
    if int(time_variable[9:11]) >= 5:
        return str(int(time_variable[:8]) + 1)
    else:
        return time_variable[:8]


def weight_5years_weather(date):
    weight = 0
    weather_list = []
    for i in range(1, 6):
        weather_list.append(history_weather(str(int(date[:4]) - i) + date[4:])[0])
    for i in weather_list:
        if '雨' in i or "雪" in i:
            weight += 0
        else:
            weight += 4
    return weight


def weight_jsl(jsl_dict):
    weight = 0
    five = int(jsl_dict['05:00'])
    eight = int(jsl_dict['08:00'])
    five_to_eight = five + eight
    if five_to_eight == 0:
        weight += 80
    if five_to_eight != 0:
        if five == 0 and eight != 0:
            weight += 60
        elif five != 0 and eight == 0:
            weight += 40
        else:
            weight += 0
    return weight


if __name__ == '__main__':
    day = get_date()
    day_type = date_judge(day)
    if day_type == 0 or day_type == 2:
        jsl_weight = weight_jsl(jsl())
        history_weight = weight_5years_weather(day)
        weight = jsl_weight + history_weight
        print('根据预测,' + day + "需要早点到的概率为" + str(weight) + '%')
        print("其中,降水量权重占比" + str(jsl_weight) + '%,同期历史天气参考占比' + str(history_weight) + '%.')
        if day_type == 0:
            print('该日为普通工作日!')
        if day_type == 2:
            print('该日为节假日调休补课!')
    elif day_type == 1 or day_type == 3:
        print('根据预测,' + day + "需要早点到的概率为0%")
        if day_type == 1:
            print('该日为法定节假日!')
        if day_type == 3:
            print('该日为休息日!')
