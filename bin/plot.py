from bokeh.plotting import figure, ColumnDataSource
from matplotlib import colors
from bokeh.layouts import row, gridplot
from bokeh.models import Span, HoverTool
import numpy as np
from bokeh.models import FuncTickFormatter


def plot_power_spectra(layerline_bessel_pairs, im_theo, im_theo_coll, nyquist, nyquist_simulation, im=None,
                       im_coll=None):
    size = 450

    source = ColumnDataSource(
        data=dict(
            zer=[0 for i in layerline_bessel_pairs] * 2,
            pos=[i[0] for i in layerline_bessel_pairs] + [-i[0] for i in layerline_bessel_pairs],
            res=[1.0 / i[0] for i in layerline_bessel_pairs] * 2,
            bes=[i[1] for i in layerline_bessel_pairs] * 2,
        )
    )

    hover1 = HoverTool(
        tooltips=[
            ("Position", "@pos"),
            ("Resolution", '@res'),
            ("Bessel Order", "@bes")
        ]
    )

    x_vals1 = np.linspace(-nyquist_simulation, nyquist_simulation, len(im_theo_coll))
    if im != None:
        x_vals2 = np.linspace(-nyquist, nyquist, len(im_coll))

    TOOLS = 'wheel_zoom,pan,crosshair,reset'

    colormap = colors.LinearSegmentedColormap.from_list('name', ['black', 'orangered', 'white'])
    bokehpalette_1 = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]
    colormap = colors.LinearSegmentedColormap.from_list('name', ['black', 'green', 'white'])
    bokehpalette_2 = [colors.rgb2hex(m) for m in colormap(np.arange(colormap.N))]

    plot1 = figure(title="Theoretical", x_range=[-nyquist_simulation, nyquist_simulation],
                   y_range=[-nyquist_simulation, nyquist_simulation],
                   plot_width=size, plot_height=size, tools=TOOLS, toolbar_location="above")
    plot1.image([im_theo], x=[-nyquist_simulation], y=[-nyquist_simulation], dw=[2 * nyquist_simulation],
                dh=[2 * nyquist_simulation], palette=bokehpalette_1)

    plot1_collapse = figure(plot_width=size / 4 - 30, plot_height=size, y_range=plot1.y_range, tools='')
    plot1_collapse.line(im_theo_coll, x_vals1, line_width=2, color='orangered')
    plot1.hbar('pos', height=nyquist_simulation / len(layerline_bessel_pairs) / 2.0, left=-nyquist_simulation,
               right=nyquist_simulation, color="white", source=source, alpha=0)
    plot1.add_tools(hover1)

    if im != None:
        plot2 = figure(x_range=plot1.x_range, y_range=plot1.y_range,
                       plot_width=size, plot_height=size, tools=TOOLS, toolbar_location="above")

        plot2.image([im], x=[-nyquist], y=[-nyquist], dw=[2 * nyquist], dh=[2 * nyquist], palette=bokehpalette_2)

        plot2_collapse = figure(title="Uploaded", plot_width=size / 4, plot_height=size, y_range=plot1.y_range,
                                tools='')
        plot2_collapse.line(-im_coll, x_vals2, line_width=2, color='green')

    if im == None:
        plots_im = [plot1]
        plots_1d = [plot1_collapse]
    else:
        plots_im = [plot1, plot2]
        plots_1d = [plot1_collapse, plot2_collapse]

    for p in plots_im:
        lines = []
        for location in [0.0, 0.0, 0.05, 0.1, 0.15, 0.2]:
            for loc in [-location, location]:
                lines.append(Span(location=loc, dimension='height', line_color='white', line_width=1, line_alpha=0.1))
                lines.append(Span(location=loc, dimension='width', line_color='white', line_width=1, line_alpha=0.1))
        p.background_fill_color = "black"
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None
        p.renderers.extend(lines)
        p.xaxis.axis_label = 'Angstrom'
        p.toolbar.logo = None
        formatcode = """return Math.round(100.0/tick)/100.0"""
        p.xaxis.formatter = FuncTickFormatter(code=formatcode)
        p.yaxis.formatter = FuncTickFormatter(code=formatcode)

    for p in plots_1d:
        p.xaxis.visible = False
        p.toolbar.logo = None
        p.toolbar_location = None

    if im != None:
        # plot2.yaxis.axis_label = 'Angstrom'
        plot2.title.text_color = "orange"

    plot1_collapse.title.text_color = "green"
    plot1_collapse.yaxis.visible = False

    sizing = "fixed"  # "fixed"#'fixed'   sizing_mode

    if im != None:
        l = gridplot([[plot1, plot1_collapse, plot2_collapse, plot2]], sizing_mode=sizing)
    else:
        l = gridplot([[plot1_collapse, plot1]], sizing_mode=sizing)

    return l
