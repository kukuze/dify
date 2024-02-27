from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from flask_restful import Resource

from controllers.console import api
from controllers.console.setup import setup_required
from controllers.console.wraps import account_initialization_required
from libs.login import login_required


def api_description(description_text):
    def decorator(func):
        # 给函数添加一个_description属性，用于存储描述文本
        func._description = description_text
        return func

    return decorator


def api_parameter_format(parameterFormat):
    def decorator(func):
        # 该函数需要传入参数的格式
        func._parameterFormat = parameterFormat
        return func

    return decorator


class ExtendedDataApiList(Resource):
    @setup_required
    @login_required
    @account_initialization_required
    def get(self):
        descriptions_list = []  # 创建一个空列表来存储描述信息
        for name, func in list(globals().items()):  # 使用list()创建globals().items()的静态副本
            if callable(func) and hasattr(func, '_description'):
                # 为每个具有描述的函数添加一个字典到列表中
                descriptions_list.append({
                    "value": name,
                    "name": func._description
                })
        return descriptions_list


@api_description("该接口传入学号即可查看学生余额")
@api_parameter_format("{stu_num='*******'}")
def query_user_balance(stu_num):
    if stu_num == "":
        return {
            "result": "请提供学号"
        }

    url = "http://dcapi1.buct.edu.cn:1080/api/app_ggetl/mh_yktlsxx?X-HW-ID=gg_etl_sjgx&X-HW-APPKEY=rtjovloG3ZoPYDBg/XlygA==&idserial=" + \
          stu_num
    payload = {}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload).json()
    # Extracting the required information and formatting it as needed
    student_number = response["retJSON"]["result"][0]["idserial"]
    last_swipe_time = response["retJSON"]["result"][0]["txdate"]
    balance = int(response["retJSON"]["result"][0]["balance"]) / 100
    # Formatting the last swipe time into a more readable format
    last_swipe_time_formatted = datetime.strptime(last_swipe_time, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    # Structured output
    output = {
        "student_number": student_number,
        "last_swipe_time": last_swipe_time_formatted,
        "balance": balance
    }
    print(output)
    return output


@api_description("该接口传入位置即可查看对应位置天气")
@api_parameter_format("{location='*****'}")
def query_weather(location):
    pass


@api_description("当前时间")
def query_current_time():
    # 设置时区为中国标准时间
    china_zone = ZoneInfo("Asia/Shanghai")

    # 获取当前时间，并应用时区
    current_time = datetime.now(china_zone).strftime("%Y-%m-%d %H:%M:%S %Z")

    return current_time


@api_description("该接口通过传入问题查找bing")
@api_parameter_format("{query='*****'}")
def query_bing(query):
    subscription_key = '6c40594304b2496dac691b5e2f4e096b'
    endpoint = 'https://api.bing.microsoft.com/v7.0/search'
    # Construct a request
    mkt = 'zh-CN'
    params = {'q': query, 'mkt': mkt}
    headers = {'Ocp-Apim-Subscription-Key': subscription_key}

    # Call the API
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        response = response.json()
        search_results = response['webPages']['value'][:3]
        text = ''
        for i, result in enumerate(search_results):
            text += f'{i + 1}: {result["name"]} - {result["snippet"]}\n'
        return text
    except Exception as ex:
        raise ex


api.add_resource(ExtendedDataApiList, '/datasets/documents/segments/extendedDataApi')
