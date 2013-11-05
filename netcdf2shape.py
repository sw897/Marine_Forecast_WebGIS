#!/usr/bin/env python
# -*- coding: utf-8 -*-

from netCDF4 import Dataset
from osgeo import ogr,osr
from shapely import geometry
import os
import numpy as np
import timeit

def fvcom2shape(netcdf, outputFormat='ESRI Shapefile'):
    pass

def roms2shape(netcdf, outputFormat='ESRI Shapefile'):
    dirName = os.path.dirname(netcdf)
    layerName = os.path.splitext(os.path.basename(netcdf))[0]
    outputFormats = {'ESRI Shapefile':'.shp', 'GeoJSON':'.geojson', 'JSON':'.json', 'SQLite':'.sqlite'}
    outputfile = os.path.join(dirName, layerName+outputFormats[outputFormat])
    if os.path.isfile(outputfile) is True:
        os.remove(outputfile)
        if outputFormat == 'ESRI Shapefile':
            os.remove(os.path.join(dirName, layerName+'.shx'))
            os.remove(os.path.join(dirName, layerName+'.dbf'))
            os.remove(os.path.join(dirName, layerName+'.prj'))
    dataDriver = ogr.GetDriverByName(outputFormat)
    dataSource = dataDriver.CreateDataSource(outputfile)
    # Make layer
    spatialReference = osr.SpatialReference()
    spatialReference.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
    layer = dataSource.CreateLayer(layerName, spatialReference, ogr.wkbPoint)
    fieldDefinitions = [('u', ogr.OFTReal), ('v', ogr.OFTReal)]
    for fieldName, fieldType in fieldDefinitions:
         layer.CreateField(ogr.FieldDefn(fieldName, fieldType))
    featureDefinition = layer.GetLayerDefn()

    # netcdf struct
    root = Dataset(netcdf, 'r')
    dim_lon = root.dimensions['eta_v']
    dim_lat = root.dimensions['xi_v']
    dim_level = root.dimensions['s_rho']
    dim_time = root.dimensions['ocean_time']
    var_lon = 'longitude'
    var_lat = 'latitude'
    var_other = ('hs', 'di', 'tm')
    latlon_map = lambda root, index, value: np.float(root.variables[value][index])
    var_map = lambda root, index_lat, index_lon, time, value : np.float(root.variables[value][time][index_lat][index_lon])

    start = timeit.default_timer()
    for i in np.arange(len(dim_lat)):
        lat = latlon_map(root, i, var_lat)
        for j in np.arange(len(dim_lon)):
            lon = latlon_map(root, j, var_lon)
            time = 0
            feature = ogr.Feature(featureDefinition)
            point = geometry.Point(lon, lat)
            feature.SetGeometry(ogr.CreateGeometryFromWkb(point.wkb))
            for var in var_other:
                value = var_map(root, i, j, time, var)
                feature.SetField(i, value)
                i = i + 1
            layer.CreateFeature(feature)
            feature.Destroy()
    print timeit.default_timer() - start
    #layer.SyncToDisk()
    root.close()

def pom2shape(netcdf, outputFormat='ESRI Shapefile', region=0):
    regions = [{'bounds':[117.,37.,122.,42.], 'resolution':1/240.}, {'bounds':[117.,22.,137.,42.], 'resolution':1/30.}]
    lat0 = regions[region]['bounds'][1]
    lon0 = regions[region]['bounds'][0]
    resolution = regions[region]['resolution']

    dirName = os.path.dirname(netcdf)
    layerName = os.path.splitext(os.path.basename(netcdf))[0]
    outputFormats = {'ESRI Shapefile':'.shp', 'GeoJSON':'.geojson', 'JSON':'.json', 'SQLite':'.sqlite'}
    outputfile = os.path.join(dirName, layerName+outputFormats[outputFormat])
    if os.path.isfile(outputfile) is True:
        os.remove(outputfile)
        if outputFormat == 'ESRI Shapefile':
            os.remove(os.path.join(dirName, layerName+'.shx'))
            os.remove(os.path.join(dirName, layerName+'.dbf'))
            os.remove(os.path.join(dirName, layerName+'.prj'))
    dataDriver = ogr.GetDriverByName(outputFormat)
    dataSource = dataDriver.CreateDataSource(outputfile)
    # Make layer
    spatialReference = osr.SpatialReference()
    spatialReference.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
    layer = dataSource.CreateLayer(layerName, spatialReference, ogr.wkbPoint)
    fieldDefinitions = [('u', ogr.OFTReal), ('v', ogr.OFTReal), ('el', ogr.OFTReal)]
    for fieldName, fieldType in fieldDefinitions:
         layer.CreateField(ogr.FieldDefn(fieldName, fieldType))
    featureDefinition = layer.GetLayerDefn()

    # netcdf struct
    root = Dataset(netcdf, 'r')
    dim_lon = root.dimensions['longitude']
    dim_lat = root.dimensions['latitude']
    dim_time = root.dimensions['time']
    # var_lon = 'longitude'
    # var_lat = 'latitude'
    var_other = ('u', 'v', 'el')
    # latlon_map = lambda root, index, value: np.float(root.variables[value][index])
    var_map = lambda root, index_lat, index_lon, time, value : np.float(root.variables[value][time][index_lat][index_lon])

    start = timeit.default_timer()
    for i in np.arange(len(dim_lat)):
        # lat = latlon_map(root, i, var_lat)
        for j in np.arange(len(dim_lon)):
            # lon = latlon_map(root, j, var_lon)
            time = 0
            feature = ogr.Feature(featureDefinition)
            lat = lat0 + i*resolution
            lon = lon0 + j*resolution
            point = geometry.Point(lon, lat)
            feature.SetGeometry(ogr.CreateGeometryFromWkb(point.wkb))
            it = 0
            for var in var_other:
                value = var_map(root, i, j, time, var)
                feature.SetField(it, value)
                it = it + 1
            layer.CreateFeature(feature)
            feature.Destroy()
    print timeit.default_timer() - start
    #layer.SyncToDisk()
    root.close()

def waves2shape(netcdf, outputFormat='ESRI Shapefile'):
    dirName = os.path.dirname(netcdf)
    layerName = os.path.splitext(os.path.basename(netcdf))[0]
    outputFormats = {'ESRI Shapefile':'.shp', 'GeoJSON':'.geojson', 'JSON':'.json', 'SQLite':'.sqlite'}
    outputfile = os.path.join(dirName, layerName+outputFormats[outputFormat])
    if os.path.isfile(outputfile) is True:
        os.remove(outputfile)
        if outputFormat == 'ESRI Shapefile':
            os.remove(os.path.join(dirName, layerName+'.shx'))
            os.remove(os.path.join(dirName, layerName+'.dbf'))
            os.remove(os.path.join(dirName, layerName+'.prj'))
    dataDriver = ogr.GetDriverByName(outputFormat)
    dataSource = dataDriver.CreateDataSource(outputfile)
    # Make layer
    spatialReference = osr.SpatialReference()
    spatialReference.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
    layer = dataSource.CreateLayer(layerName, spatialReference, ogr.wkbPoint)
    fieldDefinitions = [('hs', ogr.OFTReal), ('di', ogr.OFTReal), ('tm', ogr.OFTReal)]
    for fieldName, fieldType in fieldDefinitions:
         layer.CreateField(ogr.FieldDefn(fieldName, fieldType))
    featureDefinition = layer.GetLayerDefn()

    # netcdf struct
    root = Dataset(netcdf, 'r')
    dim_lon = root.dimensions['longitude']
    dim_lat = root.dimensions['latitude']
    dim_time = root.dimensions['time']
    var_lon = 'longitude'
    var_lat = 'latitude'
    var_other = ('hs', 'di', 'tm')
    latlon_map = lambda root, index, value: np.float(root.variables[value][index])
    var_map = lambda root, index_lat, index_lon, time, value : np.float(root.variables[value][time][index_lat][index_lon])

    start = timeit.default_timer()
    for i in np.arange(len(dim_lat)):
        lat = latlon_map(root, i, var_lat)
        for j in np.arange(len(dim_lon)):
            lon = latlon_map(root, j, var_lon)
            time = 0
            feature = ogr.Feature(featureDefinition)
            point = geometry.Point(lon, lat)
            feature.SetGeometry(ogr.CreateGeometryFromWkb(point.wkb))
            it = 0
            for var in var_other:
                value = var_map(root, i, j, time, var)
                feature.SetField(it, value)
                it = it + 1
            layer.CreateFeature(feature)
            feature.Destroy()
    print timeit.default_timer() - start
    #layer.SyncToDisk()
    root.close()

def winds2shape(netcdf, outputFormat='ESRI Shapefile'):
    dirName = os.path.dirname(netcdf)
    layerName = os.path.splitext(os.path.basename(netcdf))[0]
    outputFormats = {'ESRI Shapefile':'.shp', 'GeoJSON':'.geojson', 'JSON':'.json', 'SQLite':'.sqlite'}
    outputfile = os.path.join(dirName, layerName+outputFormats[outputFormat])
    if os.path.isfile(outputfile) is True:
        os.remove(outputfile)
        if outputFormat == 'ESRI Shapefile':
            os.remove(os.path.join(dirName, layerName+'.shx'))
            os.remove(os.path.join(dirName, layerName+'.dbf'))
            os.remove(os.path.join(dirName, layerName+'.prj'))
    dataDriver = ogr.GetDriverByName(outputFormat)
    dataSource = dataDriver.CreateDataSource(outputfile)
    # Make layer
    spatialReference = osr.SpatialReference()
    spatialReference.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')
    layer = dataSource.CreateLayer(layerName, spatialReference, ogr.wkbPoint)
    fieldDefinitions = [('u', ogr.OFTReal), ('v', ogr.OFTReal), ('slp', ogr.OFTReal)]
    for fieldName, fieldType in fieldDefinitions:
         layer.CreateField(ogr.FieldDefn(fieldName, fieldType))
    featureDefinition = layer.GetLayerDefn()

    # netcdf struct
    root = Dataset(netcdf, 'r')
    dim_lon = root.dimensions['longitude']
    dim_lat = root.dimensions['latitude']
    dim_time = root.dimensions['times']
    var_lon = 'longitude'
    var_lat = 'latitude'
    var_other = ('hu10ms', 'v10m', 'slp')
    latlon_map = lambda root, index, value: np.float(root.variables[value][index])
    var_map = lambda root, index_lat, index_lon, time, value : np.float(root.variables[value][time][index_lat][index_lon])

    start = timeit.default_timer()
    for i in np.arange(len(dim_lat)):
        lat = latlon_map(root, i, var_lat)
        for j in np.arange(len(dim_lon)):
            lon = latlon_map(root, j, var_lon)
            time = 0
            feature = ogr.Feature(featureDefinition)
            point = geometry.Point(lon, lat)
            feature.SetGeometry(ogr.CreateGeometryFromWkb(point.wkb))
            it = 0
            for var in var_other:
                value = var_map(root, i, j, time, var)
                feature.SetField(it, value)
                it = it + 1
            layer.CreateFeature(feature)
            feature.Destroy()
    print timeit.default_timer() - start
    #layer.SyncToDisk()
    root.close()

def test(netcdf):
    start = timeit.default_timer()
    root = Dataset(netcdf, 'r')
    print timeit.default_timer() - start
    for i in np.arange(10):
        #lat = latlon_map(root, i, var_lat)
        for j in np.arange(10):
            #lon = latlon_map(root, j, var_lon)
            u = root.variables['u10m'][0][i][j]
    print timeit.default_timer() - start
    root.close()

def main():
    # test("../BeihaiModel_out20130917/WRF/WRF_Meteo_NCS_2013070212UTC_180_1hr.nc")

    # winds2shape("../BeihaiModel_out20130917/WRF/WRF_Meteo_NCS_2013070212UTC_180_1hr.nc")

    # waves2shape("../BeihaiModel_out20130917/swan_ww3/swan_青岛近海/20130912_qdsea.nc")

    # waves2shape("../BeihaiModel_out20130917/swan_ww3/www3_西北太平洋/20130912_nww3.nc")

    pom2shape("../BeihaiModel_out20130917/POM/渤海潮流/bh20130913.nc", region=0)

    #pom2shape("../BeihaiModel_out20130917/POM/东中国海潮流/ecs20130913.nc", region=1)

    # roms2shape("../BeihaiModel_out20130917/ROMS/西北太平洋环流/all_hisv2c_0288.nc")

    # roms2shape("../BeihaiModel_out20130917/ROMS/青岛近海/ROMS_Currt_QD_2013091300BJS_096_1hr.nc")

    # fvcom2shape("../BeihaiModel_out20130917/FVCOM/bhe/20130910/bhe_0001.nc")

if __name__ == '__main__':
    main()


