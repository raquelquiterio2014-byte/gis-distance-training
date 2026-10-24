# GIS Distance Training — Rio de Janeiro v1

Dashboard desktop em inglês + FastAPI para calcular três distâncias geodésicas
sobre o elipsoide WGS 84. Python 3.12 recomendado para acompanhar o ambiente da Raquel.

## Início rápido, seguindo Paris

Abra esta pasta `rio` e execute `RUN_DASHBOARD.cmd`. Depois da instalação,
execute `RUN_API.cmd` para iniciar a API. Rio usa a porta **8002**; Paris usa 8001
e o exercício regional usa 8000. Abra esta pasta como projeto no PyCharm
para evitar importar os módulos `core.py` e `api.py` dos outros exercícios.

## Pontos provisórios

| ID | Referência | Latitude | Longitude |
|---|---|---:|---:|
| RIO01 | Copacabana Palace — Main Entrance | -22.9670 | -43.1786 |
| RIO02 | Christ the Redeemer — Cosme Velho Train Access | -22.9406 | -43.1985 |
| RIO03 | Sugarloaf Cable Car — Praia Vermelha Access | -22.9558 | -43.1670 |

**APPROXIMATE_PENDING_QGIS_REVIEW**: as coordenadas são referências provisórias
próximas aos acessos. Não representam entradas levantadas em campo ou confirmadas
visualmente. A entrada do hotel precisa ser ajustada no QGIS. As referências das
estações também precisam dessa conferência. RIO02 é a estação inferior de Cosme
Velho, não a estátua do Cristo. RIO03 é a estação inferior, não o cume.
Endereços oficiais e base das coordenadas constam em `data/locations.json`.

As distâncias ignoram altitude, ruas, ferrovia e percurso do teleférico. Usamos
`Geodesic.WGS84.Inverse(...)["s12"]`, em metros. Não usamos distância em graus,
Web Mercator ou Haversine esférica. Casas decimais do resultado não indicam
precisão das coordenadas. Armazenamos valores completos e arredondamos só na tela.

## Executar no PowerShell (Windows)

Extraia o ZIP e abra o PowerShell na pasta que contém `main.py` e `api.py`.

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt
.\.venv312\Scripts\python.exe main.py
```

Em um segundo PowerShell, na mesma pasta, inicie a API:

```powershell
.\.venv312\Scripts\python.exe api.py
```

Abra http://127.0.0.1:8002/docs. Encerre a API com Ctrl+C.
Como alternativa para desenvolvimento:

```powershell
.\.venv312\Scripts\python.exe -m uvicorn api:app --reload --port 8002
```

No PyCharm, abra a pasta como projeto e selecione `.venv312\Scripts\python.exe`
como interpretador. Execute `main.py` e, em outra configuração, `api.py`.
O caminho dos dados é relativo aos arquivos do projeto, não ao diretório do terminal.
O dashboard funciona sem API; a comparação exige que a API esteja ativa.
Tkinter acompanha a instalação padrão do Python para Windows; em Linux, pode exigir
instalação do pacote python3-tk pelo sistema operacional.

## Dashboard

- Distance Dashboard: gráfico das referências em longitude/latitude, barras e tabela.
- Access Points & Evidence: coordenadas, notas, fontes e status.
- API Comparison: verifica os três pares e o conjunto exato de coordenadas da API.
- Reload coordinates: relê `data/locations.json` e limpa a comparação anterior.
- Export CSV + GeoJSON: grava os quatro arquivos na pasta escolhida.

O gráfico de coordenadas é uma visão esquemática sem mapa-base; não é uma captura
QGIS nem mostra rotas. As linhas são geodésicas amostradas. O dashboard não edita
o JSON automaticamente nem publica no GitHub.

## API

| Método | Endpoint | Função |
|---|---|---|
| GET | `/health` | Estado e versão dos dados |
| GET | `/locations` | Pontos, coordenadas e metadados |
| GET | `/distances` | Os três pares e os dados utilizados |
| GET | `/distance?from_id=RIO01&to_id=RIO02` | Um par conhecido |
| POST | `/distance` | Duas coordenadas fornecidas pelo usuário |
| GET | `/geojson/points` | Pontos em GeoJSON |
| GET | `/geojson/geodesics` | Geodésicas em GeoJSON |
| GET | `/docs` | Interface Swagger |

Exemplo de corpo para POST `/distance`:

```json
{
  "origin": {"latitude": -22.9670, "longitude": -43.1786},
  "destination": {"latitude": -22.9406, "longitude": -43.1985}
}
```

IDs inexistentes retornam 404; coordenadas fora dos limites, não finitas ou campos
extras no POST retornam 422. A API é local, sem autenticação e sem alteração dos dados.
Não a exponha publicamente como um serviço de produção.

## Fluxo posterior no QGIS e comparação

1. Exporte os dados no dashboard. Abra `rio_points.geojson` em EPSG:4326.
   GeoJSON usa ordem `[longitude, latitude]`.
2. Confira visualmente os três acessos sobre um mapa-base apropriado. Ajuste
   `data/locations.json` com as coordenadas finais e registre fonte/data/método
   da conferência. Incremente `dataset_version`; só altere o status após revisão.
3. Recarregue o dashboard e exporte novamente os dados. A API relê o mesmo JSON
   em cada requisição. Compare os valores novamente após qualquer alteração.
4. No QGIS, configure o elipsoide de medição como WGS 84 e as unidades em metros.
   Calcule os três pares com medição elipsoidal usando as mesmas coordenadas.
   Não calcule comprimento cartesiano em graus nem distância em EPSG:3857.
5. Registre os resultados independentes do QGIS e suas configurações. Compare-os
   com `python_distances.csv`. Tolerância numérica sugerida: 0,01 m para valores
   sem arredondamento, com coordenadas e método idênticos. Isso NÃO é precisão
   posicional. Se a tela do QGIS arredondar mais, leve esse arredondamento em conta.

Python e API compartilham o mesmo motor: concordância entre eles verifica
consistência dos dados e do transporte. A comparação QGIS é uma etapa separada,
**ainda não executada**. O post e as imagens finais vêm depois da validação.

## Testes

```powershell
.\.venv312\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv312\Scripts\python.exe -m unittest discover -s tests -v
```

Cobrem distância de referência no equador, simetria, distância nula, limites,
valores não finitos, três pares, desigualdade triangular, exportações,
validação de pedidos e consistência API/Python. A interface desktop precisa ser
aberta no Windows para conferência visual final.

## Organização

- `main.py`: janela desktop.
- `api.py`: FastAPI e execução local pelo PyCharm.
- `core.py`: cálculo e exportação compartilhados.
- `data/locations.json`: única fonte das coordenadas.
- `tests/test_project.py`: verificações automatizadas.
- `exports/`: pasta sugerida para resultados; arquivos gerados ignorados no Git.

## Referências técnicas

- https://geographiclib.sourceforge.io/html/python/examples.html
- https://geographiclib.sourceforge.io/html/python/code.html
- https://fastapi.tiangolo.com/tutorial/first-steps/
