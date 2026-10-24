"""Run in PyCharm or PowerShell: python main.py."""
import json
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from urllib.request import Request, urlopen
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from PIL import Image, ImageTk
from core import ROOT, GEOD, load_points, calculate, all_distances, export_lines


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('GIS Training | Paris • QGIS → Python → FastAPI')
        self.geometry('1240x800')
        self.minsize(960,680)
        self.points = load_points()
        self.rows = all_distances(self.points)
        self.result = None
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TButton', padding=7)
        header = ttk.Frame(self, padding=14)
        header.pack(fill='x')
        ttk.Label(header,text='GIS Training — Paris Landmarks',font=('Segoe UI',20,'bold'),foreground='#173c55').pack(anchor='w')
        ttk.Label(header,text='Three digitized entrance points • WGS 84 geodesic distances • QGIS reference comparison').pack(anchor='w')
        body=ttk.Frame(self,padding=(14,0,14,12));body.pack(fill='both',expand=True)
        side=ttk.Frame(body,width=280,padding=10);side.pack(side='left',fill='y');side.pack_propagate(False)
        self.lookup={row['name']:code for code,row in self.points.items()}
        labels=list(self.lookup)
        ttk.Label(side,text='Origin').pack(anchor='w')
        self.origin=ttk.Combobox(side,values=labels,state='readonly');self.origin.pack(fill='x',pady=5);self.origin.set(labels[0])
        ttk.Label(side,text='Destination').pack(anchor='w',pady=(10,0))
        self.destination=ttk.Combobox(side,values=labels,state='readonly');self.destination.pack(fill='x',pady=5);self.destination.set(labels[2])
        ttk.Button(side,text='Calculate and show map',command=self.run).pack(fill='x',pady=12)
        self.summary=tk.StringVar();ttk.Label(side,textvariable=self.summary,wraplength=250,font=('Segoe UI',11)).pack(anchor='w',pady=10)
        ttk.Button(side,text='Export all results as JSON',command=self.export_json).pack(fill='x',pady=4)
        ttk.Button(side,text='Export connection lines GeoJSON',command=self.export_geojson).pack(fill='x',pady=4)
        ttk.Button(side,text='Save map as PNG',command=self.save_map).pack(fill='x',pady=4)
        ttk.Button(side,text='Open Paris in OpenStreetMap',command=lambda:webbrowser.open('https://www.openstreetmap.org/#map=14/48.8570/2.3220')).pack(fill='x',pady=4)
        ttk.Label(side,text='Approximate entrance positions.\nNo road routing.\nQGIS tolerance checks numerical agreement, not geographic accuracy.',wraplength=250,foreground='#7b4a27').pack(anchor='w',pady=15)
        tabs=ttk.Notebook(body);tabs.pack(fill='both',expand=True)
        map_tab=ttk.Frame(tabs);tabs.add(map_tab,text='Map & results')
        self.details=tk.StringVar();ttk.Label(map_tab,textvariable=self.details,padding=8).pack(side='bottom',fill='x')
        ttk.Label(map_tab,text='Coordinate plot of your points — no street basemap',padding=6).pack(anchor='w')
        self.fig=Figure(figsize=(8,5),dpi=100);self.ax=self.fig.add_subplot(111)
        self.canvas=FigureCanvasTkAgg(self.fig,master=map_tab)
        toolbar=NavigationToolbar2Tk(self.canvas,map_tab,pack_toolbar=False);toolbar.pack(side='bottom',fill='x')
        self.canvas.get_tk_widget().pack(fill='both',expand=True)
        table_tab=ttk.Frame(tabs,padding=12);tabs.add(table_tab,text='All distances')
        columns=('origin','destination','meters','qgis','difference')
        table=ttk.Treeview(table_tab,columns=columns,show='headings',height=6)
        for key,title,width in zip(columns,['Origin','Destination','Python (m)','QGIS (m)','Difference (m)'],[165,165,125,125,120]):
            table.heading(key,text=title);table.column(key,width=width,stretch=True)
        table.pack(fill='x')
        for row in self.rows:
            table.insert('', 'end',values=(row['origin_name'],row['destination_name'],f"{row['distance_m']:,.6f}",f"{row['qgis_reference_m']:,.6f}",f"{row['difference_m']:.9f}"))
        ttk.Label(table_tab,text='All three QGIS references come from your saved distance matrix.\nDistances use your recorded points, not landmark centroids.',padding=10).pack(anchor='w')
        gallery=ttk.Frame(tabs,padding=10);tabs.add(gallery,text='QGIS screenshots')
        ttk.Label(gallery,text='Your original QGIS views used to digitize the approximate entrance locations.').pack(anchor='w')
        selector=ttk.Combobox(gallery,values=labels,state='readonly');selector.pack(anchor='w',pady=8);selector.set(labels[0])
        image_label=ttk.Label(gallery);image_label.pack(fill='both',expand=True)
        def show_image(event=None):
            path=ROOT/'assets'/(self.lookup[selector.get()]+'.png')
            with Image.open(path) as im:
                im.thumbnail((800,480));self.photo=ImageTk.PhotoImage(im)
            image_label.configure(image=self.photo)
        selector.bind('<<ComboboxSelected>>',show_image);show_image()
        api_tab=ttk.Frame(tabs,padding=15);tabs.add(api_tab,text='API comparison')
        ttk.Label(api_tab,text='Start the Paris API in another terminal:',font=('Segoe UI',11,'bold')).pack(anchor='w')
        ttk.Label(api_tab,text='python -m uvicorn api:app --host 127.0.0.1 --port 8001').pack(anchor='w',pady=6)
        self.api_url=tk.StringVar(value='http://127.0.0.1:8001')
        ttk.Entry(api_tab,textvariable=self.api_url,width=55).pack(anchor='w',pady=6)
        self.api_button=ttk.Button(api_tab,text='Compare all three pairs with API',command=self.compare_api);self.api_button.pack(anchor='w',pady=6)
        ttk.Button(api_tab,text='Open API documentation',command=lambda:webbrowser.open(self.api_url.get().rstrip('/')+'/docs')).pack(anchor='w')
        self.api_text=tk.StringVar(value='The desktop works without starting the API.');ttk.Label(api_tab,textvariable=self.api_text,wraplength=750,justify='left').pack(anchor='w',pady=15)
        method=ttk.Frame(tabs,padding=15);tabs.add(method,text='Method & sources')
        ttk.Label(method,text='1. Three Point features digitized in QGIS and exported as WGS 84 GeoJSON.\n\n2. Read coordinates in longitude, latitude order. No centroids or polygon reprojection.\n\n3. Solve the inverse geodesic problem with PyProj Geod on the WGS 84 ellipsoid.\n\n4. Compare all three distances with the user-provided QGIS matrix.\n\n5. Reuse the calculation engine through FastAPI and compare HTTP responses.\n\nThe coordinates represent approximate entrances, not surveyed door positions.\nRepeated calculations using the same data do not validate physical accuracy.\n\nSource: user-digitized points on OpenStreetMap. © OpenStreetMap contributors.\nEntrance descriptions checked against official monument websites.\nSee README.md and SOURCES.md.',wraplength=760,justify='left').pack(anchor='w')
        self.run()

    def run(self):
        try:
            self.result=calculate(self.points,self.lookup[self.origin.get()],self.lookup[self.destination.get()])
            row=self.result
            self.summary.set(f"{row['distance_km']:.3f} km\n{row['distance_m']:,.3f} meters\n\nDifference from QGIS:\n{row['difference_m']:.9f} m\nAgreement within 1 m: {row['within_1m']}")
            ax=self.ax;ax.clear();ax.set_facecolor('#eef4f8')
            for connection in self.rows:
                a,b=connection['coordinates_lon_lat'];points=[a,*GEOD.npts(*a,*b,40),b]
                selected={connection['origin'],connection['destination']}=={row['origin'],row['destination']}
                ax.plot(*zip(*points),color='#1769aa' if selected else '#b4c3ca',lw=3 if selected else 1.3,zorder=2)
                mid=points[len(points)//2]
                ax.annotate(f"{connection['distance_km']:.3f} km",mid,xytext=(0,9),textcoords='offset points',fontsize=9,color='#173c55')
            offsets={'notre_dame':(-135,-25),'louvre':(8,10),'eiffel_tower':(10,-25)}
            for code,point in self.points.items():
                ax.scatter(*point['coordinates'],s=65,color='#bd4930',zorder=4)
                ax.annotate(point['name'],point['coordinates'],xytext=offsets[code],textcoords='offset points',fontweight='bold',fontsize=10)
            ax.set_xlim(2.288,2.355);ax.set_ylim(48.850,48.864)
            ax.set_aspect(1.52);ax.grid(alpha=.25);ax.set_xlabel('Longitude (°)');ax.set_ylabel('Latitude (°)')
            ax.set_title(f"{row['origin_name']} → {row['destination_name']} | {row['distance_km']:.3f} km",fontsize=11)
            self.fig.tight_layout();self.canvas.draw()
            self.details.set('\n'.join(f"{p['name']}: longitude {p['coordinates'][0]:.9f}° | latitude {p['coordinates'][1]:.9f}°" for p in self.points.values()))
        except Exception as error:
            messagebox.showerror('Calculation failed',str(error))

    def compare_api(self):
        base=self.api_url.get().rstrip('/');self.api_button.state(['disabled']);self.api_text.set('Comparing all pairs…')
        def finish(text):
            self.api_text.set(text);self.api_button.state(['!disabled'])
        def worker():
            try:
                lines=[]
                for local in self.rows:
                    payload={key:local[key] for key in ('origin','destination')}
                    req=Request(base+'/distance',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
                    with urlopen(req,timeout=5) as response: remote=json.load(response)
                    difference=abs(remote['distance_m']-local['distance_m'])
                    same=all(remote.get(k)==local[k] for k in ('origin','destination','coordinates_lon_lat','coordinate_crs','ellipsoid','method'))
                    passed=difference<=1 and same
                    lines.append(f"{local['origin_name']} ↔ {local['destination_name']}\nAPI: {remote['distance_m']:,.6f} m | Desktop difference: {difference:.9f} m\nCoordinates and method match: {same} | Agreement within 1 m: {passed}\n")
                text='\n'.join(lines)+'\nShared engine and data: an HTTP integration check, not independent positional validation.'
            except Exception as error:
                text=f'API comparison failed: {error}\nStart the Paris API on port 8001.'
            self.after(0,lambda:finish(text))
        threading.Thread(target=worker,daemon=True).start()

    def export_json(self):
        self.save_file('.json',lambda p:Path(p).write_text(json.dumps(self.rows,indent=2),encoding='utf-8'))

    def export_geojson(self):
        self.save_file('.geojson',lambda p:export_lines(self.points,p))

    def save_map(self):
        self.save_file('.png',lambda p:self.fig.savefig(p,dpi=180,bbox_inches='tight'))

    def save_file(self,extension,writer):
        path=filedialog.asksaveasfilename(defaultextension=extension,filetypes=[(extension[1:].upper(),'*'+extension)])
        if path:
            try:writer(path);messagebox.showinfo('Export','File saved successfully.')
            except Exception as error:messagebox.showerror('Export failed',str(error))


if __name__=='__main__':
    App().mainloop()
