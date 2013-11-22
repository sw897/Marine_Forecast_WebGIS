
from oceantile import *
def scalar2png(date, resource='SWAN', region='NWP', variable='hs', projection=WebMercatorProjection):
    store = globals()[resource+'Store'](date, region)
    for time in range(store.times):
        for level in range(store.levels):
            store.scalar_to_image(variable, time, level, projection=projection)


if __name__ == '__main__':
    resource = 'SWAN'
    region = 'NWP'
    variable = 'hs'
    projection = LatLonProjection
    date = datetime.date.today()
    date = datetime.date(2013,9,12)
    work_directory = '/Users/sw/github/Marine_Forecast_WebGIS/BeihaiModel_out'
    os.environ['NC_PATH'] = work_directory
    scalar2png(date, resource, region, variable, projection)
