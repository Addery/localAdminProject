"""
@Author: zhang_zhiyi
@Date: 2024/7/17_9:21
@FileName:construct.py
@LastEditors: zhang_zhiyi
@version: 2.0
@lastEditTime: 
@Description: 构造时序数据：点云区域划分，根据区域分别构造时序数据
"""
import ast
import configparser
import csv
import datetime
import math
import os
from typing import List

import numpy as np
import pandas as pd
from deprecated import deprecated
from open3d.cpu.pybind.geometry import PointCloud
from pandas import DataFrame
import open3d as o3d

from utils.util_rabbitmq import get_line, is_init, pcd2df, find_max_folder, compare_df_len


class Region(object):
    """
    投影面类：xy轴形成的投影面
    """
    MAX_X, MIN_X = 0, 60  # 投影面x轴的范围，单位米
    MAX_Y, MIN_Y = -10, 10  # 投影面y轴的范围，单位米
    GRID_SIZE = 0.5  # 投影面每个网格的大小，单位米

    def __init__(self):
        self.pcds = {}  # 子区域点云字典，索引：数据

    def set_pcd(self, index, pcd) -> None:
        """
        向子区域点云列表添加数据
        :param index: 区域索引
        :param pcd: DataFrame格式点云数据
        :return: None
        """
        self.pcds[index] = pcd

    def get_pcds(self):
        """
        获取子区域点云列表
        :return:
        """
        return self.pcds


class AnomalyPointCloudData(object):
    """
    异常点云数据类
    """

    def __init__(self):
        self.region = {}  # 异常区域数据字典：'区域索引': 'PointCloud点云数据'
        self.describe = {}  # 异常描述信息：'区域索引'：'高度偏离平均值多少'

    def set_region(self, region_index, region_data) -> None:
        """
        添加异常数据
        :param region_index: 字典的键：异常区域索引
        :param region_data: 字典的值：异常区域数据，PointCloud格式
        :return: None
        """
        self.region[region_index] = region_data

    def get_region(self) -> dict:
        """
        获取异常数据
        :return: 返回异常数据字典
        """
        return self.region

    def set_describe(self, region_index, position, bas, degree) -> None:
        """
        添加异常描述信息
        :param region_index: 区域索引
        :param position: 区域位置
        :param bas: 偏离值
        :param degree: 预警等级
        :return: None
        """
        self.describe[region_index] = [position, bas, degree]

    def get_describe(self) -> dict:
        """
        获取异常描述信息
        :return: 异常描述信息字典
        """
        return self.describe


class PointCloudData(object):
    """
    点云数据类
    """

    def __init__(self, data: DataFrame, time: datetime.datetime, preprocess_data: DataFrame, region: Region) -> None:
        self.data = data  # 原始点云数据
        self.time = time  # 点云数据采集时间
        self.preprocess_data = preprocess_data  # 预处理后的点云数据
        self.region = region  # 划分区域后的Region点云数据列表
        self.anomaly = None  # 点云异常区域对象

    def get_data(self) -> DataFrame:
        """
        获取完整点云数据
        :return: DataFrame格式的点云数据
        """
        return self.data

    def set_data(self, data):
        self.data = data

    def set_anomaly(self, anomaly) -> None:
        """
        添加点云异常区域对象
        :param anomaly: 点云异常区域对象
        :return: None
        """
        self.anomaly = anomaly

    def get_anomaly(self) -> AnomalyPointCloudData:
        """
        获取点云异常区域对象
        :return: AnomalyPointCloudData对象
        """
        return self.anomaly

    def set_preprocess_data(self, preprocess_data) -> None:
        """
        添加预处理后的点云数据
        :param preprocess_data: 预处理后的点云数据
        :return: None
        """
        self.preprocess_data = preprocess_data

    def get_preprocess_data(self) -> DataFrame:
        """
        获取预处理后的点云数据
        :return: 预处理后的点云数据，DataFrame格式
        """
        return self.preprocess_data

    def set_region(self, region: Region) -> None:
        """
        添加Region对象
        :param region: Region对象
        :return: None
        """
        self.region = region

    def get_region(self) -> Region:
        """
        获取Region点云数据列表
        :return: Region区域对象
        """
        return self.region

    def get_time(self):
        """
        获取点云数据采集时间
        :return:
        """
        return self.time


class Tunnel(object):
    """
    隧道类
    """

    def __init__(self, high, device_id, data: PointCloudData = None, camera_img=None):
        """
        TODO: 为隧道添加项目相关属性
        :param high: 隧道的实际高度
        :param device_id: 设备id
        :param data: 隧道的点云数据对象
        """
        self._high = high
        self.data = data
        self._project = {
            'device_id': device_id
        }
        self.camera_img = camera_img

    @property
    def project(self):
        return self._project

    @property
    def project_name(self):
        return self._project.get('project_name')

    @project_name.setter
    def project_name(self, value):
        self.project['project_name'] = value

    @property
    def tunnel_name(self):
        return self._project.get('tunnel_name')

    @tunnel_name.setter
    def tunnel_name(self, value):
        self.project['tunnel_name'] = value

    @property
    def working_face(self):
        return self._project.get('working_face')

    @working_face.setter
    def working_face(self, value):
        self.project['working_face'] = value

    @property
    def structure(self):
        return self._project.get('structure')

    @structure.setter
    def structure(self, value):
        self.project['structure'] = value

    @property
    def device_id(self):
        return self._project.get('device_id')

    @device_id.setter
    def device_id(self, value):
        self.project['device_id'] = value

    @property
    def mileage(self):
        return self._project.get('mileage')

    @mileage.setter
    def mileage(self, value):
        self.project['mileage'] = value

    @property
    def high(self):
        return self._high

    @high.setter
    def high(self, value):
        self.high = value

    def set_data(self, data: PointCloudData):
        """
        添加点云数据对象
        :param data: PointCloudData点云数据对象
        """
        self.data = data

    def get_data(self) -> PointCloudData:
        """
        获取点云数据对象
        :return: 点云数据对象
        """
        return self.data

    def __str__(self):
        return (f"Tunnel(high={self.high}, project_name={self.project_name}, tunnel_name={self.tunnel_name},"
                f" working_face={self.working_face}, structure={self.structure}, device_id={self.device_id},"
                f" mileage={self.mileage})")


def calculate_gap(tunnel: Tunnel, threshold: float = 0.0005) -> float:
    """
    计算 隧道的实际高度 和 点云数据最高点 两者的差距，用于calibrate_data()校准坐标数据以0为起点
    :param tunnel: 隧道对象
    :param threshold: 选取计算z轴最高处的范围
    """
    # 获取点云数据的全部z坐标数据
    point_cloud = tunnel.get_data()
    data = point_cloud.get_data()
    z_vals = data['z'].values

    # 从大到小排序
    sorted_arr = np.sort(z_vals, kind='mergesort')[::-1]
    # 计算threshold的位置
    percentile = int(len(sorted_arr) * threshold)
    # 截取前threshold的数据
    target_arr = sorted_arr[:percentile]
    # 求平均值
    max_z = target_arr.mean()

    # 计算差值并返回
    return tunnel.high - max_z


def calculate_data(pcds: dict, init: bool, config: configparser.ConfigParser):
    """
    初始化阶段写入所有列，但是非初始化阶段只需写入时序数据中有的列
    :param pcds: 区域点云对象
    :param init: 是否在初始化阶段
    :param config: 配置文件对象
    :return: 时序数据
    """
    if init:
        return None, pcds
    column_list = ast.literal_eval(config.get("detect", "column"))
    res_pcds = dict.fromkeys(column_list, math.nan)
    for k, v in pcds.items():
        if str(k) in column_list:
            res_pcds[str(k)] = v
    return column_list, res_pcds


class Segment(object):
    """
    点云区域划分类：根据点云投影到固定的xy投影面的区域划分点云
    """

    def __init__(self, data_list: list):
        self.data_list = data_list  # DataFrame点云数据列表
        self.res_list = []  # 划分区域后的子点云数据列表

    def segment(self) -> List[Region]:
        """
        划分区域
        :return: 划分结果: 子点云数据列表 List[Region]
        """
        # 遍历self.data_list
        for data in self.data_list:
            # 过滤高度在2.5米以下的数据
            # config = filter_high(config, height=2.5)
            if data is not None:
                # 划分区域
                geometries = Segment.subdivide(data)
                self.res_list.append(geometries)

        # 返回划分结果
        return self.res_list

    @staticmethod
    def subdivide(data: DataFrame) -> Region:
        """
        划分子区域
        :param data: 原始数据
        :return: 划分结果，PointCloud列表
        """
        # 提取x, y, z坐标信息
        points = data[['X', 'Y', 'Z']].values
        # 创建 Open3D 点云对象
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)

        # 投影到二维平面 (x, y)，忽略 z 坐标
        points_2d = points[:, :2]

        # 确定固定的区域范围
        min_x, max_x = Region.MIN_X, Region.MAX_X  # 固定的x范围
        min_y, max_y = Region.MIN_Y, Region.MAX_Y  # 固定的y范围

        # 定义网格大小和区域数量
        grid_size = Region.GRID_SIZE  # 网格大小
        num_x = int(np.ceil((max_x - min_x) / grid_size))
        num_y = int(np.ceil((max_y - min_y) / grid_size))

        # 划分点云数据到多个小区域
        regions = [[] for _ in range(num_x * num_y)]
        for idx, point in enumerate(points_2d):
            x_idx = int((point[0] - min_x) // grid_size)
            y_idx = int((point[1] - min_y) // grid_size)
            region_idx = x_idx + y_idx * num_x
            regions[region_idx].append(idx)

        # 创建颜色映射
        colors = np.random.rand(num_x * num_y, 3)  # 随机生成颜色

        # 创建 Open3D 点云对象列表
        geometries = Region()
        for region_idx, point_indices in enumerate(regions):
            if point_indices:  # 如果该区域有数据
                region_points = points[point_indices]
                pcd_region = o3d.geometry.PointCloud()
                pcd_region.points = o3d.utility.Vector3dVector(region_points)
                color = colors[region_idx]
                pcd_region.paint_uniform_color(color)

                # vis = o3d.visualization.Visualizer()
                # vis.create_window(window_name="Region Coloring", width=1024, height=768)
                # vis.add_geometry(pcd_region)
                #
                # # 渲染并关闭窗口
                # vis.run()
                # vis.destroy_window()

                # 2024.8.6 将pcd转化为df格式
                df_region = pcd2df(pcd_region)
                # 向区域点云对象的列表中添加数据，DataFrame格式
                geometries.set_pcd(region_idx, df_region)
            else:  # 该区域没有数据，直接用None填充
                geometries.set_pcd(region_idx, None)

        # print(type(geometries), geometries)
        # print(type(geometries.get_pcds()), geometries.get_pcds())
        # 创建 Open3D 可视化窗口并添加几何体
        # vis = o3d.visualization.Visualizer()
        # vis.create_window(window_name="Region Coloring", width=1024, height=768)
        # for k, geometry in geometries.get_pcds().items():
        #     print(type(k), k)
        #     print(type(geometry), geometry)
        #
        #     if geometry is not None:
        #         vis.add_geometry(geometry)
        #
        # # 渲染并关闭窗口
        # vis.run()
        # vis.destroy_window()

        # 返回划分区域的子点云列表对象
        return geometries


class SingleSeriesData(object):
    """
    用于规范时序数据的列名
    """

    def __init__(self, length):
        self.columns = [str(i) for i in range(length)]  # DateFrame列名：regions的索引
        self.length = length  # 长度，regions的长度

    def get_df(self, vals: list, columns) -> DataFrame:
        """
        根据列名构造DataFrame格式数据
        :param vals: 时序数据列表
        :param columns:
        :return: DataFrame格式时序数据
        """
        if columns is None:
            columns = self.columns
        return pd.DataFrame([vals], columns=columns)

    def get_columns(self) -> list:
        """
        获取所有列名
        :return: columns列名列表
        """
        return self.columns


class TimeSeriesFile(object):
    """
    时序数据文件类
    """
    # DEFAULT_TIME_SERIES_SAVE_PATH = "config/timeseries"  # 时序数据默认保存文件夹路径
    DEFAULT_TIME_SERIES_SAVE_PATH = "../data"  # 时序数据默认保存文件夹路径

    def __init__(self, length: int = 1000, count=0, directory_path: str = DEFAULT_TIME_SERIES_SAVE_PATH):
        self.length = length  # 单个时序数据文件数据项的最大长度，默认长度为1000
        self.empty = length  # 当前文件中剩余空间，默认值为length
        self.count = count  # 时序数据文件夹中的文件数量，用于时序数据文件命名
        self.directory_path = directory_path  # 时序数据保存文件夹路径

    def get_length(self) -> int:
        """
        获取单个时序数据文件数据项的最大长度
        :return: int, 单个时序数据文件数据项的最大长度
        """
        return self.length

    def get_directory_path(self) -> str:
        """
        获取时序数据保存文件夹路径
        :return: str, 时序数据保存文件夹路径
        """
        return self.directory_path

    def get_empty(self) -> str:
        """
        获取当前文件中剩余空间
        :return: int, 当前文件中剩余空间
        """
        return self.directory_path

    def set_empty(self, length: int) -> None:
        """
        修改当前文件中剩余空间
        :param length: int 实际剩余空间
        """
        self.empty = length

    def get_count(self) -> int:
        """
        获取时序数据文件夹中的文件数量
        :return: int, 时序数据文件夹中的文件数量
        """
        return self.count

    def set_count(self, count) -> None:
        """
        修改时序文件数量
        :param count: 数量值
        :return: None
        """
        self.count = count

    def create_new_file(self, ssd: SingleSeriesData, directory_path: str = DEFAULT_TIME_SERIES_SAVE_PATH) -> str:
        """
        创建新的时序数据文件
        :param directory_path: 文件目录
        :param ssd:
        :return: 生成新的文件路径
        """
        path = os.path.join(directory_path, f"{self.count}.csv")
        # 打开CSV文件，准备写入
        with open(path, mode='w', newline='', encoding='utf-8') as file:
            # 创建CSV writer对象
            writer = csv.writer(file)
            # 写入表头
            header = ssd.get_columns()
            writer.writerow(header)
        # with 自动关闭文件
        return path

    @staticmethod
    def check_for_csv_files(directory_path: str = DEFAULT_TIME_SERIES_SAVE_PATH) -> bool:
        """
        检查指定目录中是否存在 .csv 文件。
        :param directory_path: 时序数据所在文件夹
        :return: bool, 如果存在 .csv 文件则返回 True，否则返回 False
        """
        os.makedirs(directory_path, exist_ok=True)
        with os.scandir(directory_path) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith('.csv'):
                    return True
        return False

    @staticmethod
    def get_latest_csv_file(directory_path: str = DEFAULT_TIME_SERIES_SAVE_PATH):
        """
        获取目录中最新的 .csv 文件名。
        :param directory_path: str, 目录路径
        :return: str, 最新的 .csv 文件名。如果目录中没有 .csv 文件，则返回 None。
        """
        csv_files = []
        with os.scandir(directory_path) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith('.csv'):
                    csv_files.append(entry.name)
        # csv_files = [f for f in os.listdir(directory_path) if f.endswith('.csv')]
        if not csv_files:
            return None
        latest_file = max(csv_files, key=lambda x: os.path.getmtime(os.path.join(directory_path, x)))
        # latest_file = max(csv_files, key=os.path.getmtime)
        return latest_file

    @staticmethod
    def get_max_csv_file(directory_path: str = DEFAULT_TIME_SERIES_SAVE_PATH):
        csv_files = []
        with os.scandir(directory_path) as entries:
            for entry in entries:
                if entry.is_file() and entry.name.endswith('.csv'):
                    csv_files.append(entry.name)
        if not csv_files:
            return None
        return max(csv_files)

    @staticmethod
    def get_csv_row_count(path: str) -> int:
        """
        获取 .csv 文件的行数。
        :param path: str, .csv 文件路径
        :return: int, 行数
        """
        return get_line(path)

    @staticmethod
    @deprecated(reason="Use is_init()")
    def get_time_series_number(init_count: int, path: str):
        """
        统计时序数据的数量
        :param init_count: 时序数据长度，判断是否在初始化阶段
        :param path: 时序数据所在路径
        :return: 返回True说明，在初始化阶段
        """
        return is_init(init_count, path)


class Merge(object):
    """
    构建时序数据类
    """

    def __init__(self, tunnel: Tunnel = None, save_path: str = TimeSeriesFile.DEFAULT_TIME_SERIES_SAVE_PATH):
        self.tunnel = tunnel
        self.save_path = save_path

    def get_tunnel(self) -> Tunnel:
        return self.tunnel

    def merge(self, init: bool, config: configparser.ConfigParser, curr_directory) -> None:
        """
        :param init: 是否在初始化阶段，初始化阶段写入全部区域数据，非初始化阶段写入时序数据中有的数据
        :param config: 配置文件对象
        :param curr_directory: 当前时序数据保存目录
        :return:
        """
        point_cloud = self.tunnel.get_data()
        region = point_cloud.get_region()
        if region is None:
            return
        pcd_dict = region.get_pcds()
        # pcds = list(regions.get_pcds().values())

        # 用于创建文件，初始化csv文件头
        ssd = SingleSeriesData(len(pcd_dict))
        # 初始化文件夹对象
        tsf = TimeSeriesFile(length=130, directory_path=curr_directory)
        # 检索文件夹中有没有文件
        if not TimeSeriesFile.check_for_csv_files(directory_path=curr_directory):
            # 没有文件夹则创建文件
            tsf.set_count(0)
            tsf.create_new_file(ssd, directory_path=curr_directory)
        else:
            # 有文件，则检索最新的文件名称
            last_file = TimeSeriesFile.get_max_csv_file(directory_path=curr_directory)
            if last_file is not None:
                # 根据文件名重设count
                tsf.set_count(int(os.path.splitext(last_file)[0]))

        # 构建当前时序数据文件路径
        current_series_path = os.path.join(tsf.get_directory_path(), f"{tsf.count}.csv")
        # 检查当前文件行数
        length = tsf.get_length()
        line = TimeSeriesFile.get_csv_row_count(current_series_path)
        empty = length - line
        # 检查当前文件中是否还可以插入数据
        if 0 < empty <= length:  # 若有剩余空间
            # 设置剩余空间
            tsf.set_empty(empty)
        elif empty <= 0:  # 若没有剩余空间则创建新的文件
            tsf.set_count(tsf.get_count() + 1)
            current_series_path = tsf.create_new_file(ssd, directory_path=curr_directory)
        # 组合数据，注意初始化阶段和非初始化阶段有所不同
        column_list, res_pcds = calculate_data(pcd_dict, init, config)
        # 将数据写入文件
        Merge.merge_data(res_pcds, current_series_path, ssd, column_list)

    @staticmethod
    def update_df(file_line, max_csv_path, max_csv_name, update_data,
                  directory=TimeSeriesFile.DEFAULT_TIME_SERIES_SAVE_PATH):
        """
            如果文件行数 >= 数据行数：直接取文件中后面几行
            如果文件行数 < 数据行数：提取数据后面和当前文件行数相同的数据进行修改，再找上一个文件
        :return:
        """
        try:
            update_data_length = len(update_data)
            timeseries_data = pd.read_csv(max_csv_path)
            # 修正update_data数据，使用nan值填充缺失列
            update_date_modify = compare_df_len(timeseries_data, update_data)
            if file_line >= update_data_length:
                timeseries_data.iloc[-update_data_length:, :] = update_date_modify.values
                timeseries_data.to_csv(max_csv_path, index=False)
            else:
                timeseries_data = update_date_modify[-file_line:]
                timeseries_data.to_csv(max_csv_path, index=False)

                filename_list = []
                timeseries_path = directory
                with os.scandir(timeseries_path) as entries:
                    for entry in entries:
                        if entry.is_file() and entry.name.endswith('.csv') and entry.name != max_csv_name:
                            filename_list.append(entry.name)
                if not filename_list:  # 如果文件列表为空
                    return False
                sub_csv_path = os.path.join(timeseries_path, max(filename_list))
                sub_timeseries_data = pd.read_csv(sub_csv_path)
                sub_length = update_data_length - file_line
                sub_timeseries_data[-sub_length:] = update_date_modify[:sub_length]
                sub_timeseries_data.to_csv(sub_csv_path, index=False)
            return True
        except Exception as e:
            print(f"An error occurred: {e} in update_df")
            return False

    @staticmethod
    def update_df_merge(data: DataFrame, directory=TimeSeriesFile.DEFAULT_TIME_SERIES_SAVE_PATH):
        """
            1. 找到最新的.csv文件/文件名称最大的文件
            2. 求出文件的行数
            3. 判断文件行数和要修改的数据行数
        :param data:
        :param directory:
        :return:
        """
        max_csv_path, max_csv_name = find_max_folder(directory)
        if max_csv_path is None:
            return False
        file_line = get_line(max_csv_path)
        if file_line == 0:
            return False
        return Merge.update_df(file_line, max_csv_path, max_csv_name, data, directory)

    @staticmethod
    def merge_data(vals: dict, file, ssd: SingleSeriesData, column_list: list) -> None:
        """
        :param vals: 一行时序数据
        :param file: 时序数据保存路径
        :param ssd: SingleSeriesData对象，用于构造DataFrame数据对象
        :param column_list: 列名
        :return: None
        """
        z_avg = []
        for df in vals.values():
            if df is math.nan or df is None:
                z_avg.append(math.nan)
            else:
                points = df[['X', 'Y', 'Z']].values
                points = np.asarray(points)
                # 分离z坐标
                z_vals = points[:, 2]
                # 求平均值
                z_avg.append(z_vals.mean())
        # 创建时序DataFrame数据对象
        series_df = ssd.get_df(z_avg, columns=column_list)
        Merge.merge_write(series_df, file)

    @staticmethod
    def merge_write(data: DataFrame, path: str) -> None:
        """
        :param data: DataFrame时序数据
        :param path: 写入的文件路径
        :return: None
        """
        data.to_csv(path, mode='a', header=False, index=False)

    @staticmethod
    def merge_region(r: Region) -> PointCloud:
        """
        :param r: 待合并的点云分割区域对象
        :return: PointCloud
        """
        # 创建一个空的 PointCloud 对象
        merged_pc = o3d.geometry.PointCloud()
        for pc in r.get_pcds():
            if pc != 'null':
                # 将每个 PointCloud 对象的点云数据添加到 merged_pc 中
                merged_pc.points.extend(pc.points)
                if pc.colors:  # 如果存在颜色信息
                    merged_pc.colors.extend(pc.colors)
                if pc.normals:  # 如果存在法线信息
                    merged_pc.normals.extend(pc.normals)
        # o3d.visualization.draw_geometries([merged_pc], window_name='合并pcd', width=1024, height=768)
        return merged_pc


if __name__ == '__main__':
    t = Tunnel(7, 'project_name', 'tunnel_name', 'working_face', 'structure', 'device_id', 'mileage')
    print(t)
    t.project_name = 'modify_project_name'
    print(t)
    print(t.tunnel_name)
    m = Merge()
    config = configparser.ConfigParser()
    m.merge(False, config, 'project_name', 'tunnel_name', 'working_face', 'device_id', 'mileage')
#     # 接收数据
#     # receiver = Receiver()
#     # res_list = receiver.run()
#     df_list = []
#     folder_path = r"/outer/config\receive"
#     for file_name in os.listdir(folder_path):
#         file_path = os.path.join(folder_path, file_name)  # 文件路径
#         df = pd.read_csv(file_path)
#         df_list.append(df)
#
#     # 数据预处理
#     preprocessor = Preprocessor()
#     pre_list = preprocessor.run(df_list)
#
#     # 划分区域
#     segment = Segment(pre_list)
#     regions_list = segment.segment()  # 返回Region对象列表
#
#     """
#         merge_clouds[Merge对象]
#         Merge中包含Tunnel对象
#         Tunnel中包含：隧道的实际高度 和 PointCloudData点云数据对象
#         PointCloudData中包含：DataFrame点云数据、regions区域点云列表、AnomalyPointCloudData异常点云对象
#     """
#     merge_clouds = []
#     for df, pre, region in zip(df_list, pre_list, regions_list):
#         merge_clouds.append(Merge(Tunnel(6, PointCloudData(df, pre, region))))
#
#     # 构造时序数据
#     for m in merge_clouds:
#         m.merge()
#
#     # print(TimeSeriesFile.get_time_series_number())
