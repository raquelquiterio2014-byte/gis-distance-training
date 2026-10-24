# GIS Training — Python Desktop V1

Treinamento paralelo e independente do projeto oficial ERA Energy.
Interface em português para Windows / PyCharm; Python 3.12 recomendado.

## Iniciar no PyCharm

1. Extraia o ZIP inteiro. Não execute arquivos dentro do ZIP.
2. PyCharm → File → Open → escolha a pasta GIS_Training_Desktop.
3. Selecione/crie um ambiente virtual com Python 3.12.
4. Abra o Terminal do PyCharm e execute:

   python -m pip install -r requirements.txt

5. Clique com o botão direito em main.py → Run 'main'.

Alternativa no PowerShell, dentro da pasta extraída:

   py -3.12 -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe main.py

A instalação das dependências requer internet. Depois, os dados e mapas incluídos funcionam offline.
Tkinter vem no instalador padrão do Python para Windows (opção Tcl/Tk).
Não é necessário instalar QGIS, GeoPandas ou um servidor web.

## Primeiro exercício

O programa abre com as 299 regiões incluídas e o par FR10 / FRF3 selecionado.
Clique em Calcular e mostrar no mapa. Resultado esperado: 267,492772 km.
O painel mostra coordenadas, distância e diferença para o resultado do QGIS.
Use a barra sob o mapa para mover, ampliar ou salvar a figura.
A aba Imagens dos mapas inclui duas imagens reais renderizadas a partir do NUTS.
Não são fotos de satélite: são mapas cartográficos dos polígonos oficiais.

Troque os campos de origem/destino para testar outro par. A comparação com QGIS
só é apresentada para FR10–FRF3. Outros pares exigem sua própria referência QGIS.
EPSG:3035 é escolhido para este treinamento europeu. Não aplique este método
sem adaptar a projeção aos dados dos EUA ou de outras áreas do mundo.

## Exportar

- JSON: relatório com as coordenadas e método do cálculo.
- GeoJSON: dois pontos e uma linha ligando os extremos, para abrir no QGIS.
- PNG: imagem do mapa que estiver na tela.

A linha GeoJSON tem somente dois vértices. O mapa da interface desenha a ligação
com pontos intermediários geodésicos. Em QGIS, meça a linha com elipsoide WGS 84.

## Carregar seus dados

Aceita GeoJSON FeatureCollection com polígonos válidos, NUTS_ID único e coordenadas
EPSG:4326 / CRS84. Sem declaração de CRS, segue a convenção GeoJSON WGS84.
GeoPackage (.gpkg) não é aceito nesta versão: exporte para GeoJSON WGS84 no QGIS.
Arquivos inválidos são rejeitados com uma mensagem. O programa não repara
geometrias silenciosamente e não modifica o arquivo de entrada.

## Método e limites

Polígonos → EPSG:3035 → centroides → EPSG:4326 → PyProj Geod.inv, WGS84.
A distância é entre centroides regionais; não é Paris–Vignot nem rota rodoviária.
Um centroide pode ficar fora de um polígono. A generalização cartográfica e a
projeção usada influenciam sua posição. Casas decimais não indicam precisão física.
A tolerância de 1 metro é um critério de concordância numérica com o QGIS, não
uma declaração de precisão do banco. A comparação não é validação de campo.

## Organização

main.py: interface Tkinter e mapas Matplotlib.
core.py: importação, validação, centroides, distância e exportação reutilizáveis.
data/: GeoJSON oficial, sem alteração de atributos.
assets/: imagens de mapas criadas com os dados incluídos.
test_core.py: testes de cálculo e validação. Execute python -m unittest -v.

FastAPI ficará para a próxima etapa e poderá importar core.py.
