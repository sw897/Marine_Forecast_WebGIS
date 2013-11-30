import sys
from NCStore import *
from optparse import OptionParser

option_parser = OptionParser()
option_parser.add_option('--update', default=False)
options, args = option_parser.parse_args(sys.argv[1:])

def scalar2image(date, resource, region, variable, projection=WebMercatorProjection, update=False):
    store = globals()[resource+'Store'](date, region)
    for time in range(store.times):
        for level in range(store.levels):
            store.get_scalar_image(variable, time, level, projection, update)

def vector2jsontiles(date, resource, region, variables=None, projection=WebMercatorProjection, update=False):
    store = globals()[resource+'Store'](date, region)
    zs = [2,3,4,5,6,7,8,9]
    for time in range(store.times):
        for level in range(store.levels):
            for z in zs:
                store.export_to_jsontiles(z, None, time, level, projection, NcArrayUtility.uv2va, update)

def vector2imagetiles(date, resource, region, variables=None, projection=WebMercatorProjection, update=False):
    store = globals()[resource+'Store'](date, region)
    zs = [2,3,4,5,6,7,8,9]
    for time in range(store.times):
        for level in range(store.levels):
            for z in zs:
                store.export_to_imagetiles(z, None, time, level, projection, NcArrayUtility.uv2va, update)

if __name__ == '__main__':
    projection = WebMercatorProjection
    date = datetime.date.today()
    date = datetime.date(2013,9,12)
    os.environ['NC_PATH'] = '/Users/sw/github/Marine_Forecast_WebGIS/BeihaiModel_out'

    resource = 'SWAN'
    regions = ['NWP', 'NCS', 'QDSEA']
    for region in regions:
        scalar2image(date, resource, region, ['hs'], projection)

    resource = 'WRF'
    regions = ['NWP', 'NCS', 'QDSEA']
    for region in regions:
        vector2imagetiles(date, resource, region, projection=projection, update = options.update)

    resource = 'POM'
    regions = ['ECS', 'BH']
    for region in regions:
        vector2imagetiles(date, resource, region, projection=projection, update = options.update)

    resource = 'ROMS'
    regions = ['NCS', 'QDSEA']
    for region in regions:
        vector2imagetiles(date, resource, region, projection=projection, update = options.update)
