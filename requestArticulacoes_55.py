import pandas as pd
import numpy as np

autores = pd.read_csv("autores_55.csv")
proposicoes = pd.read_csv("proposicoes_55.csv")
historico = pd.read_csv("historico_55.csv")
deputados = pd.read_csv("deputados_55.csv").drop_duplicates(subset="id")

# Renomeações dentro da 55ª: PMDB e MDB são o mesmo partido
renomeacoes = {"PTN": "PODE", "PTdoB": "AVANTE", "PEN": "PATRI", "PMDB": "MDB",
               "PSDC": "DC", "SD": "SOLIDARIEDADE"}
historico["partido"] = historico["siglaPartido"].replace(renomeacoes)


# Partido do deputado em uma data
def partidoNaData(idDeputado, data):
    periodos = historico[historico["id"] == idDeputado]

    noPeriodo = periodos[(periodos["dataInicio"] <= data) & (periodos["dataFim"] >= data)]
    if len(noPeriodo) > 0:
        return noPeriodo["partido"].iloc[0]

    # Data fora dos períodos em exercício: usa o último período iniciado antes dela
    anteriores = periodos[periodos["dataInicio"] <= data]
    if len(anteriores) > 0:
        return anteriores.sort_values("dataInicio")["partido"].iloc[-1]

    return periodos.sort_values("dataInicio")["partido"].iloc[0]


# 1. Junta autores com tipo e data da proposição
autores = autores.merge(proposicoes[["id", "siglaTipo", "dataApresentacao"]],
                        left_on="idProposicao", right_on="id", suffixes=("", "_prop"))
autores = autores.drop(columns=["id_prop"])

# 2. PECs ficam fora da articulação
autores = autores[autores["siglaTipo"] != "PEC"]

# 3. Mantém só proposições com 2 ou mais deputados
qtdAutores = autores.groupby("idProposicao")["id"].transform("count")
coautorias = autores[qtdAutores > 1].copy()

# 4. Partido de cada autor na data da proposição
coautorias["data"] = coautorias["dataApresentacao"].str[:10]
coautorias["partido"] = coautorias.apply(lambda linha: partidoNaData(linha["id"], linha["data"]), axis=1)

# 5. Para cada autor: havia alguém de outro partido na mesma proposição?
partidosDaProposicao = coautorias.groupby("idProposicao")["partido"].apply(list)

def ehInterpartidaria(linha):
    if linha["partido"] == "S.PART.":
        return None   # deputado sem partido na data: não entra na conta
    outros = list(partidosDaProposicao[linha["idProposicao"]])
    outros.remove(linha["partido"])
    for partido in outros:
        if partido != "S.PART." and partido != linha["partido"]:
            return 1
    return 0

coautorias["interpartidaria"] = coautorias.apply(ehInterpartidaria, axis=1)
coautorias = coautorias[coautorias["interpartidaria"].notna()]

# 6. Resultado por deputado
totalCoautorias = coautorias.groupby("id")["idProposicao"].nunique()
interpartidarias = coautorias[coautorias["interpartidaria"] == 1].groupby("id")["idProposicao"].nunique()

# 7. Inclui os 623 deputados (quem não tem coautoria fica com zero)
articulacao = deputados[["id", "nome"]].copy()
articulacao["totalCoautorias"] = articulacao["id"].map(totalCoautorias).fillna(0).astype(int)
articulacao["coautoriasInterpartidarias"] = articulacao["id"].map(interpartidarias).fillna(0).astype(int)

# Variável de articulação: contagem de coautorias interpartidárias
articulacao["articulacao"] = articulacao["coautoriasInterpartidarias"]

# Versão em log(1 + x), usada antes da normalização no índice
articulacao["articulacaoLog"] = np.log1p(articulacao["articulacao"]).round(4)

# Proporção: só como informação de apoio (não entra no índice)
articulacao["proporcaoInterpartidaria"] = (
    articulacao["coautoriasInterpartidarias"] / articulacao["totalCoautorias"].replace(0, np.nan) * 100
).round(2)

articulacao.to_csv("articulacao_55.csv", index=False)

# Conferências
print("Proposições com coautoria (sem PEC):", coautorias["idProposicao"].nunique())
print("Deputados com coautoria:", (articulacao["totalCoautorias"] > 0).sum())
print("Deputados com articulação zero:", (articulacao["articulacao"] == 0).sum())

print("\nArticulação (contagem):")
print(articulacao["articulacao"].describe())

print("\nArticulação (log):")
print(articulacao["articulacaoLog"].describe())

print("\nOs 10 mais articulados:")
print(articulacao.sort_values("articulacao", ascending=False)
      [["nome", "totalCoautorias", "coautoriasInterpartidarias", "articulacaoLog"]]
      .head(10).to_string(index=False))