/*
  * variables, 有用的全局变量
  */
var ws_server = "http://127.0.0.1:8080";
var map, baseLayer;
var g_app = '4sd';
var sd_min = L.latLng(35, 117.5);
var sd_max = L.latLng(38.5, 123.5);
var overlayLayers = new Array();
var timer_numers = 0, timer_interval = 100;
var layerAnimationTimer;
var popup = L.popup();
var top_theme = {
    model: null,
    region: null
};
var g_test = true;

var map_config = {
    "map":{
        "center":[36, 120],
        "level":2
    }
};

var app_config = {
    '4sd':[
        ["wrf","ncs", "tile,image,isoline"],
        ["swan","ncs", "image,isoline"],
        ["pom","ncs", "tile"],
        ["roms","ncs", , "tile"],
        ["fvcom","bhs", , "image"]
    ],
    '4bh':[]
};

var nc_config = {
    "wrf":{
        "nwp":{
            "bounds": [[14.5, 103.8],[48.58, 140.4]],
            "times":72,
            "levels":1,
            "forecast_time":0
        },
        "ncs":{
            "bounds": [[28.5, 116.],[42.5, 129.]],
            "times":72,
            "levels":1,
            "forecast_time":0
        },
        "qdsea":{
            "bounds":[[35., 119.],[36.5, 121.5]],
            "times":72,
            "levels":1,
            "forecast_time":0
        }
    },
    "swan":{
        "nwp":{
            "bounds":[[15, 105],[47, 140]],
            "times":72,
            "levels":1,
            "forecast_time":0
        },
        "ncs":{
            "bounds":[[32., 117.],[42., 127.]],
            "times":72,
            "levels":1,
            "forecast_time":0
        },
        "qdsea":{
            "bounds":[[34.8958, 119.2958],[36.8042, 121.6042]],
            "times":72,
            "levels":1,
            "forecast_time":0
        }
    },
    "ww3":{
        "global":{
            "bounds":[[15., 105.],[47., 140.]],
            "times":72,
            "levels":1,
            "forecast_time":0
        },
        "nwp":{
            "bounds":[[15., 105.],[47., 140.]],
            "times":72,
            "levels":1,
            "forecast_time":0
        }
    },
    "pom":{
        "ncs":{
            "bounds":[[33.9791, 117.473],[40.9791, 124.973]],
            "times":24,
            "levels":1,
            "forecast_time":0
        }
    },
    "roms":{
        "nwp":{
            "bounds":[[-9., 99.],[42., 148.]],
            "times":1,
            "levels":25,
            "forecast_time":0
        },
        "ncs":{
            "bounds":[[32., 117.5],[41., 127.]],
            "times":96,
            "levels":6,
            "forecast_time":0
        },
        "qdsea":{
            "bounds":[[35., 119.],[37., 122.]],
            "times":96,
            "levels":6,
            "forecast_time":0
        }
    },
    "fvcomstm":{
        "bhs":{
            "bounds":[[23.2132, 117.541],[40.9903, 131.303]],
            "times":72,
            "levels":1,
            "forecast_time":0
        }
    },
    "fvcomtid":{
        "qdsea":{
            "bounds":[[34.2846, 119.174],[36.8493, 122.]],
            "times":72,
            "levels":1,
            "forecast_time":0
        },
        "dlw":{
            "bounds":[[23.2132, 117.541],[40.9903, 131.303]],
            "times":72,
            "levels":1,
            "forecast_time":0
        },
        "rzg":{
            "bounds":[[23.2132, 117.541],[40.9903, 131.303]],
            "times":72,
            "levels":1,
            "forecast_time":0
        },
        "sd":{
            "bounds":[[23.2132, 117.541],[40.9903, 131.303]],
            "times":72,
            "levels":1,
            "forecast_time":0
        }
    }
};

/*
  * functions
  */

function init() {
    initApp();
    initMap();
}

function initApp() {
    if(g_app='4sd') {
        ;
    }
    else if (g_app='4bh'){
        ;
    }
    else{
        ;
    }
}

// 初始化地图
function initMap() {
    map = L.map('map', {crs: L.CRS.EPSG3395, attributionControl: false}).setView(map_config.map.center, map_config.map.level);
    baseLayer = createBaseLayer('ocean');
    map.addLayer(baseLayer);
    var labelLayer = createLabelLayer();
    map.addLayer(labelLayer);
    L.graticule({
        style: {
            color: '#777',
            weight: 1,
            opacity: 0.5
        }
    }).addTo(map);
    map.on('click', onMapClick);
}

function changeBaseLayer(name) {
    map.removeLayer(baseLayer);
    baseLayer = createBaseLayer(name);
    map.addLayer(baseLayer);
}

function createBaseLayer(name) {
    var baseLayer = null;
    if(name == 'vector') {
        var url = 'http://{s}.tianditu.cn/vec_w/wmts?service=wmts&request=GetTile&version=1.0.0&&LAYER=vec&tileMatrixSet=w&TileMatrix={z}&TileRow={y}&TileCol={x}&style=default&format=tiles';
        var attributionstr = "天地图矢量地图 ©天地图";
        baseLayer = L.tileLayer(url, {subdomains: ['t0', 't1', 't2', 't3', 't4', 't5', 't6', 't7'], zIndex:0, attribution:attributionstr});
    }
    else if (name == 'image') {
        var url = 'http://{s}.tianditu.cn/img_w/wmts?service=wmts&request=GetTile&version=1.0.0&&LAYER=img&tileMatrixSet=w&TileMatrix={z}&TileRow={y}&TileCol={x}&style=default&format=tiles';
        var attributionstr = "天地图影像地图 ©天地图";
        baseLayer = L.tileLayer(url, {subdomains: ['t0', 't1', 't2', 't3', 't4', 't5', 't6', 't7'], zIndex:0, attribution:attributionstr});
    }
    else if (name == 'bhimage') {
        baseLayer = L.tileLayer.functional(function (view) {
            var z = 'L'+formatLength(view.zoom, 2);
            var y = 'R'+formatLength((view.tile.row).toString(16), 8);
            var x = 'C'+formatLength((view.tile.column).toString(16), 8);
            var url = 'bhimage/{z}/{y}/{x}.jpg'
                .replace('{z}', z)
                .replace('{y}', y)
                .replace('{x}', x);
            return url;
        });
    }
    else if (name == 'ocean') {
        var url = 'http://services.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}';
        var attributionstr = "ArcGIS Online OceanMap ©ESRI";
        baseLayer = L.tileLayer(url, {zIndex:0, attribution:attributionstr});
    }
    return baseLayer;
}

function createLabelLayer() {
    var labelLayerurl = 'http://{s}.tianditu.cn/cva_w/wmts?service=wmts&request=GetTile&version=1.0.0&&LAYER=cva&tileMatrixSet=w&TileMatrix={z}&TileRow={y}&TileCol={x}&style=default&format=tiles';
    var labelLayer = L.tileLayer(labelLayerurl, {zoomOffset: 0, subdomains: ['t0', 't1', 't2', 't3', 't4', 't5', 't6', 't7'], zIndex:10});
    return labelLayer;
}

function removeThemeLayers() {
    for(var i = overlayLayers.length; i--; i > -1 ) {
        map.removeLayer(overlayLayers[i]);
    }
    overlayLayers = new Array();
    top_theme.model = null;
    top_theme.region = null;
}

function queryThemeLayer() {
    map.off('click', onMapClick);
    map.on('click', onQueryThemeLayer);
}

function onQueryThemeLayer(e) {
    if(overlayLayers.length < 1) {
        alert("there is no theme layer");
        return;
    }
    var themeLayer = overlayLayers[overlayLayers.length-1];
    var url = getWebServicesUrl('pointquery', top_theme.model, top_theme.region, e.latlng);
    $.get(url, function(data){
        alert( "Data Loaded: " + JSON.stringify(data));
    });
    map.off('click', onQueryThemeLayer);
    map.on('click', onMapClick);
}

function onMapClick(e) {
    popup
        .setLatLng(e.latlng)
        .setContent("clicked at " + e.latlng.toString())
        .openOn(map);
}

function changeThemeLayer(model, region, types) {
    removeThemeLayers();
    addThemeLayer(model, region, types);
    var bounds = nc_config[model][region]["bounds"];
    var min = L.latLng(bounds[0][0], bounds[0][1])
    var max = L.latLng(bounds[1][0], bounds[1][1])
    if(g_app == "4sd" && model != "wrf") {
        min = L.latLng(sd_min.lat, sd_min.lng);
        max = L.latLng(sd_max.lat, sd_max.lng);
    }
    map.fitBounds([min,max]);
}

function addThemeLayer(model, region, types) {
    types = types.split(',');
    for(var i = 0; i < types.length; i++) {
        var themeLayer =createThemeLayer(model, region, types[i]);
        if(themeLayer != null) {
            map.addLayer(themeLayer);
            overlayLayers.push(themeLayer);
        }
    }
}

function createThemeLayer(model, region, type) {
    top_theme.model = model;
    top_theme.region = region;
    var themeLayer = null;
    if(type == 'scalar') {
        themeLayer = createImageOverlay(model, region);
    }
    else if(type == 'vector') {
        themeLayer = createImageTileOverlay(model, region);
        //themeLayer = createGeoJsonTileOverlay(model, region);
    }
    else if(type == 'isoline') {
        themeLayer = createGeoJsonOverlay(model, region);
    }
    return themeLayer;
}

function createImageOverlay(model, region) {
    var time = arguments[2]?arguments[2]:0;
    var level = arguments[3]?arguments[3]:0;
    var variables = arguments[4]?arguments[4]:'default';
    var bounds = nc_config[model][region]["bounds"];
    var min = L.latLng(bounds[0][0], bounds[0][1])
    var max = L.latLng(bounds[1][0], bounds[1][1])
    if(g_app == "4sd" && model != "wrf") {
        min = L.latLng(sd_min.lat, sd_min.lng);
        max = L.latLng(sd_max.lat, sd_max.lng);
    }
    // bug: y方向有偏差,但不清楚引入的原因,在此强制移动
    if(model == 'roms') {
        min.lat += .1
        max.lat += .1
    }
    else {
        min.lat += .16
        max.lat += .16
    }
    var url = getWebServicesUrl('image', model, region, time, level, variables);
    overlay = L.imageOverlay(url, [min,max], {opacity:.7});
    return overlay;
}

function createImageTileOverlay(model, region) {
    var time = arguments[2]?arguments[2]:0;
    var level = arguments[3]?arguments[3]:0;
    var variables = arguments[4]?arguments[4]:'default';
    var bounds = nc_config[model][region]["bounds"];
    var url = getWebServicesUrl('imagetile', model, region, time, level, variables);
    var overlay = L.tileLayer(url, {
            zIndex:100,
            bounds: bounds
        }
    );
    return overlay;
}

function createGeoJsonOverlay(model, region) {
    var time = arguments[2]?arguments[2]:0;
    var level = arguments[3]?arguments[3]:0;
    var variables = arguments[4]?arguments[4]:'default';
    var bounds = nc_config[model][region]["bounds"];
    var url = getWebServicesUrl('isoline', model, region, time, level, variables);
    var overlay = L.geoJson.ajax(url, {
            zIndex:100,
            bounds: bounds
        });
    return overlay;
}

function createGeoJsonTileOverlay(model, region) {
    var time = arguments[2]?arguments[2]:0;
    var level = arguments[3]?arguments[3]:0;
    var variables = arguments[4]?arguments[4]:'default';
    var bounds = nc_config[model][region]["bounds"];
    var url = getWebServicesUrl('jsontile', model, region, time, level, variables);
    var overlay = null;
    if(model != 'wrf') {
        overlay = L.tileLayer.geojson(url, {
                zIndex:100,
                bounds: bounds
            }, {
                opacity:1.0,
                onEachFeature: onEachMarker,
                filter: markerFilter,
                pointToLayer: addArrowMarker
            }
        );
    }else {
        overlay = L.tileLayer.geojson(url, {
                zIndex:100,
                bounds: bounds
            }, {
                opacity:1.0,
                onEachFeature: onEachMarker,
                filter: markerFilter,
                pointToLayer: addWindMarker
            }
        );
    }
    return overlay;
}

function transactionThemeLayer() {

}

function layerAnimation() {
    timer_numers++;
    var layerIndex = Math.floor(timer_numers / 20);
    if(layerIndex > overlayLayers.length - 1) {
        timer_numers = 0;
        layerIndex = 0;
    }
    var opacity = timer_numers - Math.floor(timer_numers / 20)*20;
    if(opacity > 10) {
        opacity = (20-opacity)/10;
    }
    else {
        opacity = opacity/10;
    }
    var layer = overlayLayers[layerIndex];
    // 渐隐渐现
    if (layer instanceof L.TileLayer.GeoJSON) {
        layer._recurseLayerUntilMarker(function(layer1) {layer1.setOpacity(opacity)}, layer.geojsonLayer);
        layer._recurseLayerUntilPath(function(layer1) {layer1.setStyle({'opacity':opacity})}, layer.geojsonLayer);
    }
    else{
        layer.setOpacity(opacity);
    }
}

function stopLayerAnimation(){
    timer_numers = 0;
    clearInterval(layerAnimationTimer);
}

function getWebServicesUrl(type, model, region) {
    var url = _getWebServicesUrl(type, model, region);
    url += "?date=";
    if(g_test == true) {
        if(model=="wrf")
            url += "20131125";
        else if(model=="swan")
            url += "20131114";
        else if(model=="pom")
            url += "20131210";
        else if(model=="roms")
            url += "20131115";
        else if(model=="fvcomstm")
            url += "20131116";
        else
            url += "20130912";
    }
    return url;
}

function _getWebServicesUrl(type, model, region) {
    var baseurl = ws_server;
    if(type == 'pointquery') {
        var latlng = arguments[3];
        var variables = (arguments[4]!=undefined)?arguments[4]:'default';
        return baseurl + '/v1/pointquery/' + model + '/' + region + '/' + latlng.lat + ',' + latlng.lng + '/' + variables + '.json';
    }
    var time = (arguments[3]!=undefined)?arguments[3]:0;
    // for thumbnail using method
    var method = (arguments[3]!=undefined)?arguments[3]:0;
    var level = (arguments[4]!=undefined)?arguments[4]:0;
    var variables = (arguments[5]!=undefined)?arguments[5]:'default';
    if(type == 'imagetile')
        return baseurl + '/v1/tiles/webmercator/' + model + '/' + region + '/' + level + '/' + time + '/{z}/{y}/{x}/'+variables+'.png';
    if(type == 'jsontile')
        return baseurl + '/v1/tiles/webmercator/' + model + '/' + region + '/' + level + '/' + time + '/{z}/{y}/{x}/'+variables+'.geojson';
    if(type == 'image')
        return baseurl + '/v1/images/webmercator/' + model + '/' + region + '/' + level + '/' + time + '/' + variables + '.png';
    if(type == 'isoline')
        return baseurl + '/v1/isolines/' + model + '/' + region + '/' + level + '/' + time + '/' + variables + '.geojson';
    if(type == 'legend')
        return baseurl + '/v1/legends/' + model + '/' + region + '/' + level + '/' + time + '/' + variables + '.png';
    if(type == 'thumbnail')
        return baseurl + '/v1/thumbnails/' + model + '/' + region + '/' + method + '.jpg';
    if(type == 'capabilities')
        return baseurl + '/v1/capabilities/' + model + '/' + region + '.json';
    if(type == 'capabilities2')
        return baseurl + '/v1/capabilities/' + model + '/' + region + level + '/' + time + '/' + variables + '.json';
}

function displayblock() {
    document.getElementById("menubox").style.display="block";
}

function displaynone() {
    document.getElementById("menubox").style.display="none";
}

function updateLegend(model, region) {
    if(model != null && region != null) {
        var url = getWebServicesUrl("legend", model, region);
        document.getElementById("legend").src=url;
    }
    else{
        document.getElementById("legend").src='img/nodata.gif';
    }
}

function formatLength(num, length) {
    var r = "" + num;
    while (r.length < length) {
        r = "0" + r;
    }
    return r;
}

window.onload=init()
