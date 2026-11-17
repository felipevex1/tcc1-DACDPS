import pandas as pd

# =============================================
# 1. CARREGAR OS ARQUIVOS
# =============================================

deputados = pd.read_csv("deputados_55.csv")
historico = pd.read_csv("historico_55.csv")
despesas = pd.read_csv("despesas_55.csv")

# Evita duplicação na tabela de deputados
deputados = deputados.drop_duplicates(subset="id")

# Deputados que queremos investigar
nomesInvestigar = [
    "ANDRÉ AMARAL",
    "WALTER IHOSHI",
    "LAURA CARNEIRO",
    "WADIH DAMOUS",
    "JULIÃO AMIN",
    "JHONATAN DE JESUS"
]

# =============================================
# 2. PROCURAR OS DEPUTADOS PELO NOME
# =============================================

investigados = deputados[
    deputados["nome"].str.upper().isin(nomesInvestigar)
]

print("\nDeputados encontrados:")
print(investigados[["id", "nome"]].to_string(index=False))


# =============================================
# 3. ANALISAR UM DEPUTADO POR VEZ
# =============================================

for _, deputado in investigados.iterrows():

    idDeputado = deputado["id"]
    nome = deputado["nome"]

    print("\n")
    print("=" * 70)
    print(nome, "-", idDeputado)
    print("=" * 70)

    # -----------------------------------------
    # HISTÓRICO
    # -----------------------------------------

    historicoDeputado = historico[
        historico["id"] == idDeputado
    ].copy()

    print("\nHISTÓRICO:")
    print(
        historicoDeputado[
            [
                "siglaPartido",
                "dataInicio",
                "dataFim",
                "diasExercicio"
            ]
        ].to_string(index=False)
    )

    diasExercicio = historicoDeputado["diasExercicio"].sum()

    print("\nTotal de dias em exercício:", diasExercicio)

    # -----------------------------------------
    # DESPESAS
    # -----------------------------------------

    despesasDeputado = despesas[
        despesas["id"] == idDeputado
    ].copy()

    despesasDeputado = despesasDeputado.sort_values(
        ["numAno", "numMes"]
    )

    print("\nDESPESAS MENSAIS:")
    print(
        despesasDeputado[
            [
                "numAno",
                "numMes",
                "vlrLiquido"
            ]
        ].to_string(index=False)
    )

    gastoTotal = despesasDeputado["vlrLiquido"].sum()

    print("\nGasto total: R$", round(gastoTotal, 2))

    # -----------------------------------------
    # PERÍODO DAS DESPESAS
    # -----------------------------------------

    if len(despesasDeputado) > 0:

        primeiroAno = despesasDeputado.iloc[0]["numAno"]
        primeiroMes = despesasDeputado.iloc[0]["numMes"]

        ultimoAno = despesasDeputado.iloc[-1]["numAno"]
        ultimoMes = despesasDeputado.iloc[-1]["numMes"]

        mesesComDespesa = len(despesasDeputado)

        print(
            "Primeira despesa:",
            int(primeiroMes),
            "/",
            int(primeiroAno)
        )

        print(
            "Última despesa:",
            int(ultimoMes),
            "/",
            int(ultimoAno)
        )

        print(
            "Quantidade de meses com despesa:",
            mesesComDespesa
        )

        # -------------------------------------
        # MÉDIAS
        # -------------------------------------

        gastoMedioMesComDespesa = (
            gastoTotal / mesesComDespesa
        )

        mesesExercicio = diasExercicio / 30.4375

        if mesesExercicio > 0:

            gastoMedioMesExercicio = (
                gastoTotal / mesesExercicio
            )

            print(
                "\nMeses equivalentes em exercício:",
                round(mesesExercicio, 2)
            )

            print(
                "Gasto médio / mês de exercício: R$",
                round(gastoMedioMesExercicio, 2)
            )

        print(
            "Gasto médio / mês COM despesa: R$",
            round(gastoMedioMesComDespesa, 2)
        )


# =============================================
# 4. RESUMO GERAL
# =============================================

print("\n")
print("=" * 70)
print("RESUMO")
print("=" * 70)

resumo = []

for _, deputado in investigados.iterrows():

    idDeputado = deputado["id"]
    nome = deputado["nome"]

    h = historico[historico["id"] == idDeputado]
    d = despesas[despesas["id"] == idDeputado]

    dias = h["diasExercicio"].sum()
    gasto = d["vlrLiquido"].sum()
    mesesDespesa = len(d)

    mesesExercicio = dias / 30.4375

    if mesesExercicio > 0:
        gastoPorExercicio = gasto / mesesExercicio
    else:
        gastoPorExercicio = None

    if mesesDespesa > 0:
        gastoPorMesDespesa = gasto / mesesDespesa
    else:
        gastoPorMesDespesa = None

    resumo.append({

        "id": idDeputado,

        "nome": nome,

        "diasExercicio":
            dias,

        "mesesExercicio":
            round(mesesExercicio, 2),

        "mesesComDespesa":
            mesesDespesa,

        "gastoTotal":
            round(gasto, 2),

        "gastoPorMesExercicio":
            round(gastoPorExercicio, 2)
            if gastoPorExercicio is not None
            else None,

        "gastoPorMesComDespesa":
            round(gastoPorMesDespesa, 2)
            if gastoPorMesDespesa is not None
            else None
    })


resumo = pd.DataFrame(resumo)

print(resumo.to_string(index=False))

resumo.to_csv(
    "investigacao_custo_55.csv",
    index=False
)