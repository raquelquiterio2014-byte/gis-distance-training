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
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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
        self.figure = Figure(figsize=(11.5, 3.8), dpi=100, facecolor='white')
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.overview)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.table = ttk.Treeview(self.overview, columns=('pair', 'meters', 'km'), show='headings', height=6)
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
        self.after(100, self.poll_results)

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
        draw_distance_figure(self.figure, self.dataset)
        self.canvas.draw()
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
        except Exception as exc:
            messagebox.showerror('Dataset error', str(exc))

    def calculate_pair(self):
        origin, destination = self.origin.get(), self.destination.get()
        if origin == destination:
            messagebox.showwarning('Select a pair', 'Select two different locations.')
            return
        row = next(r for r in self.rows if {r['from_id'], r['to_id']} == {origin, destination})
        self.status.set(f"{origin} / {destination}: {row['distance_m']:,.3f} m | {row['distance_km']:.3f} km. Cartographic reference locations; no route or altitude.")
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
