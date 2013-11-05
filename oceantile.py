#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import math
import netCDF4
import datetime

class Point(object):
    '''点类'''
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __str__(self):
        return '%f, %f' % (self.x, self.y)

class LatLon(object):
    '''经纬度坐标点类'''
    DEG_TO_RAD = math.pi / 180
    RAD_TO_DEG = 180 / math.pi
    MAX_MARGIN = 1.0E-9
    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon
    def equals(self, obj):
        margin = math.max(math.abs(self.lat - obj.lat),math.abs(self.lon - obj.lon))
        return margin <= self.MAX_MARGIN
    def __str__(self):
        return '%f, %f' % (self.lat, self.lon)

class IProjection(object):
    '''投影接口'''
    @classmethod
    def project(cls, latlon):
        pass
    @classmethod
    def unproject(cls, point):
        pass

class WebMercatorProjection(IProjection):
    '''Web墨卡托投影'''
    MAX_LATITUDE = 85.0511287798
    @classmethod
    def project(cls, latlon):
        d = LatLon.DEG_TO_RAD
        maxlat = cls.MAX_LATITUDE
        lat = max(min(maxlat, latlon.lat), -maxlat)
        x = latlon.lon * d
        y = lat * d
        y = math.log(math.tan((math.pi / 4) + (y / 2)))
        return Point(x, y)
    @classmethod
    def unproject(cls, point):
        d = LatLon.RAD_TO_DEG
        lon = point.x * d
        lat = (2 * math.atan(math.exp(point.y)) - (math.pi / 2)) * d
        return LatLon(lat, lon);

class LatLonProjection(IProjection):
    '''经纬度投影(本质是非投影坐标参考,在可视化时强制二维化)'''
    @classmethod
    def project(cls, latlon):
        return Point(latlon.lon, latlon.lat)
    @classmethod
    def unproject(cls, point):
        return LatLon(point.y, point.x)

class MercatorProjction(IProjection):
    '''横轴墨卡托投影'''
    pass

class TileCoord(object):
    '''瓦片坐标类'''
    def __init__(self, z, y, x, n=8):
        self.z = z
        self.y = y
        self.x = x
        self.n = n #切分子格网个数

    def __cmp__(self, other):
        return cmp(self.n, other.n) or cmp(self.z, other.z) or cmp(self.x, other.x) or cmp(self.y, other.y)

    def __repr__(self):  # pragma: no cover
        if self.n == 1:
            return '%s(%r, %r, %r)' % (self.__class__.__name__,
                                       self.z, self.x, self.y)
        else:
            return '%s(%r, %r, %r, %r)' % (self.__class__.__name__,
                                           self.z, self.x, self.y, self.n)

    def __str__(self):
        if self.n == 1:
            return '%d/%d/%d' % (self.z, self.y, self.x)
        else:
            return '%d/%d/%d:+%d/+%d' % (self.z, self.y, self.x, self.n, self.n)

    def tuple(self):
        return (self.z, self.y, self.x, self.n)

    @classmethod
    def from_string(cls, s):
        m = re.match(r'(\d+)/(\d+)/(\d+)(?::\+(\d+)/\+\4)?\Z', s)
        if not m:
            raise ValueError('invalid literal for %s.from_string: %r' % (cls.__name__, s))
        x, y, z, n = m.groups()
        return cls(int(x), int(y), int(z), int(n) if n else 1)

    @classmethod
    def from_tuple(cls, tpl):
        return cls(*tpl)

    #根据投影获取瓦片对应的范围
    def get_bbox(self, projection=LatLonProjection):
        worldextent = WorldExtent(projection)
        resolution = worldextent.resolution / math.pow(2, self.z)
        xmin = resolution * self.x + worldextent.xmin
        ymax = worldextent.ymax - resolution * self.y
        xmax = xmin + resolution
        ymin = ymax - resolution
        return [xmin, ymin, xmax, ymax]

    #根据投影切分瓦片，返回地理坐标迭代器
    def iter_points(self, projection=LatLonProjection):
        worldextent = WorldExtent(projection)
        resolution = worldextent.resolution / math.pow(2, self.z)
        new_res = resolution / self.n
        xmin = resolution * self.x + worldextent.xmin
        ymax = worldextent.ymax - resolution * self.y
        for i in xrange(0, self.n):
            for j in xrange(0, self.n):
                yield projection.unproject(Point(xmin+new_res*j, ymax-new_res*i))

    #返回子块的迭代器
    def iter_coords(self):
        for i in xrange(0, self.n):
            for j in xrange(0, self.n):
                yield (j, i)

class WorldExtent(object):
    '''世界范围与0级切片尺寸'''
    def __init__(self, projection=LatLonProjection):
        if projection == WebMercatorProjection:
            self.xmin = -math.pi
            self.xmax = math.pi
            self.ymin = -math.pi
            self.ymax = math.pi
            self.resolution = 2*math.pi
        elif projection == LatLonProjection:
            self.xmin = -180
            self.xmax = 180
            self.ymin = -90
            self.ymax = 90
            self.resolution = 180
        else:
            pass

class Extent(object):
    '''范围类'''
    def __init__(self, xmin, ymin, xmax, ymax, projection=LatLonProjection):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.projection = projection

    def __str__(self):
        return '%f, %f, %f, %f' % (self.xmin, self.ymin, self.xmax, self.ymin, self.ymax)

    def tuple(self):
        return (self.xmin, self.ymin, self.xmax, self.ymin, self.ymax)

    @classmethod
    def from_string(cls, s):
        m = re.match(r'(\f+), (\f+), (\f+), (\f+)', s)
        if not m:
            raise ValueError('invalid literal for %s.from_string: %r' % (cls.__name__, s))
        xmin, ymin, xmax, ymax = m.groups()
        return cls(float(xmin), float(ymin), float(xmax), float(ymax))

    @classmethod
    def from_tuple(cls, tpl):
        return cls(*tpl)

    #投影变换
    def transform(self, projection):
        if self.projection == projection:
            return self
        else:
            point1 = Point(self.xmin, self.ymin)
            point2 = Point(self.xmax, self.ymax)
            latlon1 = self.projection.unproject(point1)
            latlon2 = self.projection.unproject(point2)
            point1 = projection.project(latlon1)
            point2 = projection.project(latlon2)
            return Extent(point1.x, point1.y, point2.x, point2.y, projection)

    #获取指定投影下的瓦片序列
    def iter_tilecoords(self, level, projection):
        extent = self
        if self.projection != projection:
            extent = self.transform(projection)
        worldextent = WorldExtent(projection)
        nums = pow(2, level)
        col_min = int((extent.xmin - worldextent.xmin)/worldextent.resolution * nums)
        col_max = int((extent.xmax - worldextent.xmin)/worldextent.resolution * nums)
        row_min = int((worldextent.ymax - extent.ymax)/worldextent.resolution * nums)
        row_max = int((worldextent.ymax - extent.ymin)/worldextent.resolution * nums)
        for row in range(row_min, row_max+1):
            for col in range(col_min, col_max + 1):
                yield TileCoord(level, row, col)

    #不改变投影，直接按行列取值
    def iter_grid_points(self, rows, cols):
        res_lat = (self.ymax - self.ymin)/rows
        res_lon = (self.xmax - self.xmin)/cols
        for row in range(rows):
            for col in range(cols):
                yield Point(self.xmin + res_lon*col, self.ymin + res_lat*row)

class FVCOMStore(object):
    no_data = -999.
    variables = ('zeta', 'u', 'v')
    REGIONS = {
                        'BHE' : { 'times':72},
                        'QDH' : {'times':72},
                        'DLH' : {'times':72},
                        'RZG' : {'times':72},
                        'SD' : {'times':72},
                    }
    def get_value(self, latlon, time = 0):
        pass

    def get_value_direct(self, lat_index, lon_index, time = 0):
        pass

    def convert_shapefile(self):
        pass

class GridStore(object):
    '''格网存储类'''
    dim_lon = 'longitude'
    dim_lat = 'latitude'

    def __init__(self, netcdf, region = 'NWP'):
        try:
            self.extent = Extent.from_tuple(self.REGIONS[region]['extent'])
            self.times = self.REGIONS[region]['times']
            self.resolution = self.REGIONS[region]['resolution']
            self.netcdf = netCDF4.Dataset(netcdf, 'r')
            self.cols = len(self.netcdf.dimensions[self.dim_lon])-1
            self.rows = len(self.netcdf.dimensions[self.dim_lat])-1
        except Exception, e:
            print e.__str__()

    # def getraw(self, variable):
    #     value = self.netcdf.variables[variable][time][lat_index][lon_index]

    def get_value(self, latlon, time = 0, variables = None):
        if variables is None:
            variables = self.variables
        # todo 检查variabels是否都在self.netcdf.variables内
        if time < 0 or time > self.times:
            return map((lambda variable: float('nan')), variables)
        #lon_index = int((latlon.lon - self.extent.xmin) / (self.extent.xmax - self.extent.xmin) * self.cols)
        #lat_index = int((latlon.lat - self.extent.ymin) / (self.extent.ymax - self.extent.ymin) * self.rows)
        lon_index = int((latlon.lon - self.extent.xmin) / self.resolution)
        lat_index = int((latlon.lat - self.extent.ymin) / self.resolution)
        if lon_index < 0 or lon_index > self.cols or lat_index < 0 or lat_index > self.rows:
            return map((lambda variable: float('nan')), variables)
        #return map((lambda variable: self.netcdf.variables[variable][time][lat_index][lon_index]), variables)
        values = []
        for variable in variables:
            value = float(self.netcdf.variables[variable][time][lat_index][lon_index])
            if value == self.no_data:
                value = float('nan')
            values.append(value)
        return values

    def get_value_direct(self, lat_index, lon_index, time = 0, variables = None):
        if variables is None:
            variables = self.variables
        # todo 检查variabels是否都在self.netcdf.variables内
        if lon_index < 0 or lon_index > self.cols or lat_index < 0 or lat_index > self.rows or time >= self.times:
            return map((lambda variable: float('nan')), variables)
        #return map((lambda variable: self.netcdf.variables[variable][time][lat_index][lon_index]), variables)
        values = []
        for variable in variables:
            value = float(self.netcdf.variables[variable][time][lat_index][lon_index])
            if value == self.no_data or math.isnan(value):
                value = float('nan')
            values.append(value)
        return values

    def conver_shapefile(self):
        pass

class WRFStore(GridStore):
    no_data = 1e+30
    REGIONS = {
                        'NWP' : {'extent':[103.8, 14.5, 140.4, 48.58], 'times':72, 'resolution':.12},
                        'NCS' : {'extent':[116., 28.5, 129., 42.5], 'times':72, 'resolution':.04},
                        'QD' : {'extent':[119., 35., 121.5, 36.5], 'times':72, 'resolution':.01},
                    }
    #variables = ('u10m', 'v10m', 'slp')
    variables = ('u10m', 'v10m')

class SWANStore(GridStore):
    no_data = -9. #-999.0 -> -9.
    REGIONS = {
                        'NWP' : {'extent':[105., 15., 140., 47.], 'times':72, 'resolution':.1},
                        'NCS' : {'extent':[117., 32., 127., 42.], 'times':72, 'resolution':1/30.},
                        'QD' : {'extent':[119.3, 34.9, 121.6, 36.8], 'times':72, 'resolution':1/120.},
                    }
    #variables = ('hs', 'tm', 'di')
    variables = ['hs']

class WWIIIStore(GridStore):
    no_data = -999.9
    REGIONS = {
                        'NWP' : {'extent':[105., 15., 140., 47.], 'times':72, 'resolution':.1}
                    }
    #variables = ('hs', 'tm', 'di')
    variables = ['hs']

class POMStore(GridStore):
    no_data = 0 #999.0 -> 0
    REGIONS = {
                        'BH' : {'extent':[117.5, 37.2, 122., 42.], 'times':72, 'resolution':1/240.},
                        'ECS' : {'extent':[117.5, 24.5, 137., 42.], 'times':24, 'resolution':1/30.},
                    }
    #variables = ('u', 'v', 'el')
    variables = ('u', 'v')
    def get_value(self, latlon, time = 0, variables = None):
        values = GridStore.get_value(self, latlon, time = 0, variables = None)
        return map(lambda x: x/100., values)

class ROMSStore(object):
    dim_lon = 'xi_v'
    dim_lat = 'eta_u'
    no_data = 1e+37
    REGIONS = {
                        'NWP' : {'extent':[99., -9., 148., 42.], 'times':1, 'levels':25, 'resolution':.1},
                        'NCS' : {'extent':[117.5, 32., 127., 41.], 'times':96, 'levels':6, 'resolution':1/30.},
                        'QD' : {'extent':[119., 35., 122., 37.], 'times':96, 'levels':6, 'resolution':.1/30.},
                    }
    variables = ('u', 'v')

    def __init__(self, netcdf, region = 'WP'):
        self.extent = Extent.from_tuple(self.REGIONS[region]['extent'])
        self.times = self.REGIONS[region]['times']
        self.levels = self.REGIONS[region]['levels']
        self.resolution = self.REGIONS[region]['resolution']
        self.netcdf = netCDF4.Dataset(netcdf, 'r')
        self.cols = len(self.netcdf.dimensions[self.dim_lon])-1
        self.rows = len(self.netcdf.dimensions[self.dim_lat])-1

    def get_value(self, latlon, time = 0, level = -1, variables = None):
        if variables is None:
            variables = self.variables
        # todo 检查variabels是否都在self.netcdf.variables内
        if level == -1:
            level = self.levels - 1
        if time < 0 or time >= self.times or level < 0 or level >= self.levels:
            return map((lambda variable: float('nan')), variables)
        #lon_index = int((latlon.lon - self.extent.xmin) / (self.extent.xmax - self.extent.xmin) * self.cols)
        #lat_index = int((latlon.lat - self.extent.ymin) / (self.extent.ymax - self.extent.ymin) * self.rows)
        lon_index = int((latlon.lon - self.extent.xmin) / self.resolution)
        lat_index = int((latlon.lat - self.extent.ymin) / self.resolution)
        if lon_index < 0 or lon_index > self.cols or lat_index < 0 or lat_index > self.rows:
            return map((lambda variable: float('nan')), variables)
        #return map((lambda variable: self.netcdf.variables[variable][time][level][lat_index][lon_index]), variables)
        values = []
        for variable in variables:
            value = float(self.netcdf.variables[variable][time][level][lat_index][lon_index])
            if value == self.no_data or math.isnan(value):
                value = float('nan')
            values.append(value)
        return values

    def get_value_direct(self, lat_index, lon_index, time = 0, level = -1, variables = None):
        if variables is None:
            variables = self.variables
        # todo 检查variabels是否都在self.netcdf.variables内
        if level == -1:
            level = self.levels - 1
        if lon_index < 0 or lon_index > self.cols or lat_index < 0 or lat_index > self.rows or time > self.times - 1 or level > self.levels - 1:
            return map((lambda variable: float('nan')), variables)
        #return map((lambda variable: self.netcdf.variables[variable][time][level][lat_index][lon_index]), variables)
        values = []
        for variable in variables:
            value = float(self.netcdf.variables[variable][time][level][lat_index][lon_index])
            if value == self.no_data:
                value = float('nan')
            values.append(value)
        return values

# 输出后处理
def uv2va(values):
    if len(values) != 2:
        return values
    if not math.isnan(values[0]) and not math.isnan(values[1]):
        value = math.sqrt(values[0]*values[0] + values[1]*values[1])
        if abs(values[0]) > 0.000000001:
            angle = math.atan(values[1]/values[0])
        else:
            if values[1] > 0:
                angle = math.pi/2
            else:
                angle = math.pi*3/2
        if angle < 0:
            angle += 2*math.pi
    else:
        value = float('nan')
        angle = float('nan')
    return (value, angle)

def main():
    d = datetime.date.today()
    work_directory = '../BeihaiModel_out20130917'
    func_output_filter = uv2va
    map_projection = WebMercatorProjection
    # winds
    resource = 'WRF'
    region = 'NWP'
    d = datetime.date(2013,7,2)
    #waves
    resource = 'SWAN'
    region = 'NWP'
    d = datetime.date(2013,9,12)
    resource = 'WWIII'
    region = 'NWP'
    d = datetime.date(2013,9,12)
    # #pom
    # resource = 'POM'
    # region = 'ECS'
    # d = datetime.date(2013,9,13)
    # #roms
    # resource = 'ROMS'
    # region = 'NWP'
    # d = datetime.date(2013,9,13)
    # #fvcom
    # resource = 'FVCOM'
    # region = 'BHE'
    # d = datetime.date(2013,9,10)

    file_path = os.path.join(work_directory, resource, region)
    ncfile = os.path.join(file_path, str(d.year) + d.strftime("%m%d") + ".nc")
    #使用反射,通过globals()获取全局map,使用类名key构造对象, 注:如果需要动态包含外部库,使用__import__()函数)
    store = globals()[resource+'Store'](ncfile, region)

    zs = [4,5,6]
    for z in zs:
        for tilecoord in store.extent.iter_tilecoords(z, map_projection):
            json = '{'
            for latlon in tilecoord.iter_points(map_projection):
                values = store.get_value(latlon)
                string = str(func_output_filter(values))
                json +=  '[%s],' % string
            json += '}'

            dirname = os.path.join(file_path, 'output', str(tilecoord.z), str(tilecoord.y))
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            f = open(os.path.join(dirname, tilecoord.x.__str__() + '.json'), 'w')
            f.write(json)
            f.close()


if __name__ == '__main__':
    main()
