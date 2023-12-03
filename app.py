from flask import Flask, request, send_from_directory,redirect,url_for, Markup
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

@app.route("/css/<path:filename>")
def serve_css(filename):
    return send_from_directory(css_dir, filename)

@app.route("/js/<path:filename>")
def serve_js(filename):
    return send_from_directory(js_dir, filename)

@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(image_dir, filename)

# Initialize variables to store latitude and longitude
latitude = None
longitude = None

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        latitude = float(request.form["latitude"])
        longitude = float(request.form["longitude"])
        return redirect(url_for('mapa', latitude=latitude, longitude=longitude))
    else:
        user_agent = request.headers.get('User-Agent')
        if 'Mobile' in user_agent:
            return send_from_directory(os.path.dirname(__file__), "moble.html")
        else:
            return send_from_directory(os.path.dirname(__file__), "index.html")

@app.route("/mapa")
def mapa():
    latitude = request.args.get('latitude', type=float)
    longitude = request.args.get('longitude', type=float)
    # Process latitude and longitude as needed

    local=latitude, longitude
    # Separando as coordenadas do local em duas variáveis, para cálculos de ângulo
    # Separando as coordenadas do local em duas variáveis, para cálculos de ângulo
    # lat1 = latitude
    # long1 = longitude

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

    m._height = '100%'
    folium.plugins.Fullscreen().add_to(m)
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
    atenuacoes = []

    # Criando um marcador no mapa referente a localização da antena
    folium.Marker(local, popup=f"<i>Antena\n• Lat/Long: \n{local}</i>", icon=folium.Icon(color="black", icon="home")).add_to(m)


    def media_ponderada(valores, pesos):
        if len(valores) != len(pesos):
            raise ValueError("O número de valores deve ser igual ao número de pesos")

        soma_produtos = sum(x * w for x, w in zip(valores, pesos))
        soma_pesos = sum(pesos)

        if soma_pesos == 0:
            raise ValueError("A soma dos pesos não pode ser zero")

        media_ponderada = soma_produtos / soma_pesos
        return media_ponderada

    def calcular_perda_sinal(distancia, freq, h_tx, h_rx):
        # Parâmetros específicos do modelo Okumura-Hata para áreas urbanas
        a_hm = 3.2 * math.pow((11.75*(math.log10(h_rx))),2) - 4.97
        L = 69.55 + 26.16 * math.log10(freq) - 13.82 * math.log10(h_tx) - a_hm + (44.9 - 6.55 * math.log10(h_tx)) * math.log10(distancia)
        return L

    def media_ponderada_dois_pesos(valores, pesos1, pesos2):
        if len(valores) != len(pesos1) or len(valores) != len(pesos2):
            raise ValueError("O número de valores deve ser igual ao número de pesos")

        soma_produtos = sum(x * w1 * w2 for x, w1, w2 in zip(valores, pesos1, pesos2))
        soma_pesos = sum(w1 * w2 for w1, w2 in zip(pesos1, pesos2))

        if soma_pesos == 0:
            raise ValueError("A soma dos pesos não pode ser zero")

        media_ponderada = soma_produtos / soma_pesos
        return media_ponderada

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
        h_tx = 70  # em metros
        h_rx = 1.5  # em metros
        aten = calcular_perda_sinal(distancia, freq, h_tx, h_rx)
        aten1 = 20*(math.log(distancia,10)) + 20*(math.log(freq,10)) + 32.40 # Para distancia em Km e freq em MHz
        ## Recomendação ITU-R P.525-2 para cálculo de FSPL - Link: https://01189d02-b3bd-4102-9f4c-7bfdb7fd295b.usrfiles.com/ugd/01189d_91d33066b4d240509edf714048d44cc1.pdf
        ## Link: https://semfionetworks.com/blog/free-space-path-loss-diagrams/

        # Exibição dos valores de distância, direção e atenução (dB)
        # print(f'Distância entre o seu local e a TV {chave} = {distancia} km')
        # print(f'Para a TV {chave} aponte para a direção {direcao:.2f}°')
        # print(f'A atenuação da TV {chave} é de {aten:.2f} dB (FSPL) | {aten1:.2f} dB (Okumura-Hata)\n')

        # Adição da direção e distância nos vetores 'direcoes' e 'distancias', respectivamente
        direcoes.append(direcao)
        distancias.append(distancia)
        atenuacoes.append(aten)

        # Adição das informações como a distância, direção e atenução no banco de dados
        BD[chave] = f'{valor},{direcao},{freq},{erp},{distancia},{aten}'

        # Plotagem de marcadores e de retas no mapa referente à estação de TV
        folium.Marker(location=estacao, popup=f"<i>• Lat/Long: {estacao} \n• Direção: {direcao:.2f}°</i>",shadowSize=[0,0], icon=folium.Icon(color="red")).add_to(m)
        folium.Marker(location=estacao, icon=folium.DivIcon(html=f"""<div style="font-family: arial; color: blue; font-size: large">{chave}</div>""")).add_to(m)
        linha = folium.PolyLine(locations=[local,estacao], color="red")
        attr = {'fill': 'black', 'font-weight': 'bold', 'font-size': '15'}
        m.add_child(linha)
        #textline = folium.plugins.PolyLineTextPath(linha, f"Distância: {distancia:.2f} Km / Direção: {direcao:.2f}°", offset=-5, center=True, attributes= attr)
        #m.add_child(linha)
        direcao_ponderada = media_ponderada(direcoes, atenuacoes)
        direcao_ponderada2 = media_ponderada_dois_pesos(direcoes, atenuacoes, distancias)

    # Função para obter a direção de um item
    def obter_max(item):
        return float(item.split(',')[4])  # Considerando que a direção é o segundo valor na string

    # Encontrar o item com a maior direção
    item_maior_direcao = max(BD, key=lambda x: obter_max(BD[x]))
    #print(f'O item com a maior direção é: {item_maior_direcao}')

    folium.plugins.Geocoder().add_to(m)
    folium.plugins.MousePosition().add_to(m)

    # Exbição do ângulo médio entre as emissoras
    # print(f'O ângulo médio entre as emissoras é: {mean(direcoes)}°')

    # Raio do círculo em metros
    raio = max(distancias)*1000
    angulo_med = (((max(direcoes))-(min(direcoes)))/2)+min(direcoes)
    angulo_med1 = direcao_ponderada
    angulo_med2 = direcao_ponderada2
    # print('0 peso:',angulo_med)
    # print('1 peso:',direcao_ponderada)
    # print('2 peso:',direcao_ponderada2)
    folium.Marker(location=[lat1, long2],
                popup=folium.Popup('<i>The center of map</i>'),
                tooltip='Center',
                icon=folium.DivIcon(html=f"""Aponte para <b>{angulo_med:.2f}</b>°""",
                                    class_name="mapText"),
                ).add_to(m)

    # inject html into the map html
    m.get_root().html.add_child(folium.Element("""
    <style>
    .mapText {
        white-space: nowrap;
        color:red;
        font-size:large
    }
    </style>
    """))

    # get the javascript variable name of map object
    mapJsVar = m.get_name()

    # inject html into the map html
    injHtml = """
    <style>
    .mapText {
        white-space: nowrap;
        color:black;
    }
    </style>
    <script>
    window.onload = function(){
    var sizeFromZoom = function(z){return (0.25*z)+"em";}
    $('.mapText').css('font-size', sizeFromZoom({mapJsVar}.getZoom()));
    {mapJsVar}.on('zoomend', function () {
        var zoomLevel = {mapJsVar}.getZoom();
        var tooltip = $('.mapText');
        tooltip.css('font-size', sizeFromZoom(zoomLevel));
    });
    }
    </script>
    """
    m.get_root().html.add_child(folium.Element(injHtml.replace("{mapJsVar}",mapJsVar)))

    # Plotagem do semicírculo no mapa
    folium.plugins.SemiCircle(location=local, radius=raio, start_angle= (min(direcoes)), stop_angle= (max(direcoes)), fillColor='white', fillOpacity=0.0).add_to(m)
    #folium.plugins.SemiCircle(location=local, radius=raio, start_angle=angulo_med-0.01, stop_angle= angulo_med+0.01, color="#fff55b",fillColor='white', fillOpacity=0.5).add_to(m)
    #folium.plugins.SemiCircle(location=local, radius=raio, start_angle=angulo_med1-0.01, stop_angle= angulo_med1+0.01, color="#dbce00",fillColor='white', fillOpacity=0.5).add_to(m)
    folium.plugins.SemiCircle(location=local, radius=raio, start_angle=angulo_med2-0.01, stop_angle= angulo_med2+0.01, color="#65C047",fillColor='white', fillOpacity=0.5).add_to(m)

    # Cria arquivo HTML para exibir o mapa
    # map = m.save("map.html")
    # return f"Received coordinates: Latitude {latitude}, Longitude {longitude}"
    # map_html = m._repr_html_()
    html_str = m.get_root().render()
    return html_str
    # return m._repr_html_()


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=port)
