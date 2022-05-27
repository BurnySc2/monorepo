from math import pi
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.palettes import Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum, linear_cmap
from bokeh.util.hex import axial_to_cartesian, hexbin

CURRENT_DIRECTORY = Path(__file__).parent


def plot_01():
    p = figure(width=400, height=400)
    p.vbar(
        x=[1, 2, 3],
        width=0.5,
        bottom=0,
        top=[1.2, 2.5, 3.7],
        color='firebrick',
    )
    output_file(CURRENT_DIRECTORY / 'bokeh_vbar.html')
    save(p)
    # Open in browser
    # show(p)


def plot_02():

    q = np.array([0, 0, 0, -1, -1, 1, 1])
    r = np.array([0, -1, 1, 0, 1, -1, 0])

    p = figure(width=400, height=400, toolbar_location=None)
    p.grid.visible = False

    p.hex_tile(q, r, size=1, fill_color=['firebrick'] * 3 + ['navy'] * 4, line_color='white', alpha=0.5)

    x, y = axial_to_cartesian(q, r, 1, 'pointytop')

    p.text(x, y, text=[f'({q}, {r})' for (q, r) in zip(q, r)], text_baseline='middle', text_align='center')
    output_file(CURRENT_DIRECTORY / 'bokeh_hex_coords.html')
    save(p)


def plot_03():
    n = 50000
    x = np.random.standard_normal(n)
    y = np.random.standard_normal(n)

    bins = hexbin(x, y, 0.1)

    p = figure(tools='wheel_zoom,reset', match_aspect=True, background_fill_color='#440154')
    p.grid.visible = False

    p.hex_tile(
        q='q',
        r='r',
        size=0.1,
        line_color=None,
        source=bins,
        fill_color=linear_cmap('counts', 'Viridis256', 0, max(bins.counts))
    )

    output_file(CURRENT_DIRECTORY / 'bokeh_hex_tile.html')

    save(p)


def plot_04():
    p = figure(width=400, height=400)
    p.multi_polygons(
        xs=[
            [[[1, 1, 2, 2], [1.2, 1.6, 1.6], [1.8, 1.8, 1.6]], [[3, 3, 4]]],
            [[[1, 2, 2, 1], [1.3, 1.3, 1.7, 1.7]]],
        ],
        ys=[
            [[[4, 3, 3, 4], [3.2, 3.2, 3.6], [3.4, 3.8, 3.8]], [[1, 3, 1]]],
            [[[1, 1, 2, 2], [1.3, 1.7, 1.7, 1.3]]],
        ],
        color=['blue', 'red']
    )

    output_file(CURRENT_DIRECTORY / 'bokeh_multipolygons.html')
    save(p)


def plot_05():
    x = np.linspace(0, 10, 250)
    y = np.linspace(0, 10, 250)
    xx, yy = np.meshgrid(x, y)
    d = np.sin(xx) * np.cos(yy)

    p = figure(width=400, height=400)
    p.x_range.range_padding = p.y_range.range_padding = 0

    p.image(image=[d], x=0, y=0, dw=10, dh=10, palette='Spectral11', level='image')
    p.grid.grid_line_width = 0.5

    output_file(CURRENT_DIRECTORY / 'bokeh_image.html', title='image.py example')
    save(p)


def plot_06():
    x = {
        'United States': 157,
        'United Kingdom': 93,
        'Japan': 89,
        'China': 63,
        'Germany': 44,
        'India': 42,
        'Italy': 40,
        'Australia': 35,
        'Brazil': 32,
        'France': 31,
        'Taiwan': 31,
        'Spain': 29
    }

    data = pd.Series(x).reset_index(name='value').rename(columns={'index': 'country'})
    data['angle'] = data['value'] / data['value'].sum() * 2 * pi
    data['color'] = Category20c[len(x)]

    p = figure(
        height=350,
        title='Pie Chart',
        toolbar_location=None,
        tools='hover',
        tooltips='@country: @value',
        x_range=(-0.5, 1.0)
    )

    p.wedge(
        x=0,
        y=1,
        radius=0.4,
        start_angle=cumsum('angle', include_zero=True),
        end_angle=cumsum('angle'),
        line_color='white',
        fill_color='color',
        legend_field='country',
        source=data
    )

    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    output_file(CURRENT_DIRECTORY / 'bokeh_piechart.html')
    save(p)


def main():
    plot_01()
    plot_02()
    plot_03()
    plot_04()
    plot_05()
    plot_06()


if __name__ == '__main__':
    main()
