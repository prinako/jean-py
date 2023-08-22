from flask import Flask, request, send_from_directory
import os
import subprocess
import json

import sys
import math # Biblioteca para fazer os cálculos
import haversine as hs # Biblioteca para fazer o cálculo da Distância de Haversine. # Link: https://towardsdatascience.com/calculating-distance-between-two-geolocations-in-python-26ad3afe287b
from statistics import mean # Biblioteca para fazer o cálculo da média dos ângulos.
import folium # Biblioteca para plotar objetos e informações em um mapa # Link: https://python-visualization.github.io/folium/index.html
from folium import plugins

app = Flask(__name__)

# Set the port (either from the environment variable or 3000)
port = int(os.environ.get("PORT", 3000))

# Define the directory paths for static files
image_dir = os.path.join(os.path.dirname(__file__), "images")
css_dir = os.path.join(os.path.dirname(__file__), "css")
js_dir = os.path.join(os.path.dirname(__file__), "js")

# Initialize variables to store latitude and longitude
latitude = None
longitude = None

@app.route("/")
def index():
    return send_from_directory(os.path.dirname(__file__), "index.html")

@app.route("/", methods=["POST"])
def run_python_script():
    global latitude, longitude

    data = request.json
    print(data)
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    result = getMap(latitude,longitude)
    print(result)
    # script_path = os.path.join(os.path.dirname(__file__), "python", "index.py")
    # result = subprocess.run(["python", script_path, latitude, longitude], capture_output=True, text=True)

    if result:
        return result
    else:
        return f"Error: {result.stderr}", 500

@app.route("/sobre")
def sobre():
    return send_from_directory(os.path.dirname(__file__), "sobre.html")

@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory(css_dir, filename)

@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory(js_dir, filename)

@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(image_dir, filename)

def getMap(lat, long):

    local=float(lat), float(long)
    # Separando as coordenadas do local em duas variáveis, para cálculos de ângulo
    lat1 = local[0]
    long1 = local[1]

    # Exibição das coordenadas inseridas
    # print(f'\nA sua localização é: {lat1} / {long1}')

    """
    # Solicitando ao usuário as coordenadas do local
    lat1 = float(input("Digite a sua latitude: "))
    long1 = float(input("Digite a sua longitude: "))
    # Exibindo as coordenadas informadas
    print(f'A sua localização é: {lat1} / {long1}')
    # Armazenando vetor 'local' para calcular posteriormente a distância
    local = [lat1,long1]
    """
    # Criando um mapa base de acordo com as coordenadas inseridas
    m = folium.Map(local,zoom_start = 12)

    # Trecho do banco de dados da ANATEL, contendo as coordenadas das 4 principais estações de TV de Belém
    # Link: http://sistemas.anatel.gov.br/se/public/view/b/srd.php
    # Exemplo de dado armazenado: {"Nome da emissora":"lat,long,pot,ganho"}
    BD = {"Liberal":"-1.453611111111,-48.489444444444,515,61.79",
        "SBT":"-1.4566666666667,-48.490277777778,545,33",
        "Record":"-1.4502777777777,-48.484722222222,521,8",
        "RBA":"-1.4319444444443,-48.455,599,80",
        "Cultura":"-1.442556,-48.463139,635,80"
        }

    # Criando vetor 'direcoes' para posteriormente fazer a média angular
    direcoes = []
    distancias = []

    # Criando um marcador no mapa referente a localização da antena
    folium.Marker(local, popup=f"<i>Antena\n• Lat/Long: \n{local}</i>", icon=folium.Icon(color="black", icon="home")).add_to(m)

    for chave, valor in BD.items():

        # Acessando o banco de dados com as coordenadas das emissoras de TV
        lat2,long2,freq,erp = valor.split(",")

        # Transformando de string para float e armazenando as coordenadas em diferentes variáveis
        lat2 = float(lat2)
        long2 = float(long2)
        freq = float(freq)
        erp = float(erp)

        # Armazenando em um vetor 'estacao' para calcular posteriormente a distância
        estacao = [lat2,long2]

        # Calculando a distância entre a localização informada e a estação de TV
        distancia = hs.haversine(local,estacao)

        # Exibindo distância entre a localização informada e a estação de TV
        # print(f'\nCoordenadas da TV {chave} = {lat2:.2f} / {long2:.2f}')

        # Calculando a direção
        x = math.sin(math.radians(long2) - math.radians(long1)) * math.cos(math.radians(lat2))
        y = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(long2) - math.radians(long1))
        direcao = math.atan2(x,y)

        # Transformando a direção para um valor positivo
        direcao = math.degrees(direcao)
        direcao = (direcao + 360) % 360

        # Calculando a atenuação por perda por caminho em espaço livre (Free-Space Path Loss - FSPL)
        aten = 20*(math.log(distancia,10)) + 20*(math.log(freq,10)) + 32.40 # Para distancia em Km e freq em MHz
        ## Recomendação ITU-R P.525-2 para cálculo de FSPL - Link: https://01189d02-b3bd-4102-9f4c-7bfdb7fd295b.usrfiles.com/ugd/01189d_91d33066b4d240509edf714048d44cc1.pdf
        ## Link: https://semfionetworks.com/blog/free-space-path-loss-diagrams/

        # Exibição dos valores de distância, direção e atenução (dB)
        # print(f'Distância entre o seu local e a TV {chave} = {distancia} km')
        # print(f'Para a TV {chave} aponte para a direção {direcao:.2f}°')
        # print(f'A atenuação da TV {chave} é de {aten:.2f} dB\n')

        # Adição da direção e distância nos vetores 'direcoes' e 'distancias', respectivamente
        direcoes.append(direcao)
        distancias.append(distancia)

        # Adição das informações como a distância, direção e atenução no banco de dados
        BD[chave] = f'{valor},{direcao},{freq},{erp},{distancia},{aten}'

        # Inserção de cores de acordo com a distância
        # Plotagem de marcadores e de retas no mapa referente à estação de TV
        folium.Marker(location=estacao, popup=f"<i>• Lat/Long: {estacao} \n• Direção: {direcao:.2f}°</i>",shadowSize=[0,0], icon=folium.Icon(color="red")).add_to(m)
        folium.Marker(location=estacao, icon=folium.DivIcon(html=f"""<div style="font-family: arial; color: blue; font-size: large">{chave}</div>""")).add_to(m)
        linha = folium.PolyLine(locations=[local,estacao], color="red")
        attr = {'fill': 'black', 'font-weight': 'bold', 'font-size': '15'}
        textline = folium.plugins.PolyLineTextPath(linha, f"Distância: {distancia:.2f} Km / Direção: {direcao:.2f}°", offset=-5, center=True, attributes= attr)
        m.add_child(linha)
        m.add_child(textline)

    folium.TileLayer('Stamen Terrain').add_to(m)
    folium.TileLayer('Stamen Toner').add_to(m)
    folium.TileLayer('Stamen Water Color').add_to(m)
    folium.TileLayer('cartodbpositron').add_to(m)
    folium.TileLayer('cartodbdark_matter').add_to(m)
    folium.LayerControl().add_to(m)

    folium.plugins.Geocoder().add_to(m)
    folium.plugins.MousePosition().add_to(m)

    # Exbição do ângulo médio entre as emissoras
    # print(f'O ângulo médio entre as emissoras é: {mean(direcoes)}°')

    # Plotagem do semicírculo no mapa
    folium.plugins.SemiCircle(location=local, radius= max(distancias)*1000, start_angle= (min(direcoes)), stop_angle= (max(direcoes)), fillColor='white', fillOpacity=0.5).add_to(m)

    # Cria arquivo HTML para exibir o mapa
    return m._repr_html_()
    m.save("maps.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
