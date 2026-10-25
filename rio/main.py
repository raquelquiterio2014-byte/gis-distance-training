"""Offline English desktop dashboard. Start the API separately with api.py."""
import json
import queue
import threading
import tkinter as tk
import urllib.request
import webbrowser
from tkinter import filedialog, messagebox, ttk
from plotting import draw_distance_figure
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from PIL import ImageTk
from basemap import load_street_map, view_spec, openstreetmap_url
from gallery import list_screenshots, add_screenshot, screenshot_thumbnail
from core import ROOT, load_dataset, all_distances, export_dataset
from validation import independent_report, qgis_report, write_qgis_template, compare_api_payload, format_report

API_URL = 'http://127.0.0.1:8002'


class Dashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('GIS Distance Training | Rio de Janeiro')
        self.geometry('1250x830')
        self.minsize(1050, 760)
        self.configure(bg='#eef3f8')
        self.results_queue = queue.Queue()
        self.map_queue = queue.Queue()
        self.street_map = None
        self.map_busy = False
        self.show_streets = tk.BooleanVar(value=True)
        self.selected_pair = ('RIO01', 'RIO02')
        self.gallery_photo = None
        self.gallery_resize_job = None
        self.last_check_report = None
        self.qgis_status = 'PENDING'
        self.dataset = load_dataset()
        self.rows = all_distances(self.dataset)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Treeview', rowheight=30, font=('Segoe UI', 10))
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
        top = tk.Frame(self, bg='#12334b', padx=24, pady=16)
        top.pack(fill='x')
        tk.Label(top, text='RIO DE JANEIRO', font=('Segoe UI', 22, 'bold'),
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
        self.origin = ttk.Combobox(pair_controls, state='readonly', width=10, values=[p['id'] for p in self.dataset['locations']])
        self.origin.set('RIO01')
        self.origin.pack(side='left', padx=6)
        ttk.Label(pair_controls, text='Destination:').pack(side='left')
        self.destination = ttk.Combobox(pair_controls, state='readonly', width=10, values=[p['id'] for p in self.dataset['locations']])
        self.destination.set('RIO02')
        self.destination.pack(side='left', padx=6)
        ttk.Button(pair_controls, text='Calculate selected pair', command=self.calculate_pair).pack(side='left', padx=6)
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill='both', expand=True, padx=16)
        self.overview = ttk.Frame(self.tabs)
        self.points_tab = ttk.Frame(self.tabs)
        self.comparison_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.overview, text='Distance Dashboard')
        self.tabs.add(self.points_tab, text='Locations & Evidence')
        self.tabs.add(self.comparison_tab, text='API Comparison')
        self.checks_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.checks_tab, text='Numerical & QGIS Checks')
        check_controls = ttk.Frame(self.checks_tab, padding=10)
        check_controls.pack(fill='x')
        ttk.Button(check_controls, text='Run independent check', command=self.run_independent).pack(side='left', padx=4)
        ttk.Button(check_controls, text='Save QGIS CSV template', command=self.save_qgis_template).pack(side='left', padx=4)
        ttk.Button(check_controls, text='Import QGIS measurements', command=self.import_qgis).pack(side='left', padx=4)
        ttk.Button(check_controls, text='Save check report', command=self.save_check_report).pack(side='left', padx=4)
        self.checks_text = tk.Text(self.checks_tab, wrap='word', font=('Consolas', 10), padx=16, pady=16)
        checks_scroll = ttk.Scrollbar(self.checks_tab, command=self.checks_text.yview)
        self.checks_text.configure(yscrollcommand=checks_scroll.set)
        checks_scroll.pack(side='right', fill='y')
        self.checks_text.pack(fill='both', expand=True)
        self.distances_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.distances_tab, text='All Distances')
        self.gallery_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.gallery_tab, text='QGIS Screenshots')
        gallery_controls = ttk.Frame(self.gallery_tab, padding=10)
        gallery_controls.pack(fill='x')
        ttk.Button(gallery_controls, text='Add QGIS screenshots', command=self.add_gallery_images).pack(side='left', padx=4)
        ttk.Button(gallery_controls, text='Reload gallery', command=self.reload_gallery).pack(side='left', padx=4)
        self.gallery_selector = ttk.Combobox(gallery_controls, state='readonly', width=60)
        self.gallery_selector.pack(side='left', padx=8)
        self.gallery_selector.bind('<<ComboboxSelected>>', self.show_gallery_image)
        self.gallery_caption = tk.StringVar(value='No QGIS screenshots added. Use Add QGIS screenshots to select your real map captures.')
        ttk.Label(self.gallery_tab, textvariable=self.gallery_caption, padding=10, wraplength=1000).pack(fill='x')
        self.gallery_image_label = ttk.Label(self.gallery_tab, anchor='center')
        self.gallery_image_label.pack(fill='both', expand=True)
        self.gallery_image_label.bind('<Configure>', self.resize_gallery_image)
        map_controls = ttk.Frame(self.overview, padding=(8, 5))
        map_controls.pack(fill='x')
        ttk.Checkbutton(map_controls, text='Street basemap', variable=self.show_streets,
                        command=self.toggle_street_map).pack(side='left', padx=4)
        self.map_button = ttk.Button(map_controls, text='Load street map', command=self.load_map)
        self.map_button.pack(side='left', padx=4)
        ttk.Button(map_controls, text='Open Rio in OpenStreetMap',
                   command=lambda: webbrowser.open(openstreetmap_url(self.dataset))).pack(side='left', padx=4)
        ttk.Button(map_controls, text='Open origin in OpenStreetMap', command=self.open_selected_location).pack(side='left', padx=4)
        self.map_message = tk.StringVar(value='Street map loads online; coordinate view stays available if loading fails.')
        ttk.Label(self.overview, textvariable=self.map_message, wraplength=1100, padding=(12, 2)).pack(fill='x')
        self.figure = Figure(figsize=(11.5, 3.8), dpi=100, facecolor='white')
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.overview)
        self.map_toolbar = NavigationToolbar2Tk(self.canvas, self.overview, pack_toolbar=False)
        self.map_toolbar.pack(side='bottom', fill='x')
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.table = ttk.Treeview(self.distances_tab, columns=('pair', 'meters', 'km'), show='headings', height=6)
        for column, label, width in [('pair', 'Location pair', 650), ('meters', 'Distance (m)', 150), ('km', 'Distance (km)', 150)]:
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
        self.reload_gallery()
        self.tabs.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        self.after(100, self.poll_results)
        self.after(150, self.poll_map_results)
        self.after(200, self.load_map)

    def draw(self):
        self.summary.set(f"{self.dataset['coordinate_status']} | {len(self.dataset['locations'])} locations / {len(self.rows)} pairs | No street routes or altitude.\n"
                         'Christ monument and Sugarloaf summit are separate from Cosme Velho station (RIO04). QGIS review pending.')
        self.qgis_status = 'PENDING'
        self.last_check_report = None
        self.set_text(self.checks_text, 'Run the independent Vincenty check or import measured QGIS distances.\nQGIS status: PENDING until actual values are supplied.\nTemplate distances are deliberately blank; fill only qgis_distance_m using meters and a decimal point.')
        ids = [p['id'] for p in self.dataset['locations']]
        self.origin.configure(values=ids)
        self.destination.configure(values=ids)
        if self.origin.get() not in ids:
            self.origin.set(ids[0])
        if self.destination.get() not in ids:
            self.destination.set(ids[1])
        self.table.configure(height=min(10, len(self.rows)))
        self.table.delete(*self.table.get_children())
        for row in self.rows:
            self.table.insert('', 'end', values=(f"{row['from_id']} — {row['to_id']}",
                                                f"{row['distance_m']:,.2f}", f"{row['distance_km']:.3f}"))
        if self.street_map is not None:
            try:
                bounds, key = view_spec(self.dataset)
                if self.street_map.view_key != key or self.street_map.bounds_lon_lat != bounds:
                    self.street_map = None
            except ValueError:
                self.street_map = None
        self.redraw_chart()
        sections = [f"Dataset: {self.dataset['dataset_version']}\nCRS: EPSG:4326 | Ellipsoid: WGS 84\nStatus: {self.dataset['coordinate_status']}\n"]
        for p in self.dataset['locations']:
            sections.append(f"{p['id']} | {p['name']}\nLatitude: {p['latitude']:.6f} | Longitude: {p['longitude']:.6f}\n"
                            f"Point type: {p.get('point_type', 'reference')} | {p.get('coordinate_status', self.dataset['coordinate_status'])}\n{p['access_note']}\nSource: {p['source_url']}\nCoordinate basis: {p['coordinate_basis']}\n")
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
            self.load_map()
        except Exception as exc:
            messagebox.showerror('Dataset error', str(exc))

    def calculate_pair(self):
        origin, destination = self.origin.get(), self.destination.get()
        if origin == destination:
            messagebox.showwarning('Select a pair', 'Select two different locations.')
            return
        row = next(r for r in self.rows if {r['from_id'], r['to_id']} == {origin, destination})
        self.status.set(f"{origin} / {destination}: {row['distance_m']:,.3f} m | {row['distance_km']:.3f} km. Cartographic reference locations; no route or altitude.")
        self.selected_pair = (origin, destination)
        self.redraw_chart()
        self.tabs.select(self.overview)
        self.table.selection_set(self.table.get_children()[self.rows.index(row)])

    def save_chart(self):
        path = filedialog.asksaveasfilename(title='Save distance chart', defaultextension='.png',
                                          filetypes=[('PNG image', '*.png')])
        if path:
            try:
                self.figure.savefig(path, dpi=180, bbox_inches='tight')
                self.status.set('Current chart saved as PNG, including visible basemap attribution. This is not a QGIS screenshot.')
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

    def redraw_chart(self):
        basemap = self.street_map if self.show_streets.get() else None
        draw_distance_figure(self.figure, self.dataset, basemap=basemap, selected_pair=self.selected_pair)
        self.canvas.draw_idle()
        self.map_toolbar.update()

    def toggle_street_map(self):
        self.redraw_chart()
        if self.show_streets.get():
            self.load_map()
        else:
            self.map_message.set('Coordinate overview selected. Distance calculations are unchanged.')

    def on_tab_changed(self, event=None):
        if self.tabs.select() == str(self.overview) and self.show_streets.get() and self.street_map is None:
            self.load_map()
        elif self.tabs.select() == str(self.gallery_tab):
            self.show_gallery_image()

    def load_map(self):
        if self.map_busy or not self.show_streets.get() or self.tabs.select() != str(self.overview):
            return
        self.map_busy = True
        self.map_button.configure(state='disabled')
        self.map_message.set('Loading streets and neighborhoods for the current view...')
        dataset = self.dataset
        def worker():
            try:
                self.map_queue.put((dataset, load_street_map(dataset), None))
            except Exception as exc:
                self.map_queue.put((dataset, None, str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def poll_map_results(self):
        try:
            snapshot, basemap, error = self.map_queue.get_nowait()
            self.map_busy = False
            self.map_button.configure(state='normal')
            if snapshot is self.dataset:
                if error:
                    self.map_message.set(f'Street map unavailable: {error}. Coordinate view remains available; retry Load street map.')
                else:
                    self.street_map = basemap
                    self.map_message.set('OpenStreetMap streets and neighborhoods. ' +
                        ('Using previously cached tiles; the online refresh failed.' if basemap.stale else 'Current viewport loaded.') +
                        ' Lines show geodesic separations, not road routes.')
                self.redraw_chart()
            else:
                self.load_map()
        except queue.Empty:
            pass
        self.after(150, self.poll_map_results)

    def open_selected_location(self):
        point = next(p for p in self.dataset['locations'] if p['id'] == self.origin.get())
        webbrowser.open(openstreetmap_url(self.dataset, point))

    def reload_gallery(self):
        previous = self.gallery_selector.get()
        self.gallery_paths = list_screenshots()
        names = [p.name for p in self.gallery_paths]
        self.gallery_selector.configure(values=names)
        self.gallery_selector.set(previous if previous in names else names[0] if names else '')
        self.show_gallery_image()

    def add_gallery_images(self):
        paths = filedialog.askopenfilenames(title='Choose your QGIS screenshots',
                    filetypes=[('Images', '*.png *.jpg *.jpeg *.webp')])
        if not paths:
            return
        errors, imported = [], []
        for path in paths:
            try:
                imported.append(add_screenshot(path))
            except Exception as exc:
                errors.append(f'{path}: {exc}')
        self.reload_gallery()
        if imported:
            self.gallery_selector.set(imported[-1].name)
            self.show_gallery_image()
        if errors:
            messagebox.showerror('Screenshot import', '\n'.join(errors))

    def resize_gallery_image(self, event=None):
        if self.gallery_resize_job:
            self.after_cancel(self.gallery_resize_job)
        self.gallery_resize_job = self.after(150, self.show_gallery_image)

    def show_gallery_image(self, event=None):
        self.gallery_resize_job = None
        selected = next((p for p in getattr(self, 'gallery_paths', []) if p.name == self.gallery_selector.get()), None)
        if selected is None:
            self.gallery_image_label.configure(image='')
            self.gallery_photo = None
            self.gallery_caption.set('No QGIS screenshots added. Use Add QGIS screenshots to select your real map captures.')
            return
        try:
            size = (max(300, self.gallery_image_label.winfo_width() - 20),
                    max(200, self.gallery_image_label.winfo_height() - 20))
            self.gallery_photo = ImageTk.PhotoImage(screenshot_thumbnail(selected, size))
            self.gallery_image_label.configure(image=self.gallery_photo)
            self.gallery_caption.set(f'{selected.name} — user-provided capture. Imported images do not automatically validate coordinates or measurements.')
        except Exception as exc:
            self.gallery_image_label.configure(image='')
            self.gallery_photo = None
            self.gallery_caption.set(f'Cannot open screenshot: {exc}')

    def run_independent(self):
        report = independent_report(self.dataset)
        self.last_check_report = report
        self.set_text(self.checks_text, format_report(report, 'INDEPENDENT NUMERICAL CHECK'))
        self.tabs.select(self.checks_tab)
        self.status.set(f"Independent numerical check: {report['status']}. QGIS: {self.qgis_status}.")

    def save_qgis_template(self):
        path = filedialog.asksaveasfilename(title='Save QGIS measurement template',
                    initialfile='qgis_reference_template.csv', defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if path:
            try:
                write_qgis_template(self.dataset, path)
                self.status.set('Template saved. Measure in QGIS and fill qgis_distance_m; unknown values stay blank.')
            except Exception as exc:
                messagebox.showerror('Template error', str(exc))

    def import_qgis(self):
        path = filedialog.askopenfilename(title='Import completed QGIS CSV template', filetypes=[('CSV', '*.csv')])
        if path:
            try:
                report = qgis_report(self.dataset, path)
                self.qgis_status = report['status']
                self.last_check_report = report
                self.set_text(self.checks_text, format_report(report, 'QGIS / PYTHON COMPARISON'))
                self.tabs.select(self.checks_tab)
                self.status.set(f"QGIS comparison: {report['status']}. Numerical agreement does not establish positional accuracy.")
            except Exception as exc:
                self.qgis_status = 'ERROR'
                self.last_check_report = None
                self.set_text(self.checks_text, f'QGIS import rejected: {exc}\nNo comparison accepted. Re-export the template for the current dataset.')
                self.status.set('QGIS import rejected; comparison status: ERROR.')
                messagebox.showerror('QGIS comparison error', str(exc))

    def save_check_report(self):
        if self.last_check_report is None:
            messagebox.showinfo('No report', 'Run an independent check or import QGIS measurements first.')
            return
        path = filedialog.asksaveasfilename(title='Save numerical check report',
                    defaultextension='.json', filetypes=[('JSON', '*.json')])
        if path:
            try:
                from pathlib import Path
                Path(path).write_text(json.dumps(self.last_check_report, indent=2, allow_nan=False), encoding='utf-8')
                self.status.set('Numerical check report saved.')
            except Exception as exc:
                messagebox.showerror('Report export error', str(exc))

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
                report = compare_api_payload(dataset, payload)
                text = format_report(report, 'LOCAL PYTHON / FASTAPI COMPARISON')
                self.results_queue.put((dataset, report['status'], text))
            except Exception as exc:
                self.results_queue.put((dataset, 'ERROR', f'API comparison failed: {exc}\n\nStart api.py in this project and try again.'))
        threading.Thread(target=worker, daemon=True).start()

    def poll_results(self):
        try:
            snapshot, status, report = self.results_queue.get_nowait()
            if snapshot is not self.dataset:
                self.compare_button.configure(state='normal')
                self.status.set('Dataset changed during comparison; compare again.')
                self.after(100, self.poll_results)
                return
            self.set_text(self.comparison_text, report)
            self.tabs.select(self.comparison_tab)
            self.status.set(f'API comparison: {status}. QGIS comparison: {self.qgis_status}.')
            self.compare_button.configure(state='normal')
        except queue.Empty:
            pass
        self.after(100, self.poll_results)


if __name__ == '__main__':
    Dashboard().mainloop()
