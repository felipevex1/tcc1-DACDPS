import pandas as pd

proposicoes = pd.read_csv("proposicoes_55.csv")
deputados = pd.read_csv("deputados_55.csv")

idsProposicoes = set(proposicoes["id"])
idsDeputados = set(deputados["id"])

todosAutores = []

for ano in [2015, 2016, 2017, 2018, 2019]:
    url = f"https://dadosabertos.camara.leg.br/arquivos/proposicoesAutores/csv/proposicoesAutores-{ano}.csv"
    autoresAno = pd.read_csv(url, sep=";", encoding="utf-8-sig", low_memory=False)

    autoresAno = autoresAno[autoresAno["idProposicao"].isin(idsProposicoes)]
    todosAutores.append(autoresAno)
    print("Ano", ano, "-", len(autoresAno), "autorias")

autores = pd.concat(todosAutores)
autores = autores.drop_duplicates(subset=["idProposicao", "idDeputadoAutor", "nomeAutor"])

print("\nTipos de autor:")
print(autores["tipoAutor"].value_counts().to_string())
print("\nValores de proponente:")
print(autores["proponente"].value_counts().to_string())

# Mantém só deputados da lista da 55ª
autores = autores[autores["idDeputadoAutor"].notna()]
autores["idDeputadoAutor"] = autores["idDeputadoAutor"].astype(int)
autores = autores[autores["idDeputadoAutor"].isin(idsDeputados)]

autores = autores[["idProposicao", "idDeputadoAutor", "nomeAutor", "ordemAssinatura", "proponente"]]
autores = autores.rename(columns={"idDeputadoAutor": "id"})

autores.to_csv("autores_55.csv", index=False)

# Conferências
primeiros = autores[autores["ordemAssinatura"] == 1]
autoresPorProposicao = autores.groupby("idProposicao").size()

print("\nTotal de autorias de deputados:", len(autores))
print("Proposições com autor deputado:", autores["idProposicao"].nunique(), "de", len(idsProposicoes))
print("Proposições com primeiro signatário deputado:", primeiros["idProposicao"].nunique())
print("Proposições com coautoria (2+ deputados):", (autoresPorProposicao > 1).sum())
print("Deputados com alguma autoria:", autores["id"].nunique())