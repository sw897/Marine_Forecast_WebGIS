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

option_parser = OptionParser()
option_parser.add_option('--debug', action='store_true', default=False)
option_parser.add_option('--host', default='0.0.0.0', metavar='HOST')
option_parser.add_option('--port', default=8080, metavar='PORT', type=int)
option_parser.add_option('--quiet', action='store_true', default=False)
option_parser.add_option('--server', metavar='SERVER')
option_parser.add_option('--update', action='store_true', default=False)
options, args = option_parser.parse_args(sys.argv[1:])

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

update = False
if options.update:
    update = True
# put NC_PATH enviorment
os.environ['NC_PATH'] = '/data/data/BeihaiModel_out'
# for SD App
SD_App = False
SD_Extent = [117.5,35,123.5,38.5]

# 获取指定nc的元数据
@bottle.route('/v1/capabilities/<model>/<region>.json', method=['GET', 'POST'])
def capabilities(model, region):
    import json
    datestring = bottle.request.query.date
    if datestring is None or len(datestring) < 8:
        date = datetime.date.today()
    else:
        year = int(datestring[:4])
        month = int(datestring[4:6])
        day = int(datestring[6:8])
        date = datetime.date(year,month,day)
    region = region.upper()
    model = model.upper()
    store = globals()[model+'Store'](date, region)
    json = json.dumps(store.get_capabilities())
    bottle.response.content_type = 'text/json'
    bottle.response.set_header('Content-Encoding', 'utf-8')
    bottle.response.set_header('Access-Control-Allow-Origin', '*')
    bottle.response.content_length = len(json)
    return json

# 获取指定nc中固定时间与层次的元数据，包括max,min,std等统计信息
@bottle.route('/v1/capabilities/<model>/<region>/<level:int>/<time:int>/<variables>.json', method=['GET', 'POST'])
def capabilities2(model, region, time, level, variables):
    import json
    datestring = bottle.request.query.date
    if datestring is None or len(datestring) < 8:
        date = datetime.date.today()
    else:
        year = int(datestring[:4])
        month = int(datestring[4:6])
        day = int(datestring[6:8])
        date = datetime.date(year,month,day)
    region = region.upper()
    model = model.upper()
    store = globals()[model+'Store'](date, region)
    variables = store.filter_variables(variables)
    json = json.dumps(store.get_capabilities2(variables, time, level))
    bottle.response.content_type = 'text/json'
    bottle.response.set_header('Content-Encoding', 'utf-8')
    bottle.response.set_header('Access-Control-Allow-Origin', '*')
    bottle.response.content_length = len(json)
    return json

# 获取指定nc,指定专题化方法的缩略图
@bottle.route('/v1/thumbnails/<model>/<region>/<method>.jpg', method=['GET', 'POST'])
def thumbnails(model, region, method):
    region = region.upper()
    model = model.upper()
    method = method.upper()
    thumbnail = NCThumbnail(model, region, method)
    if thumbnail is None:
        bottle.abort(404)
    with open(thumbnail) as file:
        data = file.read()
        bottle.response.content_type = 'image/jpeg'
        bottle.response.set_header('Access-Control-Allow-Origin', '*')
        bottle.response.content_length = len(data)
        return data

# 动态生成指定尺寸的符号图片
@bottle.route('/v1/marker/<name>/<value:float>/<angle:float>/<size:int>.png', method=['GET', 'POST'])
def marker(name, value, angle, size):
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
@bottle.route('/v1/legends/<model>/<region>/<level:int>/<time:int>/<variables>.png', method=['GET', 'POST'])
def legends(model, region, time, level, variables):
    datestring = bottle.request.query.date
    if datestring is None or len(datestring) < 8:
        date = datetime.date.today()
    else:
        year = int(datestring[:4])
        month = int(datestring[4:6])
        day = int(datestring[6:8])
        date = datetime.date(year,month,day)
    region = region.upper()
    model = model.upper()
    store = globals()[model+'Store'](date, region)
    #defaultVariable = {'WRF':['slp'], 'SWAN':['hs'], 'WW3':['hs'], 'POM':['el'], 'ROMS':['temp'], 'FVCOMSTM':'zeta', 'FVCOMTID':'zeta'}
    variables = store.filter_variables(variables)#, defaultVariable[model])
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
@bottle.route('/v1/pointquery/<model>/<region>/<lat:float>,<lon:float>/<variables>.geojson', method=['GET', 'POST'])
def pointquery(model, region, lat, lon, variables):
    datestring = bottle.request.query.date
    if datestring is None or len(datestring) < 8:
        date = datetime.date.today()
    else:
        year = int(datestring[:4])
        month = int(datestring[4:6])
        day = int(datestring[6:8])
        date = datetime.date(year,month,day)
    region = region.upper()
    model = model.upper()
    store = globals()[model+'Store'](date, region)
    if SD_App and model != 'WRF':
        store.set_filter_extent(*SD_Extent)
    defaultVariable = {'WRF':'slp', 'SWAN':'hs', 'WW3':'hs', 'POM':'el', 'ROMS':'temp', 'FVCOMSTM':'zeta', 'FVCOMTID':'zeta'}
    variables = store.filter_variables(variables, defaultVariable[model])
    json = store.get_point_value_json(LatLon(lat,lon), variables)

    bottle.response.content_type = 'text/json'
    bottle.response.set_header('Content-Encoding', 'utf-8')
    bottle.response.set_header('Access-Control-Allow-Origin', '*')
    bottle.response.content_length = len(json)
    return json

# 按指定投影根据某几个变量生成分块geojson文件，动态缓存
@bottle.route('/v1/tiles/<projection>/<model>/<region>/<level:int>/<time:int>/<z:int>/<y:int>/<x:int>/<variables>.geojson', method=['GET', 'POST'])
def tiles(projection, model, region, time, level, z, y, x, variables):
    datestring = bottle.request.query.date
    if datestring is None or len(datestring) < 8:
        date = datetime.date.today()
    else:
        year = int(datestring[:4])
        month = int(datestring[4:6])
        day = int(datestring[6:8])
        date = datetime.date(year,month,day)
    region = region.upper()
    model = model.upper()
    store = globals()[model+'Store'](date, region)
    if SD_App and model != 'WRF':
        store.set_filter_extent(*SD_Extent)
    if projection.lower() == 'latlon':
        projection = LatLonProjection
    else:
        projection = WebMercatorProjection
    tilecoord = TileCoord(z, y, x)
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
@bottle.route('/v1/tiles/<projection>/<model>/<region>/<level:int>/<time:int>/<z:int>/<y:int>/<x:int>/<variables>.png', method=['GET', 'POST'])
def tiles2(projection, model, region, time, level, z, y, x, variables):
    datestring = bottle.request.query.date
    if datestring is None or len(datestring) < 8:
        date = datetime.date.today()
    else:
        year = int(datestring[:4])
        month = int(datestring[4:6])
        day = int(datestring[6:8])
        date = datetime.date(year,month,day)
    region = region.upper()
    model = model.upper()
    store = globals()[model+'Store'](date, region)
    if SD_App and model != 'WRF':
        store.set_filter_extent(*SD_Extent)
    if projection.lower() == 'latlon':
        projection = LatLonProjection
    else:
        projection = WebMercatorProjection
    tilecoord = TileCoord(z, y, x)
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
@bottle.route('/v1/images/<projection>/<model>/<region>/<level:int>/<time:int>/<variables>.png', method=['GET', 'POST'])
def images(projection, model, region, time, level, variables):
    datestring = bottle.request.query.date
    if datestring is None or len(datestring) < 8:
        date = datetime.date.today()
    else:
        year = int(datestring[:4])
        month = int(datestring[4:6])
        day = int(datestring[6:8])
        date = datetime.date(year,month,day)
    region = region.upper()
    model = model.upper()
    store = globals()[model+'Store'](date, region)
    if SD_App and model != 'WRF':
        store.set_filter_extent(*SD_Extent)
    if projection.lower() == 'latlon':
        projection = LatLonProjection
    else:
        projection = WebMercatorProjection
    defaultVariable = {'WRF':'slp', 'SWAN':'hs', 'WW3':'hs', 'POM':'el', 'ROMS':'temp', 'FVCOMSTM':'zeta', 'FVCOMTID':'zeta'}
    variables = store.filter_variables(variables, defaultVariable[model])
    image = store.get_scalar_image(variables, time, level, projection, update = update)
    if image is None:
        bottle.abort(404)
    with open(image) as file:
        data = file.read()
        bottle.response.content_type = 'image/png'
        bottle.response.set_header('Access-Control-Allow-Origin', '*')
        bottle.response.content_length = len(data)
        return data

# 根据某变量生成等值线,以geojson返回，动态缓存
@bottle.route('/v1/isolines/<model>/<region>/<level:int>/<time:int>/<variables>.geojson', method=['GET', 'POST'])
def isolines(model, region, time, level, variables):
    datestring = bottle.request.query.date
    if datestring is None or len(datestring) < 8:
        date = datetime.date.today()
    else:
        year = int(datestring[:4])
        month = int(datestring[4:6])
        day = int(datestring[6:8])
        date = datetime.date(year,month,day)
    region = region.upper()
    model = model.upper()
    store = globals()[model+'Store'](date, region)
    if SD_App and model != 'WRF':
        store.set_filter_extent(*SD_Extent)
    defaultVariable = {'WRF':'slp', 'SWAN':'hs', 'WW3':'hs', 'POM':'el', 'ROMS':'temp', 'FVCOMSTM':'zeta', 'FVCOMTID':'zeta'}
    variables = store.filter_variables(variables, defaultVariable[model])
    jsonfile = store.get_scalar_isoline(variables, time, level, update = update)
    if jsonfile is None:
        bottle.abort(404)
    with open(jsonfile) as file:
        data = file.read()
        bottle.response.content_type = 'text/json'
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


