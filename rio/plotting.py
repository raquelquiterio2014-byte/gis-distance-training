"""Distance chart with optional street basemap; calculations stay on WGS 84."""
import math
from itertools import combinations, cycle
from core import all_distances, geodesic_coordinates
from basemap import mercator, lon_lat
from matplotlib.ticker import FuncFormatter
import matplotlib.patheffects as pe

PALETTE = ['#168d9d', '#e49636', '#7857b6', '#29834a', '#c45470', '#5367ba']
LABELS = {'RIO01': 'Copacabana Palace', 'RIO02': 'Christ the Redeemer',
          'RIO03': 'Sugarloaf summit', 'RIO04': 'Cosme Velho station'}


def draw_distance_figure(figure, dataset, basemap=None, selected_pair=None):
    rows = all_distances(dataset)
    colors = [c for _, c in zip(rows, cycle(PALETTE))]
    figure.clear()
    ax, bars = figure.subplots(1, 2, gridspec_kw={'width_ratios': [1.4, 1]})
    if basemap is not None:
        ax.imshow(basemap.image, extent=basemap.extent, interpolation='bilinear', zorder=0)
    transform = mercator if basemap is not None else lambda lon, lat: (lon, lat)
    selected = frozenset(selected_pair or [])
    for (a, b), color in zip(combinations(dataset['locations'], 2), colors):
        coords = [transform(lon, lat) for lon, lat in geodesic_coordinates(a, b)]
        highlight = frozenset((a['id'], b['id'])) == selected
        line, = ax.plot(*zip(*coords), '--' if basemap is None else '-', color=color,
                       linewidth=3.6 if highlight else 1.7, alpha=1 if highlight or not selected else .6,
                       zorder=4 if highlight else 2)
        if basemap is not None:
            line.set_path_effects([pe.Stroke(linewidth=line.get_linewidth() + 1.5, foreground='white'), pe.Normal()])
    for p in dataset['locations']:
        xy = transform(p['longitude'], p['latitude'])
        ax.scatter(*xy, s=65, color='#12334b', edgecolor='white', linewidth=1, zorder=5)
        text = p['id'] if basemap is None else f"{p['id']}\n{LABELS.get(p['id'], p['name'])}"
        ax.annotate(text, xy, xytext=(6, 8), textcoords='offset points', fontsize=8, zorder=6,
                    bbox=dict(boxstyle='round,pad=.25', fc='white', ec='#b8c7d1', alpha=.92) if basemap else None)
    if basemap is not None:
        west, east, south, north = basemap.bounds_lon_lat
        ax.set_xlim(mercator(west, south)[0], mercator(east, north)[0])
        ax.set_ylim(mercator(west, south)[1], mercator(east, north)[1])
        ax.set_aspect('equal')
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{lon_lat(x, 0)[0]:.3f}°'))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{lon_lat(0, y)[1]:.3f}°'))
        ax.text(.99, .015, basemap.attribution, transform=ax.transAxes, ha='right', va='bottom',
                fontsize=7, zorder=8, bbox=dict(fc='white', ec='none', alpha=.95, pad=3))
        ax.set_title('Rio streets & neighborhoods — OpenStreetMap', fontsize=10)
    else:
        mean_latitude = sum(p['latitude'] for p in dataset['locations']) / len(dataset['locations'])
        ax.set_aspect(1 / math.cos(math.radians(mean_latitude)))
        ax.margins(0.2)
        ax.set_title('Reference locations — coordinate overview', fontsize=10)
        ax.ticklabel_format(useOffset=False, style='plain')
        ax.grid(alpha=0.2)
    ax.set_xlabel('Longitude (degrees)')
    ax.set_ylabel('Latitude (degrees)')
    ax.tick_params(labelsize=8)
    labels = [f"{r['from_id']} / {r['to_id']}" for r in rows]
    values = [r['distance_km'] for r in rows]
    bars.barh(labels, values, color=colors)
    bars.invert_yaxis()
    bars.set_xlim(0, max(max(values) * 1.3, 0.1))
    for i, value in enumerate(values):
        bars.text(value + 0.04, i, f'{value:.3f} km', va='center', fontsize=9)
    bars.set_xlabel('Ellipsoidal geodesic distance (km)')
    bars.set_title(f'{len(rows)} pairwise distances', fontsize=11)
    note = ('Basemap displayed in Web Mercator; distances computed on WGS 84. Lines are not travel routes.'
            if basemap is not None else 'No basemap. Dashed lines are geodesics, not travel routes. Coordinates are not field-surveyed.')
    figure.text(0.02, 0.015, note, fontsize=8, color='#526474')
    figure.tight_layout(rect=(0, 0.04, 1, 1))
    return ax, bars
