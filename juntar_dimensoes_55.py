import pandas as pd

# =============================================
# 1. CARREGAR OS TRÊS ARQUIVOS
# =============================================

lesb = pd.read_csv("lesb_55.csv")
articulacao = pd.read_csv("articulacao_55.csv")
custo = pd.read_csv("custo_55.csv")


# =============================================
# 2. VERIFICAR QUANTOS DEPUTADOS HÁ EM CADA BASE
# =============================================

print("Deputados no LESb:", lesb["id"].nunique())
print("Deputados na Articulação:", articulacao["id"].nunique())
print("Deputados no Custo:", custo["id"].nunique())


# =============================================
# 3. SELECIONAR SOMENTE AS COLUNAS NECESSÁRIAS
# =============================================

lesb = lesb[
    [
        "id",
        "nome",
        "lesb"
    ]
]

articulacao = articulacao[
    [
        "id",
        "totalCoautorias",
        "coautoriasInterpartidarias",
        "articulacao",
        "articulacaoLog"
    ]
]

custo = custo[
    [
        "id",
        "diasExercicio",
        "mesesExercicio",
        "gastoTotal",
        "gastoMensalProporcional",
        "gastoAnualProporcional"
    ]
]


# =============================================
# 4. JUNTAR LESb + ARTICULAÇÃO
# =============================================

base = lesb.merge(
    articulacao,
    on="id",
    how="left"
)


# =============================================
# 5. JUNTAR O CUSTO
# =============================================

base = base.merge(
    custo,
    on="id",
    how="left"
)


# =============================================
# 6. ACRESCENTAR A LEGISLATURA
# =============================================

base["legislatura"] = 55


# =============================================
# 7. ORGANIZAR AS COLUNAS
# =============================================

base = base[
    [
        "id",
        "nome",
        "legislatura",

        # Efetividade
        "lesb",

        # Articulação
        "totalCoautorias",
        "coautoriasInterpartidarias",
        "articulacao",
        "articulacaoLog",

        # Custo
        "diasExercicio",
        "mesesExercicio",
        "gastoTotal",
        "gastoMensalProporcional",
        "gastoAnualProporcional"
    ]
]


# =============================================
# 8. CONFERÊNCIAS
# =============================================

print("\nTotal de linhas:", len(base))
print("Deputados únicos:", base["id"].nunique())

print("\nValores ausentes:")
print(base.isna().sum())

print("\nPrimeiras linhas:")
print(base.head().to_string(index=False))


# =============================================
# 9. SALVAR
# =============================================

base.to_csv(
    "base_indice_55.csv",
    index=False
)

print("\nArquivo base_indice_55.csv criado.")