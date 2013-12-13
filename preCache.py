import sys
from NCStore import *
from optparse import OptionParser
import datetime

# do not use multiprocessing on windows, it blows
if sys.platform == 'win32':
    import Queue
    import threading
    proc_class = threading.Thread
    queue_class = Queue.Queue
else:
    import multiprocessing
    proc_class = multiprocessing.Process
    queue_class = multiprocessing.Queue


def initProc():
    proc_class.__init__(self)
    proc_class.daemon = True



option_parser = OptionParser()
option_parser.add_option('--update', default=False)
options, args = option_parser.parse_args(sys.argv[1:])

update = False
if options.update:
    update = True

def scalar2image(date, resource, region, variable, projection=WebMercatorProjection, update=False):
    store = globals()[resource+'Store'](date, region)
    store.set_filter_extent(117.5,35,123.5,38.5)
    levels = store.levels if store.levels > 0 else 1
    for level in range(levels-1, -1, -1):
        for time in range(store.times):
            store.get_scalar_image(variable, time, level, projection, update)
            store.get_legend(variable, time, level, update)

def vector2jsontiles(date, resource, region, variables=None, projection=WebMercatorProjection, update=False):
    store = globals()[resource+'Store'](date, region)
    levels = store.levels if store.levels > 0 else 1
    for level in range(levels):
        for time in range(store.times):
            for z in range(1, store.maxlevel):
                store.export_to_json_tiles(z, None, time, level, projection, NcArrayUtility.uv2va, update)
            # for test
            break
        print("vector2jsontiles %s %s time:%d level:%s over" % (resource,region, time, level))
        break

def vector2imagetiles(date, resource, region, variables=None, projection=WebMercatorProjection, update=False):
    store = globals()[resource+'Store'](date, region)
    levels = store.levels if store.levels > 0 else 1
    for level in range(levels):
        for time in range(store.times):
            for z in range(1, store.maxlevel):
                store.export_to_image_tiles(z, None, time, level, projection, NcArrayUtility.uv2va, update)
            # for test
            # break
            print("vector2imagetiles %s %s time:%d level:%s over" % (resource,region, time, level))
            dd = datetime.datetime.now()
            print dd
        # break

if __name__ == '__main__':
    projection = WebMercatorProjection
    date = datetime.date.today()
    os.environ['NC_PATH'] = '/Users/sw/github/Marine_Forecast_WebGIS/BeihaiModel_out'

    d1 = datetime.datetime.now()
    print d1

    regions = ['BHS']
    date = datetime.date(2013,11,16)
    resource = 'FVCOMSTM'
    for region in regions:
        # vector2imagetiles(date, resource, region, projection=projection, update = update)
        # vector2jsontiles(date, resource, region, projection=projection, update = update)
        scalar2image(date, resource, region, None, projection, update = update)

    #regions = ['NWP', 'NCS', 'QDSEA']
    regions = ['NCS']

    date = datetime.date(2013,11,14)
    resource = 'SWAN'
    for region in regions:
        scalar2image(date, resource, region, ['hs'], projection, update = update)

    # date = datetime.date(2013,9,12)
    # resource = 'WRF'
    # for region in regions:
    #     vector2imagetiles(date, resource, region, projection=projection, update = update)
    #     vector2jsontiles(date, resource, region, projection=projection, update = update)
    #     scalar2image(date, resource, region, ['slp'], projection, update = update)

    date = datetime.date(2013,12,10)
    resource = 'POM'
    for region in regions:
        # vector2imagetiles(date, resource, region, projection=projection, update = update)
        # vector2jsontiles(date, resource, region, projection=projection, update = update)
        scalar2image(date, resource, region, ['el'], projection=projection, update = update)

    date = datetime.date(2013,11,15)
    resource = 'ROMS'
    for region in regions:
        scalar2image(date, resource, region, ['temp'], projection=projection, update = update)
        # scalar2image(date, resource, region, ['salt'], projection=projection, update = update)
        # vector2imagetiles(date, resource, region, projection=projection, update = update)
        # vector2jsontiles(date, resource, region, projection=projection, update = update)


    d2 = datetime.datetime.now()
    print d2
