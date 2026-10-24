"""Run this file in PyCharm. No QGIS installation is needed."""
from pathlib import Path
import json
import threading
from api_client import compare_with_api
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.patches import Polygon
from PIL import Image, ImageTk
from core import load_regions, calculate, export_geojson, GEOD

ROOT=Path(__file__).resolve().parent

def polygon_parts(g):
    return [g] if g.geom_type == 'Polygon' else g.geoms

def draw_map(ax, regions, result=None, overview=False):
    ax.clear(); ax.set_facecolor('#eef4f8')
    selected = () if result is None else (result['origin'],result['destination'])
    for code,row in regions.items():
        for p in polygon_parts(row['geometry']):
            ax.add_patch(Polygon(list(p.exterior.coords),facecolor=('#f2a44b' if code in selected else '#c1d6c7'),edgecolor='#648175',linewidth=.45))
            for hole in p.interiors:
                ax.add_patch(Polygon(list(hole.coords), facecolor='#eef4f8',edgecolor='#648175',linewidth=.3))
    ax.autoscale_view()
    if result:
        a,b=result['centroids_lon_lat']
        pts=[a,*GEOD.npts(*a,*b,80),b]
        ax.plot(*zip(*pts), color='#1769aa',lw=2.5)
        for code,p in zip(selected,(a,b)):
            ax.scatter(*p,color='#bd4930',s=48,zorder=5)
            ax.annotate(code,p,xytext=((4,12) if code == selected[0] else (4,-16)) if overview else (7,9),textcoords='offset points',fontsize=10,fontweight='bold')
        if not overview:
            bounds=[regions[c]['geometry'].bounds for c in selected]
            xmin=min(v[0] for v in bounds); xmax=max(v[2] for v in bounds)
            ymin=min(v[1] for v in bounds); ymax=max(v[3] for v in bounds)
            pad=max(xmax-xmin,ymax-ymin)*.15+.1
            ax.set_xlim(xmin-pad,xmax+pad);ax.set_ylim(ymin-pad,ymax+pad)
        ax.set_title(f"{result['origin_name']} → {result['destination_name']} | {result['distance_km']:.2f} km",fontsize=11)
    if overview:
        ax.set_xlim(-12,35);ax.set_ylim(34,65);ax.set_title('Europe • NUTS 2024',fontsize=13)
    ax.set_aspect(1.5);ax.set_xlabel('Longitude (°)');ax.set_ylabel('Latitude (°)')
    ax.grid(alpha=.15)

class App(tk.Tk):
    def __init__(self):
        super().__init__();self.title('GIS Training | QGIS → Python → FastAPI')
        self.geometry('1240x820');self.minsize(950,680)
        self.regions={};self.result=None;self.lookup={}
        style=ttk.Style(self);style.theme_use('clam')
        style.configure('TButton',padding=8);style.configure('Title.TLabel',font=('Segoe UI',19,'bold'),foreground='#173c55')
        top=ttk.Frame(self,padding=16);top.pack(fill='x')
        ttk.Label(top,text='GIS Training — European Regions',style='Title.TLabel').pack(anchor='w')
        ttk.Label(top,text='NUTS 2024 • Centroids in EPSG:3035 • WGS 84 geodesic distance').pack(anchor='w')
        content=ttk.Frame(self,padding=(16,0,16,12));content.pack(fill='both',expand=True)
        side=ttk.Frame(content,width=290,padding=12);side.pack(side='left',fill='y');side.pack_propagate(False)
        ttk.Button(side,text='Load NUTS GeoJSON',command=self.load).pack(fill='x',pady=5)
        self.status=tk.StringVar(value='Loading included data…');ttk.Label(side,textvariable=self.status,wraplength=265).pack(anchor='w',pady=8)
        ttk.Label(side,text='Origin region').pack(anchor='w',pady=(12,4))
        self.origin=ttk.Combobox(side,state='readonly');self.origin.pack(fill='x')
        ttk.Label(side,text='Destination region').pack(anchor='w',pady=(12,4))
        self.dest=ttk.Combobox(side,state='readonly');self.dest.pack(fill='x')
        ttk.Button(side,text='Calculate and show map',command=self.run).pack(fill='x',pady=16)
        self.summary=tk.StringVar(value='');ttk.Label(side,textvariable=self.summary,wraplength=265,font=('Segoe UI',11)).pack(anchor='w',pady=8)
        ttk.Button(side,text='Export JSON report',command=lambda:self.export('json')).pack(fill='x',pady=4)
        ttk.Button(side,text='Export points + line GeoJSON',command=lambda:self.export('geojson')).pack(fill='x',pady=4)
        ttk.Button(side,text='Save map as PNG',command=self.save_map).pack(fill='x',pady=4)
        ttk.Label(side,text='Measures regional centroids.\nRoad routing is not included.',wraplength=265,foreground='#7b4a27').pack(anchor='w',pady=16)
        tabs=ttk.Notebook(content);tabs.pack(side='right',fill='both',expand=True)
        mapframe=ttk.Frame(tabs);tabs.add(mapframe,text='Map & results')
        self.details=tk.StringVar();ttk.Label(mapframe,textvariable=self.details,padding=8).pack(side='bottom',fill='x')
        self.fig=Figure(figsize=(8,6),dpi=100);self.ax=self.fig.add_subplot(111)
        self.canvas=FigureCanvasTkAgg(self.fig,master=mapframe);self.canvas.get_tk_widget().pack(fill='both',expand=True)
        NavigationToolbar2Tk(self.canvas,mapframe).update()
        gallery=ttk.Frame(tabs,padding=12);tabs.add(gallery,text='Map gallery')
        ttk.Label(gallery,text='Maps rendered from the included official polygons • available offline').pack(anchor='w')
        gallery_canvas=tk.Canvas(gallery,highlightthickness=0)
        gallery_scroll=ttk.Scrollbar(gallery,orient='vertical',command=gallery_canvas.yview)
        gallery_canvas.configure(yscrollcommand=gallery_scroll.set)
        gallery_scroll.pack(side='right',fill='y');gallery_canvas.pack(fill='both',expand=True)
        gallery_body=ttk.Frame(gallery_canvas)
        gallery_canvas.create_window((0,0),window=gallery_body,anchor='nw')
        gallery_body.bind('<Configure>',lambda event:gallery_canvas.configure(scrollregion=gallery_canvas.bbox('all')))
        self.photos=[]
        for filename in ('europe.png','france.png'):
            p=ROOT/'assets'/filename
            if p.exists():
                im=Image.open(p);im.thumbnail((770,300)); photo=ImageTk.PhotoImage(im);self.photos.append(photo)
                ttk.Label(gallery_body,image=photo).pack(pady=5)
        helpframe=ttk.Frame(tabs,padding=18);tabs.add(helpframe,text='How it works')
        instructions = (
            '1. Load WGS 84 GeoJSON and validate polygons and NUTS identifiers.\n\n'
            '2. Reproject to EPSG:3035 and calculate one centroid per region.\n\n'
            '3. Transform centroids to EPSG:4326 longitude/latitude.\n\n'
            '4. Calculate the WGS 84 geodesic distance with PyProj.\n\n'
            '5. Compare FR10–FRF3 with QGIS: 267,492.772273 m (1 m numerical tolerance).\n\n'
            '6. Start FastAPI in a separate terminal, then use the API comparison tab.\n\n'
            'Agreement checks numerical consistency, not territorial accuracy.\n'
            'The 20M boundaries are generalized; centroids depend on the projection.\n\n'
            'Source: Eurostat GISCO, NUTS 2024. See SOURCES.md for conditions.'
        )
        ttk.Label(helpframe,text=instructions,wraplength=720,justify='left').pack(anchor='w')
        api_frame=ttk.Frame(tabs,padding=18);tabs.add(api_frame,text='API comparison')
        ttk.Label(api_frame,text='Start the local API in another terminal:',font=('Segoe UI',11,'bold')).pack(anchor='w')
        ttk.Label(api_frame,text='python -m uvicorn api:app --host 127.0.0.1 --port 8000').pack(anchor='w',pady=8)
        ttk.Label(api_frame,text='API base URL').pack(anchor='w')
        self.api_url=tk.StringVar(value='http://127.0.0.1:8000')
        ttk.Entry(api_frame,textvariable=self.api_url,width=60).pack(anchor='w',pady=6)
        self.api_button=ttk.Button(api_frame,text='Compare API with current desktop result',command=self.compare_api)
        self.api_button.pack(anchor='w',pady=10)
        self.api_summary=tk.StringVar(value='Calculate a pair, start the API, then compare. The API uses the bundled dataset.')
        ttk.Label(api_frame,textvariable=self.api_summary,wraplength=700,justify='left').pack(anchor='w',pady=10)
        self.after(100,lambda:self.load(ROOT/'data'/'NUTS_2024.geojson'))
    def load(self,path=None):
        if path is None:
            path=filedialog.askopenfilename(filetypes=[('GeoJSON','*.geojson *.json')])
        if not path:return
        try:
            rows=load_regions(path)
            self.regions=rows;self.result=None
            self.lookup={f"{c} — {r['name']}":c for c,r in sorted(rows.items())}
            labels=list(self.lookup);self.origin['values']=labels;self.dest['values']=labels
            self.origin.set(next((s for s,c in self.lookup.items() if c=='FR10'),labels[0]))
            self.dest.set(next((s for s,c in self.lookup.items() if c=='FRF3'),labels[1]))
            self.status.set(f'{len(rows)} regions loaded\n{Path(path).name}')
            self.run()
        except Exception as e:messagebox.showerror('Load failed',str(e))
    def run(self):
        try:
            result=calculate(self.regions,self.lookup[self.origin.get()],self.lookup[self.dest.get()])
            self.result=result
            self.api_summary.set('Desktop result changed. Run the API comparison again.')
            text=f"{result['distance_km']:.3f} km\n{result['distance_m']:,.3f} meters"
            if 'difference_m' in result:
                text+=f"\n\nDifference from QGIS: {result['difference_m']:.6f} m\n"+('Agreement ≤ 1 m' if result['within_1m'] else 'Review data and transformation')
            self.summary.set(text)
            self.details.set('\n'.join(f'{code}: longitude {p[0]:.9f}° | latitude {p[1]:.9f}°' for code,p in zip((result['origin'],result['destination']),result['centroids_lon_lat'])))
            draw_map(self.ax,self.regions,result);self.fig.tight_layout();self.canvas.draw()
        except Exception as e:
            self.result=None;self.summary.set('');messagebox.showerror('Calculation failed',str(e))
    def compare_api(self):
        if self.result is None:
            self.api_summary.set('Calculate a desktop result first.')
            return
        snapshot=json.loads(json.dumps(self.result))
        base_url=self.api_url.get()
        self.api_button.state(['disabled'])
        self.api_summary.set('Contacting API…')
        def finish(text):
            self.api_button.state(['!disabled'])
            if self.result != snapshot and json.loads(json.dumps(self.result)) != snapshot:
                self.api_summary.set('Desktop result changed during comparison. Compare again.')
            else:
                self.api_summary.set(text)
        def worker():
            try:
                report=compare_with_api(snapshot,base_url)
                text=(f"API: {report['api_distance_m']:,.6f} m\n"
                      f"Desktop: {report['desktop_distance_m']:,.6f} m\n"
                      f"Difference: {report['difference_m']:.9f} m\n"
                      f"Coordinate agreement: {report['coordinates_match']}\n"
                      f"Method agreement: {report['method_matches']}\n"
                      f"Agreement within 1 m: {report['within_1m']}")
                if 'qgis_difference_m' in report:
                    text+=f"\nAPI difference from QGIS: {report['qgis_difference_m']:.9f} m"
                text+='\n\nShared data and calculation engine: this is an API integration check.'
            except Exception as error:
                text=f'API comparison failed: {error}\nCheck that the local server is running.'
            self.after(0,lambda:finish(text))
        threading.Thread(target=worker,daemon=True).start()

    def export(self,kind):
        if self.result is None:return
        path=filedialog.asksaveasfilename(defaultextension='.'+kind,filetypes=[(kind.upper(),'*.'+kind)])
        if path:
            try:
                if kind=='json':Path(path).write_text(json.dumps(self.result,ensure_ascii=False,indent=2),encoding='utf-8')
                else:export_geojson(self.result,path)
                messagebox.showinfo('Export','File saved successfully.')
            except Exception as e:messagebox.showerror('Save failed',str(e))
    def save_map(self):
        path=filedialog.asksaveasfilename(defaultextension='.png',filetypes=[('PNG','*.png')])
        if path:
            try:self.fig.savefig(path,dpi=180,bbox_inches='tight')
            except Exception as e:messagebox.showerror('Save failed',str(e))

if __name__=='__main__':App().mainloop()
