# GIS Distance Training — Rio de Janeiro v2.2

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

## Fechamento do código — v2.1

Agora a aba **Numerical & QGIS Checks** permite:

- **Run independent check**: comparar GeographicLib com Vincenty, implementado
  separadamente com `math`, sem chamar GeographicLib ou PROJ. Os seis pares
  passam na tolerância numérica de 0,01 m.
- **Save QGIS CSV template**: gerar seis linhas com as distâncias do QGIS em branco.
- **Import QGIS measurements**: importar os valores que você mediu no QGIS.
- **Save check report**: salvar o relatório da última verificação em JSON.

Preencha apenas `qgis_distance_m` no modelo, em metros, com ponto decimal.
Não altere as colunas de identificação, versão, hash das coordenadas e método.
Confirme os mesmos pontos e a medição elipsoidal WGS 84 no QGIS. O importador
rejeita pares repetidos, faltantes ou desconhecidos, coordenadas antigas, unidades
incompatíveis e números inválidos. Valores em branco continuam PENDING; um
conjunto parcialmente preenchido fica INCOMPLETE. PASS exige os seis resultados.
Isso verifica concordância numérica, não precisão geográfica nem medição em campo.

Vincenty pode não convergir para pontos quase antípodas; nesses casos a checagem
mostra erro, sem usar silenciosamente o motor principal. Os pares curtos do Rio
foram testados com sucesso.

Atalhos Windows: `SETUP.cmd`, `RUN_DASHBOARD.cmd`, `RUN_API.cmd`,
`RUN_TESTS.cmd` e `VERIFY_API.cmd`. Os atalhos de dashboard e API preparam o
ambiente automaticamente. Para `VERIFY_API.cmd`, mantenha a API aberta em outra janela.

Também pode conferir pelo PowerShell:

```powershell
.\.venv312\Scripts\python.exe verify_project.py
.\.venv312\Scripts\python.exe verify_project.py --api-url http://127.0.0.1:8002 --output verification.json
```

O primeiro comando executa a checagem independente sem exigir API ou QGIS.
O segundo exige a API ativa. Para incluir os valores realmente medidos:

```powershell
.\.venv312\Scripts\python.exe verify_project.py --api-url http://127.0.0.1:8002 --qgis-csv completed_qgis.csv --output verification.json
```

A API também expõe `GET /validation`. A comparação com o QGIS permanece pendente
até você fornecer os valores; o código não os preenche automaticamente.
A execução completa da janela deve ser conferida no Windows. Rotas a pé e de
carro pertencem ao projeto adicional e não foram incluídas nesta versão geodésica.

## Mapa de ruas e galeria — v2.2

A aba **Distance Dashboard** agora mostra ruas e bairros do OpenStreetMap atrás
dos quatro pontos, com as seis ligações e destaque do par selecionado.
Os cálculos continuam geodésicos em WGS 84; o mapa não transforma as linhas
em rotas de ruas, trem ou bondinho. As coordenadas dos locais não foram alteradas.

- **Street basemap**: ativa/desativa o mapa-base.
- **Load street map**: carrega a área atual; o primeiro carregamento precisa de internet.
- **Open Rio in OpenStreetMap**: abre a região no navegador.
- **Open origin in OpenStreetMap**: abre o local escolhido em Origin com marcador.
- **Save chart as PNG**: salva o gráfico atual, incluindo o mapa e a atribuição.
- **All Distances**: contém a tabela com os seis pares; ela foi movida para dar espaço ao mapa.

A busca do mapa roda em segundo plano. Se não houver conexão ou o serviço
estiver indisponível, o gráfico de coordenadas continua funcionando.
O cache local é reaproveitado para a área já visualizada; não há download
de áreas para uso offline nem busca antecipada de outros níveis de zoom.
A barra do Matplotlib permite ampliar/mover a imagem já carregada; para
explorar outras regiões em detalhe, use o botão do OpenStreetMap.

Na aba **QGIS Screenshots**, clique em **Add QGIS screenshots** e selecione suas
capturas reais do QGIS. Elas serão copiadas para `assets/qgis_screenshots/` sem
apagar os arquivos originais. A lista permite trocar a imagem e **Reload gallery**
atualiza a pasta. Não incluímos imagens ilustrativas como se fossem capturas
reais. A galeria não altera o status das medições ou da revisão das posições.

Após baixar a atualização, rode `SETUP.cmd` e `RUN_DASHBOARD.cmd`. A dependência
Pillow será instalada automaticamente. A API continua na porta 8002.
