"""
@Author: zhang_zhiyi
@Date: 2024/10/12_11:26
@FileName:local_db_table.py
@LastEditors: zhang_zhiyi
@version: 1.0
@lastEditTime: 
@Description:
"""


class CompanyTable(object):
    """
    company table
    """

    def __init__(self):
        self.ID = 'ID'
        self.Code = 'Code'
        self.Name = 'Name'
        self.Address = 'Address'
        self.BuyTime = 'BuyTime'

    def columns_dict(self):
        return [self.ID, self.Code, self.Name, self.Address, self.BuyTime]


class UserTable(object):
    """
    user table
    """

    def __init__(self):
        self.ID = 'ID'
        self.RealName = 'RealName'
        self.RoleClass = 'RoleClass'
        self.UserCode = 'UserCode'
        self.Phone = 'Phone'
        self.ProCode = 'ProCode'
        self.Status = 'Status'
        self.CompanyCode = 'CompanyCode'
        self.AuthCode = 'AuthCode',
        self.AuthCodeCreateTime = 'AuthCodeCreateTime'
        self.AuthCodeLimit = 'AuthCodeLimit'
        self.MiniProOpenID = 'MiniProOpenID'
        self.OffAccOpenID = 'OffAccOpenID'
        self.UnionID = 'UnionID'

    def columns_dict(self):
        return [self.ID, self.RealName, self.RoleClass, self.UserCode, self.Phone,
                self.ProCode, self.Status, self.CompanyCode, self.AuthCode,
                self.AuthCodeCreateTime, self.AuthCodeLimit, self.MiniProOpenID,
                self.OffAccOpenID, self.UnionID]


class ProjectTable(object):
    """
    project table
    """

    def __init__(self):
        self.ID = 'ID'
        self.ProCode = 'ProCode'
        self.ProName = 'ProName'
        self.ProAddress = 'ProAddress'
        self.LinkMan = 'LinkMan'
        self.Phone = 'Phone'
        self.ProCreateTime = 'ProCreateTime'
        self.ProStatus = 'ProStatus'
        self.ProCycle = 'ProCycle'
        self.CompanyCode = 'CompanyCode'

    def columns_dict(self):
        return [self.ID, self.ProCode, self.ProName, self.ProAddress, self.LinkMan, self.Phone,
                self.ProCreateTime, self.ProStatus, self.ProCycle, self.CompanyCode]


class TunnelTable(object):
    """
    tunnel table
    """

    def __init__(self):
        self.ID = "ID"
        self.TunCode = "TunCode"
        self.TunName = "TunName"
        self.LinkMan = "LinkMan"
        self.Phone = "Phone"
        self.High = "High"
        self.TunStatus = "TunStatus"
        self.ProCode = "ProCode"
        self.TunCycle = "TunCycle"
        self.TunCreateTime = "TunCreateTime"

    def columns_dict(self):
        return [self.ID, self.TunCode, self.TunName, self.LinkMan, self.Phone, self.High, self.TunStatus,
                self.ProCode, self.TunCycle, self.TunCreateTime]
        # return {
        #     "TunID": self.TunID,
        #     "TunCode": self.TunCode,
        #     "TunName": self.TunName,
        #     "LinkMan": self.LinkMan,
        #     "Phone": self.Phone,
        #     "High": self.High,
        #     "TunStatus": self.TunStatus,
        #     "ProCode": self.ProCode
        # }


class WorkSurfaceTable(object):
    """
    work_surface table
    """

    def __init__(self):
        self.ID = "ID"
        self.WorkSurCode = "WorkSurCode"
        self.WorkSurName = "WorkSurName"
        self.ProCode = "ProCode"
        self.TunCode = "TunCode"
        self.StruCode = "StruCode"

    def columns_dict(self):
        return [self.ID, self.WorkSurCode, self.WorkSurName, self.ProCode, self.TunCode, self.StruCode]
        # return {
        #     "WorkSurID": self.WorkSurID,
        #     "WorkSurCode": self.WorkSurCode,
        #     "WorkSurName": self.WorkSurName,
        #     "ProCode": self.ProCode,
        #     "TunCode": self.TunCode
        # }


class StructureTable(object):
    """
    structure table
    """

    def __init__(self):
        self.ID = "ID"
        self.StruCode = "StruCode"
        self.StruName = "StruName"
        self.FirWarningLevel = "FirWarningLevel"
        self.SecWarningLevel = "SecWarningLevel"
        self.ThirWarningLevel = "ThirWarningLevel"
        # self.ProCode = "ProCode"
        # self.TunCode = "TunCode"
        # self.WorkSurCode = "WorkSurCode"

    def columns_dict(self):
        return [self.ID, self.StruCode, self.StruName, self.FirWarningLevel, self.SecWarningLevel,
                self.ThirWarningLevel]
        # return {
        #     "StruID": self.StruID,
        #     "StruCode": self.StruCode,
        #     "StruName": self.StruName,
        #     "FirWarningLevel": self.FirWarningLevel,
        #     "SecWarningLevel": self.SecWarningLevel,
        #     "ThirWarningLevel": self.ThirWarningLevel,
        #     "ProCode": self.ProCode,
        #     "TunCode": self.TunCode,
        #     "WorkSurCode": self.WorkSurCode
        # }


class AnomalyLogTable(object):
    """
    anomaly_log table
    """

    def __init__(self):
        self.ID = "ID"
        self.Identification = "Identification"
        self.ProCode = "ProCode"
        self.TunCode = "TunCode"
        self.WorkSurCode = "WorkSurCode"
        self.StruCode = "StruCode"
        self.Mileage = "Mileage"
        self.ConEquipCode = "ConEquipCode"
        self.DataAcqEquipCode = "DataAcqEquipCode"
        self.AnomalyTime = "AnomalyTime"
        self.Year = "Year"
        self.Month = "Month"
        self.Day = "Day"
        self.Hour = "Hour"
        self.Minute = "Minute"
        self.Second = "Second"
        self.Sign = "Sign"
        self.MaxDegree = "MaxDegree"

    def columns_dict(self):
        return [self.ID, self.Identification, self.ProCode, self.TunCode, self.WorkSurCode, self.StruCode,
                self.Mileage, self.ConEquipCode, self.DataAcqEquipCode, self.AnomalyTime, self.Year,
                self.Month, self.Day, self.Hour, self.Minute, self.Second, self.Sign, self.MaxDegree]


class AnomalyLodDescTable(object):
    """
    anomaly_lod_desc table
    """

    def __init__(self):
        self.ID = "ID"
        self.Identification = "Identification"
        self.Degree = "Degree"
        self.Region = "Region"
        self.Position = "Position"
        self.Bas = "Bas"

    def columns_dict(self):
        return [self.ID, self.Identification, self.Degree, self.Region, self.Position, self.Bas]


class AnomalyLodImgTable(object):
    """
    anomaly_lod_img table
    """

    def __init__(self):
        self.ID = "ID"
        self.Identification = "Identification"
        self.AviaPicturePath = "AviaPicturePath"
        self.CameraPicturePath = "CameraPicturePath"

    def columns_dict(self):
        return [self.ID, self.Identification, self.AviaPicturePath, self.CameraPicturePath]


class EqControlTable(object):
    """
    eq_control table
    """

    def __init__(self):
        self.ID = "ID"
        self.ConEquipCode = "ConEquipCode"
        self.ConEquipName = "ConEquipName"
        self.ConEquipIP = "ConEquipIP"
        self.ProCode = "ProCode"
        self.TunCode = "TunCode"
        self.WorkSurCode = "WorkSurCode"
        self.StruCode = "StruCode"
        self.Init = "Init"

    def columns_dict(self):
        return [self.ID, self.ConEquipCode, self.ConEquipName, self.ConEquipIP, self.ProCode, self.TunCode,
                self.WorkSurCode, self.StruCode, self.Init]


class EqDataTable(object):
    """
    eq_data table
    """

    def __init__(self):
        self.ID = "ID"
        self.DataAcqEquipCode = "DataAcqEquipCode"
        self.DataAcqEquipName = "DataAcqEquipName"
        self.DataAcqEquipIP = "DataAcqEquipIP"
        self.DataAcqEquipInterval = "DataAcqEquipInterval"
        self.Distance = "Distance"
        self.DataAcaEquipStatus = "DataAcaEquipStatus"
        self.ConEquipCode = "ConEquipCode"
        self.Init = "Init"

    def columns_dict(self):
        return [self.ID, self.DataAcqEquipCode, self.DataAcqEquipName, self.DataAcqEquipIP,
                self.DataAcqEquipInterval, self.Distance, self.DataAcaEquipStatus, self.ConEquipCode, self.Init]


class PcdLogTable(object):
    """
    pcd_log table
    """

    def __init__(self):
        self.ID = "ID"
        self.ProCode = "ProCode"
        self.TunCode = "TunCode"
        self.WorkSurCode = "WorkSurCode"
        self.StruCode = "StruCode"
        self.Mileage = "Mileage"
        self.ConEquipCode = "ConEquipCode"
        self.DataAcqEquipCode = "DataAcqEquipCode"
        self.PcdLogTime = "AnomalyTime"
        self.Year = "Year"
        self.Month = "Month"
        self.Day = "Day"
        self.Hour = "Hour"
        self.Minute = "Minute"
        self.Second = "Second"

    def columns_dict(self):
        return [self.ID, self.ProCode, self.TunCode, self.WorkSurCode, self.StruCode, self.Mileage, self.ConEquipCode,
                self.DataAcqEquipCode, self.PcdLogTime, self.Year, self.Month, self.Day, self.Hour, self.Minute,
                self.Second]


class RoleTable(object):
    """
    role table
    """

    def __init__(self):
        self.ID = 'ID'
        self.RoleClass = 'RoleClass'
        self.Creator = 'Creator'
        self.CreateTime = 'CreateTime'
        self.Status = 'Status'
        self.UserCode = 'UserCode'

    def columns_dict(self):
        return [self.ID, self.RoleClass, self.Creator, self.CreateTime, self.Status, self.UserCode]


class EqControlConfTable(object):
    """
    eq_control_conf table
    """

    def __init__(self):
        self.ID = "ID"
        self.ConfCode = "ConfCode"
        self.ConEquipCode = "ConEquipCode"
        self.ConsumerRMQUsername = "ConsumerRMQUsername"
        self.ConsumerRMQPassword = "ConsumerRMQPassword"
        self.ConsumerRMQHost = "ConsumerRMQHost"
        self.ConsumerRMQPort = "ConsumerRMQPort"
        self.ConsumerRMQVirtualHost = "ConsumerRMQVirtualHost"
        self.ConsumerRMQQueueName = "ConsumerRMQQueueName"
        self.ConsumerRMQBingingKey = "ConsumerRMQBingingKey"
        self.ConsumerRMQExchangeName = "ConsumerRMQExchangeName"
        self.ConsumerRMQExchangeType = "ConsumerRMQExchangeType"
        self.ConsumerRMQFailedQueueName = "ConsumerRMQFailedQueueName"
        self.FailedExchangeErrorQueue = "FailedExchangeErrorQueue"
        self.FailedExchangeName = "FailedExchangeName"
        self.FailedExchangeType = "FailedExchangeType"
        self.AdvanceAdvance = "AdvanceAdvance"
        self.AdvancePrefetchCount = "AdvancePrefetchCount"
        self.ConnTimerConnInterval = "ConnTimerConnInterval"
        self.ProducerRMQUsername = "ProducerRMQUsername"
        self.ProducerRMQPassword = "ProducerRMQPassword"
        self.ProducerRMQHost = "ProducerRMQHost"
        self.ProducerRMQPort = "ProducerRMQPort"
        self.ProducerRMQVirtualHost = "ProducerRMQVirtualHost"
        self.ProducerRMQExchangeName = "ProducerRMQExchangeName"
        self.ProducerRMQExchangeType = "ProducerRMQExchangeType"
        self.ProducerRMQBingingKey = "ProducerRMQBingingKey"
        self.ProducerConnTimerConnInterval = "ProducerConnTimerConnInterval"
        self.WebRMQUsername = "WebRMQUsername"
        self.WebRMQPassword = "WebRMQPassword"
        self.WebRMQHost = "WebRMQHost"
        self.WebRMQPort = "WebRMQPort"
        self.WebRMQVirtualHost = "WebRMQVirtualHost"
        self.WebRMQExchangeName = "WebRMQExchangeName"
        self.WebRMQExchangeType = "WebRMQExchangeType"
        self.WebRMQBingingKey = "WebRMQBingingKey"
        self.WebRMQQueueName = "WebRMQQueueName"
        self.ConsumerRMQFailedBingingKey = "ConsumerRMQFailedBingingKey"
        self.ProducerRMQQueueName = "ProducerRMQQueueName"
        self.MonitorQueueName = "MonitorQueueName"

    def columns_dict(self):
        return [self.ID, self.ConfCode, self.ConEquipCode, self.ConsumerRMQUsername, self.ConsumerRMQPassword,
                self.ConsumerRMQHost, self.ConsumerRMQPort, self.ConsumerRMQVirtualHost, self.ConsumerRMQQueueName,
                self.ConsumerRMQBingingKey, self.ConsumerRMQExchangeName, self.ConsumerRMQExchangeType,
                self.ConsumerRMQFailedQueueName, self.FailedExchangeErrorQueue, self.FailedExchangeName,
                self.FailedExchangeType, self.AdvanceAdvance, self.AdvancePrefetchCount, self.ConnTimerConnInterval,
                self.ProducerRMQUsername, self.ProducerRMQPassword, self.ProducerRMQHost, self.ProducerRMQPort,
                self.ProducerRMQVirtualHost, self.ProducerRMQExchangeName, self.ProducerRMQExchangeType,
                self.ProducerRMQBingingKey, self.ProducerConnTimerConnInterval, self.WebRMQUsername,
                self.WebRMQPassword, self.WebRMQHost, self.WebRMQPort, self.WebRMQVirtualHost, self.WebRMQExchangeName,
                self.WebRMQExchangeType, self.WebRMQBingingKey, self.WebRMQQueueName, self.ProducerRMQQueueName,
                self.MonitorQueueName]


class EqDataConfTable(object):
    """
    eq_data_conf table
    """

    def __init__(self):
        self.ID = "ID"
        self.ConfCode = "ConfCode"
        self.DataAcqEquipCode = "DataAcqEquipCode"
        self.LidarParameterSTW = "LidarParameterSTW"
        self.LidarParameterDur = "LidarParameterDur"
        self.LidarParameterCollInter = "LidarParameterCollInter"
        self.LidarParameterConnInter = "LidarParameterConnInter"
        self.RabbitmqParameterUsername = "RabbitmqParameterUsername"
        self.RabbitmqParameterPassword = "RabbitmqParameterPassword"
        self.RabbitmqParameterHost = "RabbitmqParameterHost"
        self.RabbitmqParameterPort = "RabbitmqParameterPort"
        self.RabbitmqParameterVirtualHost = "RabbitmqParameterVirtualHost"
        self.RabbitmqParameterExchange = "RabbitmqParameterExchange"
        self.RabbitmqParameterExchangeType = "RabbitmqParameterExchangeType"
        self.RabbitmqParameterConnInterval = "RabbitmqParameterConnInterval"
        self.RabbitmqParameterRoutingKey = "RabbitmqParameterRoutingKey"
        self.RabbitmqParameterQueueName = "RabbitmqParameterQueueName"
        self.computerIP = "computerIP"
        self.sensorIP = "sensorIP"

    def columns_dict(self):
        return [self.ID, self.ConfCode, self.DataAcqEquipCode, self.LidarParameterSTW, self.LidarParameterDur,
                self.LidarParameterCollInter, self.LidarParameterConnInter, self.RabbitmqParameterUsername,
                self.RabbitmqParameterPassword, self.RabbitmqParameterHost, self.RabbitmqParameterPort,
                self.RabbitmqParameterVirtualHost, self.RabbitmqParameterExchange, self.RabbitmqParameterExchangeType,
                self.RabbitmqParameterConnInterval, self.RabbitmqParameterRoutingKey, self.RabbitmqParameterQueueName,
                self.computerIP, self.sensorIP]
