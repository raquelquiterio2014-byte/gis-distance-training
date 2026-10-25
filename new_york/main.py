"""Offline English desktop dashboard. Start the API separately with api.py."""
import json
import math
import queue
import threading
import tkinter as tk
import urllib.request
import webbrowser
from tkinter import filedialog, messagebox, ttk
from itertools import combinations
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from core import ROOT, load_dataset, all_distances, export_dataset, geodesic_coordinates

API_URL = 'http://127.0.0.1:8003'


class Dashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('GIS Distance Training | New York')
        self.geometry('1250x830')
        self.minsize(1050, 760)
        self.configure(bg='#eef3f8')
        self.results_queue = queue.Queue()
        self.dataset = load_dataset()
        self.rows = all_distances(self.dataset)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Treeview', rowheight=30, font=('Segoe UI', 10))
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
        top = tk.Frame(self, bg='#12334b', padx=24, pady=16)
        top.pack(fill='x')
        tk.Label(top, text='NEW YORK', font=('Segoe UI', 22, 'bold'),
                 bg='#12334b', fg='white').pack(anchor='w')
        tk.Label(top, text='GIS Distance Training | WGS 84 Ellipsoidal Geodesics',
                 font=('Segoe UI', 12), bg='#12334b', fg='#a9dce8').pack(anchor='w')
        self.summary = tk.StringVar()
        tk.Label(self, textvariable=self.summary, font=('Segoe UI', 10), bg='#fff2d1',
                 fg='#6b4900', padx=16, pady=9, wraplength=1150, justify='left').pack(fill='x')
        controls = ttk.Frame(self, padding=(16, 10))
        controls.pack(fill='x')
        ttk.Button(controls, text='Reload coordinates', command=self.reload).pack(side='left', padx=4)
        ttk.Button(controls, text='Export CSV + GeoJSON', command=self.export).pack(side='left', padx=4)
        self.compare_button = ttk.Button(controls, text='Compare with local API', command=self.compare_api)
        self.compare_button.pack(side='left', padx=4)
        ttk.Button(controls, text='Open API docs', command=lambda: webbrowser.open(API_URL + '/docs')).pack(side='left', padx=4)
        ttk.Button(controls, text='Save chart as PNG', command=self.save_chart).pack(side='left', padx=4)
        pair_controls = ttk.Frame(self, padding=(20, 0, 20, 8))
        pair_controls.pack(fill='x')
        ttk.Label(pair_controls, text='Origin:').pack(side='left')
        self.origin = ttk.Combobox(pair_controls, state='readonly', width=10, values=['NYC01', 'NYC02', 'NYC03'])
        self.origin.set('NYC01')
        self.origin.pack(side='left', padx=6)
        ttk.Label(pair_controls, text='Destination:').pack(side='left')
        self.destination = ttk.Combobox(pair_controls, state='readonly', width=10, values=['NYC01', 'NYC02', 'NYC03'])
        self.destination.set('NYC02')
        self.destination.pack(side='left', padx=6)
        ttk.Button(pair_controls, text='Calculate selected pair', command=self.calculate_pair).pack(side='left', padx=6)
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill='both', expand=True, padx=16)
        self.overview = ttk.Frame(self.tabs)
        self.points_tab = ttk.Frame(self.tabs)
        self.comparison_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.overview, text='Distance Dashboard')
        self.tabs.add(self.points_tab, text='Access Points & Evidence')
        self.tabs.add(self.comparison_tab, text='API Comparison')
        self.figure = Figure(figsize=(11.5, 3.8), dpi=100, facecolor='white')
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.overview)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.table = ttk.Treeview(self.overview, columns=('pair', 'meters', 'km'), show='headings', height=3)
        for column, label, width in [('pair', 'Access point pair', 650), ('meters', 'Distance (m)', 150), ('km', 'Distance (km)', 150)]:
            self.table.heading(column, text=label)
            self.table.column(column, width=width, anchor='w' if column == 'pair' else 'e')
        self.table.pack(fill='x', padx=10, pady=10)
        self.points_text = tk.Text(self.points_tab, wrap='word', font=('Segoe UI', 11), padx=16, pady=16)
        self.points_text.pack(fill='both', expand=True)
        self.comparison_text = tk.Text(self.comparison_tab, wrap='word', font=('Consolas', 11), padx=16, pady=16)
        self.comparison_text.pack(fill='both', expand=True)
        self.status = tk.StringVar(value='Ready. QGIS comparison has not been performed.')
        tk.Label(self, textvariable=self.status, anchor='w', padx=16, pady=10,
                 bg='#eef3f8', font=('Segoe UI', 10)).pack(fill='x')
        self.draw()
        self.after(100, self.poll_results)

    def draw(self):
        self.summary.set(f"{self.dataset['coordinate_status']} | 3 access references / 3 pairs | No street routes or altitude.\n"
                         'Fifth Avenue reference = St. Patrick\'s Cathedral frontage. Coordinates require QGIS review.')
        self.table.delete(*self.table.get_children())
        for row in self.rows:
            self.table.insert('', 'end', values=(f"{row['from_id']} — {row['to_id']}",
                                                f"{row['distance_m']:,.2f}", f"{row['distance_km']:.3f}"))
        self.figure.clear()
        ax, bars = self.figure.subplots(1, 2, gridspec_kw={'width_ratios': [1.15, 1]})
        colors = ['#168d9d', '#e49636', '#7857b6']
        for (a, b), color in zip(combinations(self.dataset['locations'], 2), colors):
            coords = geodesic_coordinates(a, b)
            ax.plot([p[0] for p in coords], [p[1] for p in coords], '--', color=color, linewidth=1.8)
        for p in self.dataset['locations']:
            ax.scatter(p['longitude'], p['latitude'], s=65, color='#12334b', zorder=3)
            ax.annotate(p['id'], (p['longitude'], p['latitude']), xytext=(6, 8), textcoords='offset points')
        ax.set_aspect(1 / math.cos(math.radians(sum(p['latitude'] for p in self.dataset['locations']) / 3)))
        ax.margins(0.2)
        ax.set_title('Access references — coordinate overview', fontsize=11)
        ax.set_xlabel('Longitude (degrees)')
        ax.set_ylabel('Latitude (degrees)')
        ax.ticklabel_format(useOffset=False, style='plain')
        ax.tick_params(labelsize=8)
        ax.grid(alpha=0.2)
        labels = [f"{r['from_id']} / {r['to_id']}" for r in self.rows]
        values = [r['distance_km'] for r in self.rows]
        bars.barh(labels, values, color=colors)
        bars.set_xlim(0, max(values) * 1.3)
        for i, value in enumerate(values):
            bars.text(value + 0.04, i, f'{value:.3f} km', va='center', fontsize=10)
        bars.set_xlabel('Ellipsoidal geodesic distance (km)')
        bars.set_title('Three pairwise distances', fontsize=11)
        self.figure.text(0.02, 0.015, 'Coordinate overview only; no basemap. Dashed lines show geodesics, not travel routes.', fontsize=8, color='#526474')
        self.figure.tight_layout(rect=(0, 0.04, 1, 1))
        self.canvas.draw()
        sections = [f"Dataset: {self.dataset['dataset_version']}\nCRS: EPSG:4326 | Ellipsoid: WGS 84\nStatus: {self.dataset['coordinate_status']}\n"]
        for p in self.dataset['locations']:
            sections.append(f"{p['id']} | {p['name']}\nLatitude: {p['latitude']:.6f} | Longitude: {p['longitude']:.6f}\n"
                            f"{p['access_note']}\nSource: {p['source_url']}\nCoordinate basis: {p['coordinate_basis']}\n")
        self.set_text(self.points_text, '\n'.join(sections))
        self.set_text(self.comparison_text, 'Not compared yet. Start api.py, then click Compare with local API.\n'
                      'This checks API transport and dataset consistency using the shared engine.\n'
                      'Independent QGIS validation is still pending. Numerical tolerance: 0.01 m; this is not coordinate accuracy.')

    @staticmethod
    def set_text(widget, value):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('1.0', value)
        widget.configure(state='disabled')

    def reload(self):
        try:
            dataset = load_dataset()
            rows = all_distances(dataset)
            self.dataset, self.rows = dataset, rows
            self.draw()
            self.status.set('Coordinates reloaded. Previous comparisons cleared; recompare after changes.')
        except Exception as exc:
            messagebox.showerror('Dataset error', str(exc))

    def calculate_pair(self):
        origin, destination = self.origin.get(), self.destination.get()
        if origin == destination:
            messagebox.showwarning('Select a pair', 'Select two different access points.')
            return
        row = next(r for r in self.rows if {r['from_id'], r['to_id']} == {origin, destination})
        self.status.set(f"{origin} / {destination}: {row['distance_m']:,.3f} m | {row['distance_km']:.3f} km. Approximate access references.")
        self.tabs.select(self.overview)
        self.table.selection_set(self.table.get_children()[self.rows.index(row)])

    def save_chart(self):
        path = filedialog.asksaveasfilename(title='Save distance chart', defaultextension='.png',
                                          filetypes=[('PNG image', '*.png')])
        if path:
            try:
                self.figure.savefig(path, dpi=180, bbox_inches='tight')
                self.status.set('Chart saved as PNG. Coordinate overview only, not a QGIS screenshot.')
            except Exception as exc:
                messagebox.showerror('Export error', str(exc))

    def export(self):
        directory = filedialog.askdirectory(title='Choose export folder', initialdir=str(ROOT))
        if directory:
            try:
                paths = export_dataset(self.dataset, directory)
                messagebox.showinfo('Export complete', '\n'.join(str(p) for p in paths))
                self.status.set('Exported current dashboard dataset. QGIS validation is still required.')
            except Exception as exc:
                messagebox.showerror('Export error', str(exc))

    def compare_api(self):
        self.compare_button.configure(state='disabled')
        self.status.set('Requesting local API...')
        # Capture the dataset snapshot; never access Tk from this worker.
        dataset = self.dataset
        rows = self.rows
        def worker():
            try:
                with urllib.request.urlopen(API_URL + '/distances', timeout=5) as response:
                    payload = json.load(response)
                for key in ['dataset_version', 'crs', 'ellipsoid', 'coordinate_status', 'locations']:
                    if payload.get(key) != dataset[key]:
                        raise ValueError(f'Dataset mismatch: {key}. Reload coordinates and check API project folder.')
                remote = {(r['from_id'], r['to_id']): r['distance_m'] for r in payload['distances']}
                expected = {(r['from_id'], r['to_id']) for r in rows}
                if set(remote) != expected or len(payload['distances']) != 3:
                    raise ValueError('API pair set differs from the dashboard.')
                lines = ['LOCAL PYTHON / FASTAPI COMPARISON', 'Numerical tolerance: 0.01 m\n']
                passed = True
                for row in rows:
                    key = (row['from_id'], row['to_id'])
                    delta = abs(row['distance_m'] - remote[key])
                    ok = math.isfinite(delta) and delta <= 0.01
                    passed = passed and ok
                    lines.append(f"{key[0]} / {key[1]}: delta = {delta:.6f} m | {'PASS' if ok else 'FAIL'}")
                lines.append('\nShared calculation engine; this is a consistency check.\nIndependent QGIS comparison: PENDING.')
                self.results_queue.put(('PASS' if passed else 'FAIL', '\n'.join(lines)))
            except Exception as exc:
                self.results_queue.put(('ERROR', f'API comparison failed: {exc}\n\nStart api.py in this project and try again.'))
        threading.Thread(target=worker, daemon=True).start()

    def poll_results(self):
        try:
            status, report = self.results_queue.get_nowait()
            self.set_text(self.comparison_text, report)
            self.tabs.select(self.comparison_tab)
            self.status.set(f'API comparison: {status}. QGIS comparison remains pending.')
            self.compare_button.configure(state='normal')
        except queue.Empty:
            pass
        self.after(100, self.poll_results)


if __name__ == '__main__':
    Dashboard().mainloop()
