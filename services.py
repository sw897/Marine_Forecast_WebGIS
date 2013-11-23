#!/usr/bin/env python
# -*- coding: utf-8 -*-

from optparse import OptionParser
import os
import bottle
#from daemon import Daemon
import customencoding
import math
import sys
import datetime
import StringIO

from pyncstore import *
# from pyncmarker import *

option_parser = OptionParser()
# option_parser.add_option('--cache', action='store_true')
option_parser.add_option('--debug', action='store_true', default=False)
option_parser.add_option('--host', default='0.0.0.0', metavar='HOST')
option_parser.add_option('--port', default=8080, metavar='PORT', type=int)
option_parser.add_option('--quiet', action='store_true', default=False)
option_parser.add_option('--server', metavar='SERVER')
options, args = option_parser.parse_args(sys.argv[1:])

# put NC_PATH enviorment
os.environ['NC_PATH'] = '/Users/sw/github/Marine_Forecast_WebGIS/BeihaiModel_out'

if options.debug:
    bottle.DEBUG = True
if options.server is None:
    try:
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop
        options.server = 'tornado'
        id(tornado)  # Suppress pyflakes warning 'tornado' imported but unused
    except ImportError:
        options.server = 'wsgiref'

#content_type_adder = ContentTypeAdder()

# @bottle.route('/v0/markers/<name>/<value:float>/<angle:float>/<size:int>.png', method=['GET', 'POST'])
# def markers(name, value, angle, size):
#     name = name.lower()
#     name = name[0:1].upper() + name[1:]
#     marker = globals()[name+'Marker'](value, angle, size)
#     img = Image.new("RGBA", (size, size))
#     draw = aggdraw.Draw(img)
#     marker.draw_agg(draw)
#     del draw
#     img_io = StringIO.StringIO()
#     img.save(img_io, 'png')
#     bottle.response.content_type = 'image/png'
#     bottle.response.set_header('Content-Encoding', 'utf-8')
#     bottle.response.set_header('Access-Control-Allow-Origin', '*')
#     bottle.response.content_length = len(img_io.getvalue())
#     return img_io.getvalue()

# 某nc下固定时间与层次的专题图图例，动态缓存
@bottle.route('/v1/legends/<resource>/<region>/<level:int>/<time:int>/<variable>.png', method=['GET', 'POST'])
def legends(resource, region, time, level, variable):
    date = datetime.date.today()
    # for test
    date = datetime.date(2013,9,12)
    region = region.upper()
    resource = resource.upper()
    store = globals()[resource+'Store'](date, region)
    defaultVariable = {'WRF':'slp', 'SWAN':'hs', 'WW3':'hs', 'POM':'el', 'ROMS':'temp'}
    if variable == 'default':
        variable = defaultVariable[resource]
    legend = store.get_legend(variable, time, level)
    if legend is None:
        bottle.abort(404)
    with open(legend) as file:
        data = file.read()
        bottle.response.content_type = 'image/png'
        bottle.response.set_header('Access-Control-Allow-Origin', '*')
        bottle.response.content_length = len(data)
        return data

# 查询某点对应的所有时间与层次的值
@bottle.route('/v1/point/<resource>/<region>/<lat:float>,<lon:float>/', method=['GET', 'POST'])
def point(resource, region, lat, lon):
    date = datetime.date.today()
    # for test
    date = datetime.date(2013,9,12)
    region = region.upper()
    resource = resource.upper()
    store = globals()[resource+'Store'](date, region)
    defaultVariable = {'WRF':'slp', 'SWAN':'hs', 'WW3':'hs', 'POM':'el', 'ROMS':'temp'}
    variable = defaultVariable[resource]
    json = store.export_point_json(LatLon(lat,lon), variable)

    bottle.response.content_type = 'text/json'
    bottle.response.set_header('Content-Encoding', 'utf-8')
    bottle.response.set_header('Access-Control-Allow-Origin', '*')
    bottle.response.content_length = len(json)
    return json

# 按指定投影根据某几个变量生成分块json文件，动态缓存
@bottle.route('/v1/tiles/<projection>/<resource>/<region>/<level:int>/<time:int>/<z:int>/<y:int>/<x:int>.json', method=['GET', 'POST'])
def tiles(projection, resource, region, time, level, z, y, x):
    date = datetime.date.today()
    # for test
    date = datetime.date(2013,9,12)
    region = region.upper()
    resource = resource.upper()
    store = globals()[resource+'Store'](date, region)
    if projection.lower() == 'latlon':
        projection = LatLonProjection
    else:
        projection = WebMercatorProjection
    n = 8
    if resource in ['SWAN', 'WW3']:
        n = 16
    tilecoord = TileCoord(z, y, x, n)
    #json = store.export_tile_json(tilecoord, None, time, level, projection=projection)
    jsonfile = store.get_tile_json(tilecoord, None, time, level, projection=projection)
    if jsonfile is None:
        bottle.abort(404)
    with open(jsonfile) as file:
        data = file.read()
        bottle.response.content_type = 'text/json'
        bottle.response.set_header('Access-Control-Allow-Origin', '*')
        bottle.response.content_length = len(data)
        return data

# 按指定投影根据某几个变量生成分块图片，动态缓存
@bottle.route('/v1/tiles/<projection>/<resource>/<region>/<level:int>/<time:int>/<z:int>/<y:int>/<x:int>.png', method=['GET', 'POST'])
def tiles2(projection, resource, region, time, level, z, y, x):
    date = datetime.date.today()
    # for test
    date = datetime.date(2013,9,12)
    region = region.upper()
    resource = resource.upper()
    store = globals()[resource+'Store'](date, region)
    if projection.lower() == 'latlon':
        projection = LatLonProjection
    else:
        projection = WebMercatorProjection
    n = 8
    if resource in ['SWAN', 'WW3']:
        n = 16
    tilecoord = TileCoord(z, y, x, n)
    image = store.get_tile_image(tilecoord, None, time, level, projection=projection)
    if image is None:
        bottle.abort(404)
    with open(image) as file:
        data = file.read()
        bottle.response.content_type = 'image/png'
        bottle.response.set_header('Access-Control-Allow-Origin', '*')
        bottle.response.content_length = len(data)
        return data

# 按指定投影根据某变量生成专题图，动态缓存
@bottle.route('/v1/images/<projection>/<resource>/<region>/<level:int>/<time:int>/<variable>.png', method=['GET', 'POST'])
def images(projection, resource, region, time, level, variable):
    date = datetime.date.today()
    # for test
    date = datetime.date(2013,9,12)
    region = region.upper()
    resource = resource.upper()
    store = globals()[resource+'Store'](date, region)
    if projection.lower() == 'latlon':
        projection = LatLonProjection
    else:
        projection = WebMercatorProjection
    if variable == 'default':
        variable = store.default_variables[0]
    image = store.get_variable_image(variable, time, level, projection)
    if image is None:
        bottle.abort(404)
    with open(image) as file:
        data = file.read()
        bottle.response.content_type = 'image/png'
        bottle.response.set_header('Access-Control-Allow-Origin', '*')
        bottle.response.content_length = len(data)
        return data

# 获取指定nc的元数据
@bottle.route('/v1/<resource>/<region>.json', method=['GET', 'POST'])
def capabilities(resource, region):
    import json
    date = datetime.date.today()
    # for test
    date = datetime.date(2013,9,12)
    region = region.upper()
    resource = resource.upper()
    store = globals()[resource+'Store'](date, region)
    json = json.dumps(store.get_capabilities())
    bottle.response.content_type = 'text/json'
    bottle.response.set_header('Content-Encoding', 'utf-8')
    bottle.response.set_header('Access-Control-Allow-Origin', '*')
    bottle.response.content_length = len(json)
    return json

# 获取指定nc中固定时间与层次的元数据，包括max,min等统计信息
@bottle.route('/v1/<resource>/<region>/<level:int>/<time:int>/<variable>.json', method=['GET', 'POST'])
def capabilities2(resource, region, time, level, variable):
    import json
    date = datetime.date.today()
    # for test
    date = datetime.date(2013,9,12)
    region = region.upper()
    resource = resource.upper()
    store = globals()[resource+'Store'](date, region)
    if variable == 'default':
        variable = store.default_variables
    json = json.dumps(store.get_capabilities2(variable, time, level))
    bottle.response.content_type = 'text/json'
    bottle.response.set_header('Content-Encoding', 'utf-8')
    bottle.response.set_header('Access-Control-Allow-Origin', '*')
    bottle.response.content_length = len(json)
    return json

# static route
@bottle.route('/favicon.ico')
def favicon():
    return bottle.static_file('favicon.ico', root='static')


@bottle.route('/static/<path:re:.*>')
def static(path):
    return bottle.static_file(path, root='static')


@bottle.error(404)
def error404(error):
    return 'nothing here'


if __name__ == '__main__':
    bottle.run(host=options.host, port=options.port, reloader=options.debug,
               quiet=options.quiet, server=options.server)


