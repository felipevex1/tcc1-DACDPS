import pandas as pd

despesas = pd.read_csv("despesas_55.csv")
historico = pd.read_csv("historico_55.csv")
deputados = pd.read_csv("deputados_55.csv").drop_duplicates(subset="id")

# -----------------------------------------------------
# 1. GASTO TOTAL DE CADA DEPUTADO
# -----------------------------------------------------

gastos = despesas.groupby("id")["vlrLiquido"].sum().reset_index()

gastos = gastos.rename(columns={
    "vlrLiquido": "gastoTotal"
})

# -----------------------------------------------------
# 2. DIAS EM EXERCÍCIO
# -----------------------------------------------------

dias = historico.groupby("id")["diasExercicio"].sum().reset_index()

# Evita eventual dupla contagem ou fração
dias["diasExercicio"] = dias["diasExercicio"].round()

# -----------------------------------------------------
# 3. JUNTA OS DADOS
# -----------------------------------------------------

custo = deputados[["id", "nome"]].merge(
    gastos,
    on="id",
    how="left"
)

custo = custo.merge(
    dias,
    on="id",
    how="left"
)

custo["gastoTotal"] = custo["gastoTotal"].fillna(0)
custo["diasExercicio"] = custo["diasExercicio"].fillna(0)

# -----------------------------------------------------
# 4. CONVERTE DIAS EM MESES EQUIVALENTES
# -----------------------------------------------------

# Média aproximada de dias por mês:
# 365,25 / 12 = 30,4375
custo["mesesExercicio"] = custo["diasExercicio"] / 30.4375

# -----------------------------------------------------
# 5. GASTO PROPORCIONAL AO TEMPO
# -----------------------------------------------------

custo["gastoMensalProporcional"] = (
    custo["gastoTotal"] / custo["mesesExercicio"]
)

# Caso algum deputado tenha 0 dias em exercício,
# evita divisão por zero
custo.loc[
    custo["diasExercicio"] == 0,
    "gastoMensalProporcional"
] = None

# -----------------------------------------------------
# 6. GASTO ANUAL EQUIVALENTE
# Opcional, mas útil para interpretação
# -----------------------------------------------------

custo["gastoAnualProporcional"] = (
    custo["gastoMensalProporcional"] * 12
)

# -----------------------------------------------------
# 7. ARREDONDAMENTO
# -----------------------------------------------------

custo["gastoTotal"] = custo["gastoTotal"].round(2)
custo["mesesExercicio"] = custo["mesesExercicio"].round(2)
custo["gastoMensalProporcional"] = custo["gastoMensalProporcional"].round(2)
custo["gastoAnualProporcional"] = custo["gastoAnualProporcional"].round(2)

# -----------------------------------------------------
# 8. SALVA
# -----------------------------------------------------

custo.to_csv("custo_55.csv", index=False)

# -----------------------------------------------------
# 9. CONFERÊNCIAS
# -----------------------------------------------------

print("Deputados:", len(custo))

print("\nDias em exercício:")
print(custo["diasExercicio"].describe())

print("\nGasto total:")
print(custo["gastoTotal"].describe())

print("\nGasto mensal proporcional:")
print(custo["gastoMensalProporcional"].describe())

print("\nMenores gastos mensais:")
print(
    custo.sort_values("gastoMensalProporcional")
    [["nome", "diasExercicio", "mesesExercicio",
      "gastoTotal", "gastoMensalProporcional"]]
    .head(10)
    .to_string(index=False)
)

print("\nMaiores gastos mensais:")
print(
    custo.sort_values(
        "gastoMensalProporcional",
        ascending=False
    )
    [["nome", "diasExercicio", "mesesExercicio",
      "gastoTotal", "gastoMensalProporcional"]]
    .head(10)
    .to_string(index=False)
)