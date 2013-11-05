/*
  * variables, 有用的全局变量
  */
// 可能变化
var baselayerurl = 'http://services.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}';
// other variables
//var overlayerbaseurl = "http://54.241.241.182:8080/v0/tiles/webmercator";
var overlayerbaseurl = "http://127.0.0.1:8080/v0/tiles/webmercator";
//var markebaserurl = "http://127.0.0.1:8080/v0/markers";
var staticmarkerurl = "markers";
var staticlegendurl = "legends";
// 以下不必须修改
var map;
// marker变量
var markersize=32, markertype='wind';
// 时间动画变量
var animationLayers = new Array();
var timer_numers = 0, timer_interval = 100;
var layerAnimationTimer;
// 风向array
var winddirects = new Array('西风','西南风','南风','东南风','东风','东北风','北风','西北风');

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
            "bounds":L.latLngBounds(L.latLng(14.5, 103.8), L.latLng(48.58, 140.4)),
            "minZoom":2,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":-1
        },
        "ncs":{
            "bounds":L.latLngBounds(L.latLng(28.5, 116.), L.latLng(42.5, 129.)),
            "minZoom":2,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":-1
        },
        "qd":{
            "bounds":L.latLngBounds(L.latLng(35., 119.), L.latLng(36.5, 121.5)),
            "minZoom":2,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":-1
        }
    },
    "swan": {
        "nwp":{
            "bounds":L.latLngBounds(L.latLng(15., 105.), L.latLng(47., 140.)),
            "minZoom":2,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":-1
        },
        "ncs":{
            "bounds":L.latLngBounds(L.latLng(32., 117.), L.latLng(42., 127.)),
            "minZoom":2,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":-1
        },
        "qd":{
            "bounds":L.latLngBounds(L.latLng(34.9, 119.3), L.latLng(36.8, 121.6)),
            "minZoom":2,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":-1
        }
    },
    "wwiii": {
        "nwp":{
            "bounds":L.latLngBounds(L.latLng(15., 105.), L.latLng(47., 140.)),
            "minZoom":2,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":-1
        }
    },
    "pom":{
        "bh":{
            "bounds":L.latLngBounds(L.latLng(37.2, 117.5), L.latLng(42., 122.)),
            "minZoom":2,
            "maxZoom":12,
            "times":72,
            "forecast_time":0,
            "levels":-1
        },
        "ecs":{
            "bounds":L.latLngBounds(L.latLng(24.5, 117.5), L.latLng(42., 137.)),
            "minZoom":2,
            "maxZoom":12,
            "times":24,
            "forecast_time":0,
            "levels":-1
        }
    },
    "roms":{
        "nwp":{
            "bounds":L.latLngBounds(L.latLng(-9., 99.), L.latLng(42., 148.)),
            "minZoom":2,
            "maxZoom":12,
            "times":1,
            "levels":25,
            "forecast_time":0
        },
        "ncs":{
            "bounds":L.latLngBounds(L.latLng(32., 117.5), L.latLng(41., 127.)),
            "minZoom":2,
            "maxZoom":12,
            "times":96,
            "levels":6,
            "forecast_time":0
        },
        "qd":{
            "bounds":L.latLngBounds(L.latLng(35., 119.), L.latLng(37., 122.)),
            "minZoom":2,
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
    map = L.map('map').setView(config.map.center, config.map.level);
    var baseLayer = L.tileLayer(baselayerurl, {noWrap:false});
    baseLayer.addTo(map);
    addLabelLayer();
    // todo: bug fix,remove this circle
    L.circle([0, 0], 5, {opacity:0.0, fillOpacity: 0.0}).addTo(map);
}

// 添加中文注记图层
function addLabelLayer() {
    var labelLayerurl = 'http://{s}.tianditu.cn/cva_w/wmts?service=wmts&request=GetTile&version=1.0.0&&LAYER=cva&tileMatrixSet=w&TileMatrix={z}&TileRow={y}&TileCol={x}&style=default&format=tiles';
    var labelLayer = L.tileLayer(labelLayerurl, {zoomOffset: 0, subdomains: ['t0', 't1', 't2', 't3', 't4', 't5', 't6', 't7']});
    labelLayer.addTo(map);
}

// 创建并添加专题图层
function createOverlayLayer(resource, region) {
    var time = arguments[2]?arguments[2]:0;
    var level = arguments[3]?arguments[3]:-1;
    // update global variables
    markersize= config.markers[resource].size;
    markertype = config.markers[resource].marker;
    var bounds = config[resource][region]["bounds"];
    var url = getTileUrl(overlayerbaseurl, resource, region, time, level);
    var overLayer = L.tileLayer.geojson(url, {
            bounds: bounds,
            minZoom: config[resource][region]["minZoom"],
            maxZoom: config[resource][region]["maxZoom"],
            clipTiles: true,
            unique: function (feature) {
                return feature.id;
            }
        }, {
            //style: style,
            opacity:0.0,
            onEachFeature: onEachMarker,
            filter: markerFilter,
            pointToLayer: addMarker
        }
    );
    map.addLayer(overLayer);
    animationLayers.push(overLayer);
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

// 获取nc tile的url
function getTileUrl(baseurl, resource, region) {
    var time = (arguments[3]!=undefined)?arguments[3]:0;
    var level = (arguments[4]!=undefined)?arguments[4]:-1;
    if(level > -1) {
        return baseurl + '/' + resource + '/' + region + '/' + level + '/' + time + '/{z}/{y}/{x}.json';
    }
    else {
        return baseurl + '/' + resource + '/' + region + '/' + time + '/{z}/{y}/{x}.json';
    }
}

// 获取图例legends的url
function getLegendUrl(markertype) {
    if (markertype == 'wind')
        return staticlegendurl + '/WindSpeed.png';
    if (markertype == 'arrow')
        return staticlegendurl + '/CurrentSpeed.png';
    if (markertype == 'square')
        return staticlegendurl + '/WaveHeight.png';
    return staticlegendurl + '/SurfaceWaterTemp.png';
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
    if (markertype == 'wind') {
        if (feature.properties) {
            var popupString = '<div class="popup">';
            popupString += '风力' + ': ' + feature.properties['value'] + '<br />';
            var direct = Math.round(feature.properties['angle']*4/Math.PI);
            popupString += '风向' + ': ' + winddirects[direct] + '<br />';
            popupString += '</div>';
            layer.bindPopup(popupString);
        }
    }
    else if(markertype == 'arrow') {
        if (feature.properties) {
            var popupString = '<div class="popup">';
            popupString += '速度' + ': ' + feature.properties['value'] + '<br />';
            var direct = Math.round(feature.properties['angle']*4/Math.PI);
            popupString += '方向' + ': ' + winddirects[direct] + '<br />';
            popupString += '</div>';
            layer.bindPopup(popupString);
        }
    }
    else {
        var popupString = '<div class="popup">';
            popupString += '波浪高' + ': ' + feature.properties['value'] + '<br />';
            popupString += '</div>';
            layer.bindPopup(popupString);
    }
}

// marker过滤函数
function markerFilter(feature) {
    if(isNaN(feature.properties['value']))
            return false;
    if (markertype == 'wind') {
    }
    else if(markertype == 'arrow') {
        ;
    }
    else {
        if(feature.properties['value'] < 0)
            return false;
    }
    return true;
}

// 向overlayer上添加符号marker
function addMarker(feature, latlng) {
    return new L.Marker(latlng, {icon: L.icon({
        //"iconUrl":getMarkerUrl(markebaserurl, markertype, feature.properties['value'], feature.properties['angle'], markersize)})});
        "iconUrl":getStaticMarkerUrl(markertype, feature.properties['value'], feature.properties['angle'], markersize)})});
}


// for test
initMap();
//var resource="wrf", region="nwp", time=0, level=-1;
//var resource="wrf", region="ncs", time=0, level=-1;
//var resource="wrf", region="qd", time=0, level=-1;
//var resource="swan", region="nwp", time=0, level=-1;
//var resource="swan", region="ncs", time=0, level=-1;
//var resource="swan", region="qd", time=0, level=-1;
//var resource="wwiii", region="nwp", time=0, level=-1;   //data error
var resource="pom", region="ecs", time=0, level=-1;   //pos error
//var resource="pom", region="bh", time=0, level=-1;    // pos error
//var resource="roms", region="nwp", time=0, level=0;   //data error
//var resource="roms", region="ncs", time=0, level=0; //slow
//var resource="roms", region="qd", time=0, level=0;  // very slow
createOverlayLayer(resource, region, time, level);

// // test time-multilayers
// // todo: change model,  linear
// for(var i = 0; i < 5; i++) {
//     time = i;
//     createOverlayLayer(resource, region, time, level);
// }
// // // test layer animation
// layerAnimationTimer = window.setInterval(function(){layerAnimation()}, timer_interval);



