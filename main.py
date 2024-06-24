from flask import Flask, render_template, send_file, url_for, request
import geopandas as gpd
import folium
import os
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

@app.route('/')
def homepage():
    print("Acessou a página inicial")
    return render_template('home.html')

@app.route('/processar_codigo', methods=['POST'])
def processar_codigo():
    cod_imovel_input = request.form['cod_imovel']

    goias = gpd.read_file('./AREA_imovel/AREA_IMOVEL_1.shp')
    goias = goias.to_crs(epsg=4326)
    goias_selecionado = goias[['municipio', 'geometry', 'cod_imovel']]

    imovel_filtrado = goias_selecionado[goias_selecionado['cod_imovel'] == cod_imovel_input]

    if imovel_filtrado.empty:
        return render_template('home.html', erro=f"O imóvel com o código '{cod_imovel_input}' não foi encontrado.")
    else:
        imovel_filtrado_utm = imovel_filtrado.to_crs(epsg=32722)
        nome_municipio = imovel_filtrado.iloc[0]['municipio']
        centroide_utm = imovel_filtrado_utm.geometry.centroid.iloc[0]
        centroide_wgs84 = gpd.GeoSeries([centroide_utm], crs="EPSG:32722").to_crs(epsg=4326).iloc[0]
        center = [centroide_wgs84.y, centroide_wgs84.x]

        mapa = folium.Map(location=center, zoom_start=15, tiles='OpenStreetMap')
        folium.GeoJson(imovel_filtrado).add_to(mapa)
        folium.Marker(
            location=center,
            popup=f"Código do Imóvel: {cod_imovel_input}<br>Município: {nome_municipio}",
            tooltip=cod_imovel_input,
            icon=folium.Icon(color='green', icon='info-sign')
        ).add_to(mapa)
        mapa.add_child(folium.LatLngPopup())

        mapa_html = mapa._repr_html_()

        return render_template('mapa.html', mapa_html=mapa_html, cod_imovel=cod_imovel_input)
    
def gerar_mapa(cod_imovel):
    goias = gpd.read_file('./AREA_imovel/AREA_IMOVEL_1.shp')
    goias = goias.to_crs(epsg=4326)
    imovel_filtrado = goias[goias['cod_imovel'] == cod_imovel]

    if imovel_filtrado.empty:
        return None

    # Converte para UTM para desenho preciso
    imovel_filtrado = imovel_filtrado.to_crs(epsg=32722)
    
    # Define tamanho da imagem e cor de fundo
    width, height = 800, 600
    bg_color = (255, 255, 255)  # Branco
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # Desenha o polígono
    for geom in imovel_filtrado.geometry:
        if geom.type == 'Polygon':
            x, y = zip(*list(geom.exterior.coords))
            x = [int((xi - min(x)) / (max(x) - min(x)) * width) for xi in x]
            y = [int((yi - min(y)) / (max(y) - min(y)) * height) for yi in y]
            coords = list(zip(x, y))
            draw.polygon(coords, outline="red")

    # Adiciona texto ao mapa
    font_path = "arial.ttf"
    font_size = 30
    font = ImageFont.truetype(font_path, font_size)
    text = f"Mapa do Imóvel: {cod_imovel}"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (width - text_width) / 2
    text_y = height - text_height - 10
    draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0))

    # Caminho para salvar a imagem gerada
    filepath = os.path.join("static", "img", "mapa_imovel.png")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    image.save(filepath)
    return filepath

@app.route('/download_map_image/<cod_imovel>')
def download_map_image(cod_imovel):
    filepath = gerar_mapa(cod_imovel)
    if filepath:
        return send_file(filepath, as_attachment=True)
    else:
        return "Imóvel não encontrado.", 404

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/contatos')
def contatos():
    return render_template('contatos.html')

@app.route('/codigos')
def codigos():
    return render_template('codigos.html')

if __name__ == '__main__':
    app.run(debug=True)
