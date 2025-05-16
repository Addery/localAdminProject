"""
@Author: zhang_zhiyi
@Date: 2024/10/11_9:46
@FileName:app.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: app启动脚本
"""

from flask import Flask
from flask_cors import CORS


from route.equipment import equipment_db

app = Flask(__name__)
CORS(app)

app.register_blueprint(equipment_db, url_prefix='/api/admin/local/equipment_db')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8024)

