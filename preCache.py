#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from NCStore import *
from optparse import OptionParser
import datetime

import multiprocessing as mp

def walkStoreStream(obj):
    method = getattr(obj[0], obj[1])
    method(*obj[2:])

#pool = mp.Pool(processes=mp.cpu_count())

option_parser = OptionParser()
option_parser.add_option('--update', default=False)
options, args = option_parser.parse_args(sys.argv[1:])

update = False
if options.update:
    update = True

if __name__ == '__main__':
    projection = WebMercatorProjection
    date = datetime.date.today()
    os.environ['NC_PATH'] = '/Users/sw/github/Marine_Forecast_WebGIS/BeihaiModel_out'

    #regions = ['NWP', 'NCS', 'QDSEA']

    d1 = datetime.datetime.now()
    print d1

    # region = 'BHS'
    # date = datetime.date(2013,11,16)
    # resource = 'FVCOMSTM'
    # store = globals()[resource+'Store'](date, region)
    # store.set_filter_extent(117.5,35,123.5,38.5)
    # store.scalar_to_isoline(None, 0, 0)

    # storestream = store.list_scalar_images(None, time=None, level=None, projection=projection, update=update)
    # map(walkStoreStream, storestream)
    # storestream = store.list_scalar_legends(None, time=None, level=None, update=update)
    # map(walkStoreStream, storestream)
    # # 使用多进程模式会引起netcdf底层错误
    # # pool.map(walkStoreStream, storestream)

    # storestream = store.list_tiles('image', None, None, time=None, level=None, projection=projection, postProcess=NcArrayUtility.uv2va, update=update)
    # map(walkStoreStream, storestream)

    # storestream = store.list_tiles('json', None, None, time=None, level=None, projection=projection, postProcess=NcArrayUtility.uv2va, update=update)
    # map(walkStoreStream, storestream)

    region = 'NCS'
    date = datetime.date(2013,11,14)
    resource = 'SWAN'
    store = globals()[resource+'Store'](date, region)
    store.set_filter_extent(117.5,35,123.5,38.5)
    # storestream = store.list_scalar_images(None, time=None, level=None, projection=projection, update=update)
    # map(walkStoreStream, storestream)
    storestream = store.list_scalar_isolines(None, time=None, level=None, update=update)
    map(walkStoreStream, storestream)

    region = 'NCS'
    date = datetime.date(2013,11,25)
    resource = 'WRF'
    store = globals()[resource+'Store'](date, region)
    # storestream = store.list_scalar_images(None, time=None, level=None, projection=projection, update=update)
    # map(walkStoreStream, storestream)
    storestream = store.list_scalar_isolines(None, time=None, level=None, update=update)
    # walkStoreStream(next(storestream))
    map(walkStoreStream, storestream)

    # region = 'NCS'
    # date = datetime.date(2013,12,10)
    # resource = 'POM'
    # store = globals()[resource+'Store'](date, region)
    # store.set_filter_extent(117.5,35,123.5,38.5)
    # storestream = store.list_scalar_images(None, time=None, level=None, projection=projection, update=update)
    # map(walkStoreStream, storestream)

    # region = 'NCS'
    # date = datetime.date(2013,11,15)
    # resource = 'ROMS'
    # store = globals()[resource+'Store'](date, region)
    # store.set_filter_extent(117.5,35,123.5,38.5)
    # storestream = store.list_scalar_images(None, time=None, level=None, projection=projection, update=update)
    # map(walkStoreStream, storestream)


    d2 = datetime.datetime.now()
    print d2
