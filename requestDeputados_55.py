import requests
import pandas as pd
import time

url = "https://dadosabertos.camara.leg.br/api/v2/deputados"
todosDeputados = []
pagina = 1
tentativa = 1

#Leg55
while True:
    try:
        resposta = requests.get(url, params={"idLegislatura": 55, "itens": 100, "pagina": pagina},
                                headers={"Accept": "application/json"}, timeout=60)
    except requests.exceptions.RequestException:
        print("Página", pagina, "- erro de conexão - tentativa", tentativa)
        time.sleep(10 * tentativa)
        tentativa = tentativa + 1
        continue

    if resposta.status_code != 200:
        print("Página", pagina, "- status", resposta.status_code, "- tentativa", tentativa)
        if tentativa == 5:
            print("API fora do ar. Tente mais tarde.")
            break
        time.sleep(10 * tentativa)
        tentativa = tentativa + 1
        continue

    tentativa = 1
    conteudo = resposta.json()

    deputadosPagina = conteudo["dados"]
    todosDeputados.extend(deputadosPagina)

    print("Página: ", pagina, "-", len(deputadosPagina), "deputados")
    if len(deputadosPagina) < 100:
        break

    pagina = pagina + 1
    time.sleep(1.5)

df = pd.DataFrame(todosDeputados)
print("Total de registros:", len(df))
print("Deputados únicos:", df["id"].nunique())

df = df.drop(columns=["uri", "uriPartido", "urlFoto", "email"])
df.to_csv("deputados_55.csv", index=False)