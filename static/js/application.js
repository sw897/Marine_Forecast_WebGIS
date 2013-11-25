/*
  * variables, 有用的全局变量
  */
// 可能变化
//var vectorBaseUrl = "http://54.241.241.182:8080/v0/tiles/webmercator";
var vectorBaseUrl = "http://127.0.0.1:8080/v1/tiles/webmercator";
var scalarBaseUrl = "http://127.0.0.1:8080/v1/images/webmercator";
var legendBaseUrl = "http://127.0.0.1:8080/v1/legends";
var markerbaserurl = "http://127.0.0.1:8080/v0/markers";
var staticmarkerurl = "markers";
// 以下不必须修改
var map, baseLayer,labelLayer, themeLayer=null;
// marker变量
var markersize=32, markertype='wind';
// 时间动画变量
var animationLayers = new Array();
var timer_numers = 0, timer_interval = 100;
var layerAnimationTimer;
// 风向array
var winddirects = new Array('西风','西南风','南风','东南风','东风','东北风','北风','西北风');
var g_resource,g_region;

// 全局配置对象
var config = {
    "map":{
        "center":[36, 120],
        "level":2
    },
    "markers":{
        "wrf":{"marker":"wind", "size":32},
        "swan":{"marker":"square", "size":16},
        "wwiii":{"marker":"square", "size":16},
        "pom":{"marker":"arrow", "size":32},
        "roms":{"marker":"arrow", "size":32},
        "fvcom":{"marker":"arrow", "size":32}
    },
    "wrf": {
        "nwp":{
            "bounds": [[14.5, 103.8],[48.58, 140.4]],
            "minZoom":0,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":1
        },
        "ncs":{
            "bounds": [[28.5, 116.],[42.5, 129.]],
            "minZoom":0,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":1
        },
        "qdsea":{
            "bounds":[[35., 119.],[36.5, 121.5]],
            "minZoom":0,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":1
        }
    },
    "swan": {
        "nwp":{
            "bounds":[[15, 105],[47, 140]],
            "minZoom":0,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":1
        },
        "ncs":{
            "bounds":[[32., 117.],[42., 127.]],
            "minZoom":0,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":1
        },
        "qdsea":{
            "bounds":[[34.8958, 119.2958],[36.8042, 121.6042]],
            "minZoom":0,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":1
        }
    },
    "ww3": {
        "nwp":{
            "bounds":[[15., 105.],[47., 140.]],
            "minZoom":0,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":1
        }
    },
    "pom":{
        "bh":{
            "bounds":[[37.2, 117.5],[42., 122.]],
            "minZoom":0,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":1
        },
        "ecs":{
            "bounds":[[24.5, 117.5],[42., 137.]],
            "minZoom":0,
            "maxZoom":12,
            "times":24,
            "forecast_time":0,
            "levels":1
        }
    },
    "roms":{
        "nwp":{
            "bounds":[[-9., 99.],[42., 148.]],
            "minZoom":0,
            "maxZoom":12,
            "times":1,
            "levels":25,
            "forecast_time":0
        },
        "ncs":{
            "bounds":[[32., 117.5],[41., 127.]],
            "minZoom":0,
            "maxZoom":12,
            "times":96,
            "levels":6,
            "forecast_time":0
        },
        "qdsea":{
            "bounds":[[35., 119.],[37., 122.]],
            "minZoom":0,
            "maxZoom":12,
            "times":96,
            "levels":6,
            "forecast_time":0
        }
    },
    "fvcom":{
        "qdh":{}
    }
};

/*
  * functions, 有用的全局函数
  */
// 初始化地图
function initMap() {
    map = L.map('map', {crs: L.CRS.EPSG3395}).setView(config.map.center, config.map.level);
    var baselayerurl = 'http://services.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}';
    baseLayer = L.tileLayer(baselayerurl, {noWrap:false});
    baseLayer.addTo(map);
    addLabelLayer();
    // todo: bug fix,remove this circle
    //L.circle([0, 0], 5, {opacity:0.0, fillOpacity: 0.0}).addTo(map);

    L.graticule({
        style: {
            color: '#777',
            weight: 1,
            opacity: 0.5
        }
    }).addTo(map);
}

function changeBaseLayer(name) {
    map.removeLayer(baseLayer);
    map.removeLayer(labelLayer);
    if(name == 'vector') {
        var url = 'http://{s}.tianditu.cn/vec_w/wmts?service=wmts&request=GetTile&version=1.0.0&&LAYER=vec&tileMatrixSet=w&TileMatrix={z}&TileRow={y}&TileCol={x}&style=default&format=tiles';
        baseLayer = L.tileLayer(url, {subdomains: ['t0', 't1', 't2', 't3', 't4', 't5', 't6', 't7']});
    }
    else if (name == 'image') {
        var url = 'http://{s}.tianditu.cn/img_w/wmts?service=wmts&request=GetTile&version=1.0.0&&LAYER=img&tileMatrixSet=w&TileMatrix={z}&TileRow={y}&TileCol={x}&style=default&format=tiles';
        baseLayer = L.tileLayer(url, {subdomains: ['t0', 't1', 't2', 't3', 't4', 't5', 't6', 't7']});
    }
    else {
        var url = 'http://services.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}';
        baseLayer = L.tileLayer(url);
    }
    baseLayer.addTo(map);
    addLabelLayer();
}

// 添加中文注记图层
function addLabelLayer() {
    var labelLayerurl = 'http://{s}.tianditu.cn/cva_w/wmts?service=wmts&request=GetTile&version=1.0.0&&LAYER=cva&tileMatrixSet=w&TileMatrix={z}&TileRow={y}&TileCol={x}&style=default&format=tiles';
    labelLayer = L.tileLayer(labelLayerurl, {zoomOffset: 0, subdomains: ['t0', 't1', 't2', 't3', 't4', 't5', 't6', 't7']});
    labelLayer.addTo(map);
}

function removeThemeLayer() {
    map.removeLayer(themeLayer);
}

function changeThemeLayer(resource, region) {
    if(themeLayer != null && map.hasLayer(themeLayer))
        removeThemeLayer();
    if(resource == 'swan' || resource == 'ww3') {
        themeLayer = addImageOverlay(resource, region);
    }
    else {
        // use geojson or image
        //themeLayer = addGeoJSONOverlay(resource, region);
        themeLayer = addTileOverlay(resource, region);
    }
    g_resource = resource;
    g_region = region;
    map.fitBounds(config[resource][region]["bounds"]);
}

// 创建并添加专题图层
function addImageOverlay(resource, region) {
    var time = arguments[2]?arguments[2]:0;
    var level = arguments[3]?arguments[3]:0;
    var variable = arguments[4]?arguments[4]:'default';
    var bounds = config[resource][region]["bounds"];
    var url = getImageUrl(scalarBaseUrl, resource, region, time, level, variable);
    overlay = L.imageOverlay(url, bounds, {'opacity':.5});
    map.addLayer(overlay);
    return overlay;
}

function addTileOverlay(resource, region) {
    var time = arguments[2]?arguments[2]:0;
    var level = arguments[3]?arguments[3]:0;
    // update global variables
    markersize= config.markers[resource].size;
    markertype = config.markers[resource].marker;
    var bounds = config[resource][region]["bounds"];
    var url = getImageTileUrl(vectorBaseUrl, resource, region, time, level);
    var overlay = L.tileLayer(url, {
            bounds: bounds,
            minZoom: config[resource][region]["minZoom"],
            maxZoom: config[resource][region]["maxZoom"]
        }
    );
    map.addLayer(overlay);
    return overlay;
    //animationLayers.push(overlay);
}

function addGeoJSONOverlay(resource, region) {
    var time = arguments[2]?arguments[2]:0;
    var level = arguments[3]?arguments[3]:0;
    // update global variables
    markersize= config.markers[resource].size;
    markertype = config.markers[resource].marker;
    var bounds = config[resource][region]["bounds"];
    var url = getJsonTileUrl(vectorBaseUrl, resource, region, time, level);
    var overlay = L.tileLayer.geojson(url, {
            bounds: bounds,
            minZoom: config[resource][region]["minZoom"],
            maxZoom: config[resource][region]["maxZoom"],
            clipTiles: false
        }, {
            //style: style,
            opacity:1.0,
            onEachFeature: onEachMarker,
            filter: markerFilter,
            pointToLayer: addMarker
        }
    );
    map.addLayer(overlay);
    return overlay;
    //animationLayers.push(overlay);
}

// 不同图层切换的动画
function layerAnimation() {
    timer_numers++;
    var layerIndex = Math.floor(timer_numers / 20);
    if(layerIndex > animationLayers.length - 1) {
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
    var layer = animationLayers[layerIndex];
    // 渐隐渐现
    if (layer instanceof L.TileLayer.GeoJSON) {
        layer._recurseLayerUntilMarker(function(layer1) {layer1.setOpacity(opacity)}, layer.geojsonLayer);
        layer._recurseLayerUntilPath(function(layer1) {layer1.setStyle({'opacity':opacity})}, layer.geojsonLayer);
    }
    else{
        layer.setOpacity(opacity);
    }
}

// 停止动画
function stopLayerAnimation(){
    timer_numers = 0;
    clearInterval(layerAnimationTimer);
}

// 获取nc vector json tile的url
function getJsonTileUrl(baseurl, resource, region) {
    var time = (arguments[3]!=undefined)?arguments[3]:0;
    var level = (arguments[4]!=undefined)?arguments[4]:0;
    var variables = (arguments[5]!=undefined)?arguments[5]:'default';
    return baseurl + '/' + resource + '/' + region + '/' + level + '/' + time + '/{z}/{y}/{x}/'+variables+'.json';
}

// 获取nc vector image tile的url
function getImageTileUrl(baseurl, resource, region) {
    var time = (arguments[3]!=undefined)?arguments[3]:0;
    var level = (arguments[4]!=undefined)?arguments[4]:0;
    var variables = (arguments[5]!=undefined)?arguments[5]:'default';
    return baseurl + '/' + resource + '/' + region + '/' + level + '/' + time + '/{z}/{y}/{x}/'+variables+'.png';
}

// 获取nc scalar的url
function getImageUrl(baseurl, resource, region) {
    var time = (arguments[3]!=undefined)?arguments[3]:0;
    var level = (arguments[4]!=undefined)?arguments[4]:0;
    var variables = (arguments[5]!=undefined)?arguments[5]:'default';
    return baseurl + '/' + resource + '/' + region + '/' + level + '/' + time + '/' + variables + '.png';
}

// 获取图例legends的url
function getLegendUrl(baseurl, resource, region) {
    var time = (arguments[3]!=undefined)?arguments[3]:0;
    var level = (arguments[4]!=undefined)?arguments[4]:0;
    var variables = (arguments[5]!=undefined)?arguments[5]:'default';
    return baseurl + '/' + resource + '/' + region + '/' + level + '/' + time + '/' + variables + '.png';
}

// 获取动态生成marker的url
function getMarkerUrl(baseurl, markertype, value, angle, size) {
    return baseurl + '/' + markertype + '/' + value + '/' + angle + '/' + size + ".png";
}

// 获取静态marker的url
function getStaticMarkerUrl(markertype, value, angle, size) {
    if(markertype == 'square') {
        return staticmarkerurl + '/' + markertype + '/' + parseFloat(value).toFixed(1) + '_' + size + ".png";
    }
    if(markertype == 'wind') {
        if(value < 0) value = 0;
        if(value > 39) value = 39;
    }
    else if(markertype == 'arrow') {
        if(value > 2.4) value = 2.4;
    }
    var angle = Math.floor(angle/Math.PI*180);
    if(angle >359)
        angle -= 360;
    if(markertype == 'arrow') {
        return staticmarkerurl + '/' + markertype + '/' + parseFloat(value).toFixed(1) + '/' + angle + '_' + size + ".png";
    }
    else {
        return staticmarkerurl + '/' + markertype + '/' + Math.floor(value) + '/' + angle + '_' + size + ".png";
    }
}

// marker符号后处理
function onEachMarker (feature, layer) {
    var val = feature.properties['value'];
    var value = 0;
    var angle = 0;
    if(val.length == 2) {
        value = Math.sqrt(val[0]*val[0] + val[1]*val[1]);
        if(value == 0) {
            angle = 0;
        } else {
            angle = Math.acos(val[0]/value);
            if(val[1] < 0) {
                angle = 2*Math.PI - angle;
            }
        }
    }
    else {
        value = val[0];
        angle = 0;
    }
    // var value = feature.properties['value'];
    // var angle = feature.properties['angle'];
    if (markertype == 'wind') {
        if (feature.properties) {
            var popupString = '<div class="popup">';
            popupString += '风力' + ': ' + value + '<br />';
            var direct = Math.round(angle*4/Math.PI);
            popupString += '风向' + ': ' + winddirects[direct] + '<br />';
            popupString += '</div>';
            layer.bindPopup(popupString);
        }
    }
    else if(markertype == 'arrow') {
        if (feature.properties) {
            var popupString = '<div class="popup">';
            popupString += '速度' + ': ' + value + '<br />';
            var direct = Math.round(angle*4/Math.PI);
            popupString += '方向' + ': ' + winddirects[direct] + '<br />';
            popupString += '</div>';
            layer.bindPopup(popupString);
        }
    }
    else {
        if (feature.properties) {
            var popupString = '<div class="popup">';
            popupString += '波浪高' + ': ' + value + '<br />';
            popupString += '</div>';
            layer.bindPopup(popupString);
        }
    }
}

// marker过滤函数
function markerFilter(feature) {
    return true;
}

// 向overlay上添加符号marker
function addMarker(feature, latlng) {
    var val = feature.properties['value'];
    var value = 0;
    var angle = 0;
    if(val.length == 2) {
        value = Math.sqrt(val[0]*val[0] + val[1]*val[1]);
        if(value == 0) {
            angle = 0;
        } else {
            angle = Math.acos(val[0]/value);
            if(val[1] < 0) {
                angle = 2*Math.PI - angle;
            }
        }
    }
    else {
        value = val[0];
        angle = 0;
    }
    // var value = feature.properties['value'];
    // var angle = feature.properties['angle'];
    return new L.Marker(latlng, {icon: L.icon({
        //"iconUrl":getMarkerUrl(markerbaserurl, markertype, feature.properties['value'], feature.properties['angle'], markersize)})});
        "iconUrl":getStaticMarkerUrl(markertype, value, angle, markersize)})});
}


initMap();

// for test
// // test time-multilayers
// // todo: change model,  linear
// for(var i = 0; i < 5; i++) {
//     time = i;
//     createOverlayLayer(resource, region, time, level);
// }
// // // test layer animation
// layerAnimationTimer = window.setInterval(function(){layerAnimation()}, timer_interval);

var popup = L.popup();

function onMapClick(e) {
    popup
        .setLatLng(e.latlng)
        .setContent("clicked at " + e.latlng.toString())
        .openOn(map);
}

map.on('click', onMapClick);

