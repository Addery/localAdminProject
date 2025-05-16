"""
@Author: zhang_zhiyi
@Date: 2024/10/17_14:23
@FileName:baseHttpStatus.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: 
"""
from enum import Enum


class BaseHttpStatus(Enum):
    """
    tunnelProject项目 基础http状态码枚举类1-
    """
    OK = 101  # 成功
    ERROR = 102  # 失败
    EXCEPTION = 103  # 发生异常
    PARAMETER = 104  # 参数错误
    GET_DATA_ERROR = 105  # 获取网络传递参数错误
    INFO_SAME = 106  # 修改前后信息一致
