L.TDTLatLonLayer = L.TileLayer.extend({
    getTileUrl: function (tilePoint) {
        var map = this._map,
            zoom = map.getZoom();
        return L.Util.template(this._url, L.extend({
            s: this._getSubdomain(tilePoint),
            z: tilePoint.z,
            x: tilePoint.x,
            y: tilePoint.y - Math.pow(2, zoom-2)
        }, this.options));
    }
});

L.tdtLatLonLayer = function(defs, options){
    return new L.TDTLatLonLayer(defs,options);
};
