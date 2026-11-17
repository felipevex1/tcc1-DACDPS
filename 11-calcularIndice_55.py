import pandas as pd
import numpy as np


MESES_MINIMOS = 6   # tempo mínimo de exercício para entrar na análise

base = pd.read_csv("base_indice_55.csv")


# =============================================
# 1. ELEGIBILIDADE
# =============================================

base["elegivel"] = base["mesesExercicio"] >= MESES_MINIMOS

print("Deputados elegíveis:", base["elegivel"].sum(), "de", len(base))
print("Fora da análise (menos de", MESES_MINIMOS, "meses):", (~base["elegivel"]).sum())

indice = base[base["elegivel"]].copy()


# =============================================
# 2. LOG NO LESb (a articulação já está em log)
# =============================================

indice["lesbLog"] = np.log1p(indice["lesb"])


# =============================================
# 3. NORMALIZAÇÃO MIN-MAX (0 a 1)
# =============================================

def minmax(serie):
    return (serie - serie.min()) / (serie.max() - serie.min())

indice["lesbNorm"] = minmax(indice["lesbLog"])
indice["articulacaoNorm"] = minmax(indice["articulacaoLog"])


# =============================================
# 4. ENTREGA (50/50)
# =============================================

indice["entrega"] = 0.5 * indice["lesbNorm"] + 0.5 * indice["articulacaoNorm"]


# =============================================
# 5. RAZÃO ENTREGA / GASTO (apenas para consulta)
# =============================================

indice["eficienciaRazao"] = indice["entrega"] / (indice["gastoMensalProporcional"] / 10000)


# =============================================
# 6. TESTE DE SENSIBILIDADE DOS PESOS
# =============================================

entrega70_30 = 0.7 * indice["lesbNorm"] + 0.3 * indice["articulacaoNorm"]
entrega30_70 = 0.3 * indice["lesbNorm"] + 0.7 * indice["articulacaoNorm"]

print("\nSensibilidade da entrega (Spearman com o 50/50):")
print("70/30:", round(indice["entrega"].corr(entrega70_30, method="spearman"), 3))
print("30/70:", round(indice["entrega"].corr(entrega30_70, method="spearman"), 3))


# =============================================
# 7. QUADRANTES PELA MEDIANA
# =============================================

medEntrega = indice["entrega"].median()
medGasto = indice["gastoMensalProporcional"].median()

print("\nMediana da entrega:", round(medEntrega, 4))
print("Mediana do gasto mensal: R$", round(medGasto, 2))

def quadrante(linha):
    entregaAlta = linha["entrega"] >= medEntrega
    gastoBaixo = linha["gastoMensalProporcional"] < medGasto

    if entregaAlta and gastoBaixo:
        return "Alta entrega, baixo custo"
    if entregaAlta:
        return "Alta entrega, alto custo"
    if gastoBaixo:
        return "Baixa entrega, baixo custo"
    return "Baixa entrega, alto custo"

indice["quadrante"] = indice.apply(quadrante, axis=1)

print("\nQuadrantes:")
print(indice["quadrante"].value_counts().to_string())


# =============================================
# 8. CAMADAS DE PARETO
# (só para quem teve alguma entrega)
# =============================================

comEntrega = indice[indice["entrega"] > 0].copy()
restantes = comEntrega.copy()
comEntrega["camada"] = 0
camada = 1

while len(restantes) > 0:
    naCamada = []

    for i, linha in restantes.iterrows():
        # Existe alguém que entrega mais E gasta menos?
        dominantes = restantes[
            (restantes["entrega"] > linha["entrega"]) &
            (restantes["gastoMensalProporcional"] < linha["gastoMensalProporcional"])
        ]
        if len(dominantes) == 0:
            naCamada.append(i)

    comEntrega.loc[naCamada, "camada"] = camada
    restantes = restantes.drop(naCamada)
    camada = camada + 1

indice = indice.merge(comEntrega[["id", "camada"]], on="id", how="left")

print("\nDeputados sem entrega (fora das camadas):", indice["camada"].isna().sum())
print("Total de camadas:", int(indice["camada"].max()))

print("\nCamada 1 (fronteira de eficiência):")
print(indice[indice["camada"] == 1].sort_values("gastoMensalProporcional")
      [["nome", "lesb", "coautoriasInterpartidarias", "gastoMensalProporcional", "entrega"]]
      .round(3).to_string(index=False))

print("\nDeputados por camada (primeiras 10):")
print(indice["camada"].value_counts().sort_index().head(10).to_string())


# =============================================
# 9. SALVAR (todos os 623, não elegíveis sem valores)
# =============================================

colunas = ["id", "lesbLog", "lesbNorm", "articulacaoNorm", "entrega",
           "eficienciaRazao", "quadrante", "camada"]

resultado = base.merge(indice[colunas], on="id", how="left")
resultado.to_csv("indice_55.csv", index=False)

print("\nArquivo indice_55.csv criado com", len(resultado), "deputados.")