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

from oceantile import *
from oceanmarker import *

option_parser = OptionParser()
# option_parser.add_option('--cache', action='store_true')
option_parser.add_option('--debug', action='store_true', default=False)
option_parser.add_option('--host', default='0.0.0.0', metavar='HOST')
option_parser.add_option('--port', default=8080, metavar='PORT', type=int)
option_parser.add_option('--quiet', action='store_true', default=False)
option_parser.add_option('--server', metavar='SERVER')
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

@bottle.route('/v0/markers/<name>/<value:float>/<angle:float>/<size:int>.png', method=['GET', 'POST'])
def markers(name, value, angle, size):
    name = name.lower()
    name = name[0:1].upper() + name[1:]
    marker = globals()[name+'Marker'](value, angle, size)
    img = Image.new("RGBA", (size, size))
    draw = aggdraw.Draw(img)
    marker.draw_agg(draw)
    del draw
    img_io = StringIO.StringIO()
    img.save(img_io, 'png')
    bottle.response.content_type = 'image/png'
    bottle.response.set_header('Content-Encoding', 'utf-8')
    bottle.response.set_header('Access-Control-Allow-Origin', '*')
    bottle.response.content_length = len(img_io.getvalue())
    return img_io.getvalue()

@bottle.route('/v0/legends/<name>/<value:float>/<angle:float>/<size:int>.png', method=['GET', 'POST'])
def legends(name, value, angle, size):
    name = name.lower()
    name = name[0:1].upper() + name[1:]
    marker = globals()[name+'Marker'](value, angle, size)
    img = Image.new("RGBA", (size, size))
    draw = aggdraw.Draw(img)
    marker.draw_agg(draw)
    del draw
    img_io = StringIO.StringIO()
    img.save(img_io, 'png')
    bottle.response.content_type = 'image/png'
    bottle.response.set_header('Content-Encoding', 'utf-8')
    bottle.response.set_header('Access-Control-Allow-Origin', '*')
    bottle.response.content_length = len(img_io.getvalue())
    return img_io.getvalue()

@bottle.route('/v0/point/<resource>/<region>/<lat:float>,<lon:float>/', method=['GET', 'POST'])
def point(resource, region, lat, lon):
    work_directory = '../BeihaiModel_out20130917'
    d = datetime.date.today()
    region = region.upper()
    resource = resource.upper()
    # for test
    if resource == 'WRF':
        d = datetime.date(2013,7,2)
    elif resource == 'SWAN':
        d = datetime.date(2013,9,12)
    elif resource == 'WWIII':
        d = datetime.date(2013,9,12)
    elif resource == 'POM':
        d = datetime.date(2013,9,13)
    elif resource == 'ROMS':
        d = datetime.date(2013,9,13)
    else:
        pass
    func_output_filter = uv2va
    n = 8
    if resource in ['SWAN', 'WWIII']:
        n = 16
    file_path = os.path.join(work_directory, resource, region)
    ncfile = os.path.join(file_path, str(d.year) + d.strftime("%m%d") + ".nc")
    store = globals()[resource+'Store'](ncfile, region)
    json = '{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[%f,%f]},"properties": {"value": [' % (lon, lat)
    for time in range(store.times):
        json += str(func_output_filter(store.get_value(LatLon(lat, lon), time))) + ','
    if json[-1] == ',':
        json = json[:-1]
    json += ']}}'
    json += ']}'

    bottle.response.content_type = 'text/json'
    bottle.response.set_header('Content-Encoding', 'utf-8')
    bottle.response.set_header('Access-Control-Allow-Origin', '*')
    bottle.response.content_length = len(json)
    return json

@bottle.route('/v0/tiles/<projection>/<resource>/<region>/<time:int>/<z:int>/<y:int>/<x:int>.json', method=['GET', 'POST'])
def tiles(projection, resource, region, time, z, y, x):
    work_directory = '../BeihaiModel_out20130917'
    d = datetime.date.today()
    region = region.upper()
    resource = resource.upper()
    if projection.lower() == 'latlon':
        map_projection = LatLonProjection
    else:
        map_projection = WebMercatorProjection
    # for test
    if resource == 'WRF':
        d = datetime.date(2013,7,2)
    elif resource == 'SWAN':
        d = datetime.date(2013,9,12)
    elif resource == 'WWIII':
        d = datetime.date(2013,9,12)
    elif resource == 'POM':
        d = datetime.date(2013,9,13)
    elif resource == 'ROMS':
        d = datetime.date(2013,9,13)
    else:
        pass
    func_output_filter = uv2va
    n = 8
    if resource in ['SWAN', 'WWIII']:
        n = 16
    file_path = os.path.join(work_directory, resource, region)
    ncfile = os.path.join(file_path, str(d.year) + d.strftime("%m%d") + ".nc")
    store = globals()[resource+'Store'](ncfile, region)
    tilecoord = TileCoord(z, y, x, n)
    json = '{"type":"FeatureCollection","features":['
    for latlon in tilecoord.iter_points(map_projection):
        values = store.get_value(latlon, time)
        if math.isnan(values[0]):
            continue
        atrributes = func_output_filter(values)
        if resource in ['SWAN', 'WWIII']:
            string = '{"type":"Feature","geometry":{"type":"Point","coordinates":[%.4f,%.4f]},"properties": {"value": "%.1f"}}' % \
                    (latlon.lon, latlon.lat, atrributes[0])
        else:
            string = '{"type":"Feature","geometry":{"type":"Point","coordinates":[%.4f,%.4f]},"properties": {"value": "%.1f", "angle":"%.1f"}}' % \
                    (latlon.lon, latlon.lat, atrributes[0], atrributes[1])
        json += string + ','
    if json[-1] == ',':
        json = json[:-1]
    json += ']}'

    bottle.response.content_type = 'text/json'
    bottle.response.set_header('Content-Encoding', 'utf-8')
    bottle.response.set_header('Access-Control-Allow-Origin', '*')
    bottle.response.content_length = len(json)
    return json

@bottle.route('/v0/tiles/<projection>/<resource>/<region>/<time:int>/<level:int>/<z:int>/<y:int>/<x:int>.json', method=['GET', 'POST'])
def tiles(projection, resource, region, time, level, z, y, x):
    d = datetime.date.today()
    region = region.upper()
    resource = resource.upper()
    if projection.lower() == 'latlon':
        map_projection = LatLonProjection
    else:
        map_projection = WebMercatorProjection

    # for test
    d = datetime.date(2013,9,13)
    n = 8

    work_directory = '../BeihaiModel_out20130917'
    func_output_filter = uv2va

    file_path = os.path.join(work_directory, resource, region)
    ncfile = os.path.join(file_path, str(d.year) + d.strftime("%m%d") + ".nc")
    store = globals()[resource+'Store'](ncfile, region)
    tilecoord = TileCoord(z, y, x, n)
    json = '{"type":"FeatureCollection","features":['
    for latlon in tilecoord.iter_points(map_projection):
        values = store.get_value(latlon, time, level)
        if math.isnan(values[0]):
            continue
        atrributes = func_output_filter(values)
        string = '{"type":"Feature","geometry":{"type":"Point","coordinates":[%.4f,%.4f]},"properties": {"value": "%.1f", "angle":"%.1f"}}' % \
                    (latlon.lon, latlon.lat, atrributes[0], atrributes[1])
        json += string + ','
    if json[-1] == ',':
        json = json[:-1]
    json += ']}'

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


