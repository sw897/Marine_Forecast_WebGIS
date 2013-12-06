/*
  * variables, 有用的全局变量
  */
// 可能变化
var tileBaseUrl = "http://127.0.0.1:8080/v1/tiles/webmercator";
var imageBaseLayer = "http://127.0.0.1:8080/v1/images/webmercator";
var legendBaseUrl = "http://127.0.0.1:8080/v1/legends";
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
var popup = L.popup();

// 全局配置对象
var config = {
    "map":{
        "center":[36, 120],
        "level":2
    },
    "markers":{
        "wrf":{"marker":"wind", "size":32},
        "pom":{"marker":"arrow", "size":32},
        "roms":{"marker":"arrow", "size":32},
        "fvcom":{"marker":"arrow", "size":32}
    },
    "wrf": {
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
    "swan": {
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
    "ww3": {
        "nwp":{
            "bounds":[[15., 105.],[47., 140.]],
            "times":72,
            "levels":1,
            "forecast_time":0
        }
    },
    "pom":{
        "ecs":{
            "bounds":[[24.5, 117.5],[42., 137.]],
            "times":24,
            "levels":1,
            "forecast_time":0
        },
        "ncs":{
            "bounds":[[33.9791, 117.473],[40.9791, 124.973]],
            "times":24,
            "levels":1,
            "forecast_time":0
        },
        "bh":{
            "bounds":[[37.2, 117.5],[42., 122.]],
            "times":72,
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
        },
        "qdsea":{
            "bounds":[[34.2846, 119.174],[36.8493, 122.]],
            "times":72,
            "levels":1,
            "forecast_time":0
        }
    },
    "fvcomtid":{
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
  * functions, 有用的全局函数
  */
// 初始化地图
function initMap() {
    map = L.map('map', {crs: L.CRS.EPSG3395}).setView(config.map.center, config.map.level);
    var baselayerurl = 'http://services.arcgisonline.com/ArcGIS/rest/services/Ocean_Basemap/MapServer/tile/{z}/{y}/{x}';
    baseLayer = L.tileLayer(baselayerurl, {noWrap:false});
    baseLayer.addTo(map);
    addLabelLayer();
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
    themeLayer = null;
}

function queryThemeLayer() {
}

function changeThemeLayer(resource, region) {
    if(themeLayer != null && map.hasLayer(themeLayer))
        removeThemeLayer();
    if(resource == 'swan' || resource == 'ww3') {
        themeLayer = getImageOverlay(resource, region);
    }
    else if(resource == 'wrf' || resource == 'pom' || resource == 'fvcomstm' || resource == 'fvcomtid'){
        // use geojson or image
        //themeLayer = addGeoJSONOverlay(resource, region);
        var tileLayer = getTileOverlay(resource, region);
        var imageLayer = getImageOverlay(resource, region);
        themeLayer = L.layerGroup();
        themeLayer.addLayer(tileLayer);
        themeLayer.addLayer(imageLayer);
    }
    else if(resource == 'roms'){
        themeLayer = getTileOverlay(resource, region);
    }
    if(themeLayer != null)
        map.addLayer(themeLayer)
    g_resource = resource;
    g_region = region;
    map.fitBounds(config[resource][region]["bounds"]);
    var url = getLegendUrl(legendBaseUrl, resource, region);
    //alert(url);
    var imgstr = '<img src="'+url+'" class="img-thumbnail" style="margin-right: 50px;" />';
    $('mybb').add(imgstr)
}

// 创建并添加专题图层
function getImageOverlay(resource, region) {
    var time = arguments[2]?arguments[2]:0;
    var level = arguments[3]?arguments[3]:0;
    var variable = arguments[4]?arguments[4]:'default';
    var bounds = config[resource][region]["bounds"];
    // bug: y方向有偏差,但不清楚引入的原因,在此强制移动
    var min = L.latLng(bounds[0][0] + .16, bounds[0][1])
    var max = L.latLng(bounds[1][0] + .16, bounds[1][1])
    var url = getImageUrl(imageBaseLayer, resource, region, time, level, variable);
    overlay = L.imageOverlay(url, [min,max], {'opacity':.7});
    //map.addLayer(overlay);
    return overlay;
}

function getTileOverlay(resource, region) {
    var time = arguments[2]?arguments[2]:0;
    var level = arguments[3]?arguments[3]:0;
    var bounds = config[resource][region]["bounds"];
    var url = getImageTileUrl(tileBaseUrl, resource, region, time, level);
    var overlay = L.tileLayer(url, {
            bounds: bounds
        }
    );
    //map.addLayer(overlay);
    return overlay;
    //animationLayers.push(overlay);
}

function addGeoJSONOverlay(resource, region) {
    var time = arguments[2]?arguments[2]:0;
    var level = arguments[3]?arguments[3]:0;
    // update global variables
    if(resource != 'wrf') {
        markertype = 'arrow'
    }else {
        markertype = 'wind'
    }
    var bounds = config[resource][region]["bounds"];
    var url = getJsonTileUrl(tileBaseUrl, resource, region, time, level);
    var overlay = L.tileLayer.geojson(url, {
            bounds: bounds
        }, {
            opacity:1.0,
            onEachFeature: onEachMarker,
            filter: markerFilter,
            pointToLayer: addMarker
        }
    );
    map.addLayer(overlay);
    return overlay;
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

function onMapClick(e) {
    popup
        .setLatLng(e.latlng)
        .setContent("clicked at " + e.latlng.toString())
        .openOn(map);
}

// marker符号后处理
function onEachMarker (feature, layer) {
    if (feature.properties) {
        var val = feature.properties['value'];
        var value = val[0];
        var angle = val[1];
        var popupString = '<div class="popup">';
        if (markertype == 'wind') {
            popupString += '风力' + ': ' + value + '<br />';
            var direct = Math.round(angle*4/Math.PI);
            popupString += '风向' + ': ' + winddirects[direct] + '<br />';
        }
        else if(markertype == 'arrow') {
            popupString += '速度' + ': ' + value + '<br />';
            var direct = Math.round(angle*4/Math.PI);
            popupString += '方向' + ': ' + winddirects[direct] + '<br />';
        }
        else {
            popupString += '波浪高' + ': ' + value + '<br />';
        }
        popupString += '</div>';
        layer.bindPopup(popupString);
    }
}

// marker过滤函数
function markerFilter(feature) {
    return true;
}

// 向overlay上添加符号marker
function addMarker(feature, latlng) {
    var val = feature.properties['value'];
    var value = val[0];
    var angle = val[1];
    //return new L.Marker(latlng, {icon: L.icon({"iconUrl":getStaticMarkerUrl(markertype, value, angle, markersize)})});
    if(markertype=='wind') {
        return windSymbol(latlng, value, angle);
    } else {
        return arrowSymbol(latlng, value, angle);
    }
}

var arrowSymbol = function(latlng,speed,angle){
    var lat=latlng.lat;
    var lon=latlng.lng;
    var zoom = map.getZoom();
    //在确定zoom下地图在X或Y方向的切片数
    //地图按四叉树切片，zoom=0时整体作为一块，WGS84投影世界地图拉伸为正方形
    var tiles=Math.pow(2,zoom-1);
    var pixelX=360/(256*tiles);//一个tile对应的像素为256*256
    var pixelY=pixelX/2;
    var length=10;//length为箭头长度所占像素数
    var wingLen=3;//箭头两翅长度
    var orin=latlng;
    //箭头长度比例设定
    var maxSpeed=1;
    var minSpeed=0;
    var ratio=(speed-minSpeed)/(maxSpeed-minSpeed)+1/2.0;
    if(ratio>1){
        ratio=1;
    }
    var endX=lon+Math.cos(angle)*pixelX*length*ratio;//X为X轴方向分量
    var endY=lat+Math.sin(angle)*pixelY*length*ratio;
    var end=new L.LatLng(endY,endX);
    var leftX=endX+Math.cos(parseFloat(angle)+Math.PI*5/6)*pixelX*wingLen*ratio;
    var leftY=endY+Math.sin(parseFloat(angle)+Math.PI*5/6)*pixelY*wingLen*ratio;
    var left=new L.LatLng(leftY,leftX);
    var rightX=endX+Math.cos(parseFloat(angle)+Math.PI*7/6)*pixelX*wingLen*ratio;
    var rightY=endY+Math.sin(parseFloat(angle)+Math.PI*7/6)*pixelY*wingLen*ratio;
    var right=new L.LatLng(rightY,rightX);
    var symbol=L.multiPolygon([[orin,end],
            [left,end,right]
            ],{color: '#03f', weight:1, opacity:1, fillOpacity:1}
        );
    return symbol;
};

var windSymbol = function(latlng,speed,angleStr){
    var lat=latlng.lat;
    var lon=latlng.lng;
    var symbol;
    var angle=parseFloat(angleStr)+Math.PI;//angleStr为风向与X轴正向夹角
    var zoom = map.getZoom();
    //在确定zoom下地图在X或Y方向的切片数
    //地图按四叉树切片，zoom=0时整体作为一块，WGS84投影世界地图拉伸为正方形
    var tiles=Math.pow(2,zoom-1);
    var pixelX=360/(256*tiles);//一个tile对应的像素为256*256
    var pixelY=pixelX/2;
    var n=8;//n为风矢主杆长度所占像素数
    var orinF = latlng;
    var endX=lon+Math.cos(angle)*pixelX*n;//X为X轴方向分量
    var endY=lat+Math.sin(angle)*pixelY*n;
    var endF=new L.LatLng(endY,endX);
    var tailX=lon+11*Math.cos(angle)*pixelX*n/10;
    var tailY=lat+11*Math.sin(angle)*pixelY*n/10;
    var tailF=new L.LatLng(tailY,tailX);
    //零级风
    if(speed >= 0 && speed < 0.3){
        symbol=L.polyline([orinF,endF]
        ,{color:'#03f',weight:1,opacity:1}
        );
    }
    else if(speed >= 0.3){
        //一级风
        if(speed < 1.6){
            var x1=endX+3*Math.cos(angle-Math.PI/2+0.3)*pixelX*n/10;
            var y1=endY+3*Math.sin(angle-Math.PI/2+0.3)*pixelY*n/10;
            var grade1=new L.LatLng(y1,x1);
            symbol=L.multiPolyline([
                [orinF,tailF],
                [endF,grade1]
            ],{color:'#03f',weight:1,opacity:1}
            );
        }
        else{
            var x2=endX+6*Math.cos(angle-Math.PI/2+0.3)*pixelX*n/10;
            var y2=endY+6*Math.sin(angle-Math.PI/2+0.3)*pixelY*n/10;
            var grade2=new L.LatLng(y2,x2);
            //二级风
            if(speed < 3.4){
                symbol=L.multiPolyline([
                    [orinF,tailF],
                    [endF,grade2]
                ],{color:'#03f',weight:1,opacity:1}
                );
            }
            else{
                var mPos2X=lon+8*Math.cos(angle)*pixelX*n/10;
                var mPos2Y=lat+8*Math.sin(angle)*pixelY*n/10;
                var mPos2=new L.LatLng(mPos2Y,mPos2X);
                //三级风
                if(speed < 5.5){
                    var x3=mPos2X+3*Math.cos(angle-Math.PI/2+0.3)*pixelX*n/10;
                    var y3=mPos2Y+3*Math.sin(angle-Math.PI/2+0.3)*pixelY*n/10;
                    var grade3=new L.LatLng(y3,x3);
                    symbol=L.multiPolyline([
                        [orinF,tailF],
                        [endF,grade2],
                        [mPos2,grade3]
                    ],{color:'#03f',weight:1,opacity:1}
                    );
                }
                else{
                    var x4=mPos2X+6*Math.cos(angle-Math.PI/2+0.3)*pixelX*n/10;
                    var y4=mPos2Y+6*Math.sin(angle-Math.PI/2+0.3)*pixelY*n/10;
                    var grade4=new L.LatLng(y4,x4);
                    //四级风
                    if(speed < 8.0){
                        symbol=L.multiPolyline([
                            [orinF,tailF],
                            [endF,grade2],
                            [mPos2,grade4]
                        ],{color:'#03f',weight:1,opacity:1}
                        );
                    }
                    else{
                        var mPos3X=lon+6*Math.cos(angle)*pixelX*n/10;
                        var mPos3Y=lat+6*Math.sin(angle)*pixelY*n/10;
                        var mPos3=new L.LatLng(mPos3Y,mPos3X);
                        //五级风
                        if(speed < 10.8){
                            var x5=mPos3X+3*Math.cos(angle-Math.PI/2+0.3)*pixelX*n/10;
                            var y5=mPos3Y+3*Math.sin(angle-Math.PI/2+0.3)*pixelY*n/10;
                            var grade5=new L.LatLng(y5,x5);
                            symbol=L.multiPolyline([
                                [orinF,tailF],
                                [endF,grade2],
                                [mPos2,grade4],
                                [mPos3,grade5]
                            ],{color:'#03f',weight:1,opacity:1}
                            );
                        }
                        else{
                            var x6=mPos3X+6*Math.cos(angle-Math.PI/2+0.3)*pixelX*n/10;
                            var y6=mPos3Y+6*Math.sin(angle-Math.PI/2+0.3)*pixelY*n/10;
                            var grade6=new L.LatLng(y6,x6);
                            //六级风
                            if(speed < 13.9){
                                symbol=L.multiPolyline([
                                    [orinF,tailF],
                                    [endF,grade2],
                                    [mPos2,grade4],
                                    [mPos3,grade6]
                                ],{color:'#03f',weight:1,opacity:1}
                                );
                            }
                            else{
                                var mPos4X=lon+4*Math.cos(angle)*pixelX*n/10;
                                var mPos4Y=lat+4*Math.sin(angle)*pixelY*n/10;
                                var mPos4=new L.LatLng(mPos4Y,mPos4X);
                                //七级风
                                if(speed < 17.2){
                                    var x7=mPos4X+3*Math.cos(angle-Math.PI/2+0.3)*pixelX*n/10;
                                    var y7=mPos4Y+3*Math.sin(angle-Math.PI/2+0.3)*pixelY*n/10;
                                    var grade7=new L.LatLng(y7,x7);
                                    symbol=L.multiPolyline([
                                        [orinF,tailF],
                                        [endF,grade2],
                                        [mPos2,grade4],
                                        [mPos3,grade6],
                                        [mPos4,grade7]
                                    ],{color:'#03f',weight:1,opacity:1}
                                    );
                                }
                                //八级风+
                                else{
                                    symbol=L.multiPolyline([
                                        [orinF,endF],
                                        [endF,grade4],
                                        [mPos3,grade4],
                                    ],{color:'#03f',weight:1,opacity:1}
                                    );
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    return symbol;
};

window.onload=initMap()
