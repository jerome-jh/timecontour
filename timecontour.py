#!/usr/bin/python

# Copyright 2015 Jerome Hourioux
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import urllib
import tempfile
import json
import sklearn.neighbors
import matplotlib.pyplot as plt
import matplotlib.cm
import matplotlib.colors
import numpy as np
import datetime

## Notre-Dame parvis in Paris
origin_x=2.34880
origin_y=48.85330

## Rectangle bounds
x_min = float(2)
x_max = float(2.7)
y_min = float(48.6)
y_max = float(49.1)

## Number of points to sample
n_points = 100

name = "time"

epsilon = 0.000000001

url = "https://maps.googleapis.com/maps/api/distancematrix/json?key=%s&mode=driving&units=metric&origins=%.6f,%.6f&destinations=%.6f,%.6f"

print_debug = False

def error(s):
  sys.stderr.write(s);
  exit(1)

def debug(s):
  if print_debug == True:
    sys.stderr.write(s);

def read_key():
  k = ""
  f = open("key.txt")
  if f == None:
    error("Cannot open key.txt. Exiting!\n")
  for l in f:
    ## Skip comments
    if l[0] == '#':
      continue
    else:
      if k == "":
        k = l.strip()
      else:
        error("Invalid key.txt format\n")
  if k == "":
    error("No key in key.txt\n")
  return k

def optim_param():
  L = float(abs(x_max-x_min))
  H = float(abs(y_max-y_min))
  N = int(n_points)
  min_score = N

  for n in range(2,N/2+1):
    m = N/n
    r = N - n*m
    dl = L/n
    dh = H/m
    score = r + (dl - dh)*(dl - dh)
    if score < min_score:
      min_score = score
      best = (n,m)

  debug("best " + str(best) + " score " + str(min_score) + "\n")
  return best

def parse(j):
  if j["status"] == "OVER_QUERY_LIMIT":
    error("Query quota exceeded\n")
  if j["status"] == "REQUEST_DENIED":
    error("Request denied\n")
  if j["status"] == "OK":
    if j["rows"][0]["elements"][0]["status"] == "OK":
      # Extract time
      t = int(j["rows"][0]["elements"][0]["duration"]["value"]);
      return t, None
    else:
      # Typically, no route from origin to destination
      return -1, j["rows"][0]["elements"][0]["status"]
  else:
    # Unspecified, non fatal error
    return -1, j["status"]

## Query the server with given coordinates
## Returns json object
def retrieve(x,y):
  u = url % (key, origin_y, origin_x, y, x)
  t = tempfile.NamedTemporaryFile()
  ## For debug
  #t = open(name + ".json", "w+")
  urllib.urlretrieve(u, t.name)
  return json.load(t)

## Sample n_points and write to 'o' file
def sample(o):
  o.write("#Origin: %.6f,%.6f\n"%(origin_x,origin_y))
  o.write("#Start time: " + str(datetime.datetime.today()) + "\n")
  o.write("#longitude,latitude,time in seconds\n")
  x = float(x_min)
  y = float(y_min)
  dx = abs(x_max - x_min) / (n_x - 1)
  dy = abs(y_max - y_min) / (n_y - 1)

  while x < x_max + epsilon:
    while y < y_max + epsilon:
      j = retrieve(x,y)
      t,s = parse(j)
      if t >= 0:
        o.write("%.6f,%.6f,%d\n" % (x, y, t))
      else:
        o.write("#%.6f,%.6f,%s\n" % (x, y, s))
      y += dy 
    x += dx
    y = float(y_min)

  o.write("#End time: " + str(datetime.datetime.today()) + "\n")

def read(f):
  ## Features
  X = []
  ## Known outputs
  y = []
  for l in f:
    ## Skip comments
    if l[0] == '#':
      continue
    else:
      (lon,lat,t) = l.split(',')
      X.append([float(lon), float(lat)])
      y.append(int(t))
  return X, y

def analyse(X,y):
  ## sklearn will convert the lists to np.array's anyway
  y = np.array(y) / 60
  c = sklearn.neighbors.KNeighborsRegressor(n_neighbors=4, weights='distance', p=2)
  c.fit(X, y)
  ## TODO This fails. Why?
  #print c.predict([1.5, 49.25])

  fig = plt.figure()

  xx, yy = np.meshgrid(
    np.arange(x_min, x_max, 0.01),
    np.arange(y_min, y_max, 0.01))
  Z = c.predict(np.c_[xx.ravel(),yy.ravel()])
  Z = Z.reshape(xx.shape)

  cs = plt.contour(xx,yy,Z)
  return cs
  
def output_kml_segment(points, level, o):
  o.write('<Placemark>\n')
  o.write('<name>%d</name>\n'%(level))
  o.write('<styleUrl>#%d</styleUrl>\n'%(level))
  o.write("<LineString>\n")
  o.write("<coordinates>\n")
  for p in points:
    o.write("%.6f,%.6f "%(p[0],p[1]))
  o.write("\n</coordinates>\n")
  o.write("</LineString>\n")
  o.write('</Placemark>\n')

def output_kml_segments(segs, level, o):
  for s in segs:
    output_kml_segment(s,level,o)  

def output_kml_levels(levels, o):
  ## Our own colormap
  cmap = matplotlib.colors.LinearSegmentedColormap.from_list(colors=((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)), name='mybgr')
  matplotlib.cm.register_cmap(cmap=cmap)
  scale = matplotlib.cm.ScalarMappable(matplotlib.colors.Normalize(levels[0],levels[-1]), plt.get_cmap("mybgr"))
  for l in levels:
    o.write('<Style id="%d">\n'%(l))
    o.write('<LineStyle>\n')
    o.write('<width>2</width>\n')
    o.write('<gx:labelVisibility>1</gx:labelVisibility>\n')
    c = scale.to_rgba(l)
    o.write('<color>ff%02x%02x%02x</color>\n'%(int(c[2]*255),int(c[1]*255),int(c[0]*255)))
    #<gx:labelVisibility>1</gx:labelVisibility>
    o.write('</LineStyle>\n')
    o.write('</Style>\n')

def output_kml(cs,o):
  o.write('<?xml version="1.0" encoding="UTF-8"?>\n')
  o.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
  o.write('<Document>\n')
  output_kml_levels(cs.levels,o)
  for i in range(0,len(cs.levels)):
    #print "level ",cs.levels[i]," has ",len(cs.allsegs[i])," segments"
    output_kml_segments(cs.allsegs[i], cs.levels[i], o)
  o.write('</Document>\n')
  o.write('</kml>')

#  plt.clabel(cs, inline=0)
#  plt.axes(None)
#  plt.show()
 
## Key is read from  key.txt
key = read_key()

n_x,n_y = optim_param()
sample(open(name + ".csv", "w+"))
X,y = read(open(name + ".csv"))
#sys.stdout.write('' + X + y)
cs = analyse(X,y)
output_kml(cs,open(name + ".kml", "w+"))

