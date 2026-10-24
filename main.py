"""Run this file in PyCharm. No QGIS installation is needed."""
from pathlib import Path
import json
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
            ax.annotate(code,p,xytext=(7,9),textcoords='offset points',fontsize=10,fontweight='bold')
        if not overview:
            bounds=[regions[c]['geometry'].bounds for c in selected]
            xmin=min(v[0] for v in bounds); xmax=max(v[2] for v in bounds)
            ymin=min(v[1] for v in bounds); ymax=max(v[3] for v in bounds)
            pad=max(xmax-xmin,ymax-ymin)*.15+.1
            ax.set_xlim(xmin-pad,xmax+pad);ax.set_ylim(ymin-pad,ymax+pad)
        ax.set_title(f"{result['origin_name']} → {result['destination_name']} | {result['distance_km']:.2f} km",fontsize=11)
    if overview:
        ax.set_xlim(-12,35);ax.set_ylim(34,65);ax.set_title('Europa • NUTS 2024',fontsize=13)
    ax.set_aspect(1.5);ax.set_xlabel('Longitude (°)');ax.set_ylabel('Latitude (°)')
    ax.grid(alpha=.15)

class App(tk.Tk):
    def __init__(self):
        super().__init__();self.title('GIS Training | QGIS → Python • European Data')
        self.geometry('1240x820');self.minsize(950,680)
        self.regions={};self.result=None;self.lookup={}
        style=ttk.Style(self);style.theme_use('clam')
        style.configure('TButton',padding=8);style.configure('Title.TLabel',font=('Segoe UI',19,'bold'),foreground='#173c55')
        top=ttk.Frame(self,padding=16);top.pack(fill='x')
        ttk.Label(top,text='GIS Training — European Regions',style='Title.TLabel').pack(anchor='w')
        ttk.Label(top,text='NUTS 2024 • Centroides em EPSG:3035 • Distância geodésica WGS 84').pack(anchor='w')
        content=ttk.Frame(self,padding=(16,0,16,12));content.pack(fill='both',expand=True)
        side=ttk.Frame(content,width=290,padding=12);side.pack(side='left',fill='y');side.pack_propagate(False)
        ttk.Button(side,text='Carregar GeoJSON NUTS',command=self.load).pack(fill='x',pady=5)
        self.status=tk.StringVar(value='Carregando dados incluídos…');ttk.Label(side,textvariable=self.status,wraplength=265).pack(anchor='w',pady=8)
        ttk.Label(side,text='Região de origem').pack(anchor='w',pady=(12,4))
        self.origin=ttk.Combobox(side,state='readonly');self.origin.pack(fill='x')
        ttk.Label(side,text='Região de destino').pack(anchor='w',pady=(12,4))
        self.dest=ttk.Combobox(side,state='readonly');self.dest.pack(fill='x')
        ttk.Button(side,text='Calcular e mostrar no mapa',command=self.run).pack(fill='x',pady=16)
        self.summary=tk.StringVar(value='');ttk.Label(side,textvariable=self.summary,wraplength=265,font=('Segoe UI',11)).pack(anchor='w',pady=8)
        ttk.Button(side,text='Exportar relatório JSON',command=lambda:self.export('json')).pack(fill='x',pady=4)
        ttk.Button(side,text='Exportar pontos + linha GeoJSON',command=lambda:self.export('geojson')).pack(fill='x',pady=4)
        ttk.Button(side,text='Salvar imagem do mapa PNG',command=self.save_map).pack(fill='x',pady=4)
        ttk.Label(side,text='Mede centroides de regiões.\nNão mede Paris–Vignot nem rotas por estradas.',wraplength=265,foreground='#7b4a27').pack(anchor='w',pady=16)
        tabs=ttk.Notebook(content);tabs.pack(side='right',fill='both',expand=True)
        mapframe=ttk.Frame(tabs);tabs.add(mapframe,text='Mapa e resultado')
        self.fig=Figure(figsize=(8,6),dpi=100);self.ax=self.fig.add_subplot(111)
        self.canvas=FigureCanvasTkAgg(self.fig,master=mapframe);self.canvas.get_tk_widget().pack(fill='both',expand=True)
        NavigationToolbar2Tk(self.canvas,mapframe).update()
        self.details=tk.StringVar();ttk.Label(mapframe,textvariable=self.details,padding=8).pack(fill='x')
        gallery=ttk.Frame(tabs,padding=12);tabs.add(gallery,text='Imagens dos mapas')
        ttk.Label(gallery,text='Mapas gerados com os polígonos oficiais incluídos • disponíveis offline').pack(anchor='w')
        self.photos=[]
        for filename in ('europe.png','france.png'):
            p=ROOT/'assets'/filename
            if p.exists():
                im=Image.open(p);im.thumbnail((770,300)); photo=ImageTk.PhotoImage(im);self.photos.append(photo)
                ttk.Label(gallery,image=photo).pack(pady=5)
        helpframe=ttk.Frame(tabs,padding=18);tabs.add(helpframe,text='Como funciona')
        ttk.Label(helpframe,text='1. GeoJSON em WGS 84 → validar polígonos e códigos NUTS.\n\n2. Reprojetar para EPSG:3035 e calcular um centroide por região.\n\n3. Transformar centroides para longitude/latitude EPSG:4326.\n\n4. Resolver a distância geodésica com PyProj / WGS 84.\n\n5. Comparar FR10–FRF3 com QGIS: 267.492,772273 m (tolerância numérica: 1 m).\n\nA tolerância compara cálculos; não representa a precisão territorial dos dados.\nOs limites 20M são generalizados, e o centroide depende da projeção.\n\nFonte: Eurostat GISCO, NUTS 2024. Veja FONTES.md para atribuição e condições.',wraplength=720,justify='left').pack(anchor='w')
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
            self.status.set(f'{len(rows)} regiões carregadas\n{Path(path).name}')
            self.run()
        except Exception as e:messagebox.showerror('Falha ao carregar',str(e))
    def run(self):
        try:
            result=calculate(self.regions,self.lookup[self.origin.get()],self.lookup[self.dest.get()])
            self.result=result
            text=f"{result['distance_km']:.3f} km\n{result['distance_m']:,.3f} metros"
            if 'difference_m' in result:
                text+=f"\n\nDiferença para QGIS: {result['difference_m']:.6f} m\n"+('Concordância ≤ 1 m' if result['within_1m'] else 'Revisar dados e transformação')
            self.summary.set(text)
            self.details.set('\n'.join(f'{code}: longitude {p[0]:.9f}° | latitude {p[1]:.9f}°' for code,p in zip((result['origin'],result['destination']),result['centroids_lon_lat'])))
            draw_map(self.ax,self.regions,result);self.fig.tight_layout();self.canvas.draw()
        except Exception as e:
            self.result=None;self.summary.set('');messagebox.showerror('Cálculo não realizado',str(e))
    def export(self,kind):
        if self.result is None:return
        path=filedialog.asksaveasfilename(defaultextension='.'+kind,filetypes=[(kind.upper(),'*.'+kind)])
        if path:
            try:
                if kind=='json':Path(path).write_text(json.dumps(self.result,ensure_ascii=False,indent=2),encoding='utf-8')
                else:export_geojson(self.result,path)
                messagebox.showinfo('Exportação','Arquivo salvo com sucesso.')
            except Exception as e:messagebox.showerror('Erro ao salvar',str(e))
    def save_map(self):
        path=filedialog.asksaveasfilename(defaultextension='.png',filetypes=[('PNG','*.png')])
        if path:
            try:self.fig.savefig(path,dpi=180,bbox_inches='tight')
            except Exception as e:messagebox.showerror('Erro ao salvar',str(e))

if __name__=='__main__':App().mainloop()
