"""
@Author: zhang_zhiyi
@Date: 2024/10/21_18:11
@FileName:logHttpStatus.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: 
"""
from enum import Enum


class LogHttpStatus(Enum):
    """
    tunnelProject项目 日志相关http状态码枚举类4-
    """
    NO_FIND_CODE = 440  # 日志不存在
    EXIST_CODE = 441  # 日志存在
    TOO_MANY_PROJECT = 442  # 太多日志
    NO_ANOMALY_DATA = 443
