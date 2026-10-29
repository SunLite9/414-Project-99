"""UCLA presentation style for every plot in this project.

Usage (from a notebook in notebooks/):
    import sys; sys.path.insert(0, '../style_guide')
    import ucla_style as us
    us.apply()
    fig, ax = us.figure('half')
    ax.bar(x, y, color=us.SERIES[0])
    us.save(fig, 'results/midterm/figures/my_plot.png')

All colors are official UCLA brand colors (brand.ucla.edu/identity/colors). UCLA does not allow tints or
other shades of its blues and golds, so this module never lightens or mixes them.
See STYLE_GUIDE.md for the rules behind each choice.
"""
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt

# ---- Official UCLA brand colors ----
UCLA_BLUE = '#2774AE'      # primary, dominant
UCLA_GOLD = '#FFD100'      # primary accent (large shapes / large text on blue only)
WHITE = '#FFFFFF'
DARKEST_BLUE = '#003B5C'
DARKER_BLUE = '#005587'
LIGHTER_BLUE = '#8BB8E8'
LIGHTEST_BLUE = '#DAEBFE'
DARKEST_GOLD = '#FFB81C'
DARKER_GOLD = '#FFC72C'
# UCLA design-system grays
GRAY_80 = '#333333'        # body text
GRAY_60 = '#666666'        # secondary text, tick labels
GRAY_40 = '#999999'        # reference marks (baselines, "implied by price")
GRAY_20 = '#CCCCCC'        # axis lines
GRAY_10 = '#E5E5E5'        # grid lines
GRAY_5 = '#F2F2F2'         # table banding
# UCLA denotive colors: alerts only, never a data series
SUCCESS = '#007339'
ERROR = '#D60000'

# ---- Data roles ----
SERIES = [UCLA_BLUE, DARKEST_GOLD, DARKEST_BLUE, LIGHTER_BLUE]   # categorical order, never cycled
PRIMARY = UCLA_BLUE          # the series the slide is about
REFERENCE = GRAY_40          # benchmark the series is compared with
ATTENTION = DARKEST_GOLD     # "worse than benchmark" / the one thing to look at (always direct-label it)
DARK = DARKEST_BLUE          # second data series, error bars
SEQUENTIAL = [LIGHTEST_BLUE, LIGHTER_BLUE, UCLA_BLUE, DARKER_BLUE, DARKEST_BLUE]   # UCLA blue gradient, light -> dark

FONT_STACK = ['Arial', 'Helvetica', 'Liberation Sans', 'DejaVu Sans']
SIZES = {'full': (9.0, 4.2), 'half': (5.6, 4.2), 'wide': (9.0, 3.2), 'square': (5.2, 4.6)}


def apply():
    """Set matplotlib defaults to the project style."""
    mpl.rcParams.update({
        'font.family': 'sans-serif', 'font.sans-serif': FONT_STACK, 'font.size': 12,
        'text.color': GRAY_80, 'axes.labelcolor': GRAY_80, 'axes.labelsize': 12, 'axes.titlesize': 13,
        'axes.titleweight': 'bold', 'axes.titlelocation': 'left', 'axes.titlecolor': DARKER_BLUE,
        'axes.edgecolor': GRAY_20, 'axes.linewidth': 1.0, 'axes.spines.top': False, 'axes.spines.right': False,
        'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': GRAY_10, 'grid.linewidth': 0.8, 'axes.axisbelow': True,
        'axes.prop_cycle': mpl.cycler(color=SERIES), 'axes.facecolor': WHITE, 'figure.facecolor': WHITE,
        'xtick.color': GRAY_60, 'ytick.color': GRAY_60, 'xtick.labelsize': 11, 'ytick.labelsize': 11,
        'xtick.major.size': 0, 'ytick.major.size': 0, 'xtick.major.pad': 6, 'ytick.major.pad': 6,
        'lines.linewidth': 2.0, 'lines.markersize': 8, 'patch.linewidth': 0,
        'legend.frameon': False, 'legend.fontsize': 11, 'legend.labelcolor': GRAY_80,
        'errorbar.capsize': 3, 'figure.dpi': 100, 'savefig.dpi': 200, 'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.15, 'savefig.facecolor': WHITE, 'axes.unicode_minus': True,
    })


def figure(size='full', **kw):
    """New figure at a standard slide size: 'full' (9 x 4.2 in), 'half' (5.6 x 4.2), 'wide' (9 x 3.2), 'square'."""
    return plt.subplots(figsize=SIZES.get(size, size), **kw)


def label(ax, x, y, text, **kw):
    """Direct label in text ink (never the series color)."""
    opts = dict(fontsize=10.5, color=GRAY_80, ha='center', va='bottom')
    opts.update(kw)
    return ax.text(x, y, text, **opts)


def note(fig, text):
    """Source / method note under the plot, in secondary ink."""
    fig.text(0.0, -0.02, text, ha='left', va='top', fontsize=9.5, color=GRAY_60, transform=fig.transFigure)


def save(fig, path):
    """Save as a 200-dpi PNG on white and close the figure."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
