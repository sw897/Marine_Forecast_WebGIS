
// marker符号后处理
function onEachMarker (feature, layer) {
    if (feature.properties) {
        var val = feature.properties['value'];
        var value = val[0];
        var angle = val[1];
        var popupString = '<div class="popup">';
        popupString += 'value' + ': ' + value + '<br />';
        popupString += 'angle' + ': ' + angle + '<br />';
        popupString += '</div>';
        layer.bindPopup(popupString);
    }
}

// marker过滤函数
function markerFilter(feature) {
    return true;
}

// 向overlay上添加 marker
function addWindMarker(feature, latlng) {
    var val = feature.properties['value'];
    var value = val[0];
    var angle = val[1];
    return arrowSymbol(latlng, value, angle);
}

function addWindMarker(feature, latlng) {
    var val = feature.properties['value'];
    var value = val[0];
    var angle = val[1];
    return arrowSymbol(latlng, value, angle);
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
