"""Shared chart renderer for the desktop and headless visual verification."""
import math
from itertools import combinations, cycle
from core import all_distances, geodesic_coordinates

PALETTE = ['#168d9d', '#e49636', '#7857b6', '#29834a', '#c45470', '#5367ba']


def draw_distance_figure(figure, dataset):
    rows = all_distances(dataset)
    colors = [c for _, c in zip(rows, cycle(PALETTE))]
    figure.clear()
    ax, bars = figure.subplots(1, 2, gridspec_kw={'width_ratios': [1.15, 1]})
    for (a, b), color in zip(combinations(dataset['locations'], 2), colors):
        coords = geodesic_coordinates(a, b)
        ax.plot([p[0] for p in coords], [p[1] for p in coords], '--', color=color, linewidth=1.8)
    for p in dataset['locations']:
        ax.scatter(p['longitude'], p['latitude'], s=65, color='#12334b', zorder=3)
        ax.annotate(p['id'], (p['longitude'], p['latitude']), xytext=(6, 8), textcoords='offset points')
    mean_latitude = sum(p['latitude'] for p in dataset['locations']) / len(dataset['locations'])
    ax.set_aspect(1 / math.cos(math.radians(mean_latitude)))
    ax.margins(0.2)
    ax.set_title('Reference locations — coordinate overview', fontsize=10)
    ax.set_xlabel('Longitude (degrees)')
    ax.set_ylabel('Latitude (degrees)')
    ax.ticklabel_format(useOffset=False, style='plain')
    ax.tick_params(labelsize=8)
    ax.grid(alpha=0.2)
    labels = [f"{r['from_id']} / {r['to_id']}" for r in rows]
    values = [r['distance_km'] for r in rows]
    bars.barh(labels, values, color=colors)
    bars.invert_yaxis()
    bars.set_xlim(0, max(max(values) * 1.3, 0.1))
    for i, value in enumerate(values):
        bars.text(value + 0.04, i, f'{value:.3f} km', va='center', fontsize=9)
    bars.set_xlabel('Ellipsoidal geodesic distance (km)')
    bars.set_title(f'{len(rows)} pairwise distances', fontsize=11)
    figure.text(0.02, 0.015, 'No basemap. Dashed lines are geodesics, not travel routes. Coordinates are not field-surveyed.', fontsize=8, color='#526474')
    figure.tight_layout(rect=(0, 0.04, 1, 1))
    return ax, bars
