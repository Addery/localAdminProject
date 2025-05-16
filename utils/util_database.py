"""
@Author: zhang_zhiyi
@Date: 2024/9/3_15:04
@FileName:util_database.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: 
"""
import os
import time
from datetime import datetime

from pymysql.connections import Connection
import logging
import configparser

from pymysql.cursors import Cursor, DictCursor

from dao.bin.local_db_table import TunnelTable, ProjectTable, WorkSurfaceTable, StructureTable, UserTable, \
    AnomalyLogTable, AnomalyLodDescTable, EqControlTable, EqDataTable, PcdLogTable, RoleTable, EqControlConfTable, \
    EqDataConfTable, AnomalyLodImgTable
from rmq.construct import Tunnel
from route.status_code.baseHttpStatus import BaseHttpStatus
from route.status_code.logHttpStatus import LogHttpStatus
from route.status_code.projectHttpStatus import ProjectHttpStatus


class DBUtils(object):
    """
    数据库操作类
    """

    DEFAULT_DATABASE = "tunneladmintest"
    CURRENT_PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
    DEFAULT_CONFIG_PATH = os.path.join(CURRENT_PROJECT_PATH, "../config/database.ini")
    DEFAULT_LOG_PATH = os.path.join(CURRENT_PROJECT_PATH, "../log/database.log")
    COLUMNS = {
        'project': ProjectTable().columns_dict(),
        'tunnel': TunnelTable().columns_dict(),
        'work_surface': WorkSurfaceTable().columns_dict(),
        'structure': StructureTable().columns_dict(),
        'user': UserTable().columns_dict(),
        'anomaly_log': AnomalyLogTable().columns_dict(),
        'anomaly_log_desc': AnomalyLodDescTable().columns_dict(),
        'anomaly_log_img': AnomalyLodImgTable().columns_dict(),
        'eq_control': EqControlTable().columns_dict(),
        'eq_data': EqDataTable().columns_dict(),
        'pcd_log': PcdLogTable().columns_dict(),
        'role': RoleTable().columns_dict(),
        'eq_control_conf': EqControlConfTable().columns_dict(),
        'eq_data_conf': EqDataConfTable().columns_dict()
    }

    JOIN_SQL = {
        'project': {
            'select_sql': "SELECT p.*, c.Name FROM project p LEFT JOIN company c ON p.CompanyCode = c.Code",
            'count_sql': "SELECT COUNT(*) as total FROM project p",
            'alias': "p."
        },
        'tunnel': {
            'select_sql': "SELECT t.*, p.ProName FROM tunnel t LEFT JOIN project p ON t.ProCode = p.ProCode",
            'count_sql': "SELECT COUNT(*) as total FROM tunnel t",
            'alias': "t."
        },
        'work_surface': {
            'select_sql': "SELECT w.*, p.ProName, t.TunName, s.StruName FROM work_surface w LEFT JOIN project p ON w.ProCode = p.ProCode LEFT JOIN tunnel t ON w.TunCode = t.TunCode LEFT JOIN structure s ON w.StruCode = s.StruCode",
            'count_sql': "SELECT COUNT(*) as total FROM work_surface w",
            'alias': "w."
        },
        'user': {
            'select_sql': "SELECT u.*, c.Name FROM user u LEFT JOIN company c ON u.CompanyCode = c.Code",
            'count_sql': "SELECT COUNT(*) as total FROM user u",
            'alias': "u."
        },
        'eq_control': {
            'select_sql': "SELECT eqc.*, p.ProName, t.TunName, w.WorkSurName, s.StruName FROM eq_control eqc LEFT JOIN project p ON eqc.ProCode = p.ProCode LEFT JOIN tunnel t ON eqc.TunCode = t.TunCode LEFT JOIN work_surface w ON eqc.WorkSurCode = w.WorkSurCode LEFT JOIN structure s ON eqc.StruCode = s.StruCode",
            'count_sql': "SELECT COUNT(*) as total FROM eq_control eqc",
            'alias': "eqc."
        },
        'eq_data': {
            'select_sql': "SELECT eqd.*, eqc.ConEquipName FROM eq_data eqd LEFT JOIN eq_control eqc ON eqd.ConEquipCode = eqc.ConEquipCode",
            'count_sql': "SELECT COUNT(*) as total FROM eq_data eqd",
            'alias': "eqd."
        },
        'anomaly_log': {
            'select_sql': "SELECT alog.*, p.ProName, t.TunName, w.WorkSurName, s.StruName, eqc.ConEquipName, eqd.DataAcqEquipName FROM anomaly_log alog LEFT JOIN project p ON alog.ProCode = p.ProCode LEFT JOIN tunnel t ON alog.TunCode = t.TunCode LEFT JOIN work_surface w ON alog.WorkSurCode = w.WorkSurCode LEFT JOIN structure s ON alog.StruCode = s.StruCode LEFT JOIN eq_control eqc ON alog.ConEquipCode = eqc.ConEquipCode LEFT JOIN eq_data eqd ON alog.DataAcqEquipCode = eqd.DataAcqEquipCode",
            'count_sql': "SELECT COUNT(*) as total FROM anomaly_log alog",
            'alias': "alog."
        }
    }

    def __init__(self, config_path=None):
        self.config_path = config_path or DBUtils.DEFAULT_CONFIG_PATH
        self._host = None
        self._port = None
        self._user = None
        self._password = None

        # 配置日志记录器
        logging.basicConfig(
            filename=DBUtils.DEFAULT_LOG_PATH,  # 日志输出的文件
            level=logging.INFO,  # 记录 ERROR 及以上级别的日志
            format='%(asctime)s - %(levelname)s - %(message)s'  # 自定义日志格式
        )

        # 加载配置
        self._load_config()

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def user(self):
        return self._user

    @property
    def password(self):
        return self._password

    def _load_config(self):
        """
        加载配置文件并读取数据库链接参数
        :return:
        """
        config = configparser.ConfigParser()
        if not os.path.exists(self.config_path):
            logging.error(f"配置文件 {self.config_path} 不存在.")
            raise FileNotFoundError(f"配置文件 {self.config_path} 不存在.")

        try:
            config.read(self.config_path)

            self._host = config.get("parameters", "host", fallback="localhost")
            self._port = int(config.get("parameters", "port", fallback="3306"))
            self._user = config.get("parameters", "user", fallback="root")
            self._password = config.get("parameters", "password", fallback="123456")

        except configparser.NoSectionError as e:
            logging.error(f"{e}: 配置文件缺少parameters部分")
            raise
        except configparser.NoOptionError as e:
            logging.error(f"{e}: 配置文件中缺少关键配置项")
            raise
        except Exception as e:
            logging.error(f"{e}: 读取配置文件时发生错误")
            raise

        logging.info("数据库配置成功加载")

    def connection(self, database_name=DEFAULT_DATABASE, cursor_class=Cursor):
        """
        获取数据库连接对象
        :return:
        """
        try:
            # 创建数据库连接
            conn = Connection(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                autocommit=True,
                database=database_name,
                cursorclass=cursor_class
            )
            logging.info("MySQL数据库连接成功")
            return conn
        except Exception as e:
            logging.error(f"{e}: MySQL数据库连接失败")
            raise  # 抛出异常供调用者处理

    def __str__(self):
        return f"DBUtils(host: {self._host}, port: {self._port}, user: {self._user}, password: {self._password})"

    @staticmethod
    def close_connection(con: Connection):
        """
        关闭数据库连接对象
        :param con:
        :return:
        """
        if con:
            con.close()

    @staticmethod
    def get_table_columns(con: Connection, table_name):
        """
        获取表的字段信息
        :param con:
        :param table_name:
        :return:
        """
        cursor = None
        cursor_res = None
        try:
            cursor = con.cursor()
            sql = "DESC {}".format(table_name)
            cursor.execute(sql)
            cursor_res = cursor.fetchall()
            return cursor_res
        except Exception as e:
            logging.error(f"{e}: 执行get_table_columns方法是发生异常")
            return cursor_res
        finally:
            if cursor:
                cursor.close()

    @staticmethod
    def select_table(con: Connection, table_name, *args):
        """
        返回数据库中某个表的某些字段数据
            *args: ((column, column, column),)
        :param con:
        :param table_name:
        :return:
        """
        cursor = None
        cursor_res = None
        try:
            if con:
                cursor = con.cursor()
                columns_list = list(map(str, DBUtils.COLUMNS.get(table_name)))
                if args[0]:  # 如果给定select的字段名称
                    columns_list = list(map(str, args[0]))
                columns = ', '.join(columns_list)
                # 使用参数化查询来避免 SQL 注入
                sql = "SELECT {} FROM {}".format(columns, table_name)
                cursor.execute(sql)
                cursor_res = cursor.fetchall()
                return cursor_res
        except Exception as e:
            logging.error(f"{e}: 执行select_table方法时发生异常")
            return cursor_res
        finally:
            if cursor:
                cursor.close()

    @staticmethod
    def insert_table(con: Connection, table_name, insert_dict: dict):
        """
        插入信息
        :param con:
        :param table_name:
        :param insert_dict:
        :return:
        """
        cursor = None
        try:
            cursor = con.cursor()
            columns = ", ".join(list(insert_dict.keys()))
            values = "', '".join(list(insert_dict.values()))
            values = f"'{values}'"
            sql = "INSERT INTO {}({}) VALUES({})".format(table_name, columns, values)
            cursor.execute(sql)
            return "insert table success"
        except Exception as e:
            logging.error(f"{e}: 执行insert_table方法时发生异常")
            return f"{e}: 执行insert_table方法时发生异常"
        finally:
            if cursor:
                cursor.close()

    @staticmethod
    def delete_table(con: Connection, table_name, delete_condition: dict = None):
        """
        删除数据
        :param con:
        :param table_name:
        :param delete_condition:
        :return:
        """
        cursor = None
        delete_rows = -1
        try:
            cursor = con.cursor()
            if delete_condition is None:
                sql = 'DELETE FROM {}'.format(table_name)
            else:
                column = list(delete_condition.keys())[0]
                value = list(delete_condition.values())[0]
                sql = 'DELETE FROM {} WHERE {}={}'.format(table_name, column, f"'{value}'")
            delete_rows = cursor.execute(sql)
            # test = cursor.execute('DELETE FROM project WHERE ProCode= \'1008\'')
            # print(delete_rows, test)
            return delete_rows
        except Exception as e:
            logging.error(f"{e}: 执行delete_table方法时发生异常")
            return delete_rows
        finally:
            if cursor:
                cursor.close()

    @staticmethod
    def update_table(con: Connection, table_name, update_column, update_value, target_column, target_value):
        """
        修改表中数据
        :param target_value:
        :param target_column:
        :param update_value:
        :param update_column:
        :param con: 连接对象
        :param table_name: 表名
        :return:
        """
        cursor = None
        try:
            cursor = con.cursor()
            sql = 'UPDATE {} SET {}={} WHERE {}={}'.format(table_name, update_column, f"'{update_value}'",
                                                           target_column, f"'{target_value}'")
            cursor.execute(sql)
            # cursor.execute('UPDATE project SET ProName=\'test_update1\' WHERE ProCode=\'1006\'')
            return "update table success"
        except Exception as e:
            logging.error(f"{e}: 执行update_table方法时发生异常")
            return f"{e}: 执行update_table方法时发生异常"
        finally:
            if cursor:
                cursor.close()

    @staticmethod
    def kv(key, target_dict):
        """
        根据受影响的行数匹配返回信息
        :param key:
        :param target_dict:
        :return:
        """
        if key > 1:  # 0 和 1 以外的所有正整数
            return target_dict[2]
        return target_dict[key]

    @staticmethod
    def is_exist(cursor, sql, column, status_code, msg):
        """
        校验待添加的用户是否已经存在
        :return:
        """
        cursor.execute(sql)
        select_res = cursor.fetchall()  # [{}, {}]
        if (f'{column}',) in select_res:  # 用户存在
            return {'code': status_code, 'msg': msg, 'data': {}}
        return None

    @staticmethod
    def project_is_exist(cursor, sql, code, msg):
        """
        验证ProCode是否存在
        :param cursor:
        :param sql:
        :param code:
        :param msg:
        :return:
        """
        cursor.execute(sql)
        cursor_res = cursor.fetchall()  # []
        if not cursor_res:
            return {'code': code, 'msg': msg, 'data': {}}
        return None

    @staticmethod
    def check_existence(cursor, table, column, code, error_code, error_msg):
        sql = f"""
        SELECT * From {table} WHERE {column} = '{code}'
        """
        return DBUtils.project_is_exist(cursor, sql, error_code, error_msg)

    @staticmethod
    def normalize_field(value):
        if value is None or str(value).strip() == "":
            return None
        return value

    @staticmethod
    def paging_display(data, table_name, p, ps):
        """
        :param data: request.json
        :param table_name: 表名
        :param p: 默认的页数
        :param ps: 一页中默认的记录数
        :return:
        data = {
            'page': ...,  页码
            'page_size': ...  一页多少条数据
        }
        SELECT * FROM users LIMIT 10 OFFSET 0;
        LIMIT 10 表示每次查询 10 条记录，OFFSET 0 表示从第 0 条记录开始（即第一页）
        """
        filter_item = None
        filter_value = None
        search_text = None
        try:
            page = data.get('Page', p)
            page_size = data.get('PageSize', ps)
            # 键值对筛选字段
            filter_item = DBUtils.normalize_field(data.get('Item'))
            filter_value = DBUtils.normalize_field(data.get('Value'))
            # 模糊查询字段
            search_text = DBUtils.normalize_field(data.get('SearchText'))
            # 指定所属单位筛选字段
            pro_code = DBUtils.normalize_field(data.get('ProCode'))
            tun_code = DBUtils.normalize_field(data.get('TunCode'))

            # 区间筛选字段
            start = DBUtils.normalize_field(data.get('start'))
            end = DBUtils.normalize_field(data.get('end'))
            column = DBUtils.normalize_field(data.get('column'))
            offset = (page - 1) * page_size
        except Exception as e:
            return {'code': BaseHttpStatus.GET_DATA_ERROR.value, 'msg': '查找失败', 'data': {'exception': str(e)}}

        # 校验必填字段
        if not all([str(page), str(page_size)]):
            return {'code': BaseHttpStatus.PARAMETER.value, 'msg': '缺少必要的字段', 'data': {}}

        if offset < 0:
            return {'code': BaseHttpStatus.PARAMETER.value, 'msg': 'page不合法', 'data': {}}

        con = None
        cursor = None
        try:
            dbu = DBUtils()
            con = dbu.connection(cursor_class=DictCursor)
            con.autocommit(False)

            values_tuple = []
            with con.cursor() as cursor:
                # 查询总记录数
                cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
                total = cursor.fetchone()['total']

                # 正常查询
                sql = f"""
                        SELECT * FROM {table_name} 
                        """

                # 是否要根据编号进行筛选
                if pro_code is not None and tun_code is not None:
                    sql += f" WHERE ProCode = %s AND TunCode = %s"
                    values_tuple.append(pro_code)
                    values_tuple.append(tun_code)
                elif tun_code is not None:
                    sql += f" WHERE TunCode = %s"
                    values_tuple.append(tun_code)
                elif pro_code is not None:
                    sql += f" WHERE ProCode = %s"
                    values_tuple.append(pro_code)

                # 是否要在分页结果中进行模糊查询
                if search_text is not None:
                    # 获取数据表的字段名称 需要查数据库速度慢
                    # db_columns = DBUtils.get_table_columns(con, table_name)
                    db_columns = DBUtils.COLUMNS[table_name]

                    if pro_code is None and tun_code is None:
                        sql += " WHERE"
                    else:
                        sql += " AND"
                    for i, value in enumerate(db_columns):
                        values_tuple.append(f'%{search_text}%')
                        if i == len(db_columns) - 1:
                            sql += f" {value} LIKE %s"
                            continue
                        sql += f" {value} LIKE %s OR"

                # 分页查询
                sql += f"ORDER BY ID DESC LIMIT %s OFFSET %s"
                values_tuple.append(page_size)
                values_tuple.append(offset)

                # 执行sql
                cursor.execute(sql, values_tuple)
                items = cursor.fetchall()

                # 是否要在分页结果中进行筛选(键值对筛选字段)
                filter_items = []
                if filter_item is not None and filter_value is not None:
                    for v in items:
                        if v[filter_item] == filter_value:
                            filter_items.append(v)
                else:
                    filter_items = items

                if not filter_items:
                    return {'code': BaseHttpStatus.ERROR.value, 'msg': '查找失败', 'data': {}}

                # 是否要进行区间筛选
                section_filter_items = []
                if all([start, end, column]):
                    if "Time" in column:
                        start_dt = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
                        end_dt = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
                        for item in filter_items:
                            item_dt = datetime.strptime(item[column], "%Y-%m-%d %H:%M:%S")
                            if start_dt <= item_dt <= end_dt:
                                section_filter_items.append(item)
                    elif "Mileage" in column:
                        start_in = int(start)
                        end_in = int(end)
                        for item in filter_items:
                            item_in = int(item[column])
                            if start_in <= item_in <= end_in:
                                section_filter_items.append(item)
                else:
                    section_filter_items = filter_items

                data = {
                    'items': section_filter_items,
                    # 'total': total,  # 总记录数
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_page': (total + page_size - 1) // page_size  # 总页数
                }
                con.commit()
                return {'code': BaseHttpStatus.OK.value, 'msg': '查找成功', 'data': data}
        except Exception as e:
            if con:
                con.rollback()
            return {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '查找失败', 'data': {'exception': str(e)}}
        finally:
            if cursor:
                cursor.close()
            if con:
                DBUtils.close_connection(con)

    @staticmethod
    def modify_sql_by_join(table_name):
        """
        根据 table_name 拼接联表查询语句
        """
        join_data = DBUtils.JOIN_SQL[table_name]
        return join_data['select_sql'], join_data['count_sql'], join_data['alias']

    @staticmethod
    def paging_display_condition_on_sql(data, table_name, p, ps, join=False):
        con = None
        cursor = None
        select_sql = f"SELECT * FROM {table_name}"
        count_sql = f"SELECT COUNT(*) as total FROM {table_name}"
        alias = ""
        if join:
            select_sql, count_sql, alias = DBUtils.modify_sql_by_join(table_name)
        try:
            page = data.get('Page', p)
            page_size = data.get('PageSize', ps)
            offset = (page - 1) * page_size

            if page <= 0 or page_size <= 0:
                return {'code': BaseHttpStatus.PARAMETER.value, 'msg': '分页参数不合法', 'data': {}}

            # 构建动态 WHERE 子句
            where_clauses = []
            params = []

            # 编号筛选
            pro_code = DBUtils.normalize_field(data.get('ProCode'))
            tun_code = DBUtils.normalize_field(data.get('TunCode'))
            if pro_code:
                where_clauses.append(f"{alias}ProCode = %s")
                params.append(pro_code)
            if tun_code:
                where_clauses.append(f"{alias}TunCode = %s")
                params.append(tun_code)

            # 模糊查询
            search_text = DBUtils.normalize_field(data.get('SearchText'))
            if search_text:
                db_columns = DBUtils.COLUMNS[table_name]
                like_clauses = [f"{alias}{col} LIKE %s" for col in db_columns]
                where_clauses.append(f"({' OR '.join(like_clauses)})")
                params.extend([f"%{search_text}%"] * len(db_columns))

            # 键值对筛选
            filter_item = DBUtils.normalize_field(data.get('Item'))
            filter_value = DBUtils.normalize_field(data.get('Value'))
            if filter_item and filter_value:
                where_clauses.append(f"{alias}{filter_item} = %s")
                params.append(filter_value)

            # 区间筛选
            start = DBUtils.normalize_field(data.get('Start'))
            end = DBUtils.normalize_field(data.get('End'))
            column = DBUtils.normalize_field(data.get('Column'))
            if start and end and column:
                if "AnomalyTime" in column:
                    where_clauses.append(f"{alias}{column} BETWEEN %s AND %s")
                    params.extend([start, end])
                elif "Mileage" in column:
                    where_clauses.append(f"{alias}{column} BETWEEN %s AND %s")
                    params.extend([int(start), int(end)])

            # 拼接 WHERE 子句
            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # SQL 拼接
            sql_data = f"""
                {select_sql}
                {where_sql}
                ORDER BY ID DESC
                LIMIT %s OFFSET %s
            """
            sql_count = f"""
                {count_sql}
                {where_sql}
            """
            params_for_data = params + [page_size, offset]

            # 执行
            con = DBUtils().connection(cursor_class=DictCursor)
            con.autocommit(False)
            with con.cursor() as cursor:
                cursor.execute(sql_count, params)
                total = cursor.fetchone()['total']

                cursor.execute(sql_data, params_for_data)
                items = cursor.fetchall()

            total_page = (total + page_size - 1) // page_size
            return {
                'code': BaseHttpStatus.OK.value,
                'msg': '查找成功',
                'data': {
                    'items': items,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_page': total_page
                }
            }
        except Exception as e:
            if con:
                con.rollback()
            return {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '查找失败', 'data': {'exception': str(e)}}
        finally:
            if cursor:
                cursor.close()
            if con:
                DBUtils.close_connection(con)

    @staticmethod
    def search(data):
        try:
            table_name = data.get('TableName')
            columns = data.get('Columns', None)
        except Exception as e:
            return {'code': BaseHttpStatus.GET_DATA_ERROR.value, 'msg': '查找失败', 'data': {'exception': str(e)}}

        # 校验必填字段
        if not all([table_name]):
            return {'code': BaseHttpStatus.PARAMETER.value, 'msg': '缺少必要的字段', 'data': {}}, 200

            con = None
            cursor = None
        try:
            dbu = DBUtils()
            con = dbu.connection(cursor_class=DictCursor)
            con.autocommit(False)
            cursor = con.cursor()

            if columns is not None:
                columns_list = columns.split(',')
                sql = None
                for column in columns_list:
                    if sql is None:
                        sql = f"SELECT {column}"
                    else:
                        sql += f", {column}"
                sql += f" From {table_name}"
            else:
                sql = f"""
                    SELECT * FROM {table_name}
                """
            cursor.execute(sql)
            res = cursor.fetchall()
            con.commit()
            if res:
                return {
                    'code': BaseHttpStatus.OK.value,
                    'msg': '查找成功',
                    'data': {
                        'total': len(res),
                        'items': res
                    }
                }
            return {'code': BaseHttpStatus.ERROR.value, 'msg': '不存在符合要求的记录', 'data': {}}
        except Exception as e:
            if con:
                con.rollback()
            return {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '查找失败', 'data': {'exception': str(e)}}
        finally:
            if cursor:
                cursor.close()
            if con:
                DBUtils.close_connection(con)

    @staticmethod
    def search_by_some_item(table_name, item, value, join=False, data=None):
        # 校验必填字段
        if not all([item, value]):
            return {'code': BaseHttpStatus.PARAMETER.value, 'msg': '缺少必要的字段', 'data': {}}, 200

        con = None
        cursor = None
        select_sql = f"SELECT * FROM {table_name}"
        count_sql = f"SELECT COUNT(*) as total FROM {table_name}"
        alias = ""
        if join:
            select_sql, count_sql, alias = DBUtils.modify_sql_by_join(table_name)
        try:
            dbu = DBUtils()
            con = dbu.connection(cursor_class=DictCursor)
            cursor = con.cursor()
            con.autocommit(False)

            sql_count = f"""
                {count_sql}
                WHERE {alias}{item} = %s
            """

            sql_data = f"""
                {select_sql}
                WHERE {alias}{item} = %s
            """

            with con.cursor() as cursor:
                cursor.execute(sql_count, value)
                total = cursor.fetchone()['total']

                cursor.execute(sql_data, value)
                items = cursor.fetchall()

            # # 统计符合要求的记录总数量
            # cursor.execute(f"SELECT COUNT(*) as total FROM {table_name} Where {item} = %s", value)
            # total = cursor.fetchone()['total']
            #
            # sql = f"""
            #     SELECT * FROM {table_name} WHERE {item} = %s
            # """
            # cursor.execute(sql, value)
            # res = cursor.fetchall()
            con.commit()
            # if res:
            return {
                'code': BaseHttpStatus.OK.value,
                'msg': '查找成功',
                'data': {
                    'total': total,
                    'items': items
                }
            }
            # return {'code': BaseHttpStatus.ERROR.value, 'msg': '不存在符合要求的记录', 'data': {}}
        except Exception as e:
            if con:
                con.rollback()
            return {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '查找失败', 'data': {'exception': str(e)}}
        finally:
            if cursor:
                cursor.close()
            if con:
                DBUtils.close_connection(con)

    @staticmethod
    def log_insert(tunnel: Tunnel):
        """
        :param tunnel:
        :return:
        """
        # now = datetime.now()
        con = None
        cursor = None
        try:
            # 获取异常数据
            data = tunnel.get_data()
            anomaly = data.get_anomaly()
            if anomaly:
                anomaly_describe = anomaly.get_describe()
                k = list(anomaly_describe.keys())
                position, bas, degree = [], [], []
                for e in k:
                    position.append(anomaly_describe.get(e)[0])
                    bas.append(anomaly_describe.get(e)[1])
                    degree.append(anomaly_describe.get(e)[2])

                acq_code = tunnel.device_id
                dbu = DBUtils()
                con = dbu.connection(cursor_class=DictCursor)
                cursor = con.cursor()
                acq_sql = """
                SELECT ConEquipCode, Distance FROM eq_data WHERE DataAcqEquipCode = %s
                """
                cursor.execute(acq_sql, acq_code)
                acq_res = cursor.fetchone()
                if not acq_res:
                    return None

                # 数据采集器编号对应的中控设备编号
                con_code = acq_res['ConEquipCode']
                distance = acq_res['Distance']

                con_sql = """
                SELECT * FROM eq_control WHERE ConEquipCode = %s
                """
                cursor.execute(con_sql, con_code)
                con_res = cursor.fetchone()
                if not con_res:
                    return None

                data = {
                    # 'DescCode': str(time.time()),
                    'Degree': degree,
                    'Identification': str(time.time()),
                    'Region': k,
                    'Position': position,
                    'Bas': bas,
                    'ProCode': con_res['ProCode'],
                    'TunCode': con_res['TunCode'],
                    'WorkSurCode': con_res['WorkSurCode'],
                    'StruCode': con_res['StruCode'],
                    'Mileage': distance,
                    'ConEquipCode': con_code,
                    'DataAcqEquipCode': acq_code,
                    'AnomalyTime': str(data.get_time().strftime("%Y-%m-%d %H:%M:%S"))
                }
                res = DBUtils.log_insert_db(data)
                return True if res['code'] == BaseHttpStatus.OK.value else False
        except Exception as e:
            if con:
                con.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
            if con:
                DBUtils.close_connection(con)

    # @staticmethod
    # def log_insert_db(data):
    #     result_dict = {
    #         0: {
    #             'code': BaseHttpStatus.ERROR.value,
    #             'msg': '添加失败',
    #             'data': ''
    #         },
    #         1: {
    #             'code': BaseHttpStatus.OK.value,
    #             'msg': '添加成功',
    #             'data': ''
    #         },
    #         2: {
    #             'code': LogHttpStatus.TOO_MANY_PROJECT.value,
    #             'msg': '添加了多个日志',
    #             'data': ''
    #         }
    #     }
    #     try:
    #         desc_code = data.get('DescCode', str(time.time()))
    #         degree = data.get('Degree')
    #         identification = data.get('Identification')
    #         region = data.get('Region')
    #         position = data.get('Position')
    #         bas = data.get('Bas')
    #         pro_code = data.get('ProCode')
    #         tun_code = data.get('TunCode')
    #         work_sur_code = data.get('WorkSurCode')
    #         stru_code = data.get('StruCode')
    #         mileage = data.get('Mileage')
    #         equ_code = data.get('ConEquipCode')
    #         acq_code = data.get('DataAcqEquipCode')
    #         anomaly_time = data.get('AnomalyTime')
    #     except Exception as e:
    #         return {'code': BaseHttpStatus.GET_DATA_ERROR.value, 'msg': '添加失败', 'data': {str(e)}}
    #
    #     # 校验必填字段
    #     if not all(
    #             [desc_code, degree, region, position, bas, pro_code, tun_code, work_sur_code, stru_code, mileage,
    #              equ_code, acq_code, anomaly_time, identification]):
    #         return {'code': BaseHttpStatus.PARAMETER.value, 'msg': '缺少必要的字段', 'data': {}}
    #
    #     con = None
    #     cursor = None
    #     try:
    #         dbu = DBUtils()
    #         con = dbu.connection()
    #         cursor = con.cursor()
    #         con.autocommit(False)
    #
    #         # 验证DescCode是否存在
    #         sql = "SELECT * From anomaly_log_desc WHERE DescCode = {}".format(f"'{desc_code}'")
    #         res = DBUtils.project_is_exist(cursor, sql, LogHttpStatus.NO_FIND_CODE.value, "不存在")
    #         if not res:
    #             return {'code': LogHttpStatus.EXIST_CODE.value, 'msg': '日志已经存在', 'data': {}}
    #
    #         # 验证各个Code
    #         checks = [
    #             ('tunnel', 'TunCode', tun_code, ProjectHttpStatus.NO_FIND_CODE.value, "该隧道不存在"),
    #             ('project', 'ProCode', pro_code, ProjectHttpStatus.NO_FIND_CODE.value, "该项目不存在"),
    #             ('structure', 'StruCode', stru_code, ProjectHttpStatus.NO_FIND_CODE.value, "该结构物不存在"),
    #             ('work_surface', 'WorkSurCode', work_sur_code, ProjectHttpStatus.NO_FIND_CODE.value,
    #              "该工作面不存在"),
    #             ('eq_control', 'ConEquipCode', equ_code, ProjectHttpStatus.NO_FIND_CODE.value, "该中控设备不存在"),
    #             ('eq_data', 'DataAcqEquipCode', acq_code, ProjectHttpStatus.NO_FIND_CODE.value,
    #              "该数据采集器不存在"),
    #         ]
    #         for table, column, code, error_code, error_msg in checks:
    #             res = DBUtils.check_existence(cursor, table, column, code, error_code, error_msg)
    #             if res:
    #                 return res
    #
    #         desc_sql = """
    #             INSERT INTO anomaly_log_desc
    #             (DescCode, Identification, Degree, Region, Position, Bas) VALUES (%s, %s, %s, %s, %s, %s)
    #             """
    #         log_sql = """
    #             INSERT INTO
    #             anomaly_log
    #             (
    #             Identification, ProCode, TunCode, WorkSurCode, StruCode, Mileage, ConEquipCode, DataAcqEquipCode,
    #             AnomalyTime, Year, Month, Day, Hour, Minute, Second
    #             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    #             """
    #
    #         anomaly_len = len(degree)
    #         if anomaly_len <= 0:
    #             return {'code': LogHttpStatus.NO_ANOMALY_DATA.value, 'msg': '添加失败', 'data': {}}
    #         if anomaly_len == 1:
    #             cursor.execute(desc_sql, (
    #                 desc_code, identification, str(degree[0]), str(region[0]), str(position[0]), str(bas[0])))
    #         else:
    #             for d, r, p, b in zip(degree, region, position, bas):
    #                 cursor.execute(desc_sql, (desc_code, identification, str(d), str(r), str(p), str(b)))
    #                 desc_code = str(float(desc_code) + 1)
    #
    #         now = datetime.strptime(anomaly_time, '%Y-%m-%d %H:%M:%S')
    #         rows = cursor.execute(log_sql, (
    #             identification, pro_code, tun_code, work_sur_code, stru_code, mileage, equ_code, acq_code,
    #             anomaly_time, now.year, now.month, now.day, now.hour, now.minute, now.second))
    #         con.commit()
    #         return DBUtils.kv(rows, result_dict)
    #     except Exception as e:
    #         if con:
    #             con.rollback()
    #         return {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '添加失败', 'data': {str(e)}}
    #     finally:
    #         if cursor:
    #             cursor.close()
    #         if con:
    #             DBUtils.close_connection(con)

    @staticmethod
    def anomaly_log_insert(data):
        """
        在 anomaly_log 表中插入记录
        """
        result_dict = {
            0: {
                'code': BaseHttpStatus.ERROR.value,
                'msg': '添加失败',
                'data': ''
            },
            1: {
                'code': BaseHttpStatus.OK.value,
                'msg': '添加成功',
                'data': ''
            },
            2: {
                'code': LogHttpStatus.TOO_MANY_PROJECT.value,
                'msg': '添加了多个日志',
                'data': ''
            }
        }
        try:
            log_data = data.get('LogData')
            desc_data = data.get('DescData')
            img_data = data.get('ImgData')

            pro_code = log_data.get('ProCode')
            tun_code = log_data.get('TunCode')
            work_sur_code = log_data.get('WorkSurCode')
            stru_code = log_data.get('StruCode')
            mileage = log_data.get('Mileage')
            equ_code = log_data.get('ConEquipCode')
            acq_code = log_data.get('DataAcqEquipCode')
            anomaly_time = log_data.get('AnomalyTime')
            identification = log_data.get('Identification', f'{pro_code}_{tun_code}_{work_sur_code}_{str(time.time())}')
            sign = log_data.get('Sign', 0)
            degree = desc_data.get('Degree')
            company_code = data.get('CompanyCode', '07361dfa-defc-4a08-ba11-5a495db9e565')
        except Exception as e:
            return {'code': BaseHttpStatus.GET_DATA_ERROR.value, 'msg': '添加失败', 'data': {str(e)}}

        if not all([identification, pro_code, tun_code, work_sur_code, stru_code, mileage, equ_code, acq_code,
                    anomaly_time, str(sign), degree, company_code]):
            return {'code': BaseHttpStatus.PARAMETER.value, 'msg': '插入记录时缺少必要的字段', 'data': {}}

        con = None
        cursor = None
        try:
            dbu = DBUtils()
            con = dbu.connection()
            cursor = con.cursor()
            con.autocommit(False)

            # 验证各个Code
            checks = [
                ('tunnel', 'TunCode', tun_code, ProjectHttpStatus.NO_FIND_CODE.value, "该隧道不存在"),
                ('project', 'ProCode', pro_code, ProjectHttpStatus.NO_FIND_CODE.value, "该项目不存在"),
                ('structure', 'StruCode', stru_code, ProjectHttpStatus.NO_FIND_CODE.value, "该结构物不存在"),
                ('work_surface', 'WorkSurCode', work_sur_code, ProjectHttpStatus.NO_FIND_CODE.value,
                 "该工作面不存在"),
                ('eq_control', 'ConEquipCode', equ_code, ProjectHttpStatus.NO_FIND_CODE.value, "该中控设备不存在"),
                ('eq_data', 'DataAcqEquipCode', acq_code, ProjectHttpStatus.NO_FIND_CODE.value,
                 "该数据采集器不存在")
            ]
            for table, column, code, error_code, error_msg in checks:
                res = DBUtils.check_existence(cursor, table, column, code, error_code, error_msg)
                if res:
                    return res

            # identification 是否已经存在
            id_sql = f"SELECT * FROM anomaly_log WHERE Identification = '{identification}'"
            res = DBUtils.project_is_exist(cursor, id_sql, BaseHttpStatus.OK.value, "预警详情记录不存在")
            if not res:
                raise Exception('预警详情记录已经存在')

            log_sql = """
                INSERT INTO 
                anomaly_log 
                (
                Identification, ProCode, TunCode, WorkSurCode, StruCode, Mileage, ConEquipCode, DataAcqEquipCode, 
                AnomalyTime, Year, Month, Day, Hour, Minute, Second, Sign, MaxDegree, CompanyCode
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            # 取出 Degree 中最大的预警等级
            max_degree = '三'
            if degree:
                if '一' in degree:
                    max_degree = '一'
                elif '二' in degree:
                    max_degree = '二'
                elif '三' in degree:
                    max_degree = '三'

            now = datetime.strptime(anomaly_time, '%Y-%m-%d %H:%M:%S')
            rows = cursor.execute(log_sql, (
                identification, pro_code, tun_code, work_sur_code, stru_code, mileage, equ_code, acq_code, anomaly_time,
                now.year, now.month, now.day, now.hour, now.minute, now.second, sign, max_degree))
            res = DBUtils.kv(rows, result_dict)
            if res.get('code') != 101:
                return res

            # anomaly_log_desc_insert
            DBUtils.anomaly_log_desc_insert(identification, desc_data, cursor)

            # anomaly_log_img_insert
            DBUtils.anomaly_log_img_insert(identification, img_data, cursor)

            con.commit()
            return {'code': BaseHttpStatus.OK.value, 'msg': '添加成功', 'data': {}}
        except Exception as e:
            if con:
                con.rollback()
            return {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '添加失败', 'data': {str(e)}}
        finally:
            if cursor:
                cursor.close()
            if con:
                DBUtils.close_connection(con)

    @staticmethod
    def anomaly_log_desc_insert(identification, desc_data, cursor):
        """
        在 anomaly_log_desc 表中插入详细记录
        """
        try:
            degree = desc_data.get('Degree')
            region = desc_data.get('Region')
            position = desc_data.get('Position')
            bas = desc_data.get('Bas')
        except Exception as e:
            raise Exception(f"添加失败, {BaseHttpStatus.GET_DATA_ERROR.value}")

        if not all([identification, degree, region, position, bas]):
            raise Exception(f'插入详情缺少必要的字段, {BaseHttpStatus.PARAMETER.value}')

        try:
            # identification 是否已经存在
            id_sql = f"SELECT * FROM anomaly_log_desc WHERE Identification = '{identification}'"
            res = DBUtils.project_is_exist(cursor, id_sql, BaseHttpStatus.OK.value, "预警详情记录不存在")
            if not res:
                raise Exception('预警详情记录已经存在')

            insert_sql = "INSERT INTO anomaly_log_desc (Identification, Degree, Region, Position, Bas) VALUES(%s, %s, %s, %s, %s)"
            # for d, r, p, b in zip(degree, region, position, bas):
            #     row = cursor.execute(insert_sql, (identification, str(d), str(r), str(p), str(b)))
            row = cursor.execute(insert_sql, (identification, str(degree), str(region), str(position), str(bas)))
            if row != 1:
                raise Exception('插入预警详细内容失败')
        except Exception as e:
            raise Exception(f'{str(e)}')

    @staticmethod
    def anomaly_log_img_insert(identification, img_data, cursor):
        """
        在 anomaly_log_img 表中插入图像数据
        """
        try:
            avia_img = img_data.get('AviaPicturePath')
            camera_img = img_data.get('CameraPicturePath')
        except Exception as e:
            raise Exception(f'添加失败, {BaseHttpStatus.GET_DATA_ERROR.value}')

        if not all([identification, avia_img, camera_img]):
            raise Exception(f'插入图片时缺少必要的字段, {BaseHttpStatus.PARAMETER.value}')

        try:
            # identification 是否已经存在
            id_sql = f"SELECT * FROM anomaly_log_img WHERE Identification = '{identification}'"
            res = DBUtils.project_is_exist(cursor, id_sql, BaseHttpStatus.OK.value, "预警详情记录不存在")
            if not res:
                raise Exception('预警详情记录已经存在')

            insert_sql = "INSERT INTO anomaly_log_img (Identification, AviaPicturePath, CameraPicturePath) VALUES (%s, %s, %s)"
            row = cursor.execute(insert_sql, (identification, avia_img, camera_img))
            if row != 1:
                raise Exception('插入预警详细图片内容失败')
        except Exception as e:
            raise Exception(f'{str(e)}')

    @staticmethod
    def get_log_by_columns(data: dict):
        try:
            filters = {
                "ProCode": data.get('ProCode', None),
                "TunCode": data.get('TunCode', None),
                "WorkSurCode": data.get('WorkSurCode', None),
                "StruCode": data.get('StruCode', None),
                "ConEquipCode": data.get('ConEquipCode', None),
                "DataAcqEquipCode": data.get('DataAcqEquipCode', None),
                "Year": data.get('Year', None),
                "Month": data.get('Month', None),
                "Day": data.get('Day', None),
                "Hour": data.get('Hour', None),
                "Minute": data.get('Minute', None),
                "Second": data.get('Second', None)
            }
        except Exception as e:
            return {'code': BaseHttpStatus.GET_DATA_ERROR.value, 'msg': '检索失败', 'data': {'exception': str(e)}}

        con = None
        cursor = None
        try:
            dbu = DBUtils()
            con = dbu.connection(cursor_class=DictCursor)
            cursor = con.cursor()
            con.autocommit(False)

            # 构建动态查询语句
            sql = "SELECT Identification, AnomalyTime FROM anomaly_log WHERE 1=1"
            params = []
            for field, value in filters.items():
                if value:
                    sql += f" AND {field} = %s"
                    params.append(value)
            cursor.execute(sql, params)
            items = cursor.fetchall()
            if not items:
                return {'code': BaseHttpStatus.ERROR.value, 'msg': '查找失败', 'data': {}}

            # TODO: 同时满足多个identification条件下的desc记录
            identifications = [item['Identification'] for item in items]
            placeholders = ', '.join(['%s'] * len(identifications))
            desc_sql = f"SELECT ID, Identification, Degree, Region, Position, Bas FROM anomaly_log_desc WHERE Identification IN ({placeholders})"
            cursor.execute(desc_sql, identifications)
            desc = cursor.fetchall()

            res = {
                "items": items,
                "total": len(items),
                "id": identifications,
                "desc": desc
            }
            # 返回结果
            return {'code': BaseHttpStatus.OK.value, 'msg': '检索成功', 'data': res}
        except Exception as e:
            if con:
                con.rollback()
            return {'code': BaseHttpStatus.EXCEPTION.value, 'msg': '检索失败', 'data': {'exception': str(e)}}
        finally:
            if cursor:
                cursor.close()
            if con:
                DBUtils.close_connection(con)

    @staticmethod
    def pcd_path2db(path, time: datetime, tunnel: Tunnel):
        con = None
        cursor = None
        try:
            dbu = DBUtils()
            con = dbu.connection(cursor_class=DictCursor)
            cursor = con.cursor()
            acq_sql = "SELECT ConEquipCode, Distance FROM eq_data WHERE DataAcqEquipCode = %s"
            cursor.execute(acq_sql, tunnel.device_id)
            acq_res = cursor.fetchone()
            if not acq_res:
                return None

            con_sql = "SELECT * FROM eq_control WHERE ConEquipCode = %s"
            cursor.execute(con_sql, acq_res['ConEquipCode'])
            con_res = cursor.fetchone()
            if not con_res:
                return None

            str_time = time.strftime("%Y-%m-%d %H:%M:%S")
            sql = """
            INSERT INTO pcd_log 
            (ProCode, TunCode, WorkSurCode, StruCode, Mileage, ConEquipCode, DataAcqEquipCode, 
            AnomalyTime, Year, Month, Day, Hour, Minute, Second, Path) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(sql, (
                con_res['ProCode'], con_res['TunCode'], con_res['WorkSurCode'], con_res['StruCode'],
                acq_res['Distance'], con_res['ConEquipCode'], tunnel.device_id, str_time, time.year,
                time.month, time.day, time.hour, time.minute, time.second, str(os.path.abspath(path))))
            con.commit()
            return True
        except Exception as e:
            if con:
                con.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            if con:
                DBUtils.close_connection(con)

    @staticmethod
    def get_path_in_db(data: dict):
        """
        如果不传递任何字段，则默认返回当前最新时间点的文件路径
        如果只传递了年月日三个字段的信息，则默认返当日最新的文件路径
        :param data:
        :return:
        """
        try:
            filters = {
                "Year": data.get('Year', None),
                "Month": data.get('Month', None),
                "Day": data.get('Day', None),
                "Hour": data.get('Hour', None),
                "Minute": data.get('Minute', None),
                "Second": data.get('Second', None)
            }
        except Exception as e:
            print(e)
            return None

        con = None
        cursor = None
        try:
            dbu = DBUtils()
            con = dbu.connection(cursor_class=DictCursor)
            cursor = con.cursor()

            sql = "SELECT Path FROM pcd_log WHERE 1=1"
            params = []
            for k, v in filters.items():
                if v:
                    sql += f" AND {k} = %s"
                    params.append(v)
            cursor.execute(sql, params)
            res = cursor.fetchall()[-1]

            if not res:
                return None
            return res['Path']
        except Exception as e:
            print(e)
            return None
        finally:
            if cursor:
                cursor.close()
            if con:
                DBUtils.close_connection(con)


# if __name__ == '__main__':
#     data = {
#         'Page': 1,
#         'PageSize': 10,
#         'ProCode': '1001',
#         # 'TunCode': '1002',
#         # 'SearchText': 'name1',  # 模糊查询
#         # 'Item': 'ProCode',  # 指定筛选
#         # 'Value': '1002'  # 指定筛选
#     }
#     print(DBUtils.paging_display(data, 'user', data.get('Page'), data.get('PageSize')))

if __name__ == '__main__':
    # start = datetime(2025, 4, 27, 10, 10, 50)
    # end = datetime(2025, 4, 27, 10, 11, 0)
    data = {
        'Page': 1,
        'PageSize': 10,
        # 'ProCode': '1001',
        # 'SearchText': '27',
        # 'Item': 'Hour',
        # 'Value': 10,
        # 'Start': start,
        # 'End': end,
        # 'Column': 'AnomalyTime'
    }
    start = time.time()
    print(DBUtils.paging_display_condition_on_sql(data, 'tunnel', 1, 10, join=True))
    # print(DBUtils.paging_display(data, 'anomaly_log', 1, 10))
    print(time.time() - start)
    # print(DBUtils.search_by_some_item('anomaly_log', 'ProCode', '1003'))
    # now = datetime.now()
    # data = {
    #     'LogData': {
    #         'ProCode': '1003',
    #         'TunCode': '1001',
    #         'WorkSurCode': '49914',
    #         'StruCode': '1001',
    #         'Mileage': '80',
    #         'ConEquipCode': '8899',
    #         'DataAcqEquipCode': '453',
    #         "AnomalyTime": f'{now.strftime("%Y-%m-%d %H:%M:%S")}'
    #     },
    #     'DescData': {
    #         "Degree": ['一', '二', '三'],
    #         "Region": [1, 2, 3],
    #         "Position": [(1, 2, 3), (1, 2, 3), (1, 2, 3)],
    #         "Bas": [3, 3, 3]
    #     },
    #     'ImgData': {
    #         'AviaPicturePath': r'E:\07-code\tunnelProject\adminProject\data\pic\pcd.png',
    #         'CameraPicturePath': r'E:\07-code\tunnelProject\adminProject\data\pic\camera.png'
    #     }
    # }
    # print(DBUtils.anomaly_log_insert(data))
