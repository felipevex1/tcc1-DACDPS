import requests
import pandas as pd
import time

deputados = pd.read_csv("deputados_55.csv")
ids = deputados["id"].unique()

INICIO_LEG = pd.Timestamp("2015-02-01 00:00")
FIM_LEG = pd.Timestamp("2019-01-31 23:59")

partidosRenomeados = {"PMDB": "MDB",
    "PTdoB": "AVANTE",
    "PTN": "PODE",
    "PEN": "PATRI",
    "SD": "SOLIDARIEDADE",
    "PSDC": "DC",}

periodos = []
falhas = []
contador = 0

for idDeputado in ids:
    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{idDeputado}/historico"

    # 1. Requisição com até 5 tentativas
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

    historico = pd.DataFrame(resposta.json()["dados"])

    # 2. Limpeza
    historico = historico[historico["idLegislatura"] == 55]
    historico = historico[historico["situacao"].notna()]
    historico["situacao"] = historico["situacao"].str.upper().str.strip()
    historico["siglaPartido"] = historico["siglaPartido"].str.replace("*", "", regex=False).str.strip()   # NOVO: remove os asteriscos (PP** vira PP)
    historico["siglaPartido"] = historico["siglaPartido"].replace(partidosRenomeados)
    historico = historico.drop_duplicates(subset=["dataHora", "siglaPartido", "situacao"])

    if historico.empty:
        falhas.append(idDeputado)
        continue

    # 3. Cada evento dura até o começo do próximo
    historico["inicio"] = pd.to_datetime(historico["dataHora"])
    historico = historico.sort_values("inicio")
    historico["fim"] = historico["inicio"].shift(-1).fillna(FIM_LEG)
    historico["inicio"] = historico["inicio"].clip(lower=INICIO_LEG)
    historico["fim"] = historico["fim"].clip(upper=FIM_LEG)

    # 4. Conta só os dias em exercício
    historico["dias"] = (historico["fim"] - historico["inicio"]).dt.total_seconds() / 86400
    historico["diasExercicio"] = historico["dias"].where(historico["situacao"] == "EXERCÍCIO", 0)

    # 5. Junta eventos seguidos do mesmo partido
    historico["bloco"] = (historico["siglaPartido"] != historico["siglaPartido"].shift()).cumsum()

    for bloco, grupo in historico.groupby("bloco"):
        diasExercicio = grupo["diasExercicio"].sum()
        if diasExercicio > 0:
            periodos.append({
                "id": idDeputado,
                "nome": grupo["nome"].iloc[0],
                "siglaPartido": grupo["siglaPartido"].iloc[0],
                "siglaUf": grupo["siglaUf"].iloc[0],
                "idLegislatura": 55,
                "dataInicio": grupo["inicio"].min().strftime("%Y-%m-%d"),
                "dataFim": grupo["fim"].max().strftime("%Y-%m-%d"),
                "diasExercicio": round(diasExercicio),
            })

    # 6. Salva o progresso a cada 50 deputados
    contador = contador + 1
    if contador % 50 == 0:
        pd.DataFrame(periodos).to_csv("historico_55_parcial.csv", index=False)
        print("Progresso:", contador, "deputados")

    time.sleep(0.5)

df = pd.DataFrame(periodos)
df.to_csv("historico_55.csv", index=False)

print("Total de períodos:", len(df))
print("Deputados com períodos:", df["id"].nunique())
print("Deputados que trocaram de partido:", (df.groupby("id").size() > 1).sum())
print("Falhas:", falhas)