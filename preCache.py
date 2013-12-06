import sys
from NCStore import *
from optparse import OptionParser
import datetime

option_parser = OptionParser()
option_parser.add_option('--update', default=False)
options, args = option_parser.parse_args(sys.argv[1:])

def scalar2image(date, resource, region, variable, projection=WebMercatorProjection, update=False):
    store = globals()[resource+'Store'](date, region)
    levels = store.levels if store.levels > 0 else 1
    for level in range(levels):
        for time in range(store.times):
            store.get_scalar_image(variable, time, level, projection, update)
        print("scalar2image %s %s time:%d level:%s over" % (resource,region, time, level))

def vector2jsontiles(date, resource, region, variables=None, projection=WebMercatorProjection, update=False):
    store = globals()[resource+'Store'](date, region)
    zs = [2,3,4,5,6,7,8,9]
    levels = store.levels if store.levels > 0 else 1
    for level in range(levels):
        for time in range(store.times):
            for z in zs:
                store.export_to_json_tiles(z, None, time, level, projection, NcArrayUtility.uv2va, update)
            # for test
            break
        print("vector2jsontiles %s %s time:%d level:%s over" % (resource,region, time, level))
        break

def vector2imagetiles(date, resource, region, variables=None, projection=WebMercatorProjection, update=False):
    store = globals()[resource+'Store'](date, region)
    zs = [2,3,4,5,6,7,8,9]
    levels = store.levels if store.levels > 0 else 1
    for level in range(levels):
        for time in range(store.times):
            for z in zs:
                store.export_to_image_tiles(z, None, time, level, projection, NcArrayUtility.uv2va, update)
            # for test
            break
        print("vector2imagetiles %s %s time:%d level:%s over" % (resource,region, time, level))
        break

if __name__ == '__main__':
    projection = WebMercatorProjection
    date = datetime.date.today()
    date = datetime.date(2013,9,12)
    os.environ['NC_PATH'] = '/Users/sw/github/Marine_Forecast_WebGIS/BeihaiModel_out'

    d1 = datetime.datetime.now()
    print d1
    resource = 'FVCOMSTM'
    regions = ['BHS', 'QDSEA']
    for region in regions:
        vector2imagetiles(date, resource, region, projection=projection, update = options.update)
        vector2jsontiles(date, resource, region, projection=projection, update = options.update)
        scalar2image(date, resource, region, None, projection, update = options.update)

    resource = 'SWAN'
    regions = ['NWP', 'NCS', 'QDSEA']
    for region in regions:
        scalar2image(date, resource, region, ['hs'], projection, update = options.update)

    resource = 'WRF'
    regions = ['NWP', 'NCS', 'QDSEA']
    for region in regions:
        vector2imagetiles(date, resource, region, projection=projection, update = options.update)
        vector2jsontiles(date, resource, region, projection=projection, update = options.update)
        scalar2image(date, resource, region, ['slp'], projection, update = options.update)

    resource = 'POM'
    regions = ['ECS', 'BH']
    for region in regions:
        vector2imagetiles(date, resource, region, projection=projection, update = options.update)
        vector2jsontiles(date, resource, region, projection=projection, update = options.update)
        scalar2image(date, resource, region, ['el'], projection=projection, update = options.update)

    resource = 'ROMS'
    regions = ['NCS', 'QDSEA']
    for region in regions:
        vector2imagetiles(date, resource, region, projection=projection, update = options.update)
        vector2jsontiles(date, resource, region, projection=projection, update = options.update)
    d2 = datetime.datetime.now()
    print d2
