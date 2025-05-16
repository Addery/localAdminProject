"""
@Author: zhang_zhiyi
@Date: 2024/10/12_17:29
@FileName:projectHttpStatus.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: tunnelProject项目 工程相关http状态码枚举类3-
"""
from enum import Enum


class ProjectHttpStatus(Enum):
    """
    tunnelProject项目 工程相关http状态码枚举类3-
    """
    NO_FIND_CODE = 301  # 项目不存在
    EXIST_CODE = 302  # 项目存在
    TOO_MANY_PROJECT = 303  # 太多项目

