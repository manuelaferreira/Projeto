import subprocess
subprocess.check_call(['python','-m','pip','install','flask','geopy','pandas'])

from flask import Flask, jsonify, request, render_template
import csv
from geopy.distance import geodesic
import pandas as pd
import json

app = Flask(__name__)

# Carregar o CSV com as ONGs
def carregar_ongs():
    try:
        # Carregar o arquivo CSV
        df = pd.read_csv("ongs.csv")  # Certifique-se de que este arquivo contém latitude e longitude
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            raise ValueError("O arquivo ongs.csv deve conter as colunas 'latitude' e 'longitude'.")
        return df
    except Exception as e:
        print(f"Erro ao carregar ONGs: {e}")
        return pd.DataFrame()

# Carregar dados ao iniciar
df_ongs = carregar_ongs()

# Rota principal para exibir a interface
@app.route('/')
def index():
    return render_template('index.html')

# Rota para processar a localização do usuário
@app.route('/definir_localizacao', methods=['POST'])
def definir_localizacao():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"erro": "Nenhum dado enviado."}), 400

        print("Dados recebidos:", data)  # Verifique os dados recebidos
        
        latitude_usuario = data.get('latitude')
        longitude_usuario = data.get('longitude')

        if not latitude_usuario or not longitude_usuario:
            return jsonify({"erro": "Coordenadas inválidas."}), 400
        
        try:
            latitude_usuario = float(latitude_usuario)
            longitude_usuario = float(longitude_usuario)
        except ValueError:
            return jsonify({"erro": "As coordenadas devem ser números válidos."}), 400

        localizacao_usuario = (latitude_usuario, longitude_usuario)
        print(f"Localização do usuário: {localizacao_usuario}")  # Verifique a localização

        # Calcular a distância para cada ONG
        def calcular_distancia(ong):
            return geodesic(localizacao_usuario, (ong['latitude'], ong['longitude'])).kilometers

        # Adicionar coluna de distância
        df_ongs['distancia'] = df_ongs.apply(
            lambda row: calcular_distancia({'latitude': row['latitude'], 'longitude': row['longitude']}), 
            axis=1
        )
        print("Distâncias calculadas:", df_ongs['distancia'].head())  # Verifique as distâncias calculadas

        # Ordenar por distância e selecionar as 10 mais próximas
        ongs_ordenadas = df_ongs.sort_values("distancia").head(10)

        # Arredondar a distância para 2 casas decimais antes de enviar
        ongs_ordenadas['distancia'] = ongs_ordenadas['distancia'].round(2)

        # Converter o resultado para JSON
        resultado = ongs_ordenadas.to_dict(orient="records")
        return jsonify(resultado)
    
    except Exception as e:
        print(f"Erro no processamento da requisição: {e}")  # Adiciona log para depuração
        return jsonify({"erro": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

