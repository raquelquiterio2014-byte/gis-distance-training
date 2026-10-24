# GIS Distance Training — Rio de Janeiro v2

Agora são **quatro localizações e seis pares de distâncias**.

| ID | Local | Latitude | Longitude |
|---|---|---:|---:|
| RIO01 | Copacabana Palace — Main Entrance | -22.967 | -43.1786 |
| RIO02 | Christ the Redeemer — Monument | -22.9519173 | -43.2104585 |
| RIO03 | Sugarloaf Mountain — Summit | -22.9494891 | -43.1561568 |
| RIO04 | Cosme Velho — Train Station Entrance | -22.9406 | -43.1985 |

RIO02 é o próprio Cristo Redentor; RIO03 é o cume do Pão de Açúcar.
A estação de Cosme Velho foi preservada com as mesmas coordenadas como RIO04.
O Copacabana Palace permanece como RIO01. A estação da Praia Vermelha saiu do conjunto.

As posições do Cristo e do cume foram obtidas dos pontos cartográficos do OpenStreetMap;
não são coordenadas exatas verificadas em campo. A entrada do hotel e a estação
continuam como referências aproximadas. Revisão visual e comparação no QGIS pendentes.
As fontes individuais estão em `data/locations.json` e `SOURCES.md`.

## Executar no PowerShell

Baixe e extraia a versão atual do repositório. Entre na pasta `rio`:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt
.\.venv312\Scripts\python.exe main.py
```

Em outro terminal, dentro da mesma pasta:

```powershell
.\.venv312\Scripts\python.exe api.py
```

Ou execute `RUN_DASHBOARD.cmd` e, depois da instalação, `RUN_API.cmd`.
API: http://127.0.0.1:8002/docs. Encerre a API com Ctrl+C.
No PyCharm, abra a pasta `rio` e selecione o interpretador `.venv312`.

O dashboard está em inglês, mostra quatro pontos e seis linhas/barras/resultados,
permite escolher qualquer par, exportar CSV/GeoJSON/PNG e comparar com a API.
As listas e contagens acompanham os dados carregados. A API e o dashboard usam
o mesmo motor: concordância entre eles não substitui a comparação independente no QGIS.

## Resultados desta versão

| Par | Distância (m) | Distância (km) |
|---|---:|---:|
| RIO01 – RIO02 | 3669.395 | 3.669395 |
| RIO01 – RIO03 | 3009.670 | 3.009670 |
| RIO01 – RIO04 | 3565.505 | 3.565505 |
| RIO02 – RIO03 | 5575.656 | 5.575656 |
| RIO02 – RIO04 | 1753.597 | 1.753597 |
| RIO03 – RIO04 | 4453.059 | 4.453059 |

A distância **Cosme Velho–Cristo** é geodésica sobre o elipsoide WGS 84:
não mede o percurso do trem. Não incluímos ruas, relevo, altitude ou trajeto do bondinho.

## Próxima etapa no QGIS

Abra `data/rio_entrances.geojson` (nome histórico, agora com quatro pontos mistos)
e `data/rio_geodesics.geojson` (seis linhas). Configure elipsoide de medição WGS 84
e unidades em metros. Confira cada posição e registre os seis resultados independentes.
GeoJSON usa longitude antes de latitude; EPSG:4326.

Se houver ajuste, edite `data/locations.json`, incremente `dataset_version`, clique
em **Reload coordinates**, exporte novamente e refaça as comparações.
Não reutilize as referências ou imagens antigas de três pontos para a versão v2.
A tolerância de 0,01 m verifica consistência numérica, não precisão das posições.

## Testes

```powershell
.\.venv312\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv312\Scripts\python.exe -m unittest discover -s tests -v
```

O README em inglês detalha endpoints, metodologia e arquivos.
