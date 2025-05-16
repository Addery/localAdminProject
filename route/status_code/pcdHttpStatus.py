"""
@Author: zhang_zhiyi
@Date: 2024/10/12_10:55
@FileName:pcdHttpStatus.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: tunnelProject项目 pcd点云数据相关http状态码枚举类 5-
"""
from enum import Enum


class PCDHttpStatus(Enum):
    """
    tunnelProject项目 pcd点云数据相关http状态码枚举类5-
    """
    OK = 510  # 访问成功
    PARAMETER_ERROR = 511  # 参数错误
    EXCEPTION = 512  # 发生异常
    NO_FIND_LOG_FILE = 521  # 没找到文件
    NO_FIND_DATA = 522  # 没找到数据
    DATA_OVERDUE = 523  # 数据逾期，不在本地数据保存范围内
