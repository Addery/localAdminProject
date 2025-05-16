"""
@Author: zhang_zhiyi
@Date: 2025/4/22_15:33
@FileName:configHttpStatus.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: 
"""
from enum import Enum


class ConfigHttpStatus(Enum):
    """
    配置文件 基础http状态码枚举类6-
    """
    OK = 101  # 成功
    ERROR = 602  # 错误
    EXCEPTION = 603  # 异常
    PATH_NOT_EXISTS = 604  # 文件不存在
    PARAMETER = 605  # 参数异常
    NO_FIND_CODE = 606  # 记录不存在
    TOO_MANY_PROJECT = 607  # 多条记录被修改
    NO_EXIST = 608  # 设备不在线
    CONF_EXIST = 609  # 该设备已有配置文件
