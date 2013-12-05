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

from NCStore import *
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

# for test
update = False

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
@bottle.route('/v1/<resource>/<region>/<level:int>/<time:int>/<variables>.json', method=['GET', 'POST'])
def capabilities2(resource, region, time, level, variables):
    import json
    date = datetime.date.today()
    # for test
    date = datetime.date(2013,9,12)
    region = region.upper()
    resource = resource.upper()
    store = globals()[resource+'Store'](date, region)
    variables = store.filter_variables(variables)
    json = json.dumps(store.get_capabilities2(variables, time, level))
    bottle.response.content_type = 'text/json'
    bottle.response.set_header('Content-Encoding', 'utf-8')
    bottle.response.set_header('Access-Control-Allow-Origin', '*')
    bottle.response.content_length = len(json)
    return json

# 动态生成指定尺寸的符号图片
@bottle.route('/v1/markers/<name>/<value:float>/<angle:float>/<size:int>.png', method=['GET', 'POST'])
def markers(name, value, angle, size):
    name = name.lower()
    name = name[0:1].upper() + name[1:]
    symbol = globals()[name+'Symbol'](value, angle)
    symbol.zoom(size/2./symbol.size)
    symbol.pan(np.array([size/2., size/2.]))
    img = Image.new("RGBA", (size, size))
    draw = aggdraw.Draw(img)
    draw.setantialias(True)
    style = SimpleLineStyle()
    symbol.draw_agg(draw, style)
    draw.flush()
    del draw
    img_io = StringIO.StringIO()
    img.save(img_io, 'png')
    bottle.response.content_type = 'image/png'
    bottle.response.set_header('Content-Encoding', 'utf-8')
    bottle.response.set_header('Access-Control-Allow-Origin', '*')
    bottle.response.content_length = len(img_io.getvalue())
    return img_io.getvalue()

# 某nc下固定时间与层次的专题图图例，动态缓存
@bottle.route('/v1/legends/<resource>/<region>/<level:int>/<time:int>/<variables>.png', method=['GET', 'POST'])
def legends(resource, region, time, level, variables):
    date = datetime.date.today()
    # for test
    date = datetime.date(2013,9,12)
    region = region.upper()
    resource = resource.upper()
    store = globals()[resource+'Store'](date, region)
    #defaultVariable = {'WRF':['slp'], 'SWAN':['hs'], 'WW3':['hs'], 'POM':['el'], 'ROMS':['temp'], 'FVCOMSTM':'zeta', 'FVCOMTID':'zeta'}
    variables = store.filter_variables(variables)#, defaultVariable[resource])
    legend = store.get_legend(variables, time, level)
    if legend is None:
        bottle.abort(404)
    with open(legend) as file:
        data = file.read()
        bottle.response.content_type = 'image/png'
        bottle.response.set_header('Access-Control-Allow-Origin', '*')
        bottle.response.content_length = len(data)
        return data

# 查询某点对应的所有时间与层次的值
@bottle.route('/v1/point/<resource>/<region>/<lat:float>,<lon:float>/<variables>.json', method=['GET', 'POST'])
def point(resource, region, lat, lon, variables):
    date = datetime.date.today()
    # for test
    date = datetime.date(2013,9,12)
    region = region.upper()
    resource = resource.upper()
    store = globals()[resource+'Store'](date, region)
    defaultVariable = {'WRF':'slp', 'SWAN':'hs', 'WW3':'hs', 'POM':'el', 'ROMS':'temp', 'FVCOMSTM':'zeta', 'FVCOMTID':'zeta'}
    variables = store.filter_variables(variables, defaultVariable[resource])
    json = store.get_point_value_json(LatLon(lat,lon), variables)

    bottle.response.content_type = 'text/json'
    bottle.response.set_header('Content-Encoding', 'utf-8')
    bottle.response.set_header('Access-Control-Allow-Origin', '*')
    bottle.response.content_length = len(json)
    return json

# 按指定投影根据某几个变量生成分块json文件，动态缓存
@bottle.route('/v1/tiles/<projection>/<resource>/<region>/<level:int>/<time:int>/<z:int>/<y:int>/<x:int>/<variables>.json', method=['GET', 'POST'])
def tiles(projection, resource, region, time, level, z, y, x, variables):
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
    variables = store.filter_variables(variables)
    #json = store.export_tile_json(tilecoord, variables, time, level, projection=projection)
    jsonfile = store.get_json_tile(tilecoord, variables, time, level, projection=projection, postProcess = NcArrayUtility.uv2va, update = update)
    if jsonfile is None:
        bottle.abort(404)
    with open(jsonfile) as file:
        data = file.read()
        bottle.response.content_type = 'text/json'
        bottle.response.set_header('Access-Control-Allow-Origin', '*')
        bottle.response.content_length = len(data)
        return data

# 按指定投影根据某几个变量生成瓦片，动态缓存
@bottle.route('/v1/tiles/<projection>/<resource>/<region>/<level:int>/<time:int>/<z:int>/<y:int>/<x:int>/<variables>.png', method=['GET', 'POST'])
def tiles2(projection, resource, region, time, level, z, y, x, variables):
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
    variables = store.filter_variables(variables)
    image = store.get_image_tile(tilecoord, variables, time, level, projection=projection, postProcess = NcArrayUtility.uv2va, update = update)
    if image is None:
        bottle.abort(404)
    with open(image) as file:
        data = file.read()
        bottle.response.content_type = 'image/png'
        bottle.response.set_header('Access-Control-Allow-Origin', '*')
        bottle.response.content_length = len(data)
        return data

# 按指定投影根据某变量生成专题图，动态缓存
@bottle.route('/v1/images/<projection>/<resource>/<region>/<level:int>/<time:int>/<variables>.png', method=['GET', 'POST'])
def images(projection, resource, region, time, level, variables):
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
    defaultVariable = {'WRF':'slp', 'SWAN':'hs', 'WW3':'hs', 'POM':'el', 'ROMS':'temp', 'FVCOMSTM':'zeta', 'FVCOMTID':'zeta'}
    variables = store.filter_variables(variables, defaultVariable[resource])
    image = store.get_scalar_image(variables, time, level, projection, update = update)
    if image is None:
        bottle.abort(404)
    with open(image) as file:
        data = file.read()
        bottle.response.content_type = 'image/png'
        bottle.response.set_header('Access-Control-Allow-Origin', '*')
        bottle.response.content_length = len(data)
        return data

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


