#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import math
import datetime
import  netCDF4
import numpy as np
try:
    import Image, ImageDraw, aggdraw
    lib_agg = True
except:
    lib_agg = False
try:
    from osgeo import ogr, osr
    from shapely import geometry
    lib_agg = True
except:
    lib_gdal = False

class Point(object):
    '''点类'''
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __str__(self):
        return '%f, %f' % (self.x, self.y)

class RowCol(object):
    '''行列类: row:y, col:x'''
    def __init__(self, row, col):
        self.row = row
        self.col = col
    def __str__(self):
        return '%f, %f' % (self.row, self.col)

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
    def get_bbox(self, projection=LatLonProjection, buffer=0):
        worldextent = WorldExtent(projection)
        resolution = worldextent.resolution / math.pow(2, self.z)
        xmin = resolution * self.x + worldextent.xmin
        ymax = worldextent.ymax - resolution * self.y
        xmax = xmin + resolution
        ymin = ymax - resolution
        return [xmin - buffer*resolution, ymin - buffer*resolution, xmax + buffer*resolution, ymax + buffer*resolution]

    #根据投影切分瓦片，返回地理坐标迭代器
    def iter_points(self, projection=LatLonProjection):
        worldextent = WorldExtent(projection)
        resolution = worldextent.resolution / math.pow(2, self.z)
        new_res = resolution / self.n
        xmin = resolution * self.x + worldextent.xmin
        ymax = worldextent.ymax - resolution * self.y
        for i in xrange(0, self.n):
            for j in xrange(0, self.n):
                yield projection.unproject(Point(xmin+new_res*(j+.5), ymax-new_res*(i+.5))) # 取格网中心点

    #返回子块的迭代器
    def iter_coords(self):
        for i in xrange(0, self.n):
            for j in xrange(0, self.n):
                yield (j, i)

class WorldExtent(object):
    '''世界范围与0级切片尺寸'''
    def __init__(self, projection=LatLonProjection):
        if projection == WebMercatorProjection:
            pi = math.pi
            self.xmin = -math.pi
            self.xmax = math.pi
            self.ymin = -pi
            self.ymax = pi
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
        return '%f, %f, %f, %f' % (self.xmin, self.ymin, self.xmax, self.ymax)

    def __eq__(self, other):
        eq = (self.xmin == other.xmin)
        eq = eq and (self.xmax == other.xmax)
        eq = eq and (self.ymin == other.ymin)
        eq = eq and (self.ymax == other.ymax)
        eq = eq and (self.projection == other.projection)
        return eq

    def tuple(self):
        return (self.xmin, self.ymin, self.xmax, self.ymax)

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

class SimpleLineStyle(object):
    color = (255, 255, 255)
    width = 1

class MarineSymbol(object):
    def __init__(self, value, angle):
        self.value = float(value)
        self.angle = float(angle)

    def zoom(self, scale):
        self.points = self.points*scale
        if hasattr(self, 'polygon'):
            self.polygon = self.polygon*scale

    def pan(self, pos):
        for i, point in enumerate(self.points):
            self.points[i] = point + pos
        if hasattr(self, 'polygon'):
            for i, point in enumerate(self.polygon):
                self.polygon[i] = point + pos

    def rotate(self, angle):
        xx = np.array([[math.cos(angle), -math.sin(angle)], [math.sin(angle), math.cos(angle)]])
        self.points = self.points.dot(xx)
        if hasattr(self, 'polygon'):
            self.polygon = self.polygon.dot(xx)

    def draw_agg(self, draw, style):
        pass

class WindSymbol(MarineSymbol):
    def __init__(self, value, angle):
        self.value = float(value)
        self.angle = float(angle)
        self.level = self.speed2level(self.value)
        self.size = 4
        if self.level < 9:
            points = np.array([[0, 4], [0, 0], [0, 0], [1, 0], [1, 0], [2, 0], [0, 1], [1, 1], [1, 1], [2, 1], [0, 2], [1, 2], \
                [1, 2], [2, 2], [0, 3], [1, 3], [1, 3], [2, 3]])
            self.points = points[0:2*(self.level+1)]
        else:
            self.points = np.array([[0, 4], [0, 0], [0, 0], [2, 2], [0, 2], [2, 2]])
        self.rotate(angle)
    def speed2level(self, speed):
        values = [0.3, 1.6, 3.4, 5.5, 8.0, 10.8, 13.9, 17.2, 20.8, 24.5, 28.5, 32.6, 32.6]
        for i in range(len(values)):
            if speed < values[i]:
                break
        return i

    def level2speed(self, level):
        values = [0.3, 1.6, 3.4, 5.5, 8.0, 10.8, 13.9, 17.2, 20.8, 24.5, 28.5, 32.6, 32.6]
        if level > len(values) - 1:
            level = len(values) - 1
        return values[level]

    def draw_agg(self, draw, style):
        #draw.setantialias(True)
        pen = aggdraw.Pen(tuple(style.color), style.width)
        for it in range(len(self.points)/2):
            draw.line(tuple(list(self.points[2*it]) + list(self.points[2*it+1])), pen)
        #draw.flush()

class ArrowSymbol(MarineSymbol):
    def __init__(self, value, angle):
        self.value = float(value)
        self.angle = float(angle)
        self.points = np.array([[0, 0], [0, 4]])
        self.polygon = np.array([[-.5, 1], [0, 0], [.5, 1]])
        self.size = 4
        self.rotate(angle)

    def segment_zoom(self, vs):
        if self.value < vs[1]:
            scale = .5
        elif self.value > vs[2]:
            scale = 1.
        else:
            scale = .5 + (self.value-vs[1])/(vs[2]-vs[1])
        self.points = self.points*scale

    def draw_agg(self, draw, style):
        #draw.setantialias(True)
        points = list(self.polygon[0]) + list(self.polygon[1]) + list(self.polygon[2]) + list(self.polygon[0])
        pen = aggdraw.Pen(tuple(style.color), style.width)
        brush = aggdraw.Brush(tuple(style.color))
        draw.polygon(tuple(points), pen, brush)
        draw.line(tuple(list(self.points[0]) + list(self.points[1])), pen)
        #draw.flush()

class NcArrayUtility(object):
    @classmethod
    def get_stats(cls, values):
        vmax = np.nanmax(values)
        vmin = np.nanmin(values)
        mean = np.nanmean(values)
        std = np.nanstd(values)
        return (vmax, vmin, mean, std)

    @classmethod
    def get_value_parts(cls, values):
        vmax = np.nanmax(values)
        vmin = np.nanmin(values)
        mean = np.nanmean(values)
        std = np.nanstd(values)
        times = 3
        vmax_fix = mean + times*std
        vmin_fix = mean - times*std
        vmax_fix = vmax if vmax < vmax_fix else vmax_fix
        vmin_fix = vmin if vmin > vmin_fix else vmin_fix
        vs = [vmin, vmin_fix, vmax_fix, vmax]
        return vs

    @classmethod
    def get_value_marks(cls, value_parts, mark_numbers=6, padding=0):
        value_marks = []
        mmin = value_parts[1]
        mmax = value_parts[2]
        step = (mmax-mmin)/mark_numbers
        start = mmin + padding*step
        if step < 1:
            step = round(step*10)
            for i in range(mark_numbers):
                v = round(start*10+step*i)
                if v > mmax*10:
                    if i == 1:
                        value_marks.append(round(mmax*10)/10.)
                    else:
                        break
                else:
                    value_marks.append(v/10.)
        else:
            step = int(round(step))
            for i in range(mark_numbers):
                v = int(round(start+step*i))
                if v > mmax:
                    if i == 1:
                        value_marks.append(int(mmax))
                    else:
                        break
                else:
                    value_marks.append(v)
        return value_marks

    @classmethod
    def uv2va(cls, uv):
        if len(uv) != 2:
            return uv
        if math.isnan(uv[0]) or math.isnan(uv[1]):
            value = np.nan
            angle = np.nan
        else:
            value = math.sqrt(uv[0]*uv[0] + uv[1]*uv[1])
            if uv[0] > value: uv[0] = value
            if uv[0] < -value: uv[0] = -value
            if abs(value) < .0000001:
                value = 0
                angle = 0
            else:
                angle = math.acos(uv[0]/value)
                if uv[1] < 0:
                    angle = 2*math.pi - angle
        return [value, angle]

    @classmethod
    def nan2val(cls, values, val=-9999):
        nan2num = lambda x, val: val if np.isnan(x) else x
        array_nan2num = np.vectorize(nan2num, otypes=[np.float])
        return array_nan2num(values, val)

class HueGradient(object):
    @classmethod
    def value_to_hue(cls, v, vs, hs):
        if v > vs[2]:
            h1 = hs[2]
            h2 = hs[3]
            v1 = vs[2]
            v2 = vs[3]
        elif v < vs[1]:
            h1 = hs[0]
            h2 = hs[1]
            v1 = vs[0]
            v2 = vs[1]
        else:
            h1 = hs[1]
            h2 = hs[2]
            v1 = vs[1]
            v2 = vs[2]
        h = cls.nolinear_gradient(v, v1, v2, h1, h2)
        return h

    @classmethod
    def get_hue_parts(cls, vs):
        hs = [240, 230, 10, 0]
        if vs[1] == vs[0]:
            hs[1] = hs[0]
        if vs[2] == vs[3]:
            hs[2] = hs[3]
        return hs

    @classmethod
    def linear_gradient(cls, v, v1,v2,h1,h2):
        k = (h2-h1)*1./(v2-v1)
        return h1+(v-v1)*k

    #非线性插值, x 的2次方函数
    @classmethod
    def nolinear_gradient(cls, v, v1,v2,h1,h2):
        if v1 == v2:
            return h1
        x = (v-v1)*1./(v2-v1)*4
        if x < 2: y = math.pow(x, 2)
        else: y = 8 - math.pow(4-x, 2)
        return h1 +  (h2-h1)*y/8

class ColorModelUtility(object):
    @classmethod
    def hex2rgb(cls, hex):
        r = hex >> 16
        g = (hex >> 8) & 0xff
        b = hex & 0xff
        return (r, g, b)

    @classmethod
    def rgb2hex(cls, rgb):
        if rgb == None or len(rgb) != 3 or min(rgb) < 0 or max(rgb) > 255:
            return 0xFFFFFF
        return rgb[0] << 16 | rgb[1] << 8 | rgb[2]

    @classmethod
    def hsv2rgb(cls, hsv):
        h = float(hsv[0])
        s = float(hsv[1])
        v = float(hsv[2])
        h60 = h / 60.0
        h60f = math.floor(h60)
        hi = int(h60f) % 6
        f = h60 - h60f
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        r, g, b = 0, 0, 0
        if hi == 0: r, g, b = v, t, p
        elif hi == 1: r, g, b = q, v, p
        elif hi == 2: r, g, b = p, v, t
        elif hi == 3: r, g, b = p, q, v
        elif hi == 4: r, g, b = t, p, v
        elif hi == 5: r, g, b = v, p, q
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        return [r, g, b]

    @classmethod
    def rgb2hsv(cls, rgb):
        r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
        mx = max(r, g, b)
        mn = min(r, g, b)
        df = mx-mn
        if mx == mn: h = 0
        elif mx == r: h = (60 * ((g-b)/df) + 360) % 360
        elif mx == g: h = (60 * ((b-r)/df) + 120) % 360
        elif mx == b: h = (60 * ((r-g)/df) + 240) % 360
        if mx == 0:s = 0
        else:s = df/mx
        v = mx
        return [h, s, v]

class ColorStyle(object):
    def __init__(self):
        self.hs = []
        self.vs = []
    def getColor(self, v):
        pass


class NCThumbnail(object):
    def __init__(self, model, region, method):
        self.model = model
        self.region = region
        self.method = method
        self.date = datetime.date.today()
        # for test
        self.date = datetime.date(2013, 9, 12)

    def getFileName(self):
        #model_dir = {"WRF":"WRF_met", "SWAN":"SWAN_wav", "POM":"ROMS_cur", "ROMS":"ROMS_cur", "FVCOMSTM":"FVCOM_stm", "FVCOMTID":"FVCOM_tid"}
        dirname = os.path.join('static', 'img', "thumbnails")
        filename = "%s_%s_%s.jpg" % (self.model, self.region, self.method)
        filename = os.path.join(dirname, filename)
        return filename.lower()

    def generate(self):
        filename = self.getFileName()
        model_regions = {"wrf":["nwp","ncs","qdsea"], "swan":["nwp","ncs","qdsea"], "ww3":["global", "nwp"], "pom":["ncs"], "roms":["nwp", "ncs", "qdsea"], "fvcomstm":["bhs"]}
        type_methods = {}
        for model in model_regions:
            regions = model_regions[model]
            for region in regions:
                store = globals()[model+'Store'](date, region)
                pass

class NCStore(object):
    '''NC文件库抽象类'''
    def __init__(self, date, region):
        pass

    # 获取nc文件的元数据信息
    def get_capabilities(self):
        pass

    # 获取nc文件指定时间层与深度层的元数据信息
    def get_capabilities2(self, variables=None, time=0, level=0):
        pass

    # 过滤输出结果是否为nan
    def is_valid_values(self, values):
        for v in values:
            if np.isnan(v):
                return False
        return True

    # 过滤输入变量是否有效,并删除无效变量,如全部无效,返回默认值
    def filter_variables(self, variables, defaults = None):
        if defaults is None:
            defaults = self.default_variables
        if variables == 'default':
            variables = defaults
            if not isinstance(variables, list):
                variables = [variables]
        else:
            variables = []
            temp = variables.split(',')
            for var in temp:
                var = var.strip()
                if var in self.variables:
                    variables.append(var)
            if len(variables) < 1:
                variables = defaults
        return variables

    # 获取行列号
    def get_colrow(self, latlon):
        if latlon is not None:
            lon_index = int((latlon.lon - self.extent.xmin) / self.resolution)
            lat_index = int(math.ceil((latlon.lat - self.extent.ymin) / self.resolution))
            return RowCol(lat_index, lon_index)
        else:
            return None

    # 获取坐标
    def get_latlon(self, rowcol):
        if rowcol is not None:
            lon = rowcol.col*(self.extent.xmax-self.extent.xmin)/self.cols+self.extent.xmin
            lat = rowcol.row*(self.extent.ymax-self.extent.ymin)/self.rows+self.extent.ymin
            return LatLon(lat, lon)
        else:
            return None

    # 设置过滤extent
    def set_filter_extent(self, xmin,ymin,xmax,ymax):
        rowcol_min = self.get_colrow(LatLon(ymin,xmin))
        rowcol_max = self.get_colrow(LatLon(ymax,xmax))
        self.min_row = rowcol_min.row if rowcol_min.row > 0 else 0
        self.min_col = rowcol_min.col if rowcol_min.col > 0 else 0
        self.max_row = rowcol_max.row if rowcol_max.row < self.rows else self.rows
        self.max_col = rowcol_max.col if rowcol_max.col < self.cols else self.cols
        self.filter_extent = Extent(xmin,ymin,xmax,ymax)
        if not self.filter_extent == self.extent:
            self.ncfs = os.path.join(self.ncfs, str(self.filter_extent))

    # 设置times过滤
    def set_filter_times(self, times):
        if self.times > times:
            self.times = times

    def is_valid_rowcol(self, rowcol):
        if rowcol is not None:
            if rowcol.col < self.min_col or rowcol.col > self.max_col-1 or rowcol.row < self.min_row or rowcol.row > self.max_row-1:
                return False
        return True

    # 获取某些变量标量化的值
    def get_scalar_values(self, variables=None, time=0, level=0):
        pass

    # 获取某些变量标量化的值, 如果time,level为None,merge所有结果
    def get_scalar_values2(self, variables=None, time=None, level=None):
        pass

    # 获取某几个变量的值,以list返回
    def get_vector_values(self, variables=None, time=0, level=0):
        pass

    # 标量场的分值图
    def scalar_to_image(self, variables, time, level, projection):
        pass

    # 标量场的等值线
    def scalar_to_isoline(self, variables, time, level):
        from matplotlib import _cntr as cntr
        # z = np.array(z)
        # x,y = np.mgrid[:z.shape[0],:z.shape[1]]
        # c = cntr.Cntr(x,y,z)
        # # trace a contour at z == 0.5
        # res = c.trace(0.5)
        # # result is a list of arrays of vertices and path codes
        # # (see docs for matplotlib.path.Path)
        pass

    # 矢量场的grid图
    def vector_to_grid_image(self, variables, time, level, projection):
        pass

    # 矢量场的grid表达的image瓦片
    def vector_to_grid_image_tile(self, tilecoord, variables, time, level, projection, postProcess = None):
        pass

    # 矢量场的grid表达的json瓦片
    def vector_to_grid_json_tile(self, tilecoord, variables, time, level, projection, postProcess = None):
        pass

    # 矢量场的jit图
    def vector_to_jit_image(self, variables, time, level, projection):
        pass

    # 矢量场的lit图
    def vector_to_lit_image(self, variables, time, level, projection):
        pass

    # 矢量场的lic图
    def vector_to_lic_image(self, variables, time, level, projection):
        pass

    # 矢量场的ostr图
    def vector_to_ostr_image(self, variables, time, level, projection):
        pass

    # 矢量场的gstr图
    def vector_to_gstr_image(self, variables, time, level, projection):
        pass

    def get_legend_filename(self, variables, time, level):
        dirname = os.path.join(self.ncfs, ','.join(variables), "legend")
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        if not self.universal_legend:
            filename = os.path.join(dirname,  "%d_%d" % (time, level) + '.png')
        else:
            filename = os.path.join(dirname,  'universal.png')
        return filename

    def get_scalar_image_filename(self, variables, time, level, projection):
        if projection == WebMercatorProjection:
            code = '3857'
        else:
            code = '4326'
        dirname = os.path.join(self.ncfs, ','.join(variables), "image", code)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        filename = os.path.join(dirname,  "%d_%d" % (time, level) + '.png')
        return filename

    def get_scalar_isoline_filename(self, variables, time, level):
        dirname = os.path.join(self.ncfs, ','.join(variables), "isoline")
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        filename = os.path.join(dirname,  "%d_%d" % (time, level) + '.geojson')
        return filename

    def get_json_tile_filename(self, tilecoord, variables, time, level, projection):
        if projection == WebMercatorProjection:
            code = '3857'
        else:
            code = '4326'
        dirname = os.path.join(self.ncfs, ','.join(variables), "json_tile", code, "%d_%d" % (time, level), str(tilecoord.z), str(tilecoord.y))
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        filename = os.path.join(dirname,  "%d" % tilecoord.x + '.geojson')
        return filename

    def get_image_tile_filename(self, tilecoord, variables, time, level, projection, postProcess = None):
        if projection == WebMercatorProjection:
            code = '3857'
        else:
            code = '4326'
        dirname = os.path.join(self.ncfs, ','.join(variables), "image_tile", code, "%d_%d" % (time, level), str(tilecoord.z), str(tilecoord.y))
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        filename = os.path.join(dirname,  "%d" % tilecoord.x + '.png')
        return filename

    # 获取图例
    def get_legend(self, variables = None, time = 0, level = 0, update = False):
        if variables is None:
            variables = self.default_scalar
        filename = self.get_legend_filename(variables, time, level)
        update = update | self.check_cache_valid(filename)
        if update:
            filename = self.generate_legend(variables, time, level)
        return filename

    # 获取指定点的值
    def get_point_value_json(self, latlon, variables = None, level=None, time=None, postProcess = None):
        pass

    # 获取某标量的分值图
    def get_scalar_image(self, variables = None, time = 0, level = 0, projection = LatLonProjection, update = False):
        if variables is None:
            variables = self.default_scalar
        filename = self.get_scalar_image_filename(variables, time, level, projection)
        update = update | self.check_cache_valid(filename)
        if update:
            filename = self.scalar_to_image(variables, time, level, projection)
        return filename

    # 获取某标量的等值线
    def get_scalar_isoline(self, variables = None, time = 0, level = 0, update = False):
        if variables is None:
            variables = self.default_scalar
        filename = self.get_scalar_isoline_filename(variables, time, level)
        update = update | self.check_cache_valid(filename)
        if update:
            json = self.scalar_to_isoline(variables, time, level)
            fp = open(filename, 'w')
            fp.write(json)
            fp.close()
        return filename

    # 获取向量的grid image tile
    def get_image_tile(self, tilecoord, variables, time, level, projection, postProcess = None, update = False):
        if variables is None:
            variables = self.default_variables
        filename = self.get_image_tile_filename(tilecoord, variables, time, level, projection)
        update = update | self.check_cache_valid(filename)
        if update:
            if isinstance(self, TINStore):
                filename = self.vector_to_nogrid_image_tile(tilecoord, variables, time, level, projection, postProcess)
            else:
                filename = self.vector_to_grid_image_tile(tilecoord, variables, time, level, projection, postProcess)
        return filename

    # 获取向量的 grid or nogrid json tile (TIN:nogrid)
    def get_json_tile(self, tilecoord, variables, time, level, projection, postProcess = None, update = False):
        if variables is None:
            variables = self.default_variables
        filename = self.get_json_tile_filename(tilecoord, variables, time, level, projection)
        update = update | self.check_cache_valid(filename)
        if update:
            if isinstance(self, TINStore):
                json = self.vector_to_nogrid_json_tile(tilecoord, variables, time, level, projection, postProcess)
            else:
                json = self.vector_to_grid_json_tile(tilecoord, variables, time, level, projection, postProcess)
            fp = open(filename, 'w')
            fp.write(json)
            fp.close()
        return filename

    # 生成图例
    def generate_legend(self, variables, time=None, level=None):
        if not self.universal_legend:
            vs_values = self.get_scalar_values(variables, time, level)
        else:
            vs_values = self.get_scalar_values2(variables)
        vs = NcArrayUtility.get_value_parts(vs_values)
        hs = HueGradient.get_hue_parts(vs)
        size = (204, 34)
        margin_x = 10
        margin_y = 3
        font_margin_x = -5
        font_margin_y = 3
        bar_x = 186
        bar_y = 12
        len_mark = 5
        font = aggdraw.Font('black', 'static/fonts/arial.ttf',10)
        black_pen = aggdraw.Pen('black')
        img = Image.new("RGBA", size)
        draw = aggdraw.Draw(img)
        draw.setantialias(True)
        # draw color bar
        for i in range(bar_x):
            h = HueGradient.nolinear_gradient(i, 0, bar_x, hs[0], hs[3])
            rgb = ColorModelUtility.hsv2rgb((h, 1., 1.))
            pen = aggdraw.Pen(tuple(rgb), 1)
            draw.line((i+margin_x,0+margin_y,i+margin_x,bar_y+margin_y), pen)
        # draw color bar bound
        draw.rectangle((0+margin_x, 0+margin_y, bar_x+margin_x, bar_y+margin_y), black_pen)
        # draw scalar marker
        value_marks = NcArrayUtility.get_value_marks(vs)
        pos1 = int((hs[1]-hs[0])*1./(hs[3]-hs[0])*bar_x)
        pos2 = int((hs[2]-hs[0])*1./(hs[3]-hs[0])*bar_x)
        for v in value_marks:
            pos = (v-vs[1])*1./(vs[2]-vs[1])*(pos2-pos1) + pos1
            if pos<0:pos=0
            if pos>bar_x:pos=bar_x
            draw.line((pos+margin_x, bar_y+margin_y, pos+margin_x, bar_y+len_mark+margin_y), black_pen)
            draw.text((pos+margin_x+font_margin_x, bar_y+len_mark+font_margin_y+margin_y), str(v), font)
        # save
        draw.flush()
        del draw
        legend = self.get_legend_filename(variables, time, level)
        img.save(legend, "png")
        return legend

    #输出shapefile
    def export_to_shapefile(self, projection=LatLonProjection):
        pass

    # 输出 scalar legends 序列
    def list_scalar_legends(self, variables = None, time = None, level = None, update=False):
        if variables is None:
            variables = self.default_scalar
        if level is None:
            levels = self.levels if self.levels > 0 else 1
            levels = range(levels-1, -1, -1)
        else:
            levels = [level]
        if time is None:
            times = range(self.times)
        else:
            times = [time]
        for level in levels:
            for time in times:
                yield (self, "get_legend", variables, time, level, update)

    # 输出 scalar isoline 序列
    def list_scalar_isolines(self, variables = None, time = None, level = None, update=False):
        if variables is None:
            variables = self.default_scalar
        if level is None:
            levels = self.levels if self.levels > 0 else 1
            levels = range(levels-1, -1, -1)
        else:
            levels = [level]
        if time is None:
            times = range(self.times)
        else:
            times = [time]
        for level in levels:
            for time in times:
                yield (self, "get_scalar_isoline", variables, time, level, update)

    # 输出 scalar images 序列
    def list_scalar_images(self, variables = None, time = None, level = None, projection=LatLonProjection, update=False):
        if variables is None:
            variables = self.default_scalar
        if level is None:
            levels = self.levels if self.levels > 0 else 1
            levels = range(levels-1, -1, -1)
        else:
            levels = [level]
        if time is None:
            times = range(self.times)
        else:
            times = [time]
        for level in levels:
            for time in times:
                yield (self, "get_scalar_image", variables, time, level, projection, update)

    #输出 vector grid image or geojson tiles 序列, type=image|json, default is image
    def list_tiles(self, type='image', z=None, variables = None, time = None, level = None, projection=LatLonProjection, postProcess=NcArrayUtility.uv2va, update=False):
        if variables is None:
            variables = self.default_variables
        if z is None:
            zs = range(1, self.maxlevel)
        else:
            zs = [z]
        if level is None:
            levels = self.levels if self.levels > 0 else 1
            levels = range(levels-1, -1, -1)
        else:
            levels = [level]
        if time is None:
            times = range(self.times)
        else:
            times = [time]

        for level in levels:
            for time in times:
                for z in zs:
                    for tilecoord in self.filter_extent.iter_tilecoords(z, projection):
                        yield (self, 'get_%s_tile' % type, tilecoord, variables, time, level, projection, postProcess, update)

    #判断缓存是否需要更新
    def check_cache_valid(self, filename):
        update = False
        if not os.path.isfile(filename):
            update = True
        else:
            # todo:检查文件时效性
            pass
        return update

    # 清除缓存数据
    def clean_cache(self):
        import shutil
        shutil.rmtree(self.ncfs)

class Triangle(object):
    '''三角形类'''
    def __init__(self, center, nele=-1):
        #中心点
        self.center = center
        self.nele = nele
    def __str__(self):
        return '%s, %d' % (str(self.center), self.nele)

class TINStore(NCStore):
    def __init__(self, date, region):
        self.no_data = -999.
        self.dimensions = {'node' : 'node', 'element' : 'nele', 'time':'time'}
        self.variables = {
            'lon': 'getLon',
            'lat': 'getLat',
            'h':'getH',
            'nv': 'getNV',
            'u':'getU',
            'v':'getV',
            'zeta':'getZeta'
        }
        self.default_vector = ['u', 'v']
        self.default_scalar = ['zeta']
        self.default_variables = self.default_vector

    def init(self):
        if not os.path.isdir(self.ncfs):
            os.mkdir(self.ncfs)
        if not os.path.isdir(self.shpfs):
            os.mkdir(self.shpfs)
        ncfile = self.ncfs + '.nc'
        self.nc = netCDF4.Dataset(ncfile, 'r')
        self.nodes = len(self.nc.dimensions[self.dimensions['node']])
        self.elements = len(self.nc.dimensions[self.dimensions['element']])
        self.times = len(self.nc.dimensions[self.dimensions['time']])
        self.levels = 0
        # for scalar image, generate grid nc
        self.gridnc = os.path.join(self.shpfs, 'grid.nc')
        self.cols = int((self.extent.xmax - self.extent.xmin)/self.resolution)
        self.rows = int((self.extent.ymax - self.extent.ymin)/self.resolution)
        self.set_filter_extent(self.extent.xmin, self.extent.ymin, self.extent.xmax, self.extent.ymax)
        self.universal_legend = True

    def get_capabilities(self):
        capabilities = {
            "region":self.region,
            "date":self.date,
            "dimensions":self.dimensions,
            "variables":self.variables,
            "default_variables":self.default_vector,
            "default_scalar":self.default_scalar,
            "extent":str(self.extent),
            "times":self.times,
            "elements":self.elements,
            "nodes":self.nodes
        }
        return capabilities

    def get_capabilities2(self, variables=None, time=0, level=0):
        if variables == None:
            variables = self.default_scalar
        values = self.get_scalar_values(variables, time)
        vmax, vmin, mean, std = NcArrayUtility.get_stats(values)
        capabilities = {
            "variables":','.join(variables),
            "extent":str(self.extent),
            "time":time,
            "max":vmax,
            "min":vmin,
            "mean":mean,
            "std":std
         }
        return capabilities

    def is_valid_params(self, element = None, time = None, node = None):
        if element != None:
            if element < 0 or element > self.elements - 1:
                return False
        if time != None:
            if time < 0 or time > self.times - 1:
                return False
        if node != None:
            if node < 0 or node > self.nodes - 1:
                return False
        return True

    def getLon(self, node=None):
        if node is None:
            return self.nc.variables['lon']
        else:
            return self.nc.variables['lon'][node]

    def getLat(self, node=None):
        if node is None:
            return self.nc.variables['lat']
        else:
            return self.nc.variables['lat'][node]

    def getH(self, node=None):
        if node is None:
            return self.nc.variables['h']
        else:
            return self.nc.variables['h'][node]

    def getNV(self, element=None):
        # 获取的点号从1开始编号,通过-1恢复从0编号
        if element is None:
            return [self.nc.variables['nv'][0]-1, self.nc.variables['nv'][1]-1, self.nc.variables['nv'][2]-1]
        else:
            return [self.nc.variables['nv'][0][element]-1, self.nc.variables['nv'][1][element]-1, self.nc.variables['nv'][2][element]-1]

    def getU(self, time=0, siglay=0, element=None):
        if element is None:
            return self.nc.variables['u'][time][siglay]
        else:
            return self.nc.variables['u'][time][siglay][element]

    def getV(self, time=0, siglay=0, element=None):
        if element is None:
            return self.nc.variables['v'][time][siglay]
        else:
            return self.nc.variables['v'][time][siglay][element]

    def getZeta(self, time=0, node=None):
        if node is None:
            return self.nc.variables['zeta'][time]
        else:
            return self.nc.variables['zeta'][time][node]

    def get_scalar_values(self, variables=None, time=0, level=0):
        if variables == None:
            variables = self.default_scalar
        if isinstance(variables, list):
            values = None
            for var in variables:
                val = getattr(self, self.variables[var])(time=time)
                val = val[:self.elements]
                val = pow(val, 2)
                if values is None:
                    values = val
                else:
                    values += val
            values = pow(values, .5)
        else:
            values = getattr(self, self.variables[variables])(time=time)
            values = values[:self.elements]
        return values

    def get_scalar_values2(self, variables=None, time=None, level=None):
        levels = self.levels if self.levels > 0 else 1
        times = self.times
        if level is not None:
            levels = [level]
        else:
            levels = range(levels)
        if time is not None:
            times = [time]
        else:
            times = range(times)
        if variables == None:
            variables = self.default_variables
        stack = None
        for level in levels:
            for time in times:
                if isinstance(variables, list):
                    values = None
                    for var in variables:
                        val = getattr(self, self.variables[var])(time=time)
                        val = val[:self.elements]
                        val = pow(val, 2)
                        if values is None:
                            values = val
                        else:
                            values += val
                    values = pow(values, .5)
                else:
                    values = getattr(self, self.variables[variables])(time=time)
                    values = values[:self.elements]
                if stack is None:
                    stack = values
                else:
                    stack = np.vstack((stack, values))
        return stack

    def get_vector_values(self, variables=None, time=0, level=0):
        if variables == None:
            variables = self.default_vector
        values = []
        if isinstance(variables, list):
            for var in variables:
                val = getattr(self, self.variables[var])(time=time)
                val = val[:self.elements]
                values.append(val)
        else:
            val = getattr(self, self.variables[variables])(time=time)
            val = val[:self.elements]
            values.append(val)
        return values

    def export_nodes(self, outputFormat='ESRI Shapefile'):
        dirName = self.shpfs
        layerName = 'nodes'
        outputFormats = {'ESRI Shapefile':'.shp', 'GeoJSON':'.geojson', 'JSON':'.json', 'SQLite':'.sqlite'}
        outputfile = os.path.join(dirName, layerName+outputFormats[outputFormat])
        if os.path.isfile(outputfile) is True:
            os.remove(outputfile)
            if outputFormat == 'ESRI Shapefile':
                os.remove(os.path.join(dirName, layerName+'.shx'))
                os.remove(os.path.join(dirName, layerName+'.dbf'))
                os.remove(os.path.join(dirName, layerName+'.prj'))
        dataDriver = ogr.GetDriverByName(outputFormat)
        dataSource = dataDriver.CreateDataSource(outputfile)
        # Make layer
        spatialReference = osr.SpatialReference()
        spatialReference.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
        layer = dataSource.CreateLayer(layerName, spatialReference, ogr.wkbPoint)
        fieldDefinitions = [('node', ogr.OFTInteger)]
        for fieldName, fieldType in fieldDefinitions:
             layer.CreateField(ogr.FieldDefn(fieldName, fieldType))
        featureDefinition = layer.GetLayerDefn()

        for node in range(self.nodes):
            lat = self.getLat(node)
            lon = self.getLon(node)
            feature = ogr.Feature(featureDefinition)
            point = geometry.Point(lon, lat)
            feature.SetGeometry(ogr.CreateGeometryFromWkb(point.wkb))
            feature.SetField(0, node)
            layer.CreateFeature(feature)
            feature.Destroy()
        #layer.SyncToDisk()
        dataSource.ExecuteSQL('CREATE SPATIAL INDEX ON %s' % layerName)
        dataSource.SyncToDisk()
        dataSource.Release()

    def export_elements(self, outputFormat='ESRI Shapefile'):
        dirName = self.shpfs
        layerName = 'elements'
        outputFormats = {'ESRI Shapefile':'.shp', 'GeoJSON':'.geojson', 'JSON':'.json', 'SQLite':'.sqlite'}
        outputfile = os.path.join(dirName, layerName+outputFormats[outputFormat])
        if os.path.isfile(outputfile) is True:
            os.remove(outputfile)
            if outputFormat == 'ESRI Shapefile':
                os.remove(os.path.join(dirName, layerName+'.shx'))
                os.remove(os.path.join(dirName, layerName+'.dbf'))
                os.remove(os.path.join(dirName, layerName+'.prj'))
        dataDriver = ogr.GetDriverByName(outputFormat)
        dataSource = dataDriver.CreateDataSource(outputfile)
        # Make layer
        spatialReference = osr.SpatialReference()
        spatialReference.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
        layer = dataSource.CreateLayer(layerName, spatialReference, ogr.wkbPolygon)
        fieldDefinitions = [('element', ogr.OFTInteger)]
        for fieldName, fieldType in fieldDefinitions:
             layer.CreateField(ogr.FieldDefn(fieldName, fieldType))
        featureDefinition = layer.GetLayerDefn()

        nodes1,nodes2,nodes3 = self.getNV()
        for element in range(self.elements):
            #node1,node2,node3 = self.getNV(element)
            feature = ogr.Feature(featureDefinition)
            #polygon = geometry.Polygon([(self.getLon(node1), self.getLat(node1)), (self.getLon(node2), self.getLat(node2)), (self.getLon(node3), self.getLat(node3))])
            polygon = geometry.Polygon([(self.getLon(nodes1[element]), self.getLat(nodes1[element])), (self.getLon(nodes2[element]), self.getLat(nodes2[element])), (self.getLon(nodes3[element]), self.getLat(nodes3[element]))])
            feature.SetGeometry(ogr.CreateGeometryFromWkb(polygon.wkb))
            feature.SetField(0, element)
            layer.CreateFeature(feature)
            feature.Destroy()
        #layer.SyncToDisk()
        dataSource.ExecuteSQL('CREATE SPATIAL INDEX ON %s' % layerName)
        dataSource.SyncToDisk()
        dataSource.Release()

    def export_element_centers(self, outputFormat='ESRI Shapefile'):
        dirName = self.shpfs
        layerName = 'element_centers'
        outputFormats = {'ESRI Shapefile':'.shp', 'GeoJSON':'.geojson', 'JSON':'.json', 'SQLite':'.sqlite'}
        outputfile = os.path.join(dirName, layerName+outputFormats[outputFormat])
        if os.path.isfile(outputfile) is True:
            os.remove(outputfile)
            if outputFormat == 'ESRI Shapefile':
                os.remove(os.path.join(dirName, layerName+'.shx'))
                os.remove(os.path.join(dirName, layerName+'.dbf'))
                os.remove(os.path.join(dirName, layerName+'.prj'))
        dataDriver = ogr.GetDriverByName(outputFormat)
        dataSource = dataDriver.CreateDataSource(outputfile)
        # Make layer
        spatialReference = osr.SpatialReference()
        spatialReference.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
        layer = dataSource.CreateLayer(layerName, spatialReference, ogr.wkbPoint)
        fieldDefinitions = [('element', ogr.OFTInteger)]
        for fieldName, fieldType in fieldDefinitions:
             layer.CreateField(ogr.FieldDefn(fieldName, fieldType))
        featureDefinition = layer.GetLayerDefn()

        nodes = self.getNV()
        for element in range(self.elements):
            feature = ogr.Feature(featureDefinition)
            lat = (self.getLat(nodes[0][element])+self.getLat(nodes[1][element])+self.getLat(nodes[2][element]))/3.
            lon = (self.getLon(nodes[0][element])+self.getLon(nodes[1][element])+self.getLon(nodes[2][element]))/3.
            point = geometry.Point(lon, lat)
            feature.SetGeometry(ogr.CreateGeometryFromWkb(point.wkb))
            feature.SetField(0, element)
            layer.CreateFeature(feature)
            feature.Destroy()
        #layer.SyncToDisk()
        dataSource.ExecuteSQL('CREATE SPATIAL INDEX ON %s' % layerName)
        dataSource.SyncToDisk()
        dataSource.Release()

    def export_elements_gridnc(self):
        ncfile = self.gridnc
        if os.path.isfile(ncfile) is True:
            os.remove(ncfile)
        gridnc = netCDF4.Dataset(ncfile, 'w', format='NETCDF3_CLASSIC')
        lat = gridnc.createDimension('lat', self.rows)
        lon = gridnc.createDimension('lon', self.cols)
        temp = gridnc.createDimension('temp', 1)
        element = gridnc.createVariable('element', 'i4', ('temp', 'lat','lon'))
        ds, layer = self.get_assist_handle('vector')
        if layer is None:
            gridnc.close()
            print 'get layer error'
            return
        for row in range(self.rows):
            for col in range(self.cols):
                latlon = self.get_latlon(RowCol(row, col))
                layer.ResetReading()
                point = geometry.Point(latlon.lon, latlon.lat)
                point = ogr.CreateGeometryFromWkb(point.wkb)
                layer.SetSpatialFilter(point)
                pFeature = layer.GetNextFeature()
                if pFeature is not None:
                    nele = pFeature.GetFieldAsInteger('element')
                    element[0, row, col] = nele
                else:
                    element[0, row, col] = -1
        gridnc.close()

    def get_assist_handle(self, type='raster'):
        if type == 'raster':
            ncfile = self.gridnc
            if not os.path.isfile(ncfile):
                self.export_elements_gridnc()
            nc = netCDF4.Dataset(ncfile, 'r')
            values = nc.variables['element'][0]
            nc.close()
            return values
        else:
            if type == 'vector-nodes':
                layerName = 'element_centers'
            else:
                layerName = 'elements'
            shp = os.path.join(self.shpfs, layerName+'.shp')
            if not os.path.isfile(shp):
                if layerName == 'elements':
                    self.export_elements()
                else:
                    self.export_element_centers()
            dataSource = ogr.Open(shp)
            if dataSource is None:
                print "Open %s failed.\n" % shp
                return None
            layer = dataSource.GetLayerByName(layerName)
            layer.ResetReading()
            return [dataSource, layer]

    def get_triangle(self, latlon, handle):
        if isinstance(handle, list):
            rowcol = self.get_colrow(latlon)
            if not self.is_valid_rowcol(rowcol):
                return Triangle(latlon)
            point = geometry.Point(latlon.lon, latlon.lat)
            point = ogr.CreateGeometryFromWkb(point.wkb)
            layer = handle[1]
            layer.ResetReading()
            layer.SetSpatialFilter(point)
            pFeature = layer.GetNextFeature()
            if pFeature is not None:
                nele = pFeature.GetFieldAsInteger('element')
                return Triangle(latlon, nele)
            else:
                return Triangle(latlon)
        else:
            rowcol = self.get_colrow(latlon)
            if not self.is_valid_rowcol(rowcol):
                return Triangle(latlon)
            nele = handle[rowcol.row, rowcol.col]
            if nele is None: nele = -1
            return Triangle(latlon, nele)

    def get_triangles(self, tilecoord, handle, projection=LatLonProjection, nogrid=False, buffer=0.):
        grid = []
        if isinstance(handle, list):
            layer = handle[1]
            #非grid化的取我特征点的方法:隔几个点取一个
            if nogrid:
                maxlevel = self.maxlevel
                if tilecoord.z > maxlevel-1:
                    step = 1
                else:
                    #根据选取原则,点数为sqrt(resolution1/resolution2)
                    #step = int(math.pow(2, (maxlevel-tilecoord.z)/2.))
                    step = int(math.pow(2, (maxlevel-tilecoord.z)))
                layer.ResetReading()
                bbox = tilecoord.get_bbox(projection, buffer=buffer)
                min = projection.unproject(Point(bbox[0], bbox[1]))
                max = projection.unproject(Point(bbox[2], bbox[3]))
                # 根据bbox过滤
                if min.lon < self.filter_extent.xmin:min.lon = self.filter_extent.xmin
                if min.lat < self.filter_extent.ymin:min.lat = self.filter_extent.ymin
                if max.lon > self.filter_extent.xmax:max.lon = self.filter_extent.xmax
                if max.lat > self.filter_extent.ymax:max.lat = self.filter_extent.ymax
                layer.SetSpatialFilterRect(min.lon, min.lat, max.lon, max.lat)
                # 以下方法的问题:边界处瓦片内的点少, 则密度大, 造成视觉不好
                # 如果步长大于按最少符号数表现,则取小步长
                # step2 = layer.GetFeatureCount()/(tilecoord.n*tilecoord.n)
                # if step > step2:
                #     step = step2
                pFeature = layer.GetNextFeature()
                while pFeature is not None:
                    geom = pFeature.GetGeometryRef()
                    latlon = LatLon(geom.GetY(0), geom.GetX(0))
                    nele = pFeature.GetFieldAsInteger('element')
                    triangle = Triangle(latlon, nele)
                    grid.append(triangle)
                    for i in range(step):
                        pFeature = layer.GetNextFeature()
            else:
                for latlon in tilecoord.iter_points(projection):
                    rowcol = self.get_colrow(latlon)
                    if not self.is_valid_rowcol(rowcol):
                        grid.append(Triangle(latlon))
                    layer.ResetReading()
                    point = geometry.Point(latlon.lon, latlon.lat)
                    point = ogr.CreateGeometryFromWkb(point.wkb)
                    layer.SetSpatialFilter(point)
                    pFeature = layer.GetNextFeature()
                    if pFeature is not None:
                        nele = pFeature.GetFieldAsInteger('element')
                        triangle = Triangle(latlon, nele)
                        grid.append(triangle)
                    else:
                        grid.append(Triangle(latlon))
        else:
            for latlon in tilecoord.iter_points(projection):
                rowcol = self.get_colrow(latlon)
                if not self.is_valid_rowcol(rowcol):
                    grid.append(Triangle(latlon))
                else:
                    nele = handle[rowcol.row, rowcol.col]
                    if nele is None: nele = -1
                    triangle = Triangle(latlon, nele)
                    grid.append(triangle)
        return grid

    def scalar_to_image(self, variables, time, level=0, projection=LatLonProjection):
        if variables == None:
            variables = self.default_scalar
        values = self.get_scalar_values(variables, time, level)
        if not self.universal_legend:
            vs_values = values
        else:
            vs_values = self.get_scalar_values2(variables)
        vs = NcArrayUtility.get_value_parts(vs_values)
        hs = HueGradient.get_hue_parts(vs)

        nodes = self.getNV()
        elements = self.get_assist_handle('raster')
        if projection == LatLonProjection:
            # width = self.cols
            # height = self.rows
            width = self.max_col - self.min_col
            height = self.max_row - self.min_row
            size = (width, height)
            img = Image.new("RGBA", size)
            draw = aggdraw.Draw(img)
            draw.setantialias(True)
            for row in range(height):
                for col in range(width):
                    nele = elements[row+self.min_row, col+self.min_col]
                    if nele < 0 or np.isnan(float(nele)): continue
                    tri_nodes = [nodes[i][nele] for i in range(3)]
                    vals = [values[node] for node in tri_nodes]
                    v = sum(vals)/len(vals)
                    if np.isnan(v): continue
                    h = HueGradient.value_to_hue(v, vs, hs)
                    rgb = ColorModelUtility.hsv2rgb((h, 1., 1.))
                    pen = aggdraw.Pen(tuple(rgb), 1)
                    draw.rectangle((col, height-row, col+1, height-1-row), pen)
            draw.flush()
            del draw
            filename = self.get_scalar_image_filename(variables, time, level, projection)
            img.save(filename, "png")
            return filename
        else:
            # ll_min = LatLon(self.extent.ymin, self.extent.xmin)
            # ll_max = LatLon(ll_min.lat + self.resolution*self.rows, ll_min.lon + self.resolution*self.cols)
            ll_min = LatLon(self.filter_extent.ymin, self.filter_extent.xmin)
            ll_max = LatLon(ll_min.lat + self.resolution*(self.max_row-self.min_row), ll_min.lon + self.resolution*(self.max_col-self.min_col))
            wm_min = WebMercatorProjection.project(ll_min)
            wm_max = WebMercatorProjection.project(ll_max)
            # width = self.cols
            width = self.max_col-self.min_col
            height = int(math.ceil((wm_max.y - wm_min.y)/(wm_max.x-wm_min.x)*width))
            wm_resolution = (wm_max.x-wm_min.x)/width
            size = (width, height)
            img = Image.new("RGBA", size)
            draw = aggdraw.Draw(img)
            draw.setantialias(True)
            for row in range(height):
                pt = Point(0, row*wm_resolution+wm_min.y)
                ll = WebMercatorProjection.unproject(pt)
                ll_row = int((ll.lat-ll_min.lat)/self.resolution)
                for col in range(width):
                    nele = elements[ll_row+self.min_row, col+self.min_col]
                    if nele < 0 or np.isnan(float(nele)): continue
                    tri_nodes = [nodes[i][nele] for i in range(3)]
                    vals = [values[node] for node in tri_nodes]
                    v = sum(vals)/len(vals)
                    if np.isnan(v):
                        continue
                    h = HueGradient.value_to_hue(v, vs, hs)
                    rgb = ColorModelUtility.hsv2rgb((h, 1., 1.))
                    pen = aggdraw.Pen(tuple(rgb), 1)
                    draw.rectangle((col, height-row, col+1, height-1-row), pen)
            draw.flush()
            del draw
            filename = self.get_scalar_image_filename(variables, time, level, projection)
            img.save(filename, "png")
            return filename

    def scalar_to_isoline(self, variables, time, level):
        from matplotlib import _tri as tri
        #from matplotlib import _cntr as cntr
        if variables == None:
            variables = self.default_scalar
        values = self.get_scalar_values(variables, time, level)
        pass

    def vector_to_grid_image_tile(self, tilecoord, variables, time, level=0, projection=LatLonProjection, postProcess = None):
        imagesize = 256
        # v_values = self.get_vector_values(variables, time, level)
        # values = None
        # for val in v_values:
        #     val = pow(val, 2)
        #     if values is None: values = val
        #     else: values += val
        # values = pow(values, .5)
        # vs = NcArrayUtility.get_value_parts(values)
        if not self.universal_legend:
            vs_values = self.get_scalar_values(variables, time, level)
        else:
            vs_values = self.get_scalar_values2(variables)
        vs = NcArrayUtility.get_value_parts(vs_values)
        hs = HueGradient.get_hue_parts(vs)
        handle = self.get_assist_handle('vector')
        size = (imagesize,imagesize)
        img = Image.new("RGBA", size)
        draw = aggdraw.Draw(img)
        draw.setantialias(True)
        it = -1
        for triangle in self.get_triangles(tilecoord, handle=handle, projection=projection):
            it += 1
            if triangle.nele < 0: continue
            values = [getattr(self, self.variables[variable])(time=time, element=triangle.nele) for variable in variables]
            if not self.is_valid_values(values): continue
            if postProcess is not None:
                values = postProcess(values)
            h = HueGradient.value_to_hue(values[0], vs, hs)
            if np.isnan(h): continue
            style = SimpleLineStyle()
            style.color = ColorModelUtility.hsv2rgb((h, 1., 1.))
            symbol = ArrowSymbol(values[0], values[1])
            symbol.segment_zoom(vs)
            if symbol is not None:
                gridsize = imagesize/tilecoord.n
                scale = gridsize/2./symbol.size
                symbol.zoom(scale)
                i = it / tilecoord.n
                j = it % tilecoord.n
                pos_x = gridsize*j + gridsize/2.
                pos_y = gridsize*i + gridsize/2.
                symbol.pan(np.array([pos_x, pos_y]))
                symbol.draw_agg(draw, style)
        # save
        draw.flush()
        del draw
        tile = self.get_image_tile_filename(tilecoord, variables, time, level, projection)
        img.save(tile, "png")
        return tile

    #非grid化,使用删除一定量中间点的方法表现,生成image时缓冲8pixels,防止边界符号切断
    def vector_to_nogrid_image_tile(self, tilecoord, variables, time, level=0, projection=LatLonProjection, postProcess = None):
        imagesize = 256
        board = 8
        buffer = board/256.
        # v_values = self.get_vector_values(variables, time, level)
        # values = None
        # for val in v_values:
        #     val = pow(val, 2)
        #     if values is None: values = val
        #     else: values += val
        # values = pow(values, .5)
        # vs = NcArrayUtility.get_value_parts(values)
        if not self.universal_legend:
            vs_values = self.get_scalar_values(variables, time, level)
        else:
            vs_values = self.get_scalar_values2(variables)
        vs = NcArrayUtility.get_value_parts(vs_values)
        hs = HueGradient.get_hue_parts(vs)
        handle = self.get_assist_handle('vector-nodes')
        size = (imagesize+2*board,imagesize+2*board)
        img = Image.new("RGBA", size)
        draw = aggdraw.Draw(img)
        draw.setantialias(True)
        bbox = tilecoord.get_bbox(projection, buffer=buffer)
        min = projection.unproject(Point(bbox[0], bbox[1]))
        max = projection.unproject(Point(bbox[2], bbox[3]))
        len_x = max.lon-min.lon
        len_y = max.lat-min.lat
        for triangle in self.get_triangles(tilecoord, handle=handle, projection=projection, nogrid=True, buffer=buffer):
            if triangle.nele < 0: continue
            values = [getattr(self, self.variables[variable])(time=time, element=triangle.nele) for variable in variables]
            if not self.is_valid_values(values): continue
            if postProcess is not None:
                values = postProcess(values)
            h = HueGradient.value_to_hue(values[0], vs, hs)
            if np.isnan(h): continue
            style = SimpleLineStyle()
            style.color = ColorModelUtility.hsv2rgb((h, 1., 1.))
            symbol = ArrowSymbol(values[0], values[1])
            symbol.segment_zoom(vs)
            if symbol is not None:
                gridsize = imagesize/tilecoord.n
                scale = gridsize/2./symbol.size
                symbol.zoom(scale)
                dx = triangle.center.lon - min.lon
                dy = triangle.center.lat - min.lat
                pos_x = int(dx/len_x*(imagesize+2*board))
                pos_y = int((len_y-dy)/len_y*(imagesize+2*board))
                symbol.pan(np.array([pos_x, pos_y]))
                symbol.draw_agg(draw, style)
        # save
        draw.flush()
        del draw
        tile = self.get_image_tile_filename(tilecoord, variables, time, level, projection)
        img2 = img.crop((board, board, imagesize+board, imagesize+board))
        img2.save(tile, "png")
        return tile

    def vector_to_grid_json_tile(self, tilecoord, variables, time, level=0, projection=LatLonProjection, postProcess = None):
        if variables is None:
            variables = self.default_variables
        handle = self.get_assist_handle('vector')
        json = '{"type":"FeatureCollection","features":['
        for triangle in self.get_triangles(tilecoord, handle, projection):
            if triangle.nele < 0: continue
            values = [getattr(self, self.variables[variable])(time=time, element=triangle.nele) for variable in variables]
            if not self.is_valid_values(values): continue
            if postProcess is not None:
                values = postProcess(values)
            str_val = ''
            for v in values:
                str_val += "%.2f" % v
                str_val += ','
            if str_val[-1] == ',':
                str_val = str_val[:-1]
            string = '{"type":"Feature","geometry":{"type":"Point","coordinates":[%.4f,%.4f]},"properties": {"value": [%s]}}' % \
                        (triangle.center.lon, triangle.center.lat, str_val)
            json += string + ','
        if json[-1] == ',':
            json = json[:-1]
        json += ']}'
        return json

    # 非grid化,使用删除一定量中间点的方法输出
    def vector_to_nogrid_json_tile(self, tilecoord, variables, time, level=0, projection=LatLonProjection, postProcess = None):
        if variables is None:
            variables = self.default_variables
        handle = self.get_assist_handle('vector-nodes')
        json = '{"type":"FeatureCollection","features":['
        bbox = tilecoord.get_bbox(projection)
        min = projection.unproject(Point(bbox[0], bbox[1]))
        max = projection.unproject(Point(bbox[2], bbox[3]))
        len_x = max.lon-min.lon
        len_y = max.lat-min.lat
        for triangle in self.get_triangles(tilecoord, handle=handle, projection=projection, nogrid=True):
            if triangle.nele < 0: continue
            values = [getattr(self, self.variables[variable])(time=time, element=triangle.nele) for variable in variables]
            bfilter = self.is_valid_values(values)
            if not bfilter: continue
            if postProcess is not None:
                values = postProcess(values)
            str_val = ''
            for v in values:
                str_val += "%.2f" % v
                str_val += ','
            if str_val[-1] == ',':
                str_val = str_val[:-1]
            string = '{"type":"Feature","geometry":{"type":"Point","coordinates":[%.4f,%.4f]},"properties": {"value": [%s]}}' % \
                        (triangle.center.lon, triangle.center.lat, str_val)
            json += string + ','
        if json[-1] == ',':
            json = json[:-1]
        json += ']}'
        return json

    def get_point_value_json(self, latlon, variables = None, level=None, time=None, postProcess = None):
        if variables is None:
            variables = self.default_variables
        json = '{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[%f,%f]},"properties": {"value": [' % (latlon.lon, latlon.lat)
        times = self.times
        levels = self.levels if self.levels > 0 else 1
        if level is not None:
            levels = [level]
        else:
            levels = range(levels)
        if time is not None:
            times = [time]
        else:
            times = range(times)
        handle = self.get_assist_handle()
        for level in levels:
            for time in times:
                for variable in variables:
                    triangle = self.get_triangle(latlon, handle)
                    if triangle.nele < 0: continue
                    value = getattr(self, self.variables[variable])(time=time, element=triangle.nele)
                    json += '%.6f' % value + ','
        if json[-1] == ',':
            json = json[:-1]
        json += ']}}'
        json += ']}'
        return json

class FVCOMSTMStore(TINStore):
    def __init__(self, date, region='BHS'):
        TINStore.__init__(self,date, region)
        regions = {
                            'BHS' : {'extent':[117.541, 23.2132, 131.303, 40.9903], 'resolution':.02, 'maxlevel':10}
                        }
        try:
            self.region = region
            self.date = str(date.year) + date.strftime("%m%d")
            self.extent = Extent.from_tuple(regions[region]['extent'])
            self.resolution = regions[region]['resolution']
            self.maxlevel = regions[region]['maxlevel']
            subdir = 'FVCOM_stm'
            regiondir = region
            if regiondir == 'QDSEA':
                regiondir = 'QDsea'
            subnames = [subdir, regiondir, self.date + '0000UTC', '072', '1hr']
            filename = '_'.join(subnames)
            self.ncfs = os.path.join(os.environ['NC_PATH'], subdir, filename)
            self.shpfs = os.path.join(os.environ['NC_PATH'], subdir, region)
            self.init()
        except Exception, e:
            print e.__str__()

class FVCOMTIDStore(TINStore):
    def __init__(self, date, region='DLW'):
        TINStore.__init__(self,date, region)
        regions = {
                            'QDSEA' : {'extent':[119.174, 34.2846, 122., 36.8493], 'resolution':.01, 'maxlevel':12},
                            'DLW' : {'extent':[103.8, 14.5, 140.4, 48.58], 'resolution':.01, 'maxlevel':12},
                            'RZG' : {'extent':[103.8, 14.5, 140.4, 48.58], 'resolution':.01, 'maxlevel':12},
                            'SD' : {'extent':[103.8, 14.5, 140.4, 48.58], 'resolution':.01, 'maxlevel':12},
                        }
        try:
            self.region = region
            self.date = str(date.year) + date.strftime("%m%d")
            self.extent = Extent.from_tuple(regions[region]['extent'])
            self.resolution = regions[region]['resolution']
            self.maxlevel = regions[region]['maxlevel']
            subdir = 'FVCOM_tid'
            regiondir = region
            subnames = ['FVCOM_crt', regiondir, self.date + '0000UTC', '072', '1hr']
            filename = '_'.join(subnames)
            self.ncfs = os.path.join(os.environ['NC_PATH'], subdir, filename)
            self.shpfs = os.path.join(os.environ['NC_PATH'], subdir, region)
            self.init()
        except Exception, e:
            print e.__str__()

class GridStore(NCStore):
    '''格网存储类'''

    def __init__(self, date, region):
        pass

    def init(self):
        if not os.path.isdir(self.ncfs):
            os.mkdir(self.ncfs)
        ncfile = self.ncfs + '.nc'
        self.nc = netCDF4.Dataset(ncfile, 'r')
        self.cols = len(self.nc.dimensions[self.dimensions['lon']])-1
        self.rows = len(self.nc.dimensions[self.dimensions['lat']])-1
        self.times = len(self.nc.dimensions[self.dimensions['time']])
        if self.dimensions['level'] is None:
            self.levels = 0
        else:
            self.levels = len(self.nc.dimensions[self.dimensions['level']])
        self.set_filter_extent(self.extent.xmin, self.extent.ymin, self.extent.xmax, self.extent.ymax)
        self.universal_legend = True

    def get_capabilities(self):
        capabilities = {
            "region":self.region,
            "date":self.date,
            "dimensions":self.dimensions,
            "variables":''.jself.variables,
            "default_variables":self.default_variables,
            "extent":str(self.extent),
            "times":self.times,
            "levels":self.levels,
            "resolution":self.resolution,
            "cols":self.cols,
            "rows":self.rows
        }
        return capabilities

    def get_capabilities2(self, variables=None, time=0, level=0):
        if variables == None:
            variables = self.default_scalar
        values = self.get_scalar_values(variables, time, level)
        vmax, vmin, mean, std = NcArrayUtility.get_stats(values)
        capabilities = {
            "variables":','.join(variables),
            "extent":str(self.extent),
            "time":time,
            "level":level,
            "resolution":self.resolution,
            "cols":self.cols,
            "rows":self.rows,
            "max":vmax,
            "min":vmin,
            "mean":mean,
            "std":std
         }
        return capabilities

    def is_valid_params(self, time = None, level = None):
        if time != None:
            if time < 0 or time > self.times - 1:
                return False
        if level != None:
            if self.levels > 0:
                if level < 0 or level > self.levels -1:
                    return False
        return True

    def get_value(self, variable = None, latlon = None, time = 0, level = 0):
        rowcol = None
        if latlon is not None:
            rowcol = self.get_colrow(latlon)
        return self.get_value_direct(variable, rowcol, time, level)

    def get_value_direct(self, variable = None, rowcol = None, time = 0, level = 0):
        if not self.is_valid_rowcol(rowcol):
            return np.nan
        if not self.is_valid_params(time, level):
            return np.nan
        if not (variable in self.variables):
            return np.nan
        value = self.get_variable(variable, rowcol, time, level)
        return value

    def get_variable(self, variable, rowcol, time, level):
        netcdf = self.nc
        variable =  self.variables[variable]
        nodata2nan = lambda x: np.nan if x == self.no_data else float(x)
        if rowcol is not None:
            #if isinstance(self, ROMSStore):
            if self.levels > 0:
                value = netcdf.variables[variable][time][level][rowcol.row][rowcol.col]
            else:
                value = netcdf.variables[variable][time][rowcol.row][rowcol.col]
            value = float(value)
            return nodata2nan(value)
        else:
            #if isinstance(self, ROMSStore):
            if self.levels > 0:
                value = netcdf.variables[variable][time][level]
            else:
                value = netcdf.variables[variable][time]
            # # masked array to nparray
            # if isinstance(value, np.ma.masked_array):
            #     value = value.data
            array_nodata2nan = np.vectorize(nodata2nan, otypes=[np.float])
            return array_nodata2nan(value)

    def get_scalar_values(self, variables=None, time=0, level=0):
        if variables == None:
            variables = self.default_variables
        if isinstance(variables, list):
            values = None
            for var in variables:
                val = self.get_value_direct(var, None, time, level)
                val = val[:self.rows, :self.cols]
                val = pow(val, 2)
                if values is None:
                    values = val
                else:
                    values += val
            values = pow(values, .5)
        else:
            values = self.get_value_direct(variables, None, time, level)
            values = values[:self.rows, :self.cols]
        return values

    def get_scalar_values2(self, variables=None, time=None, level=None):
        levels = self.levels if self.levels > 0 else 1
        times = self.times
        if level is not None:
            levels = [level]
        else:
            levels = range(levels)
        if time is not None:
            times = [time]
        else:
            times = range(times)
        if variables == None:
            variables = self.default_variables
        stack = None
        for level in levels:
            for time in times:
                if isinstance(variables, list):
                    values = None
                    for var in variables:
                        val = self.get_value_direct(var, None, time, level)
                        val = val[:self.rows, :self.cols]
                        val = pow(val, 2)
                        if values is None:
                            values = val
                        else:
                            values += val
                    values = pow(values, .5)
                else:
                    values = self.get_value_direct(variables, None, time, level)
                    values = values[:self.rows, :self.cols]
                if stack is None:
                    stack = values
                else:
                    stack = np.vstack((stack, values))
        return stack

    def get_vector_values(self, variables=None, time=0, level=0):
        if variables == None:
            variables = self.default_variables
        values = []
        if isinstance(variables, list):
            for var in variables:
                val = self.get_value_direct(var, None, time, level)
                val = val[:self.rows, :self.cols]
                values.append(val)
        else:
            val = self.get_value_direct(variables, None, time, level)
            val = val[:self.rows, :self.cols]
            values.append(val)
        return values

    def scalar_to_image(self, variables, time, level, projection):
        if variables == None:
            variables = self.default_scalar
        values = self.get_scalar_values(variables, time, level)
        # vs = NcArrayUtility.get_value_parts(values)
        if not self.universal_legend:
            vs_values = values
        else:
            vs_values = self.get_scalar_values2(variables)
        vs = NcArrayUtility.get_value_parts(vs_values)
        hs = HueGradient.get_hue_parts(vs)

        if projection == LatLonProjection:
            # width = self.cols
            # height = self.rows
            width = self.max_col - self.min_col
            height = self.max_row - self.min_row
            size = (width, height)
            img = Image.new("RGBA", size)
            draw = aggdraw.Draw(img)
            draw.setantialias(True)
            for row in range(height):
                for col in range(width):
                    v = values[row+self.min_row, col+self.min_col]
                    if np.isnan(v):
                        continue
                    h = HueGradient.value_to_hue(v, vs, hs)
                    rgb = ColorModelUtility.hsv2rgb((h, 1., 1.))
                    pen = aggdraw.Pen(tuple(rgb), 1)
                    draw.rectangle((col, height-row, col+1, height-1-row), pen)
            draw.flush()
            del draw
            filename = self.get_scalar_image_filename(variables, time, level, projection)
            img.save(filename, "png")
            return filename
        else:
            # ll_min = LatLon(self.extent.ymin, self.extent.xmin)
            # ll_max = LatLon(ll_min.lat + self.resolution*self.rows, ll_min.lon + self.resolution*self.cols)
            ll_min = LatLon(self.filter_extent.ymin, self.filter_extent.xmin)
            ll_max = LatLon(ll_min.lat + self.resolution*(self.max_row-self.min_row), ll_min.lon + self.resolution*(self.max_col-self.min_col))
            wm_min = WebMercatorProjection.project(ll_min)
            wm_max = WebMercatorProjection.project(ll_max)
            # width = self.cols
            width = self.max_col-self.min_col
            height =int(math.ceil((wm_max.y - wm_min.y)/(wm_max.x-wm_min.x)*width))
            wm_resolution = (wm_max.x-wm_min.x)*1./width
            size = (width, height)
            img = Image.new("RGBA", size)
            draw = aggdraw.Draw(img)
            draw.setantialias(True)
            for row in range(height):
                pt = Point(0, row*wm_resolution+wm_min.y)
                ll = WebMercatorProjection.unproject(pt)
                ll_row = int((ll.lat-ll_min.lat)/self.resolution)
                for col in range(width):
                    v = values[ll_row+self.min_row, col+self.min_col]
                    if np.isnan(v): continue
                    h = HueGradient.value_to_hue(v, vs, hs)
                    if np.isnan(h): continue
                    rgb = ColorModelUtility.hsv2rgb((h, 1., 1.))
                    pen = aggdraw.Pen(tuple(rgb), 1)
                    draw.rectangle((col, height-row, col+1, height-1-row), pen)
            draw.flush()
            del draw
            filename = self.get_scalar_image_filename(variables, time, level, projection)
            img.save(filename, "png")
            return filename

    def scalar_to_isoline(self, variables, time, level):
        from matplotlib import _cntr as cntr
        if variables == None:
            variables = self.default_scalar
        # values = self.get_scalar_values(variables, time, level)
        # vs = NcArrayUtility.get_value_parts(values)
        if not self.universal_legend:
            vs_values = self.get_scalar_values(variables, time, level)
        else:
            vs_values = self.get_scalar_values2(variables)
        vs = NcArrayUtility.get_value_parts(vs_values)
        hs = HueGradient.get_hue_parts(vs)
        value_marks = np.array(NcArrayUtility.get_value_marks(vs, padding=1))
        z = NcArrayUtility.nan2val(values)
        z = np.array(z)
        xmin = self.extent.xmin
        ymin = self.extent.ymin
        resolution = self.resolution
        x,y = np.mgrid[:z.shape[0],:z.shape[1]]
        x = x*resolution + xmin
        y = y*resolution + ymin
        c = cntr.Cntr(x,y,z)
        json = '{"type":"FeatureCollection","features":['
        for mark in value_marks:
            res = c.trace(mark)
            nseg = len(res)//2
            segments,codes = res[:nseg],res[nseg:]
            for segment in segments:
                json += '{"type":"Feature","geometry":'
                json += '{"type":"LineString","coordinates":['
                for point in segment:
                    json += '['+str(point[0])+','+str(point[1])+'],'
                if json[-1] == ',':
                    json = json[:-1]
                json += ']}'
                h = HueGradient.value_to_hue(mark, vs, hs)
                if np.isnan(h):
                    color = '255,255,255'
                else:
                    rgb = ColorModelUtility.hsv2rgb((h, 1., 1.))
                    color = '%d,%d,%d' % tuple(rgb)
                json += ',"properties":{"value":'+str(mark)+', "color":"%s"}' % color
                json += '},'
        if json[-1] == ',':
            json = json[:-1]
        json += ']}'
        return json

    def vector_to_grid_image_tile(self, tilecoord, variables, time, level, projection, postProcess = None):
        imagesize = 256
        v_values = self.get_vector_values(variables, time, level)
        # values = None
        # for val in v_values:
        #     val = pow(val, 2)
        #     if values is None: values = val
        #     else: values += val
        # values = pow(values, .5)
        # vs = NcArrayUtility.get_value_parts(values)
        if not self.universal_legend:
            vs_values = self.get_scalar_values(variables, time, level)
        else:
            vs_values = self.get_scalar_values2(variables)
        vs = NcArrayUtility.get_value_parts(vs_values)
        hs = HueGradient.get_hue_parts(vs)
        size = (imagesize,imagesize)
        img = Image.new("RGBA", size)
        draw = aggdraw.Draw(img)
        draw.setantialias(True)
        it = -1
        for latlon in tilecoord.iter_points(projection):
            it += 1
            values = []
            rowcol = self.get_colrow(latlon)
            if not self.is_valid_rowcol(rowcol): continue
            for i,v in enumerate(variables):
                values.append(v_values[i][rowcol.row, rowcol.col])
            #values = [self.get_value(variable, latlon, time, level) for variable in variables]
            bfilter = self.is_valid_values(values)
            if not bfilter: continue
            if postProcess is not None:
                values = postProcess(values)
            h = HueGradient.value_to_hue(values[0], vs, hs)
            if np.isnan(h): continue
            style = SimpleLineStyle()
            style.color = ColorModelUtility.hsv2rgb((h, 1., 1.))
            symbol = None
            if isinstance(self, WRFStore):
                symbol = WindSymbol(values[0], values[1])
                style.width = 2
            elif isinstance(self, ROMSStore) or isinstance(self, POMStore):
                symbol = ArrowSymbol(values[0], values[1])
                symbol.segment_zoom(vs)
            if symbol is not None:
                gridsize = imagesize/tilecoord.n
                scale = gridsize/2./symbol.size
                symbol.zoom(scale)
                i = it / tilecoord.n
                j = it % tilecoord.n
                pos_x = gridsize*(j + .5)
                pos_y = gridsize*(i + .5)
                symbol.pan(np.array([pos_x, pos_y]))
                symbol.draw_agg(draw, style)
        # save
        draw.flush()
        del draw
        tile = self.get_image_tile_filename(tilecoord, variables, time, level, projection)
        img.save(tile, "png")
        return tile

    def vector_to_grid_json_tile(self, tilecoord, variables, time, level, projection, postProcess = None):
        if variables is None:
            variables = self.default_variables
        json = '{"type":"FeatureCollection","features":['
        for latlon in tilecoord.iter_points(projection):
            values = [self.get_value(variable, latlon, time, level) for variable in variables]
            if not self.is_valid_values(values): continue
            if postProcess is not None:
                values = postProcess(values)
            str_val = ''
            for v in values:
                str_val += "%.2f" % v
                str_val += ','
            if str_val[-1] == ',':
                str_val = str_val[:-1]
            string = '{"type":"Feature","geometry":{"type":"Point","coordinates":[%.4f,%.4f]},"properties": {"value": [%s]}}' % \
                        (latlon.lon, latlon.lat, str_val)
            json += string + ','
        if json[-1] == ',':
            json = json[:-1]
        json += ']}'
        return json

    def get_point_value_json(self, latlon, variables = None, level=None, time=None, postProcess = None):
        if variables is None:
            variables = self.default_variables
        json = '{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[%f,%f]},"properties": {"value": [' % (latlon.lon, latlon.lat)
        values = []
        levels = self.levels if self.levels > 0 else 1
        times = self.times
        if level is not None:
            levels = [level]
        else:
            levels = range(levels)
        if time is not None:
            times = [time]
        else:
            times = range(times)
        for level in levels:
            for time in times:
                for variable in variables:
                    value = self.get_value(variable, latlon, time, level)
                    values.append(value)
                    json += '%.6f' % value + ','
        if json[-1] == ',':
            json = json[:-1]
        json += ']}}'
        json += ']}'
        return json

class WRFStore(GridStore):
    def __init__(self, date, region = 'NWP'):
        self.no_data = 1e+30
        self.dimensions = {'lon' : 'longitude', 'lat' : 'latitude', 'time':'times', 'level':None}
        self.variables = {'u': 'u10m', 'v': 'v10m', 'slp': 'slp'}
        self.default_variables = ['u', 'v']
        self.default_scalar = ['slp']
        self.default_vector = ['u', 'v']
        regions = {
                            'NWP' : {'extent':[103.8, 14.5, 140.4, 48.58], 'resolution':.12, 'maxlevel':10},
                            'NCS' : {'extent':[116., 28.5, 129., 42.5], 'resolution':.04, 'maxlevel':10},
                            'QDSEA' : {'extent':[119., 35., 121.5, 36.5], 'resolution':.01, 'maxlevel':10},
                        }
        try:
            self.region = region
            self.date = str(date.year) + date.strftime("%m%d")
            self.extent = Extent.from_tuple(regions[region]['extent'])
            self.resolution = regions[region]['resolution']
            self.maxlevel = regions[region]['maxlevel']
            subdir = 'WRF_met'
            regiondir = region
            if regiondir == 'QDSEA':
                regiondir = 'QDsea'
            subnames = [subdir, regiondir, self.date + '12UTC', '084', '1hr']
            filename = '_'.join(subnames)
            self.ncfs = os.path.join(os.environ['NC_PATH'], subdir, filename)
            self.init()
        except Exception, e:
            print e.__str__()

class SWANStore(GridStore):
    def __init__(self, date, region = 'NWP'):
        self.no_data = -9. #-999.0 -> -9.
        self.dimensions = {'lon' : 'longitude', 'lat' : 'latitude', 'time':'time', 'level':None}
        self.variables = {'hs': 'hs', 'tm': 'tm', 'di': 'di'}
        self.default_variables = ['hs']
        self.default_scalar = ['hs']
        self.default_vector = ['hs']
        regions = {
                        'NWP' : {'extent':[105., 15., 140., 47.], 'resolution':.1, 'maxlevel':10},
                        'NCS' : {'extent':[117., 32., 127., 42.], 'resolution':1/30., 'maxlevel':10},
                        'QDSEA' : {'extent':[119.2958, 34.8958, 121.6042, 36.8042], 'resolution':1/120., 'maxlevel':10},
                    }
        try:
            self.region = region
            self.date = str(date.year) + date.strftime("%m%d")
            self.extent = Extent.from_tuple(regions[region]['extent'])
            self.resolution = regions[region]['resolution']
            self.maxlevel = regions[region]['maxlevel']
            subdir = 'SWAN_wav'
            dirmap = {'NWP':'nw', 'NCS':'nchina', 'QDSEA':'qdsea'}
            regiondir = region
            if regiondir == 'QDSEA':
                regiondir = 'QDsea'
            subnames = [subdir, regiondir, self.date + '12UTC', '120', '1hr']
            filename = '_'.join(subnames)
            self.ncfs = os.path.join(os.environ['NC_PATH'], subdir, dirmap[region], filename)
            self.init()
        except Exception, e:
            print e.__str__()

class WW3Store(SWANStore):
    def __init__(self, date, region = 'NWP'):
        self.no_data = -9. #-999.0 -> -9.
        self.dimensions = {'lon' : 'longitude', 'lat' : 'latitude', 'time':'time', 'level':None}
        self.variables = {'hs': 'hs', 'tm': 'tm', 'di': 'di'}
        self.default_variables = ['hs']
        self.default_scalar = ['hs']
        self.default_vector = ['hs']
        regions = {
                        'GLB': {'extent':[105., 15., 140., 47.], 'resolution':.1, 'maxlevel':10},
                        'NWP': {'extent':[105., 15., 140., 47.], 'resolution':.1, 'maxlevel':10},
                    }
        try:
            self.region = region
            self.date = str(date.year) + date.strftime("%m%d")
            self.extent = Extent.from_tuple(regions[region]['extent'])
            self.resolution = regions[region]['resolution']
            self.maxlevel = regions[region]['maxlevel']
            subdir = 'SWAN_wav'
            dirmap = {'GLB':'global', 'NWP':'nww3'}
            regiondir = region
            if regiondir == 'QDSEA':
                regiondir = 'QDsea'
            subnames = ['WW3_wav', regiondir, self.date + 'UTC', '120', '1hr']
            filename = '_'.join(subnames)
            self.ncfs = os.path.join(os.environ['NC_PATH'], subdir, dirmap[region], filename)
            self.init()
        except Exception, e:
            print e.__str__()

class POMStore(GridStore):
    def __init__(self, date, region = 'ECS'):
        self.no_data = 0 #999.0 -> 0
        self.dimensions = {'lon' : 'longitude', 'lat' : 'latitude', 'time':'time', 'level':None}
        self.variables = {'u': 'u', 'v': 'v', 'el': 'el'}
        self.default_variables = ['u', 'v']
        self.default_scalar = ['el']
        self.default_vector = ['u', 'v']
        regions = {
                        'ECS' : {'extent':[117.5, 24.5, 137., 42.], 'resolution':1/30., 'maxlevel':10},
                        'NCS' : {'extent':[117.473, 33.9791, 124.973, 40.9791], 'resolution':1/30., 'maxlevel':10},
                        'BH' : {'extent':[117.5, 37.2, 122., 42.], 'resolution':1/240., 'maxlevel':10},
                    }
        try:
            self.region = region
            self.date = str(date.year) + date.strftime("%m%d")
            self.extent = Extent.from_tuple(regions[region]['extent'])
            self.resolution = regions[region]['resolution']
            self.maxlevel = regions[region]['maxlevel']
            subdir = 'ROMS_cur'
            regiondir = region
            if regiondir == 'QDSEA':
                regiondir = 'QDsea'
            if region == 'ECS':
                subnames = ['POM_crt', regiondir, self.date + '0000BJS', '072', '1hr']
            elif region == 'BH':
                subnames = ['POM_crt', regiondir, self.date + '0000BJS', 'a24', '1hr']
            else:
                subnames = ['POM_cut', regiondir, self.date + '00BJS', '072', '1hr']
            filename = '_'.join(subnames)
            self.ncfs = os.path.join(os.environ['NC_PATH'], subdir, filename)
            self.init()
        except Exception, e:
            print e.__str__()

class ROMSStore(GridStore):
    def __init__(self, date, region = 'NWP'):
        self.no_data = 1e+37
        self.dimensions = {'lon' : 'xi_v', 'lat' : 'eta_u', 'time':'ocean_time', 'level':'s_rho'}
        self.variables = {'u': 'u', 'v': 'v', 'temp':'temp', 'salt':'salt'}
        self.default_variables = ['u', 'v']
        self.default_scalar = ['temp']
        self.default_vector = ['u', 'v']
        regions = {
                        'NWP' : {'extent':[99., -9., 148., 42.], 'resolution':.1, 'maxlevel':10},
                        'NCS' : {'extent':[117.5, 32., 127., 41.], 'resolution':1/30., 'maxlevel':10},
                        'QDSEA' : {'extent':[119., 35., 122., 37.], 'resolution':1/30., 'maxlevel':10},
                    }
        try:
            self.region = region
            self.date = str(date.year) + date.strftime("%m%d")
            self.extent = Extent.from_tuple(regions[region]['extent'])
            self.resolution = regions[region]['resolution']
            self.maxlevel = regions[region]['maxlevel']
            subdir = 'ROMS_cur'
            regiondir = region
            if regiondir == 'QDSEA':
                regiondir = 'QDsea'
            #subnames = ['ROMS_crt', regiondir, self.date + '0000BJS', '072', '1hr']
            subnames = [subdir, regiondir, self.date + '00BJS', 'a24', '1hr']
            filename = '_'.join(subnames)
            self.ncfs = os.path.join(os.environ['NC_PATH'], subdir, filename)
            self.init()
        except Exception, e:
            print e.__str__()


