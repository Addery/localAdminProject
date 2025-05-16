"""
@Author: zhang_zhiyi
@Date: 2025/5/12_16:48
@FileName:test.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: 
"""

import requests

ip = "http://192.168.1.8"
port = "8024"


def start_control():
    url = f"{ip}:{port}/api/admin/local/equipment_db/startControl"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'ConEquipCode': '1001',
        'IP': '192.168.1.8'
    }
    response = requests.post(url, json=data, headers=headers)
    print(response.json())
    print(response.status_code)


def stop_control():
    url = f"{ip}:{port}/api/admin/local/equipment_db/stopControl"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'ConEquipCode': '1001',
        'IP': '192.168.1.8'
    }
    response = requests.post(url, json=data, headers=headers)
    print(response.json())
    print(response.status_code)


def init_control():
    url = f"{ip}:{port}/api/admin/local/equipment_db/initControl"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'TunCode': '1001',
        'ConEquipCode': '1001',
        'ConfIP': '192.168.1.8',
        'IP': '192.168.1.8'
    }
    response = requests.post(url, json=data, headers=headers)
    print(response.json())
    print(response.status_code)


def update_control():
    url = f"{ip}:{port}/api/admin/local/equipment_db/updateControl"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'OldConEquipCode': '1001',
        'ConEquipCode': '1001',
        'TunCode': '1001',
        'OldConfIP': '192.168.1.8',
        'ConfIP': '192.168.1.8'
    }
    response = requests.post(url, json=data, headers=headers)
    print(response.json())
    print(response.status_code)


def start_data():
    url = f"{ip}:{port}/api/admin/local/equipment_db/startData"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'DataAcqEquipCode': '1001',
        'IP': '192.168.1.8'
    }
    response = requests.post(url, json=data, headers=headers)
    print(response.json())
    print(response.status_code)


def stop_data():
    url = f"{ip}:{port}/api/admin/local/equipment_db/stopData"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'DataAcqEquipCode': '1001',
        'IP': '192.168.1.8'
    }
    response = requests.post(url, json=data, headers=headers)
    print(response.json())
    print(response.status_code)


def init_data():
    url = f"{ip}:{port}/api/admin/local/equipment_db/initData"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'ConEquipCode': '1001',
        'DataAcqEquipCode': '1001',
        'ConfIP': '192.168.1.8',
    }
    response = requests.post(url, json=data, headers=headers)
    print(response.json())
    print(response.status_code)


def update():
    url = f"{ip}:{port}/api/admin/local/equipment_db/updateData"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'OldDataAcqEquipCode': '1001',
        'DataAcqEquipCode': '1001',
        'ConEquipCode': '1001',
        'OldConfIP': '192.168.1.8',
        'ConfIP': '192.168.1.10'
    }
    response = requests.post(url, json=data, headers=headers)
    print(response.json())
    print(response.status_code)


if __name__ == '__main__':
    start_control()
    # stop_control()
    # init_control()

    start_data()
    # stop_data()
    # init_data()
