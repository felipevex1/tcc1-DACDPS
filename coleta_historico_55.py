import requests
import pandas as pd
import time

deputados = pd.read_csv("deputados_55.csv")
ids = deputados["id"].unique()

todosEventos = []
falhas = []

for idDeputado in ids:
    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{idDeputado}/historico"

    tentativa = 1
    sucesso = False
    while tentativa <= 5:
        try:
            resposta = requests.get(url, headers={"Accept": "application/json"}, timeout=60)
            if resposta.status_code == 200:
                sucesso = True
                break
            print("Deputado", idDeputado, "- status", resposta.status_code, "- tentativa", tentativa)
        except requests.exceptions.RequestException:
            print("Deputado", idDeputado, "- erro de conexão - tentativa", tentativa)
        time.sleep(10 * tentativa)
        tentativa = tentativa + 1

    if not sucesso:
        falhas.append(idDeputado)
        continue

    todosEventos.extend(resposta.json()["dados"])
    time.sleep(0.5)

df = pd.DataFrame(todosEventos)
df = df[df["idLegislatura"] == 55]
df = df[["id", "nome", "siglaPartido", "siglaUf", "idLegislatura", "dataHora", "situacao"]]
df.to_csv("historico_bruto_55.csv", index=False)

print("Eventos:", len(df))
print("Deputados:", df["id"].nunique())
print("Falhas:", falhas)