"""
@Author: zhang_zhiyi
@Date: 2024/7/24_11:49
@FileName:util_pcd.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description: 点云数据存储工具类
"""
import ast
import configparser
import shutil
from datetime import datetime, timedelta

import os

import pandas as pd
from deprecated import deprecated
from open3d.cpu.pybind.geometry import PointCloud
import open3d as o3d
from pandas import DataFrame

from rmq.construct import PointCloudData, Tunnel
from utils.util_database import DBUtils


def df2pcd(data: DataFrame) -> PointCloud:
    """
    转换3D点云数据格式：DataFrame--->PointCloud
    :param data: 原始DataFrame格式的3D点云数据
    :return: PointCloud3D点云格式
    """
    points = data[['X', 'Y', 'Z']].values
    colors = data[['R', 'G', 'B']].values
    # 创建 Open3D 点云对象
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    pcd.colors = o3d.utility.Vector3dVector(colors)
    return pcd


def pcd2png(pcd: PointCloud, path: str):
    # 创建可视化窗口并设置窗口名称、大小
    vis = o3d.visualization.Visualizer()
    # vis = o3d.visualization.VisualizerWithOffscreenRendering()
    vis.create_window(window_name="Point Cloud", width=1024, height=768)

    # 添加点云到窗口
    vis.add_geometry(pcd)

    # 渲染
    vis.poll_events()
    vis.update_renderer()

    # 保存可视化结果为图像文件
    path = os.path.join(path, 'test.png')
    vis.capture_screen_image(path)
    # 关闭窗口
    vis.destroy_window()
    return path


def write_log(now, log_path, time_list):
    """
    RabbitMQ
    Queue: inner2outer
    :param now:
    :param log_path:
    :param time_list:
    :return:
    """
    time = datetime.strptime(now, '%Y-%m-%d %H:%M:%S.%f')
    # 构建保存路径
    save_path = os.path.join(log_path, str(time.year), str(time.month), str(time.day), str(time.hour),
                             str(time.minute), str(time.second))
    os.makedirs(save_path, exist_ok=True)
    # 创建 ConfigParser 对象
    config = configparser.ConfigParser()
    for i, data in enumerate(time_list):
        config['Time'] = {
            'time': data
        }
        with open(os.path.join(save_path, f"{i}.ini"), 'w') as configfile:
            config.write(configfile)


def number2str(number_list):
    res_list = []
    for e in number_list:
        if e == 1:
            res_list.append("一")
        elif e == 2:
            res_list.append("二")
        elif e == 3:
            res_list.append("三")
    return res_list


def write_anomaly_log(now, log_path, time_list, anomaly_list):
    """
    RabbitMQ
    Queue: inner2outer
    :param now:
    :param log_path:
    :param time_list:
    :param anomaly_list:
    :return:
    """
    time = datetime.strptime(now, '%Y-%m-%d %H:%M:%S.%f')
    # 构建保存路径
    save_path = os.path.join(log_path, str(time.year), str(time.month), str(time.day), str(time.hour),
                             str(time.minute), str(time.second))
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    # 创建 ConfigParser 对象
    config = configparser.ConfigParser()
    for i, data in enumerate(zip(time_list, anomaly_list)):
        position, bas, degree = [], [], []
        for element in list(data[1].values()):
            position.append(element[0])
            bas.append(element[1])
            degree.append(element[2])
        config['Time'] = {
            'time': data[0]
        }
        config['Anomalies'] = {
            'region index': str(list(data[1].keys())),
            'position': position,
            'bas': bas,
            # 'degree': number2str(degree)
            'degree': degree
        }
        with open(os.path.join(save_path, f"{i}.ini"), 'w') as configfile:
            config.write(configfile)


def get_region_dict(path):
    """
    http://127.0.0.1:8024/outer/service/compare
    :param path:
    :return:
    """
    if not os.path.exists(path):
        return None
    root_folder = find_latest_root_folder(path)
    latest_path = str(find_max_folder(root_folder))
    if latest_path is None:
        return None
    else:
        root_filepath = get_root_filename(latest_path)
    return root_filepath


def get_log_data(path):
    """
    获取日志信息中的区域索引和区域偏移值，以字典形式返回
    :param path:
    :return:
    """
    config = configparser.ConfigParser()
    config.read(path)
    res_dict = {}
    if config.has_option("Anomalies", "region index") and config.has_option("Anomalies", "bas"):
        region_index = ast.literal_eval(config.get("Anomalies", "region index"))
        region_bas = ast.literal_eval(config.get("Anomalies", "bas"))
        for i, b in zip(region_index, region_bas):
            res_dict[i] = b
        return res_dict
    return None


def get_log_bas_dict(path):
    """
    http://127.0.0.1:8024/outer/service/compare
    :param path:
    :return:
    """
    if not os.path.exists(path):
        return None
    log_folder = find_latest_ini_folder(path)
    latest_log_path = str(find_max_log(log_folder))
    if latest_log_path is None:
        return None
    else:
        log_dict = get_log_data(latest_log_path)
        if log_dict is None:
            return None
    return log_dict


def df_mean(data: DataFrame):
    data_z = data.loc[:, 'Z']


def compare_log(region_index, root_log, comparison_log):
    """
    比较
    :param region_index:
    :param root_log:
    :param comparison_log:
    :return:
    """
    # 修正region_index
    region_index = region_index.split('.')[0]
    root_bas, compare_bas = root_log.get(region_index), comparison_log.get(region_index)
    if root_bas - compare_bas >= 0.02:
        return True
    return False


def compare_region(root, comparison, root_log, comparison_log):
    """
    1.先找到comparison中不同于root的区域索引
    2.在找到相同的索引检索日志
    :param root:
    :param comparison:
    :param root_log:
    :param comparison_log:
    :return:
    """
    # 读取root数据，并将颜色设置为默认的绿色
    res_list = {}
    for i, v in root.items():
        data = color_df(pd.read_csv(v, usecols=['X', 'Y', 'Z', 'R', 'G', 'B']), [118, 238, 198])
        res_list[i] = data
    # 对比两个数据，找到root中没有的区域替换res_list对应的数据，找到相同的数据查阅日志进行比对差距大的进行替换
    root_keys, comparison_keys = root.keys(), comparison.keys()
    compare_message = []  # TODO：用于存储对比信息
    for k in comparison_keys:
        if k not in root_keys:
            res_list[k] = pd.read_csv(comparison.get(k), usecols=['X', 'Y', 'Z', 'R', 'G', 'B'])
        elif k in root_keys:
            root_dict, compare_dict = get_log_bas_dict(root_log), get_log_bas_dict(comparison_log)
            if root_dict is None or compare_dict is None:
                return None
            if compare_log(k, root_dict, compare_dict):
                res_list[k] = pd.read_csv(comparison.get(k), usecols=['X', 'Y', 'Z', 'R', 'G', 'B'])
    return res_list


@deprecated(reason="use merge_data")
def merge_df_dict(init_dict, compare_res_dict):
    """
    替换数据
    :param init_dict:
    :param compare_res_dict:
    :return:
    """
    for k, v in compare_res_dict.items():
        init_dict[k] = v

    df_list = []
    for e in list(init_dict.values()):
        df_list.append(e)
    res_df = pd.concat(df_list, ignore_index=True)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(res_df[['X', 'Y', 'Z']].values)
    pcd.colors = o3d.utility.Vector3dVector(res_df[['R', 'G', 'B']].values / 255.0)
    o3d.visualization.draw_geometries([pcd])

    coordinate_list, color_list = [], []
    for df in init_dict.values():
        # 检查是否有颜色列
        has_color = all(col in df.columns for col in ['R', 'G', 'B'])
        for line in df.itertuples(index=False):
            coordinate_list.extend([line.X, line.Y, line.Z])
            if has_color:
                color_list.extend([line.R, line.G, line.B])
            else:
                color_list.extend([0, 0, 0])
    return coordinate_list, color_list


def compare_data(init_region, root, comparison, root_log, comparison_log):
    """
    http://127.0.0.1:8024/outer/service/compare
    对比接口
        1.以第一个时间点的数据为基准
        2.找出第二个时间点中不同的异常区域
        3.将两者之间相同的异常区域通过日志信息进行比对
        4.用后者不同于前者或者差距较大的数据替换前者中的数据
    :return:
    """
    # 拿到两个数据的区域字典
    init_dict, root_dict, comparison_dict = get_root_data(init_region), get_region_dict(root), get_region_dict(
        comparison)
    if root_dict is None:
        return {'msg': 'root数据不存在'}
    if comparison_dict is None:
        return {'msg': 'comparison数据不存在'}
    if init_dict is None:
        return {'msg': '初始化数据不存在'}
    # 比较两个数据
    compare_res_dict = compare_region(root_dict, comparison_dict, root_log, comparison_log)
    if compare_res_dict is None:
        return {'msg': 'root或者comparison数据不存在'}
    coordinate_list, color_list = merge_data(init_dict, compare_res_dict, True)
    return {'xyz': str(coordinate_list), 'rgb': str(color_list)}


def data_visual(path, init_path):
    """
    http://127.0.0.1:8024/outer/service/log_data_visual
    :param path:
    :param init_path:
    :return:
    """
    init = {}
    with os.scandir(init_path) as entries:
        for entry in entries:
            init[entry.name[:-4]] = pd.read_csv(entry.path)
    # 寻找最新的文件夹
    latest_path = find_latest_folder(path)
    if latest_path is None:
        return None
    # 将其保存为字典形式 anomaly 文件名：dataframe
    anomaly = {}
    with os.scandir(str(latest_path)) as entries:
        for entry in entries:
            anomaly[entry.name[:-4]] = pd.read_csv(entry.path)

    # 遍历root的键，将其dataframe的rgb设置为绿色，找到与anomaly键相同的键，将其dataframe的rgb设置为红色
    k_a_list, k_r_list = list(anomaly.keys()), list(init.keys())
    for k in k_a_list:
        if k in k_r_list:
            init[k] = anomaly.get(k)

    # 组合数据xyz: [], rgb: []
    res_df = pd.concat(list(init.values()), ignore_index=True)
    has_rgb = all(col in res_df.columns for col in ['R', 'G', 'B'])

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(res_df[['X', 'Y', 'Z']].values)
    pcd.colors = o3d.utility.Vector3dVector(res_df[['R', 'G', 'B']].values / 255.0)
    o3d.visualization.draw_geometries([pcd])

    xyz, rgb = [], []
    for row in res_df.itertuples(index=False):
        # 添加坐标
        xyz.extend([row.X, row.Y, row.Z])
        # 添加颜色或默认值
        if has_rgb:
            rgb.extend([row.R, row.G, row.B])
        else:
            rgb.extend([0, 0, 0])
    return {'xyz': xyz, 'rgb': rgb}


def get_log_data_tag(path):
    """
    http://127.0.0.1:8024/outer/service/log
    :param path:
    :return:
    """
    directory_names = []
    current_path = os.path.dirname(path)

    while current_path and current_path != os.path.sep:
        current_path, tail = os.path.split(current_path)
        if tail:
            directory_names.insert(0, tail)
        else:
            if current_path:
                directory_names.insert(0, current_path)
            break
    tag_list = ['project_name', 'tunnel_name', 'working_face', 'mileage', 'device_id', 'year', 'month', 'day', 'hour',
                'minute', 'second']
    tag = {}
    for i, (t, element) in enumerate(zip(tag_list, directory_names[-12:])):
        if i == 5 or i == 6:  # 跳过 -7 和 -6 对应的元素
            continue
        tag[t] = element
    return tag


def find_log_path(path):
    """
    http://127.0.0.1:8024/outer/service/log
    :param path:
    :return:
    """
    log_path_list = []
    if not os.path.exists(path):
        print("not found path")
    for root, dirs, files in os.walk(path):
        # 检查当前目录的文件是否包含 .ini 文件
        if any(file.endswith('.ini') for file in files):
            log_path_list.append(root)
    return log_path_list


def process_log(log_path):
    """
    处理单个日志文件
    http://127.0.0.1:8024/outer/service/log
    :param log_path:
    :return:
    """
    latest_log = find_max_log(log_path)
    if latest_log is None:
        return None

    config = configparser.ConfigParser()
    config.read(str(latest_log))
    if not config.has_section('Anomalies'):
        return None

    try:
        now = datetime.strptime(config.get('Time', 'time'), '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        return None  # 如果时间格式不正确，跳过此日志

    time_str = f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}"
    index = ast.literal_eval(config.get('Anomalies', 'region index'))
    position = ast.literal_eval(config.get('Anomalies', 'position'))
    bas = ast.literal_eval(config.get('Anomalies', 'bas'))
    degree = ast.literal_eval(config.get('Anomalies', 'degree'))
    tag = get_log_data_tag(log_path)

    return time_str, index, position, bas, degree, tag


def find_log(path):
    """
    http://127.0.0.1:8024/outer/service/log
    :param path:
    :return:
    """
    log_path_list = find_log_path(path)
    if not log_path_list:
        return None

    time, index, position, bas, degree, tag = [], [], [], [], [], []

    # 使用线程池来并发处理日志文件，提升速度
    # with ThreadPoolExecutor() as executor:
    #     results = list(executor.map(process_log, log_path_list))
    #
    # for result in results:
    #     if result:
    #         t, idx, pos, b, deg, tg = result
    #         time.append(t)
    #         index.append(idx)
    #         position.append(pos)
    #         bas.append(b)
    #         degree.append(deg)
    #         tag.append(tg)

    for log_path in log_path_list:
        config = configparser.ConfigParser()
        latest_log = find_max_log(log_path)
        if latest_log is None:
            continue
        config.read(str(latest_log))
        if not config.has_section('Anomalies'):
            continue

        now = datetime.strptime(config.get('Time', 'time'), '%Y-%m-%d %H:%M:%S.%f')

        time.append(f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}")
        index.append(ast.literal_eval(config.get('Anomalies', 'region index')))
        position.append(ast.literal_eval(config.get('Anomalies', 'position')))
        bas.append(ast.literal_eval(config.get('Anomalies', 'bas')))
        degree.append(ast.literal_eval(config.get('Anomalies', 'degree')))
        tag.append(get_log_data_tag(log_path))

    if not time:
        return None
    return time, index, position, bas, degree, tag


@deprecated(reason="deprecated")
def filter_degree(time, index, position, bas, degree, tag):
    # 预警等级大于1再添加至列表中
    log_list = []  # [[time, [position], [bas], [degree], tag]
    for data in zip(time, index, position, bas, degree, tag):
        p, b, d = [], [], []
        for i, e in enumerate(data[4]):
            print(d)
            if e > 0:
                p.append(data[2][i])
                b.append(data[3][i])
                d.append(e)
        log_list.append([data[0], p, b, d])
    return log_list


def show_log(path):
    """
    http://127.0.0.1:8024/outer/service/log
    :param path:
    :return:
    """
    res = find_log(path)
    if res is None:  # 日志文件不存在
        return None

    time, index, position, bas, degree, tag = res
    res_log = []
    for t, ind, pos, b, deg, tag in zip(time, index, position, bas, degree, tag):
        """
        index, position, bas, degree
        """
        anomaly_message = ""
        # 构造异常信息
        for i in range(len(deg)):
            x, _, _ = pos[i]
            anomaly_message += f"距离雷达水平距离{format(x, '.2f')}m处在垂直方向上发生{format(b[i] * 1000, '.2f')}mm偏移"
            if i != len(degree) - 1:
                anomaly_message += '，'

        res_log.append([t, max(deg), anomaly_message, ind, tag])
    return res_log


def find_latest_log(path):
    """
    http://127.0.0.1:8024/outer/service/log
    :param path:
    :return:
    """
    latest_file = None
    latest_mtime = None

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.ini'):
                file_path = os.path.join(root, file)
                file_time = os.path.getmtime(file_path)
                if latest_mtime is None or file_time > latest_mtime:
                    latest_file = file_path
                    latest_mtime = file_time
    return latest_file


def count_directories(path, tag):
    """
    返回目标path中的文件夹数量
    :param path:
    :param tag: True表示文件夹，False表示文件
    :return:
    """
    try:
        with os.scandir(path) as entries:
            # 使用生成器表达式过滤出文件夹并计数
            if tag:
                directories = sum(1 for entry in entries if entry.is_dir())
            else:
                directories = sum(1 for entry in entries if entry.is_file())
        return directories
    except Exception as e:
        print(f"An error occurred: {e} in count_directories")
        return None


def process_init_file(path, tag):
    """

    :param path:
    :param tag:
    :return:
    """
    if os.path.exists(path):
        os.remove(path) if tag else shutil.rmtree(path)


def recreate_init_file(path):
    """
    重新创建初始化目录
    :param path:
    :return:
    """
    if os.path.exists(path):
        shutil.rmtree(path)
        os.makedirs(path)


def write_init(path: str, init: bool, data: PointCloudData, init_name, region_name):
    """
    init.csv完整的原始数据
    regions.csv完整的预处理后的区域数据
    :param path:
    :param init:
    :param data:
    :param init_name:
    :param region_name:
    :return:
    """
    try:
        # 获取数据
        all_data = data.get_data()
        regions_data = data.get_region().get_pcds()
        os.makedirs(path, exist_ok=True)
        # 构建保存路径
        init_save_path = os.path.join(path, init_name)
        # process_init_file(init_save_path, True)
        regions_save_path = os.path.join(path, region_name)
        # process_init_file(regions_save_path, False)
        # 写入数据
        all_data.to_csv(init_save_path, index=False)
        if write_df(regions_save_path, path, regions_data, init):
            return True
        else:
            return False
    except Exception as e:
        print(f"An error occurred: {e} in write_init")
        return False


def set_color_by_degree(degree):
    """
    根据预警等级选择颜色
        正常：绿色[118, 238, 198]
        一级预警：黄色[238, 180, 34]
        二级预警：橙色[238, 64, 0]
        三级预警：红色[178, 34, 34]
    :param degree:
    :return:
    """
    colors = {
        "一": [238, 180, 34],
        "二": [238, 64, 0],
        "三": [178, 34, 34]
    }

    for d, c in colors.items():
        if degree == d:
            return c

    # 默认返回正常颜色 绿色
    return [118, 238, 198]


def color_df(data: DataFrame, rgb: list) -> DataFrame:
    """
    修改点云颜色
        正常：绿色[118, 238, 198]
        一级预警：黄色[238, 180, 34]
        二级预警：橙色[238, 64, 0]
        三级预警：红色[178, 34, 34]
    :param data:
    :param rgb:
    :return:
    """
    r, g, b = rgb
    data['R'], data['G'], data['B'] = r, g, b
    return data


def write_df(path, init_path, data, init):
    """
    将点云区域字典数据写入目标路径
    :param path:
    :param init_path:
    :param data:
    :param init: 是否是在初始化，若是初始化直接修改颜色为绿色，若不是需要进行判断
    :return:
    """
    try:
        os.makedirs(path, exist_ok=True)
        if init:  # 初始化阶段
            for k in data.keys():
                df = data.get(k)
                if df is not None:
                    df = color_df(df, [118, 238, 198])
                    df.to_csv(os.path.join(path, f"{k}.csv"), index=False)
            return True
        else:  # 非初始化阶段
            if data is not None:  # 如果有异常数据则将有异常的区域数据写入文件
                regions = data.get_region()
                describes = data.get_describe()
                for k in regions.keys():
                    df = regions.get(k)
                    if df is not None:
                        rgb = set_color_by_degree(describes.get(k)[2])
                        df = color_df(df, rgb)
                        df.to_csv(os.path.join(path, f"{k}.csv"), index=False)
            return True
    except Exception as e:
        print(f"An error occurred: {e} in write_df")
        return False


def write_single_df(path: str, init_path: str, init: bool, tunnel: Tunnel):
    """
    写入一个划分区域的点云数据/部分数据（异常数据）
    :param path:
    :param init_path:
    :param init:
    :param tunnel:
    :return:
    """
    """
        1.构建目录
        2.写入数据
            检查目录中文件数量
                若为0则创建root目录，写入完整点云数据
                如不为0,则获取文件数量，用文件数量命名文件夹/用秒数PointCloudData对象中的time属性命名目录
    """
    try:
        data = tunnel.get_data()
        # time = datetime.strptime(now, '%Y-%m-%d %H:%M:%S.%f')
        time = data.get_time()
        # 构建保存路径
        save_path = os.path.join(path, str(time.year), str(time.month), str(time.day), str(time.hour), str(time.minute),
                                 str(time.second))
        os.makedirs(save_path, exist_ok=True)
        # 判断文件中的文件数量
        folder_count = count_directories(save_path, True)
        if folder_count is None:
            return False
        else:
            # 不包含root目录，直接通过时间检索
            # 将pcd文件保存地址写入数据库
            if not DBUtils.pcd_path2db(save_path, time, tunnel):
                return False
            anomaly = data.get_anomaly()
            return write_df(save_path, init_path, anomaly, init)
            # 包含root目录
            # filename = 'root' if folder_count == 0 else str(folder_count)
            # final_path = os.path.join(save_path, filename)
            # anomaly = data.get_anomaly()
            # return write_df(final_path, init_path, anomaly, init)
    except Exception as e:
        print(f"An error occurred: {e} in write_single_df")
        return False


def write_single_normal_log(path, time: datetime, file_name):
    """
    写入正常日志信息至本地文件
    :param path:
    :param time:
    :param file_name:
    :return:
    """
    try:
        config = configparser.ConfigParser()
        if not config.has_section('Time'):
            config.add_section('Time')
        config.set('Time', 'time', time.strftime('%Y-%m-%d %H:%M:%S.%f'))
        # config['Time'] = {'time': time.strftime('%Y-%m-%d %H:%M:%S.%f')}
        with open(os.path.join(path, f"{str(file_name)}.ini"), 'w') as configfile:
            config.write(configfile)
        return True
    except Exception as e:
        print(f"An error occurred: {e} in write_single_normal_log")
        return False


def write_single_anomaly_log(path, time: datetime, file_name, anomaly_data):
    """
    写入异常日志信息至本地文件
    :param path:
    :param time:
    :param file_name:
    :param anomaly_data:
    :return:
    """
    try:
        # self.describe[region_index] = [position, bas, degree]
        anomaly_describe = anomaly_data.get_describe()
        k = list(anomaly_describe.keys())
        position, bas, degree = [], [], []
        for e in k:
            position.append(anomaly_describe.get(e)[0])
            bas.append(anomaly_describe.get(e)[1])
            degree.append(anomaly_describe.get(e)[2])

        config = configparser.ConfigParser()
        if not config.has_section('Time'):
            config.add_section('Time')
        config.set('Time', 'time', time.strftime('%Y-%m-%d %H:%M:%S.%f'))

        if not config.has_section('Anomalies'):
            config.add_section('Anomalies')
        anomalies_data = {
            'region index': str(k),
            'position': str(position),
            'bas': str(bas),
            'degree': str(degree)
        }
        for k, v in anomalies_data.items():
            config.set('Anomalies', k, v)

        # 确保目录存在
        os.makedirs(path, exist_ok=True)

        with open(os.path.join(path, f"{file_name}.ini"), 'w') as configfile:
            config.write(configfile)
        return True
    except Exception as e:
        print(f"An error occurred: {e} in write_single_anomaly_log")
        return False


def write_single_log(now: str, path: str, data: PointCloudData):
    """
    写入日志信息
    :param now:
    :param path:
    :param data:
    :return:
    """
    """
        1.构建目录
        2.记录日志
            检查目录中文件数量,根据文件数量命名日志
            如有异常记录异常信息
            如没有异常记录时间信息
    """
    try:
        # 获取异常数据
        anomaly = data.get_anomaly()
        # 构建保存路径
        time = datetime.strptime(now, '%Y-%m-%d %H:%M:%S.%f')
        save_path = os.path.join(path, str(time.year), str(time.month), str(time.day), str(time.hour),
                                 str(time.minute), str(time.second))
        os.makedirs(save_path, exist_ok=True)
        # 写入日志
        folder_count = count_directories(save_path, False)
        if folder_count is None:
            return False
        else:  # 记录日志
            if not anomaly or len(anomaly.get_describe()) == 0:
                return write_single_normal_log(save_path, data.get_time(), str(folder_count))
            else:
                return write_single_anomaly_log(save_path, time, str(folder_count), anomaly)
    except Exception as e:
        print(f"An error occurred: {e} in write_single_log")
        return False


def write_single_anomaly_log_db():
    pass


def write_single_normal_log_db():
    pass


def write_single_log_db(tunnel: Tunnel):
    return DBUtils.log_insert(tunnel)


def write_df2pcd(now: str, path: str, datas) -> None:
    """
    http://127.0.0.1/outer/service/receive
    将原始数据写入.pcd文件，方便后续接口调用
    :param now: 数据采集时间
    :param path: 保存路径
    :param datas: 原始DataFrame格式的3D点云数据
    :return: None
    """
    time = datetime.strptime(now, '%Y-%m-%d %H:%M:%S.%f')
    # 构建文件子目录名称
    # name = fr"{now.year}\{now.month}\{now.day}\{now.hour}\{now.minute}"
    # name = fr"{now.month}\{now.day}\{now.hour}\{now.minute}"

    # 构建保存路径
    save_path = os.path.join(path, str(time.year), str(time.month), str(time.day), str(time.hour),
                             str(time.minute), str(time.second))
    # 写入文件
    for i, data in enumerate(datas):
        root = str(i)
        if i == 0:  # 这次数据的第一个数据保存目录文件夹命名为root
            root = 'root'
        final_path = os.path.join(save_path, root)

        if not os.path.exists(final_path):  # 如果文件夹不存在则创建文件夹
            os.makedirs(final_path)

        for k in data.keys():
            if data.get(k) is not None:
                df = pd.DataFrame.from_dict(data.get(k))
                df.to_csv(os.path.join(final_path, f"{k}.csv"), index=False)
                # points = config[['X', 'Y', 'Z']].values
                # pcd = o3d.geometry.PointCloud()
                # pcd.points = o3d.utility.Vector3dVector(points)
                # o3d.io.write_point_cloud(os.path.join(save_path, f"{now.second}-{i}.pcd"), pcd)


def find_max_log(path):
    filename_list = []
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.endswith('.ini'):
                config = configparser.ConfigParser()
                config.read(entry.path)
                if config.has_section("Anomalies"):
                    filename_list.append(entry.name)
    if not filename_list:
        return None
    return os.path.join(path, max(filename_list))


def content(path: str) -> dict:
    """
    http://127.0.0.1/outer/service/tree
    :param path:
    :return:
    """
    # 若目录不存在
    if not os.path.exists(path):
        return {'msg': '目录不存在'}

    res_list = []
    # 找到每一个包含ini文件的目录
    log_path_list = find_log_path(path)
    if not log_path_list:
        return {'msg': '信息不存在'}

    # 获取每个目录中的最新的ini文件中的time属性
    config = configparser.ConfigParser()
    for log_path in log_path_list:
        max_log_path = find_max_log(log_path)
        if max_log_path is None:
            continue
        config.read(str(max_log_path))
        now = datetime.strptime(config['Time']['time'], '%Y-%m-%d %H:%M:%S.%f')
        res_list.append(f"{now.hour:02d}:{now.minute:02d}:{now.second:02d}")

    if not res_list:
        return {'msg': '不存在异常日志信息'}
    return {'config': res_list}


def find_max_folder(directory):
    """
    http://127.0.0.1:8024/outer/service/history
    :param directory:
    :return:
    """
    if directory is None:
        return None

    try:
        filename_list = []
        with os.scandir(directory) as entries:
            for entry in entries:
                if count_directories(directory, True) == 1 and entry.name == 'root':
                    return entry.path
                elif entry.is_dir() and entry.name != 'root' and len(os.listdir(entry.path)) != 0:
                    filename_list.append(entry.name)
        if not filename_list:  # 如果文件列表为空
            return None
        return os.path.join(directory, max(filename_list))
    except Exception as e:
        print(f"{str(e)} in outer/util/find_max_folder")
        return None


@deprecated(reason="Use find_max_folder(directory)")
def get_latest_folder(directory):
    """
    http://127.0.0.1:8024/outer/service/history
    :param directory:
    :return:
    """
    latest_folder = None
    latest_time = 0

    for root, dirs, _ in os.walk(directory):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            dir_time = os.path.getmtime(dir_path)
            if dir_time > latest_time:
                latest_time = dir_time
                latest_folder = dir_path

    return latest_folder


def get_latest_csv(path):
    """
    http://127.0.0.1:8024/outer/service/history
    :param path:
    :return:
    """
    if not os.path.exists(path):
        return {'msg': '目录不存在'}
    """
    获取目录及其子目录中最新的 .pcd 文件名。
    """
    latest_file = None
    latest_mtime = -1

    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith('.pcd'):
                file_path = os.path.join(root, file)
                file_mtime = os.path.getmtime(file_path)
                if file_mtime > latest_mtime:
                    latest_mtime = file_mtime
                    latest_file = file_path

    if latest_file is None:
        return {'msg': '不存在雷达扫描数据'}
    return {'msg': latest_file}


def find_latest_ini_folder(directory):
    """
    http://127.0.0.1:8024/outer/service/history
    :param directory:
    :return:
    """
    # 获取所有子文件夹路径
    folders = find_log_path(directory)

    # 初始化用于存储最新文件夹路径的变量
    latest_folder = None
    latest_time = None

    # 遍历所有子文件夹
    for folder in folders:
        # 获取文件夹的修改时间
        folder_time = os.path.getmtime(folder)
        # 更新最新文件夹
        if latest_time is None or folder_time > latest_time:
            latest_folder = folder
            latest_time = folder_time

    return latest_folder


def find_latest_root_folder(directory):
    """
    http://127.0.0.1:8024/outer/service/history
    :param directory:
    :return:
    """
    latest_folder = None
    # latest_root_folder = None
    latest_time = 0

    for root, dirs, _ in os.walk(directory):
        if 'root' in dirs:
            root_path = os.path.join(root, 'root')
            folder = root
            root_time = os.path.getmtime(root_path)
            if root_time > latest_time:
                latest_time = root_time
                latest_folder = folder
                # latest_root_folder = root_path

    # return latest_folder, latest_root_folder
    return latest_folder


def find_latest_folder(directory):
    """
    http://127.0.0.1:8024/outer/service/log_data_visual
    :param directory:
    :return:
    """
    latest_folder = None
    latest_time = None

    for root, dirs, _ in os.walk(directory):
        if 'root' in dirs:
            for d in dirs:
                file_path = os.path.join(root, d)
                file_time = os.path.getmtime(file_path)
                if latest_time is None or file_time > latest_time:
                    latest_folder = file_path
                    latest_time = file_time
            break
    return latest_folder


def find_root_folder(directory):
    """
    http://127.0.0.1:8024/outer/service/history
    :param directory:
    :return:
    """
    for root, dirs, _ in os.walk(directory):
        if 'root' in dirs:
            return os.path.join(root, 'root')
    return None


def get_root_data(directory):
    """
    http://127.0.0.1:8024/outer/service/history
    :param directory:
    :return:
    """
    datas = {}
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.endswith('.csv'):
                datas[entry.name] = pd.read_csv(entry.path)
    return datas


def get_root_filename(directory):
    """
    http://127.0.0.1:8024/outer/service/history
    :param directory:
    :return:
    """
    paths = {}
    with os.scandir(directory) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.endswith('.csv'):
                paths[entry.name] = entry.path
    return paths


def merge_data(datas, target=None, is_df=False):
    """
    paths为初始化目录中的数据，如果directory为None会直接返回初始化数据
    directory为None的情况：
        1. 目标目录不存在
        2. 非初始化阶段只记录异常数据，为None也可能时不存在异常数据
    http://127.0.0.1:8024/outer/service/history
    :param datas:
    :param target:
    :param is_df:
    :return:
    """
    # df_list = []
    if not is_df:
        if target is not None:
            with os.scandir(target) as entries:
                for entry in entries:
                    if entry.is_file() and entry.name.endswith('.csv'):
                        datas[entry.name] = entry.path
            # for e in list(datas.values()):
            #     df_list.append(pd.read_csv(e, usecols=['X', 'Y', 'Z', 'R', 'G', 'B']))
    else:
        for k, v in target.items():
            datas[k] = v
        # df_list = [e for e in list(datas.values())]

    # res_df = pd.concat(df_list, ignore_index=True)
    # pcd = o3d.geometry.PointCloud()
    # pcd.points = o3d.utility.Vector3dVector(res_df[['X', 'Y', 'Z']].values)
    # pcd.colors = o3d.utility.Vector3dVector(res_df[['R', 'G', 'B']].values / 255.0)
    # o3d.visualization.draw_geometries([pcd])

    coordinate_list, color_list = [], []
    for data in datas.values():
        # 读取 CSV 文件时只加载需要的列
        if not is_df:
            data = pd.read_csv(data, usecols=['X', 'Y', 'Z', 'R', 'G', 'B'])
        # 检查是否有颜色列
        has_color = all(col in data.columns for col in ['R', 'G', 'B'])
        for line in data.itertuples(index=False):
            coordinate_list.extend([line.X, line.Y, line.Z])
            if has_color:
                color_list.extend([line.R, line.G, line.B])
            else:
                color_list.extend([0, 0, 0])
    return coordinate_list, color_list


def get_history(init_path, path=None):
    """
    http://127.0.0.1/outer/service/history
    :param path:
    :param init_path:
    :return:
    """
    # 获取包含root文件夹的最新目录的路径
    # root_folder = find_latest_root_folder(path)
    # latest_path = find_max_folder(root_folder)
    root_filepath = get_root_filename(init_path)
    # coordinate_list, color_list = merge_data(root_filepath, latest_path)
    coordinate_list, color_list = merge_data(root_filepath, path)
    return {'xyz': str(coordinate_list), 'rgb': str(color_list)}


def get_path_by_time(data: dict):
    res = DBUtils.get_path_in_db(data)
    if res is not None:
        return res


def get_path(data: dict, path, cls: str, tag):
    """
    http://127.0.0.1/outer/service/tree
    http://127.0.0.1/outer/service/history
    http://127.0.0.1/outer/service/log
    http://127.0.0.1/outer/service/log_data_visual
    http://127.0.0.1/outer/service/compare
    根据body体传入字段组装目录结构
    :param data:
    :param path:
    :param cls:
    :param tag:
    :return:
    """
    # 获取目录结构
    # project_list = [data.get('project_name'), data.get('tunnel_name'), data.get('working_face'), data.get('mileage'),
    #                 data.get('device_id')]
    # for e in project_list:
    #     if e is not None:
    #         path = os.path.join(path, str(e))
    acq_code = data.get('DataAcqEquipCode')
    data_path = os.path.join(path, str(acq_code), 'data', cls)

    date_list = [data.get('Year'), data.get('Month'), data.get('Day'), data.get('Hour'), data.get('Minute'),
                 data.get('Second')]
    for e in date_list:
        if e is not None:
            data_path = os.path.join(data_path, str(e))
    return content(data_path) if tag == 'tree' else path, data_path
    # return content(data_path) if tag == 'tree' else data_path


def get_pcd_list(path):
    """
    获取path地址中的区域点云数据字典
    :param path:
    :return: {区域索引: 区域csv文件地址}
    """
    res = {}
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_file() and entry.name.endswith('.csv'):
                name = entry.name.split('.')[0]
                res[name] = {'path': entry.path, 'bas': '0'}
    return res


def compare_log_information(root_bas: dict, compare_bas: dict, compare: dict):
    compare_bas_res, compare_bas_log = {}, {}
    for k, v in compare_bas.items():
        bas = v
        if k in root_bas.keys():
            temp = abs(float(root_bas[k]) - float(v))
            if temp >= 0.2:
                bas = temp
        compare_bas_res[k] = {'bas': str(bas), 'path': compare[k].get('path')}
        compare_bas_log[k] = str(bas)
    return compare_bas_res, compare_bas_log


def get_xyz_rgb_list(init: dict, compare: dict):
    coordinate_list, color_list = [], []
    # df_list = []
    for k, v in init.items():
        r, g, b = (118, 238, 198)
        data = pd.read_csv(v.get('path'), usecols=['X', 'Y', 'Z', 'R', 'G', 'B'])
        has_color = all(col in data.columns for col in ['R', 'G', 'B'])
        if has_color and k in compare.keys():
            r, g, b = (178, 34, 34)
        else:
            r, g, b = (118, 238, 198) if has_color else (0, 0, 0)

        data['R'], data['G'], data['B'] = r, g, b

        # 提取坐标和颜色
        # coordinates = data[['X', 'Y', 'Z']].to_numpy().flatten()  # 转换为 NumPy 数组并展开
        # colors = data[['R', 'G', 'B']].to_numpy().flatten()  # 转换为 NumPy 数组并展开
        # coordinate_list.extend(coordinates)
        # color_list.extend(colors)
        # df_list.append(data)

        for line in data.itertuples(index=False):
            coordinate_list.extend([line.X, line.Y, line.Z])
            color_list.extend([line.R, line.G, line.B])
        # df_list.append(data)
    return coordinate_list, color_list


def data_is_overdue(data: dict):
    year = data.get('Year')
    month = data.get('Month')
    day = data.get('Day')
    hour = data.get('Hour')
    minute = data.get('Minute')
    second = data.get('Second')
    columns_time = datetime(year, month, day, hour, minute, second)
    # 拿到当前的时间
    current_time = datetime.now()
    # 计算三天的时间范围
    three_days_ago = current_time - timedelta(days=3)
    # 判断字段中的时间是否在范围内
    if three_days_ago <= columns_time <= current_time:
        return True
    return False


if __name__ == '__main__':
    # start = time.time()
    # get_history(r"E:\07-code\remote_study\tunnelProject\outer\config\history\2024\8\8\17",
    #             r"E:\07-code\remote_study\tunnelProject\outer\config\init\regions")
    # print(f"获取历史数据耗时：{time.time() - start}")
    # find_log(r'E:\07-code\tunnelProject\outer\config\log')
    # print(get_log_data_tag(r'E:\07-code\tunnelProject\outer\config\log\2024\7\29\18\12\20\0.ini'))
    # data_visual(r'E:\07-code\tunnelProject\outer\config\history\2024\7\30\14')
    # print(content("config/log/2024/8/1"))
    # print(find_max_log(r'E:\07-code\remote_study\tunnelProject\outer\config\log\2024\8\1\12\14\20'))
    config = {
        'project_name': 'test_project_name',
        'tunnel_name': 'test_tunnel_name',
        'working_face': 'test_working_face',
        'mileage': 'test_mileage',
        'device_id': 'test_device_id',
        'year': 2024,
        'month': 8,
        'day': 29
    }
    print(get_path(config, "../data", "log", 'tree'))

    # start = time.time()
    # print(show_log(
    #     r"E:\07-code\tunnelProject\outer\data\test_project_name\test_tunnel_name\test_working_face\test_mileage\test_device_id\data\log\2024\8\29"))
    # print(f"show_log:{time.time() - start}")

    # print(data_visual(r"E:\07-code\tunnelProjectTemp\outer\config\history\2024\8\7\16",
    #                   r"E:\07-code\tunnelProjectTemp\outer\config\init\regions"))
    # start = time.time()
    # print(find_max_folder(r"E:\07-code\tunnelProjectTemp\outer\config\history\2024\8\7\16\3\12"))
    # print(f"find_max_folder:{time.time() - start}")
    # start = time.time()
    # print(get_latest_folder(r"E:\07-code\tunnelProjectTemp\outer\config\history\2024\8\7\16\3\12"))
    # print(f"get_latest_folder:{time.time() - start}")
    # get_history(r"E:\07-code\tunnelProjectTemp\outer\config\history\2024\8\7\16\3\12",
    #             r"E:\07-code\tunnelProjectTemp\outer\config\init\regions")
    # print(get_region_dict("config/history/2024/8/15"))
    # print(find_latest_ini_folder(r"E:\07-code\remote_study\tunnelProject\outer\config\log\2024\8\16"))
    # print(get_log_bas_dict(r"E:\07-code\remote_study\tunnelProject\outer\config\log\2024\8\16"))

    # start = time.time()
    # compare_data("config/init/regions", "config/history/2024\8/16\9", "config/history/2024\8/16/10",
    #              "config/log/2024\8/16\9", "config/log/2024\8/16/10")
    # print(f"compare_data:{time.time() - start}")
    # if not os.path.exists(r'E:\07-code\tunnelProject\outer\data\test_project_name\test_tunnel_name\test_working_face\test_mileage\test_device_id\data\log\2024\8\29'):
    #     print("no found this path")
    pass
