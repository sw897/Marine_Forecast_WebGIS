#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import numpy as np
from scipy.spatial import ConvexHull, convex_hull_plot_2d
from scipy.spatial import Delaunay, delaunay_plot_2d
from scipy.spatial import Voronoi, voronoi_plot_2d
from shapely import geometry
import matplotlib.pyplot as plt

class Point():
    def __init__(self,x,y):
        self.x = x
        self.y = y

def GetAreaOfTriangle(p1,p2,p3):
    '''计算三角形面积'''
    area = 0
    p1p2 = GetLineLength(p1,p2)
    p2p3 = GetLineLength(p2,p3)
    p3p1 = GetLineLength(p3,p1)
    s = (p1p2 + p2p3 + p3p1)/2
    area = s*(s-p1p2)*(s-p2p3)*(s-p3p1)
    area = math.sqrt(area)
    return area


def GetLineLength(p1,p2):
    '''计算边长'''
    length = math.pow((p1.x-p2.x),2) + math.pow((p1.y-p2.y),2)
    length = math.sqrt(length)
    return length

def getVirPoints(hull):
    polygon = geometry.Polygon([hull.points[id] for id in hull.vertices])
    dis = polygon.length*1./len(polygon.exterior.coords)
    print dis
    paraline = polygon.exterior.parallel_offset(distance=dis, side='right', join_style=2, mitre_limit=9999999.)
    #print paraline.coords
    #return np.append(np.array(paraline.coords), np.array(paraline.coords(0)), axis = 0)
    return np.array(paraline.coords)

points = np.random.rand(5, 2)
plt.plot(points[:,0], points[:,1], 'o')
#print round(math.sqrt(.5)*len(points))
hull = ConvexHull(points=points)
for simplex in hull.simplices:
    plt.plot(points[simplex,0], points[simplex,1], 'k-')
# plt.show()
tri = Delaunay(points=points)
#plt.triplot(points[:,0], points[:,1], tri.simplices.copy(), 'r-')
# plt.triplot(points[:,0], points[:,1], tri.simplices.copy())
# plt.plot(points[:,0], points[:,1], 'o')
# plt.show()

#vor = Voronoi(points)
# voronoi_plot_2d(vor)
# plt.show()

#print hull.vertices
#temp = np.array([hull.points[id] for id in hull.vertices])
#plt.plot(temp[:,0], temp[:,1], 'r-')
virpoints = getVirPoints(hull)
plt.plot(virpoints[:,0], virpoints[:,1], 'o')
#plt.plot(virpoints[:,0], virpoints[:,1], 'b--')
plt.show()

points = np.append(points, virpoints, axis=0)
tri = Delaunay(points=points)
#plt.triplot(points[:,0], points[:,1], tri.simplices.copy(), 'g--')

vor = Voronoi(points, furthest_site=False)
voronoi_plot_2d(vor)
plt.show()
