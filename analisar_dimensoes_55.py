import pandas as pd

base = pd.read_csv("base_indice_55.csv")

# Variáveis que pretendemos utilizar
variaveis = base[
    [
        "lesb",
        "articulacaoLog",
        "gastoMensalProporcional"
    ]
]

print("CORRELAÇÃO DE PEARSON")
print(variaveis.corr(method="pearson").round(3))

print("\nCORRELAÇÃO DE SPEARMAN")
print(variaveis.corr(method="spearman").round(3))


# Também vamos verificar LESb x articulação sem log
print("\nLESb x articulação bruta")
print(
    base[
        ["lesb", "articulacao"]
    ].corr(method="spearman").round(3)
)