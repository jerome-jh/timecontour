# timecontour

A small program to draw contour lines corresponding to travel time, by car, from a point of origin.

## Prerequisite

### Python packages

Python 2.x with following additional packages:

* scikit-learn: http://scikit-learn.org
* numpy: required by scikit-learn. http://www.numpy.org/
* matplotlib: http://matplotlib.org

### Google API key

You need an API key for the Google Distance Matrix API: https://developers.google.com/maps/documentation/distancematrix/

The free key allows 2500 request by 24h. Write your key in key.txt.

## Usage

`./timecontour.py`

This will generate two files:

* time.csv: contains the raw results
* time.kml: contains the contour lines, displayable in Google Maps or Google
  earth

You may want to change settings :) In order to do this you have to edit timecontour.py variables:

* origin_x: longitude of the point of origin, in decimal degrees
* origin_y: latitude of the point of origin, in decimal degrees
* x_min: west limit of the rectangle to sample
* x_max: east limit of the rectangle to sample
* y_min: south limit of the rectangle to sample
* y_max: north limit of the rectangle to sample
* n_points: number of points to sample into the given rectangle. Remember the
  2500 limit per 24h.
* name: name prefix of the files to write to

## Inner working

The program samples travel times on a rectangular grid. The grid is choosen so that the query budget (n_points) is exhausted and cells are almost square. Travel times do not depend on traffic, so you may run the program whenever you want and get consistent results. Taking traffic into account requires a paid key.

A k-neighbours algorithm, with k=4, is used to interpolate travel times between known samples. This is a bit overkill, since samples are regularly spaced and it would be quite easy to interpolate the values inside a rectangle. Still scikit-learn provides an immediate and more robust solution.

Matplotlib is used to extract the contours lines, but without displaying them.

## Legalese

The code is provided under the Apache 2.0 license.
Google indicates its API can only be used if results are displayed on a Google
Map. So you know what to do with the generated KML.

