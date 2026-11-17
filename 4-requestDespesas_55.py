import pandas as pd

anos = [2015, 2016, 2017, 2018, 2019]
todasDespesas = []

for ano in anos:
    url = f"http://www.camara.leg.br/cotas/Ano-{ano}.csv.zip"
    despesasAno = pd.read_csv(url, sep=";", compression="zip", encoding="utf-8-sig", low_memory=False)

    despesasAno = despesasAno[despesasAno["ideCadastro"].notna()]
    despesasAno = despesasAno[despesasAno["codLegislatura"] == 55]

    despesasAno = despesasAno[["ideCadastro", "txNomeParlamentar", "numAno", "numMes", "vlrLiquido"]]
    todasDespesas.append(despesasAno)

    print("Ano", ano, "-", len(despesasAno), "despesas da 55ª")

despesas = pd.concat(todasDespesas)
despesas["ideCadastro"] = despesas["ideCadastro"].astype(int)
despesas = despesas.rename(columns={"ideCadastro": "id"})

# Manter só os deputados da lista oficial da 55ª   <-- NOVO
deputados = pd.read_csv("deputados_55.csv")
idsApi = set(deputados["id"])
despesas = despesas[despesas["id"].isin(idsApi)]

print("Total de despesas:", len(despesas))
print("Deputados com despesas:", despesas["id"].nunique())

# Gasto por deputado e por mês
gastoMensal = despesas.groupby(["id", "numAno", "numMes"])["vlrLiquido"].sum().reset_index()

gastoMensal.to_csv("despesas_55.csv", index=False)
print("Linhas no arquivo final:", len(gastoMensal))

