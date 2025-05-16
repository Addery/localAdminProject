"""
@Author: zhang_zhiyi
@Date: 2024/10/18_11:06
@FileName:equipHttpStatus.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: 
"""
from enum import Enum


class EquipHttpStatus(Enum):
    """
    tunnelProject项目 设备相关http状态码枚举类3-
    """
    NO_FIND_CODE = 311  # 设备不存在
    EXIST_CODE = 312  # 设备存在
    TOO_MANY_PROJECT = 313  # 太多设备
