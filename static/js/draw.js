var MultiPolyline = L.multiPolyline([
      [
         [35,120],
         [35,120.5]
      ],
      [
         [35.5,120],
         [35.5,120.5]
      ],
      [
         [34,120],
         [35.5,120]
      ]],
      {color: 'red',weight:'2',opacity:'0.8'}
    ).addTo(map);
    /*
    var group= L.layerGroup();
    for(i=0;i<50;i++)
    {
       for(j=0;j<50;j++)
       {
           group
             .addLayer(L.polyline([[25+0.5*i,115+0.5*j],
             [25.5+0.5*i,115.5+0.5*j]], {color: 'green',weight:'2',opacity:'0.8'}));
       }
    }
    group.addTo(map);
    */
    /*
    var groupPolygon= L.layerGroup();
    for(m=0;m<50;m++)
       for(n=0;n<50;n++)
       {
           rgb = 'RGB('+ (m*5) + ',' + (255-n*5) + ',0)';
           //alert(rgb);
           groupPolygon.addLayer(L.polygon([
                [30+m*0.1,120.1+n*0.1],
                [30+m*0.1,120+n*0.1],
                [30.1+m*0.1,120+n*0.1],
                [30.1+m*0.1,120.1+n*0.1]
                ],{color:rgb, weight:'2',opacity:'1',fillOpacity:'1'})
            );
       }
    groupPolygon.addTo(map);*/
    /*
    var recgroup=L.layerGroup();
    for(m=0;m<50;m++)
       for(n=0;n<50;n++)
       {
           rgb = 'RGB('+ (m*5) + ',' + (255-n*5) + ',0)';
           recgroup.addLayer(L.rectangle([
                [30+m*0.2,120+n*0.2],
                [30.2+m*0.1,120.2+n*0.2]
                ],{color:rgb, weight:'2',opacity:'1',fillOpacity:'1'})
            );
       }
    recgroup.addTo(map);
    var rec=L.rectangle([[30,110],[31,111]]).addTo(map);
    */

    //map.on('zoomend',function(){alert(map.getZoom());});

    //map.fitBounds(drawF(30,100,16,1).getBounds());

    var drawF=function(lat,lon,speed,angle){
        var symbol;
        //angle+=Math.PI;
        //var aa=new Array({X:1,Y:1},{X:1,Y:1});
        //alert(aa[1].X);
        //var aa={X:1,Y:1};
        //alert(aa.X);
        var zoom = map.getZoom()+2;
        var orinF = new L.LatLng(lat, lon);
        var endX=lon+Math.cos(angle)*zoom/10;
        var endY=lat+Math.sin(angle)*zoom/10;
        var endF=new L.LatLng(endY,endX);
        var tailX=lon+11*Math.cos(angle)*zoom/100;
        var tailY=lat+11*Math.sin(angle)*zoom/100;
        var tailF=new L.LatLng(tailY,tailX);
        var col=setcolor(speed);
        //零级风
        if(speed >= 0 && speed < 0.3){
            symbol=L.polyline([orinF,endF]
            ,{color: setcolor(speed),weight:'2',opacity:'0.8'}
            );
        }
        else if(speed >= 0.3){
            //一级风
            if(speed < 1.6){
                var x1=endX+3*Math.cos(angle-Math.PI/2+0.3)*zoom/100;
                var y1=endY+3*Math.sin(angle-Math.PI/2+0.3)*zoom/100;
                var grade1=new L.LatLng(y1,x1);
                symbol=L.multiPolyline([
                    [orinF,tailF],
                    [endF,grade1]
                ],{color: setcolor(speed),weight:'2',opacity:'0.8'}
                );
            }
            else{
                var x2=endX+6*Math.cos(angle-Math.PI/2+0.3)*zoom/100;
                var y2=endY+6*Math.sin(angle-Math.PI/2+0.3)*zoom/100;
                var grade2=new L.LatLng(y2,x2);
                //二级风
                if(speed < 3.4){
                    symbol=L.multiPolyline([
                        [orinF,tailF],
                        [endF,grade2]
                    ],{color: setcolor(speed),weight:'2',opacity:'0.8'}
                    );
                }
                else{
                    var mPos2X=lon+8*Math.cos(angle)*zoom/100;
                    var mPos2Y=lat+8*Math.sin(angle)*zoom/100;
                    var mPos2=new L.LatLng(mPos2Y,mPos2X);
                    //三级风
                    if(speed < 5.5){
                        var x3=mPos2X+3*Math.cos(angle-Math.PI/2+0.3)*zoom/100;
                        var y3=mPos2Y+3*Math.sin(angle-Math.PI/2+0.3)*zoom/100;
                        var grade3=new LatLng(y3,x3);
                        symbol=L.multiPolyline([
                            [orinF,tailF],
                            [endF,grade2],
                            [mPos2,grade3]
                        ],{color: setcolor(speed),weight:'2',opacity:'0.8'}
                        );
                    }
                    else{
                        var x4=mPos2X+6*Math.cos(angle-Math.PI/2+0.3)*zoom/100;
                        var y4=mPos2Y+6*Math.sin(angle-Math.PI/2+0.3)*zoom/100;
                        var grade4=new L.LatLng(y4,x4);
                        //四级风
                        if(speed < 8.0){
                            symbol=L.multiPolyline([
                                [orinF,tailF],
                                [endF,grade2],
                                [mPos2,grade4]
                            ],{color: setcolor(speed),weight:'2',opacity:'0.8'}
                            );
                        }
                        else{
                            var mPos3X=lon+6*Math.cos(angle)*zoom/100;
                            var mPos3Y=lat+6*Math.sin(angle)*zoom/100;
                            var mPos3=new L.LatLng(mPos3Y,mPos3X);
                            //五级风
                            if(speed < 10.8){
                                var x5=mPos3X+3*Math.cos(angle-Math.PI/2+0.3)*zoom/100;
                                var y5=mPos3Y+3*Math.sin(angle-Math.PI/2+0.3)*zoom/100;
                                var grade5=new L.LatLng(y5,x5);
                                symbol=L.multiPolyline([
                                    [orinF,tailF],
                                    [endF,grade2],
                                    [mPos2,grade4],
                                    [mPos3,grade5]
                                ],{color: setcolor(speed),weight:'2',opacity:'0.8'}
                                );
                            }
                            else{
                                var x6=mPos3X+6*Math.cos(angle-Math.PI/2+0.3)*zoom/100;
                                var y6=mPos3Y+6*Math.sin(angle-Math.PI/2+0.3)*zoom/100;
                                var grade6=new L.LatLng(y6,x6);
                                //六级风
                                if(speed < 13.9){
                                    symbol=L.multiPolyline([
                                        [orinF,tailF],
                                        [endF,grade2],
                                        [mPos2,grade4],
                                        [mPos3,grade6]
                                    ],{color: setcolor(speed),weight:'2',opacity:'0.8'}
                                    );
                                }
                                else{
                                    var mPos4X=lon+4*Math.cos(angle)*zoom/100;
                                    var mPos4Y=lat+4*Math.sin(angle)*zoom/100;
                                    var mPos4=new L.LatLng(mPos4Y,mPos4X);
                                    //七级风
                                    if(speed < 17.2){
                                        var x7=mPos4X+3*Math.cos(angle-Math.PI/2+0.3)*zoom/100;
                                        var y7=mPos4Y+3*Math.sin(angle-Math.PI/2+0.3)*zoom/100;
                                        var grade7=new L.LatLng(y7,x7);
                                        symbol=L.multiPolyline([
                                            [orinF,tailF],
                                            [endF,grade2],
                                            [mPos2,grade4],
                                            [mPos3,grade6],
                                            [mPos4,grade7]
                                        ],{color: setcolor(speed),weight:'3',opacity:'0.8'}
                                        );
                                    }
                                    //八级风+
                                    else{
                                        symbol=L.multiPolyline([
                                            [orinF,tailF],
                                            [endF,grade4],
                                            [mPos3,grade4],
                                        ],{color: setcolor(speed),weight:'2',opacity:'0.8'}
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

    //map.on('zoomend',function(){drawF(30,100,16,1).addTo(map);});
    //drawF(30,100,16,1).addTo(map);
    function setcolor(speed){
        var col, r, g, b;
        if (speed >= 0 && speed < 5) {
            col = speed - 0;
            r = 0;
            g = Math.round(col * 51);
            b = 255;
        }
        else if (speed >= 5 && speed < 10) {
            col = speed - 5;
            r = 0;
            g = 255;
            b = Math.round(255 - col * 51);
        }
        else if (speed >= 10 && speed < 15) {
            col = speed - 10;
            r = Math.round(col * 51);
            g = 255;
            b = 0;
        }
        else if (speed >= 15 && speed < 20) {
            col = speed - 15;
            r = 255;
            g = Math.round(255 - col * 51);
            b = 0;
        }
        else {
            r = 255;
            g = 0;
            b = 0;
        }
        return 'RGB('+r+','+g+','+b+')';
    }
