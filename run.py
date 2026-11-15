import pandas as pd

autores = pd.read_csv("autores_55.csv")
proposicoes = pd.read_csv("proposicoes_55.csv")

autores = autores.merge(proposicoes[["id", "siglaTipo"]], left_on="idProposicao", right_on="id", suffixes=("", "_prop"))

# 1. Quantos autores por proposição, por tipo
porProposicao = autores.groupby(["idProposicao", "siglaTipo"]).size().reset_index(name="autores")
print("Média e máximo de autores por tipo:")
print(porProposicao.groupby("siglaTipo")["autores"].agg(["mean", "max"]))

# 2. Quantos deputados têm pelo menos uma coautoria
coautoradas = porProposicao[porProposicao["autores"] > 1]["idProposicao"]
deputadosComCoautoria = autores[autores["idProposicao"].isin(coautoradas)]["id"].nunique()
print("\nDeputados com pelo menos uma coautoria:", deputadosComCoautoria, "de 623")