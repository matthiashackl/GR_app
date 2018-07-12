# Seismicity App

This simple Python app is intended to demo different programming aspects and provides an earthquake analyst with
basic information about seismicity in an area of interest.

This is a web server application with an interactive web map that makes use of scientific data in a geospatial
context. It applies a set of libraries from the scientific Python stack to estimate the magnitude of completeness
and fit the Gutenberg Richter relationship to the magnitude frequency distribution of the earthquakes in an user
selected area. The user interface consists of an interactive map, plot, and text information.

## Run the app

```
bokeh serve --show GR_app.py
```


## Dependencies

* numpy
* matplotlib
* bokeh
* pandas


A test version of the available [here](http://ec2-18-196-129-109.eu-central-1.compute.amazonaws.com:5006/GR_app).