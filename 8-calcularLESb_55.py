import pandas as pd

proposicoes = pd.read_csv("proposicoes_55.csv")
autores = pd.read_csv("autores_55.csv")
deputados = pd.read_csv("deputados_55.csv").drop_duplicates(subset="id")

estagios = ["INI", "COM", "PLE", "SEN", "LEI"]
nivel = {"INI": 0, "COM": 1, "PLE": 2, "SEN": 3, "LEI": 4}

# 1. Crédito ao primeiro signatário
primeiros = autores[autores["ordemAssinatura"] == 1][["idProposicao", "id"]]
primeiros = primeiros.drop_duplicates(subset="idProposicao")

base = primeiros.merge(proposicoes[["id", "siglaTipo", "estagio", "peso"]],
                       left_on="idProposicao", right_on="id", suffixes=("", "_prop"))
base = base.drop(columns=["id_prop"])
base["nivel"] = base["estagio"].map(nivel)

print("Proposições creditadas:", len(base))

# 2. Tabela com os 623 deputados
lesb = deputados[["id", "nome"]].copy()
N = len(lesb)
somaFracoes = 0

# 3. Para cada estágio: pontos do deputado / pontos da Câmara
for k, estagio in enumerate(estagios):
    # Cumulativo: quem chegou à LEI também conta em INI, COM, PLE e SEN
    chegaram = base[base["nivel"] >= k]
    pontos = chegaram.groupby("id")["peso"].sum()

    lesb["pts_" + estagio] = lesb["id"].map(pontos).fillna(0)
    totalCamara = lesb["pts_" + estagio].sum()

    lesb["fr_" + estagio] = lesb["pts_" + estagio] / totalCamara
    somaFracoes = somaFracoes + lesb["fr_" + estagio]

    print(estagio, "- pontos da Câmara:", int(totalCamara))

# 4. Soma das cinco frações x N/5 (média = 1)
lesb["lesb"] = (somaFracoes * N / 5).round(4)

colunas = ["id", "nome"] + ["pts_" + e for e in estagios] + ["lesb"]
lesb = lesb[colunas]
lesb.to_csv("lesb_55.csv", index=False)

# Conferências
print("\nMédia do LESb:", round(lesb["lesb"].mean(), 4), "(deve ser 1)")
print("Deputados com LESb zero:", (lesb["lesb"] == 0).sum())
print("\nDistribuição:")
print(lesb["lesb"].describe())

print("\nOs 10 mais efetivos:")
print(lesb.sort_values("lesb", ascending=False)
      [["nome", "pts_INI", "pts_LEI", "lesb"]].head(10).to_string(index=False))