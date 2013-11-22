#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os,sys
import math
import Image, ImageDraw, aggdraw
import numpy as np

def hex2rgb(hex):
    r = hex >> 16
    g = (hex >> 8) & 0xff
    b = hex & 0xff
    return (r, g, b)

def rgb2hex(rgb):
    if rgb == None or len(rgb) != 3 or min(rgb) < 0 or max(rgb) > 255:
        return 0xFFFFFF
    return rgb[0] << 16 | rgb[1] << 8 | rgb[2]

def hsv2rgb(hsv):
    h = float(hsv[0])
    s = float(hsv[1])
    v = float(hsv[2])
    h60 = h / 60.0
    h60f = math.floor(h60)
    hi = int(h60f) % 6
    f = h60 - h60f
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    r, g, b = 0, 0, 0
    if hi == 0: r, g, b = v, t, p
    elif hi == 1: r, g, b = q, v, p
    elif hi == 2: r, g, b = p, v, t
    elif hi == 3: r, g, b = p, q, v
    elif hi == 4: r, g, b = t, p, v
    elif hi == 5: r, g, b = v, p, q
    r, g, b = int(r * 255), int(g * 255), int(b * 255)
    return [r, g, b]

def rgb2hsv(rgb):
    r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx-mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g-b)/df) + 360) % 360
    elif mx == g:
        h = (60 * ((b-r)/df) + 120) % 360
    elif mx == b:
        h = (60 * ((r-g)/df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = df/mx
    v = mx
    return [h, s, v]

#线性插值
def linear_gradient(v, v1,v2,h1,h2):
    k = (h2-h1)/(v2-v1)
    return h1+(v-v1)*k

#非线性插值, x 的2次方函数
def nolinear_gradient(v, v1,v2,h1,h2):
    x = (v-v1)/(v2-v1)*4
    if x < 2:
        y = math.pow(x, 2)
    else:
        y = 8 - math.pow(4-x, 2)
    return h1 +  (h2-h1)*y/8


fun_gradient = nolinear_gradient

def draw_legend(c_type):
    path = "static/legends/"
    v1 = 0.
    v2 = 186.
    h1 = 240.
    h2 = 0.
    size = (204, 34)
    delta_x = 10
    delta_y = 3
    delta_font_x = -5
    black_pen = aggdraw.Pen('black')
    font = aggdraw.Font('black', '/Library/Fonts/Georgia.ttf',10)
    img = Image.new("RGBA", size)
    draw = aggdraw.Draw(img)
    for i in range(int(v2)+1):
        h = fun_gradient(i, v1, v2, h1, h2)
        hsv = (h, 1., 1.)
        rgb = hsv2rgb(hsv)
        pen = aggdraw.Pen(tuple(rgb), 1)
        draw.line((i+delta_x,0+delta_y,i+delta_x,12+delta_y), pen)
    draw.rectangle((0+delta_x,0+delta_y,int(v2)+delta_x,12+delta_y), black_pen)
    if c_type == 'WindSpeed':
        xs = range(7)
        for x in xs:
            pos_x = x*26+13
            h = fun_gradient(pos_x, v1, v2, h1, h2)
            hsv = (h, 1., 1.)
            print(hsv2rgb(hsv))
            draw.line((pos_x+delta_x, 12+delta_y, pos_x+delta_x, 17+delta_y), black_pen)
            draw.text((pos_x+delta_x+delta_font_x, 20+delta_y), str((x+1)*5), font)
    elif c_type == 'WaveHeight':
        xs = range(6)
        for x in xs:
            pos_x = x*36
            h = fun_gradient(pos_x, v1, v2, h1, h2)
            hsv = (h, 1., 1.)
            print(hsv2rgb(hsv))
            draw.line((pos_x+delta_x, 12+delta_y, pos_x+delta_x, 17+delta_y), black_pen)
            draw.text((pos_x+delta_x+delta_font_x, 20+delta_y), str(x*5), font)
    elif c_type == 'CurrentSpeed':
        xs = range(5)
        for x in xs:
            pos_x = x*45.5
            h = fun_gradient(pos_x, v1, v2, h1, h2)
            hsv = (h, 1., 1.)
            print(hsv2rgb(hsv))
            draw.line((pos_x+delta_x, 12+delta_y, pos_x+delta_x, 17+delta_y), black_pen)
            draw.text((pos_x+delta_x+delta_font_x, 20+delta_y), "%.1f" % (x*.5), font)
    elif c_type == 'SurfaceWaterTemp':
        xs = range(6)
        for x in xs:
            pos_x = x*36
            draw.line((pos_x+delta_x, 12+delta_y, pos_x+delta_x, 17+delta_y), black_pen)
            draw.text((pos_x+delta_x+delta_font_x, 20+delta_y), str(30+x*10), font)
    elif c_type == 'BottomWaterTemp':
        xs = range(5)
        for x in xs:
            pos_x = x*34 + 27
            draw.line((pos_x+delta_x, 12+delta_y, pos_x+delta_x, 17+delta_y), black_pen)
            draw.text((pos_x+delta_x+delta_font_x, 20+delta_y), str(45+x*5), font)
    draw.flush()
    del draw
    img.save(path+c_type+".png", "png")


class Marker(object):
    def __init__(self, value, angle, size):
        self.value = value
        self.angle = angle
        self.sym = False
        self.color = (0, 0, 255)
        self.width = 2

        self.keycolors = [(0, 0, 255), (255, 0, 0)]
        self.keyvalues = [0, 12]

    def zoom(self):
        self.points = self.points*self.scale
        if hasattr(self, 'polygon'):
            self.polygon = self.polygon*self.scale

    def pan(self):
        self.points = self.points + self.pos
        if hasattr(self, 'polygon'):
            self.polygon = self.polygon + self.pos

    def rotate(self):
        if not self.sym:
            xx = np.array([[math.cos(self.angle), -math.sin(self.angle)], [math.sin(self.angle), math.cos(self.angle)]])
            self.points = self.points.dot(xx)
            if hasattr(self, 'polygon'):
                self.polygon = self.polygon.dot(xx)

    # 多段颜色模型
    def get_color_parts(self, value):
        part = 0
        for i in range(len(self.keyvalues)-1):
            if value < self.keyvalues[i]:
                break
            part += 1
        # value不可能比keyvalues[0]小，所以part最小为1
        # value不可能比keyvalues[-1]大, 所以part最大为len-1
        value1 = self.keyvalues[part-1]
        value2 = self.keyvalues[part]
        # rgb line
        # color1 = np.array(self.keycolors[part-1])
        # color2 = np.array(self.keycolors[part])
        # color = color1 + (value-value1)/(value2-value1)*(color2-color1)
        # hsv line
        hsv1 = rgb2hsv(self.keycolors[part-1])
        hsv2 = rgb2hsv(self.keycolors[part])
        h = fun_gradient(value, value1, value2, hsv1[0], hsv2[0])
        color = hsv2rgb([h, 1.0, 1.0])
        return [int(v) for v in color]

    def set_color(self):
        self.color =  self.get_color_parts(self.value)

    def init(self):
        self.zoom()
        self.rotate()
        self.pan()
        self.set_color()

    def draw_pil(self, draw):
        pass

    def draw_agg(self, draw):
        pass

class WindMarker(Marker):
    def __init__(self, value, angle, size):
        Marker.__init__(self, value, angle, size)
        self.angle = self.angle + math.pi/2
        self.value = float(value)
        self.scale = size / 8
        self.pos = size / 2
        self.keycolors = [(0, 0, 255), (0, 9, 255), (255, 17, 0), (255, 0, 0)]
        self.keyvalues = [0., 5., 35., 100.]
        if self.value > self.keyvalues[-1]:
            self.value = self.keyvalues[-1]-0.00001
        if self.value < self.keyvalues[0]:
            self.value = self.keyvalues[0]
        self.level = self.speed2level(self.value)
        if self.level < 9:
            points = np.array([[0, 4], [0, 0], [0, 0], [1, 0], [1, 0], [2, 0], [0, 1], [1, 1], [1, 1], [2, 1], [0, 2], [1, 2], \
                [1, 2], [2, 2], [0, 3], [1, 3], [1, 3], [2, 3]])
            self.points = points[0:2*(self.level+1)]
        else:
            self.points = np.array([[0, 4], [0, 0], [0, 0], [2, 2], [0, 2], [2, 2]])
        self.init()

    def speed2level(self, speed):
        values = [0.3, 1.6, 3.4, 5.5, 8.0, 10.8, 13.9, 17.2, 20.8, 24.5, 28.5, 32.6, 32.6]
        for i in range(len(values)):
            if speed < values[i]:
                break
        return i

    def level2speed(self, level):
        values = [0.3, 1.6, 3.4, 5.5, 8.0, 10.8, 13.9, 17.2, 20.8, 24.5, 28.5, 32.6, 32.6]
        if level > len(values) - 1:
            level = len(values) - 1
        return values[level]

    def draw_pil(self, draw):
        for it in range(len(self.points)/2):
            draw.line(tuple(list(self.points[2*it]) + list(self.points[2*it+1])), fill = tuple(self.color), width = self.width)

    def draw_agg(self, draw):
        draw.setantialias(True)
        pen = aggdraw.Pen(tuple(self.color), self.width)
        for it in range(len(self.points)/2):
            draw.line(tuple(list(self.points[2*it]) + list(self.points[2*it+1])), pen)
        draw.flush()

class SquareMarker(Marker):
    def __init__(self, value, angle, size):
        Marker.__init__(self, value, angle, size)
        self.sym = True
        self.scale = size
        self.pos = 0
        self.value = float(value)
        self.keycolors = [(0, 0, 255), (0, 255, 204), (255, 104, 0), (255, 0, 0)]
        self.keyvalues = [0., 1., 10., 100.]
        if self.value > self.keyvalues[-1]:
            self.value = self.keyvalues[-1]-0.00001
        elif self.value < self.keyvalues[0]:
            self.value = self.keyvalues[0]
        self.points = np.array([[0, 0], [1, 1]])
        self.init()
    def draw_pil(self, draw):
        draw.rectangle(tuple(list(self.points[0]) + list(self.points[1])), fill = tuple(self.color))
    def draw_agg(self, draw):
        draw.setantialias(True)
        pen = aggdraw.Pen(tuple(self.color), self.width)
        brush = aggdraw.Brush(tuple(self.color))
        draw.rectangle(tuple(list(self.points[0]) + list(self.points[1])), pen, brush)
        draw.flush()

class ArrowMarker(Marker):
    def __init__(self, value, angle, size):
        Marker.__init__(self, value, angle, size)
        self.angle = self.angle - math.pi/2
        self.scale = size / 6
        self.pos = size / 2
        self.width = 1

        self.value = float(value)
        self.keycolors = [(0, 0, 255), (255, 144, 0), (255, 0, 0)]
        self.keyvalues = [0.0, 2.0, 10.0]
        if self.value > self.keyvalues[-1]:
            self.value = self.keyvalues[-1]-0.00001
        elif self.value < self.keyvalues[0]:
            self.value = self.keyvalues[0]

        self.points = np.array([[0, 0], [0, 3]])
        self.polygon = np.array([[-.5, 1], [0, 0], [.5, 1]])
        self.init()
    def draw_pil(self, draw):
        points = list(self.polygon[0]) + list(self.polygon[1]) + list(self.polygon[2]) + list(self.polygon[0])
        #points = reduce(lambda pt: list(pt), self.polygon, )
        draw.polygon(tuple(points), fill = tuple(self.color))
        draw.line(tuple(list(self.points[0]) + list(self.points[1])), fill = tuple(self.color), width = self.width)
    def draw_agg(self, draw):
        draw.setantialias(True)
        points = list(self.polygon[0]) + list(self.polygon[1]) + list(self.polygon[2]) + list(self.polygon[0])
        pen = aggdraw.Pen(tuple(self.color), self.width)
        brush = aggdraw.Brush(tuple(self.color))
        draw.polygon(tuple(points), pen, brush)
        draw.line(tuple(list(self.points[0]) + list(self.points[1])), pen)
        draw.flush()

def generate_wind_markers(size = 32):
    path = "static/markers"
    markername = "Wind"
    for j in range(40):
        path2 = os.path.join(path, markername.lower(), str(int(j)))
        if not os.path.isdir(path2):
            os.makedirs(path2)
        for i in range(360):
            marker = globals()[markername+'Marker'](j, i/180.*math.pi, size)
            img = Image.new("RGBA", (size, size))
            #draw = ImageDraw.Draw(img)
            #marker.draw_pil(draw)
            draw = aggdraw.Draw(img)
            marker.draw_agg(draw)
            del draw
            filename = os.path.join(path2, str(i) + '_' + str(size) + '.png')
            img.save(filename, "PNG")

def generate_arrow_markers(size = 32):
    path = "static/markers"
    markername = "Arrow"
    for j in range(25):
        j = j/10.
        path2 = os.path.join(path, markername.lower(), "%.1f" % j)
        if not os.path.isdir(path2):
            os.makedirs(path2)
        for i in range(360):
            marker = globals()[markername+'Marker'](j, i/180.*math.pi, size)
            img = Image.new("RGBA", (size, size))
            # draw = ImageDraw.Draw(img)
            # marker.draw_pil(draw)
            draw = aggdraw.Draw(img)
            marker.draw_agg(draw)
            del draw
            filename = os.path.join(path2, str(i) + '_' + str(size) + '.png')
            img.save(filename, "PNG")

def generate_square_markers(size = 32):
    path = "static/markers"
    markername = "Square"
    path2 = os.path.join(path, markername.lower())
    if not os.path.isdir(path2):
        os.makedirs(path2)
    for i in range(256):
        i = i/10.
        marker = globals()[markername+'Marker'](i, 0, size)
        img = Image.new("RGBA", (size, size))
        # draw = ImageDraw.Draw(img)
        # marker.draw_pil(draw)
        draw = aggdraw.Draw(img)
        marker.draw_agg(draw)
        del draw
        temp = "%.1f" % i
        filename = os.path.join(path2, temp + '_' + str(size) + '.png')
        img.save(filename, "PNG")

def test():
    marker = WindMarker(4.7, 5.2, 64)
    #marker = SquareMarker(0.1, 0, 64)
    #marker = ArrowMarker(4.1, 0, 64)
    size = (64,64)
    img = Image.new("RGBA", size)
    draw = ImageDraw.Draw(img)
    marker.draw_pil(draw)
    del draw
    #img = img.resize(size, Image.ANTIALIAS)
    img.save("test.png", "PNG")

def markers():
    #generate_wind_markers(32)
    generate_square_markers(16)
    #generate_arrow_markers(32)

def legends():
    legends = ['WindSpeed', 'WaveHeight', 'CurrentSpeed', 'SurfaceWaterTemp', 'BottomWaterTemp']
    legends = ['WaveHeight']
    for c_type in legends:
        draw_legend(c_type)

if __name__ == '__main__':
    markers()
    #test()
    #legends()
