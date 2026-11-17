import pandas as pd

# =============================================
# 1. PERÍODO DA 55ª LEGISLATURA
# =============================================

INICIO_LEG = pd.Timestamp("2015-02-01 00:00")
FIM_LEG = pd.Timestamp("2019-01-31 23:59")


# =============================================
# 2. MUDANÇAS DE NOME, FUSÕES E INCORPORAÇÕES
# =============================================

mudancas = [
    ("PTN", "PODE", "2017-05-16"),
    ("PTdoB", "AVANTE", "2017-09-12"),
    ("PEN", "PATRI", "2018-04-26"),
    ("PATRI", "PATRIOTA", "2019-03-01"),
    ("PMDB", "MDB", "2018-05-15"),
    ("PSDC", "DC", "2018-05-17"),
    ("SD", "SOLIDARIEDADE", "2018-06-28"),
    ("PR", "PL", "2019-02-09"),
    ("PRB", "REPUBLICANOS", "2019-08-15"),
    ("PPS", "CIDADANIA", "2019-09-19"),
    ("PTC", "AGIR", "2022-03-31"),
    ("PMN", "MOBILIZA", "2023-12-05"),
    ("PMB", "DEMOCRATA", "2025-12-02"),
    ("DEM", "UNIÃO", "2022-02-08"),
    ("PSL", "UNIÃO", "2022-02-08"),
    ("PTB", "PRD", "2023-11-09"),
    ("PATRIOTA", "PRD", "2023-11-09"),
    ("PRP", "PATRIOTA", "2019-03-28"),
    ("PPL", "PCdoB", "2019-05-28"),
    ("PHS", "PODE", "2019-09-19"),
    ("PROS", "SOLIDARIEDADE", "2023-02-14"),
    ("PSC", "PODE", "2023-06-15"),
]

sucessao = {}

for antiga, nova, data in mudancas:
    sucessao[(antiga, nova)] = pd.Timestamp(data)


# =============================================
# 3. CARREGAR HISTÓRICO BRUTO
# =============================================

eventos = pd.read_csv("historico_bruto_55.csv")

# Remove linhas sem situação parlamentar
eventos = eventos[eventos["situacao"].notna()]

# Padroniza situação
eventos["situacao"] = (
    eventos["situacao"]
    .str.upper()
    .str.strip()
)

# Remove asteriscos das siglas
eventos["siglaPartido"] = (
    eventos["siglaPartido"]
    .str.replace("*", "", regex=False)
    .str.strip()
)

# Remove eventos exatamente duplicados
eventos = eventos.drop_duplicates(
    subset=[
        "id",
        "dataHora",
        "siglaPartido",
        "situacao"
    ]
)

# Converte data para formato datetime
eventos["inicio"] = pd.to_datetime(
    eventos["dataHora"]
)


# =============================================
# 4. SITUAÇÕES QUE CONTAM COMO ATUAÇÃO
# =============================================

# IMPORTANTE:
# EXERCÍCIO e CONVOCADO passam a contar como período
# efetivo de atuação parlamentar.

situacoesEmExercicio = [
    "EXERCÍCIO",
    "CONVOCADO"
]


# =============================================
# 5. PROCESSAR CADA DEPUTADO
# =============================================

periodos = []

for idDeputado, historico in eventos.groupby("id"):

    historico = (
        historico
        .sort_values("inicio")
        .copy()
    )

    # -----------------------------------------
    # Cada evento dura até o começo do próximo
    # -----------------------------------------

    historico["fim"] = (
        historico["inicio"]
        .shift(-1)
        .fillna(FIM_LEG)
    )

    # Limita o intervalo às datas da legislatura
    historico["inicio"] = (
        historico["inicio"]
        .clip(lower=INICIO_LEG)
    )

    historico["fim"] = (
        historico["fim"]
        .clip(upper=FIM_LEG)
    )

    # -----------------------------------------
    # Calcular duração de cada evento
    # -----------------------------------------

    historico["dias"] = (
        historico["fim"]
        - historico["inicio"]
    ).dt.total_seconds() / 86400

    # Evita eventual valor negativo
    historico.loc[
        historico["dias"] < 0,
        "dias"
    ] = 0

    # -----------------------------------------
    # NOVA REGRA
    #
    # Conta dias quando a situação é:
    # EXERCÍCIO ou CONVOCADO
    # -----------------------------------------

    historico["diasExercicio"] = (
        historico["dias"]
        .where(
            historico["situacao"]
            .isin(situacoesEmExercicio),
            0
        )
    )


    # =========================================
    # 6. IDENTIFICAR TROCAS REAIS DE PARTIDO
    # =========================================

    bloco = 0
    blocos = []

    siglaAnterior = None

    for _, linha in historico.iterrows():

        sigla = linha["siglaPartido"]

        if (
            siglaAnterior is not None
            and sigla != siglaAnterior
        ):

            dataMudanca = sucessao.get(
                (siglaAnterior, sigla)
            )

            # Considera mudança automática quando
            # ocorreu perto da data oficial de
            # renomeação/fusão/incorporação.
            automatica = (
                dataMudanca is not None
                and linha["inicio"]
                >= dataMudanca
                - pd.Timedelta(days=30)
            )

            # Se não foi mudança automática,
            # consideramos troca real do deputado.
            if not automatica:
                bloco = bloco + 1

        blocos.append(bloco)

        siglaAnterior = sigla

    historico["bloco"] = blocos


    # =========================================
    # 7. GERAR OS PERÍODOS
    # =========================================

    for numeroBloco, grupo in historico.groupby("bloco"):

        diasExercicio = (
            grupo["diasExercicio"].sum()
        )

        # Só guarda períodos em que houve
        # efetivamente exercício/convocação.
        if diasExercicio > 0:

            periodos.append({

                "id":
                    idDeputado,

                "nome":
                    grupo["nome"].iloc[0],

                # Mostra a sigla vigente no final
                # daquele período/bloco.
                "siglaPartido":
                    grupo["siglaPartido"].iloc[-1],

                # Mantém todas as siglas encontradas
                # dentro daquele período.
                "siglasNoPeriodo":
                    " | ".join(
                        dict.fromkeys(
                            grupo["siglaPartido"]
                        )
                    ),

                "siglaUf":
                    grupo["siglaUf"].iloc[0],

                "idLegislatura":
                    55,

                "dataInicio":
                    grupo["inicio"]
                    .min()
                    .strftime("%Y-%m-%d"),

                "dataFim":
                    grupo["fim"]
                    .max()
                    .strftime("%Y-%m-%d"),

                "diasExercicio":
                    round(diasExercicio),
            })


# =============================================
# 8. CRIAR DATAFRAME FINAL
# =============================================

df = pd.DataFrame(periodos)


# =============================================
# 9. SALVAR
# =============================================

df.to_csv(
    "historico_55.csv",
    index=False
)


# =============================================
# 10. CONFERÊNCIAS
# =============================================

print(
    "Total de períodos:",
    len(df)
)

print(
    "Deputados:",
    df["id"].nunique()
)

# Para contar trocas, S.PART. não é partido
partidosValidos = df[
    df["siglaPartido"] != "S.PART."
]

quantidadePartidos = (
    partidosValidos
    .groupby("id")["siglaPartido"]
    .nunique()
)

print(
    "Deputados que trocaram de partido:",
    (quantidadePartidos > 1).sum()
)

print("\nSiglas:")
print(
    df["siglaPartido"]
    .value_counts()
)


# =============================================
# 11. VALIDAÇÃO DOS CASOS PROBLEMÁTICOS
# =============================================

idsValidacao = [
    195143,  # André Amaral
    141560,  # Walter Ihoshi
    74856,   # Laura Carneiro
    189593,  # Wadih Damous
    141474,  # Julião Amin
    160531,  # Jhonatan de Jesus
]

print("\n")
print("=" * 70)
print("VALIDAÇÃO DOS DIAS EM EXERCÍCIO")
print("=" * 70)

for idDeputado in idsValidacao:

    teste = df[
        df["id"] == idDeputado
    ]

    if len(teste) == 0:
        print(
            "\nDeputado",
            idDeputado,
            "não encontrado."
        )

        continue

    nome = teste["nome"].iloc[0]

    print("\n", nome)

    print(
        teste[
            [
                "siglaPartido",
                "siglasNoPeriodo",
                "dataInicio",
                "dataFim",
                "diasExercicio"
            ]
        ].to_string(index=False)
    )

    print(
        "Total de dias:",
        teste["diasExercicio"].sum()
    )

    print(
        "Meses equivalentes:",
        round(
            teste["diasExercicio"].sum()
            / 30.4375,
            2
        )
    )