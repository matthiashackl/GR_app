# GR_app.py
#
# This simple Python app is intended to demo different programming aspects and provides an earthquake analyst with
# basic information about seismicity in an area of interest.
#
# This is a web server application with an interactive web map that makes use of scientific data in a geospatial
# context. It applies a set of libraries from the scientific Python stack
#

import numpy as np
import pandas as pd
from pyproj import Proj, transform
from pylab import cm
from matplotlib.colors import rgb2hex

from bokeh.plotting import figure, curdoc
from bokeh.layouts import column, row
from bokeh.tile_providers import CARTODBPOSITRON, STAMEN_TERRAIN
from bokeh.models import ColumnDataSource, HoverTool, Span
from bokeh.models.widgets import Div


def read_gem_catalogue(fp='data/isc-gem-cat.csv'):
    """Reads in catalogue data"""
    
    gem = pd.read_csv(fp, sep=',', skiprows=61)
    gem.columns = gem.columns.str.replace('\s+', '')
    gem['date'] = pd.to_datetime(gem['#date'].str.strip())
    gem['date_str'] = gem['date'].dt.strftime("%Y-%m-%d  %H:%M")
    gem['mw'] = gem.round({'mw':1})['mw']
    catalogue = gem[['date', 'lon', 'lat', 'depth', 'mw', 'date_str']].copy()
    catalogue['easting'], catalogue['northing'] = transform(Proj(init='epsg:4326'), 
                                                            Proj(init='epsg:3857'),
                                                            catalogue['lon'].values,
                                                            catalogue['lat'].values)
    return catalogue


def get_hex_color(depths):
    """Returns hex (html) color as a function of depth"""
    
    cmap = cm.get_cmap('RdPu')
    colors = cmap(np.log(depths)/np.max(np.log(depths)))
    return [rgb2hex(i) for i in colors]


def calculate_GR(catalogue):
    """Estimates the magnitude of completeness and fits Gutenberg Richter relation
    'log(N) = a - b*mag' to the earthquake selection."""
    
    try:
        number_of_events = len(catalogue)
        Mc = catalogue[['mw', 'date']].groupby('mw').count().idxmax().values[0]        
        number_of_years = catalogue['date'].max().year - catalogue['date'].min().year        
        magnitudes = np.arange(np.min(catalogue['mw']), np.max(catalogue['mw'])+0.1, 0.1)
        frequency = np.array([len(catalogue.loc[catalogue['mw']>=m]) for m in magnitudes])/number_of_years
        b,a = np.polyfit(magnitudes[magnitudes>Mc], np.log10(frequency[magnitudes>Mc]), 1)
        GR_dict = {'mag': magnitudes, 'freq': frequency, 'mc': Mc, 'b': -b, 'a': a, 'noe': number_of_events}
    except:
        div.text = "<h2>Not enough earthquakes selected</h2>"
    return GR_dict


def line_fit(GR_dict):
    """Returns line parameters based on a and b values."""

    gr_x = GR_dict['mag']
    gr_y = 10**(GR_dict['a'] - gr_x * GR_dict['b'])
    return (gr_x, gr_y)


def create_label(GR_dict):
    text="""<h2>Gutenberg Richter parameters:</h2>
    <h3>Number of selected Events: <b>%i</b> </h3>
    <h3>Magnitude of completeness: <b>%.1f</b> </h3>           
    <h3>a = <b>%.2f</b> </h3>
    <h3>b = <b>%.2f</b> </h3>""" % (GR_dict['noe'], GR_dict['mc'], GR_dict['a'], GR_dict['b'])
    return text
    

def callback(attr, old, new):
    """Estimates GR statistics and updates the UI upon earthquake selection."""
    print(len(eq_source.selected.indices), ' earthquakes selected')
    indices = eq_source.selected.indices
    GR_dict = calculate_GR(catalogue.iloc[indices])
    gr_source.data = dict(x=GR_dict['mag'],
                          y=GR_dict['freq'])
    gr_x, gr_y = line_fit(GR_dict)
    gr_line.data_source.data = dict(x=gr_x, y=gr_y)
    div.text = create_label(GR_dict)
    vline.location = GR_dict['mc']


#################################
# Here starts the main part
#################################

# Load and prepare data
catalogue = read_gem_catalogue()
GR_dict = calculate_GR(catalogue)

eq_source = ColumnDataSource(data=dict(x=catalogue['easting'].values,
                                       y=catalogue['northing'].values,
                                       size=catalogue['mw'].values**3/30,
                                       color=get_hex_color(catalogue['depth'].values),
                                       date=catalogue['date_str'],
                                       mw=catalogue['mw'].values,
                                       depth=catalogue['depth'].values))

gr_source = ColumnDataSource(data=dict(x=GR_dict['mag'],
                                       y=GR_dict['freq']))


################################
# prepare map plot

hover = HoverTool(tooltips=[("Date", "@date"),
                            ("Magitude (Mw)", "@mw"),
                            ("Depth (km)", "@depth")])

mapa = figure(x_range=(-20000000, 20000000), y_range=(-5000000, 8000000),
           x_axis_type="mercator", y_axis_type="mercator", title='Earthquake Catalogue',
           tools=[hover,"pan,poly_select,wheel_zoom,reset"],
           plot_width=1000)

# plot base map
mapa.add_tile(CARTODBPOSITRON)

# plot earthquakes
mapa.circle('x', 'y', source=eq_source, size='size', fill_alpha=0.5, color='color')

# trigger the GR calculation upon event selection
eq_source.on_change("selected", callback)


################################
# magnitude frequency plot 

gr = figure(plot_width=600, plot_height=400, title='Gutenberg Richter',
            y_axis_type="log", tools=[], logo=None)

gr_points = gr.circle('x', 'y', source=gr_source)

gr_x, gr_y = line_fit(GR_dict)
gr_line = gr.line(gr_x, gr_y, line_color='green', line_width=3)

vline = Span(location=GR_dict['mc'], dimension='height', line_color='red', line_width=1)
gr.renderers.extend([vline])

gr.xaxis.axis_label = "Magnitude"
gr.yaxis.axis_label = "Cumulative Annual Frequency"


################################
# add text field
div = Div(text=create_label(GR_dict), width=400, height=400)

################################
# return the final app
curdoc().add_root(column(mapa, row(gr, div)))
    
