"""
@Author: zhang_zhiyi
@Date: 2024/7/25_11:59
@FileName:userHttpStatus.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: tunnelProject项目 用户相关http状态码枚举类2-
"""
from enum import Enum


class UserHttpStatus(Enum):
    """
    tunnelProject项目 用户相关http状态码枚举类2-
    """
    NO_USER = 201  # 用户未注册
    LOGIN_PASSWORD_ERROR = 202  # 密码不正确
    USER_HAS_EXISTED = 203  # 用户已经存在
    TOO_MANY_USER = 204  # 多个用户信息重复
    USER_INFO_CLASH = 205  # 用户信息冲突





