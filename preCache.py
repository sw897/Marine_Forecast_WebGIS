#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from NCStore import *
from optparse import OptionParser
import datetime

import multiprocessing as mp

option_parser = OptionParser()
option_parser.add_option('--update', default=False)
options, args = option_parser.parse_args(sys.argv[1:])

update = False
if options.update:
    update = True

def walkStoreStream(obj):
    method = getattr(obj[0], obj[1])
    method(*obj[2:])

if __name__ == '__main__':

    d1 = datetime.datetime.now()
    print d1

    # pool = mp.Pool(processes=mp.cpu_count())

    debug = True
    os.environ['NC_PATH'] = '/data/data/BeihaiModel_out'
    projection = WebMercatorProjection
    model_caches = {
        'WRF':{'regions':['NCS'], 'scalar':True, 'legend':True, 'imagetile':True, 'jsontile':False, 'isoline':True, 'extentlimit':False},
<<<<<<< HEAD
        'SWAN':{'regions':['NCS'], 'scalar':True, 'legend':True, 'imagetile':False, 'jsontile':False, 'isoline':False, 'extentlimit':False},
        'POM':{'regions':['NCS'], 'scalar':True, 'legend':True, 'imagetile':True, 'jsontile':False, 'isoline':False, 'extentlimit':False},
        'ROMS':{'regions':['NCS'], 'scalar':True, 'legend':True, 'imagetile':True, 'jsontile':False, 'isoline':False, 'extentlimit':False},
        'FVCOMSTM':{'regions':['BHS'], 'scalar':True, 'legend':True, 'imagetile':True, 'jsontile':False, 'isoline':False, 'extentlimit':False}
=======
        'SWAN':{'regions':['NCS'], 'scalar':True, 'legend':True, 'imagetile':False, 'jsontile':False, 'isoline':False, 'extentlimit':True},
        'POM':{'regions':['NCS'], 'scalar':True, 'legend':True, 'imagetile':True, 'jsontile':False, 'isoline':False, 'extentlimit':True},
        'ROMS':{'regions':['NCS'], 'scalar':True, 'legend':True, 'imagetile':True, 'jsontile':False, 'isoline':False, 'extentlimit':True},
        'FVCOMSTM':{'regions':['BHS'], 'scalar':True, 'legend':True, 'imagetile':True, 'jsontile':False, 'isoline':False, 'extentlimit':True}
>>>>>>> master
    }

    for model in model_caches:
        if debug:
            if model == 'FVCOMSTM':
                date = datetime.date(2013,11,16)
            elif model == 'SWAN':
                date = datetime.date(2013,11,14)
            elif model == 'WRF':
                date = datetime.date(2013,11,25)
            elif model == 'POM':
                date = datetime.date(2013,12,10)
            elif model == 'ROMS':
                date = datetime.date(2013,11,15)
        else:
            date = datetime.date.today()
        for region in model_caches[model]['regions']:
            store = globals()[model+'Store'](date, region)
            if model_caches[model]['extentlimit']:
                store.set_filter_extent(117.5,35,123.5,38.5)
            if model_caches[model]['scalar']:
                storestream = store.list_scalar_images(projection=projection, update=update)
                map(walkStoreStream, storestream)
                # for test, 只生成一个
                # walkStoreStream(next(storestream))
                # 使用多进程模式会引起netcdf底层错误
                # pool.map(walkStoreStream, storestream)
            if model_caches[model]['legend']:
                storestream = store.list_scalar_legends(update=update)
                map(walkStoreStream, storestream)
            if model_caches[model]['imagetile']:
                storestream = store.list_tiles('image', projection=projection, update=update)
                map(walkStoreStream, storestream)
            if model_caches[model]['jsontile']:
                storestream = store.list_tiles('json', projection=projection, update=update)
                map(walkStoreStream, storestream)
            if model_caches[model]['isoline']:
                storestream = store.list_scalar_isolines(update=update)
                map(walkStoreStream, storestream)

    d2 = datetime.datetime.now()
    print d2
