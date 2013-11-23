
from pyncstore import *
from optparse import OptionParser

option_parser = OptionParser()
options, args = option_parser.parse_args(sys.argv[1:])

def scalar2image(date, resource, region, variable, projection=WebMercatorProjection):
    store = globals()[resource+'Store'](date, region)
    for time in range(store.times):
        for level in range(store.levels):
            store.scalar_to_image(variable, time, level, projection=projection)

def tile2json(date, resource, region, variables=None, projection=WebMercatorProjection):
    store = globals()[resource+'Store'](date, region)
    zs = [4,5,6]
    for z in zs:
        store.export_to_jsontiles(z, variables, projection)

if __name__ == '__main__':
    resource = 'SWAN'
    region = 'NWP'
    variable = 'hs'
    projection = LatLonProjection
    date = datetime.date.today()
    date = datetime.date(2013,9,12)
    os.environ['NC_PATH'] = '/Users/sw/github/Marine_Forecast_WebGIS/BeihaiModel_out'
    scalar2image(date, resource, region, variable, projection)
