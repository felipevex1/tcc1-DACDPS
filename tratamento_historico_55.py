import pandas as pd

INICIO_LEG = pd.Timestamp("2015-02-01 00:00")
FIM_LEG = pd.Timestamp("2019-01-31 23:59")

# Renomeações, fusões e incorporações: (sigla antiga, sigla nova, data)
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

# Limpeza
eventos = pd.read_csv("historico_bruto_55.csv")
eventos = eventos[eventos["situacao"].notna()]
eventos["situacao"] = eventos["situacao"].str.upper().str.strip()
eventos["siglaPartido"] = eventos["siglaPartido"].str.replace("*", "", regex=False).str.strip()
eventos = eventos.drop_duplicates(subset=["id", "dataHora", "siglaPartido", "situacao"])
eventos["inicio"] = pd.to_datetime(eventos["dataHora"])

periodos = []

for idDeputado, historico in eventos.groupby("id"):
    historico = historico.sort_values("inicio").copy()

    # Cada evento dura até o começo do próximo
    historico["fim"] = historico["inicio"].shift(-1).fillna(FIM_LEG)
    historico["inicio"] = historico["inicio"].clip(lower=INICIO_LEG)
    historico["fim"] = historico["fim"].clip(upper=FIM_LEG)
    historico["dias"] = (historico["fim"] - historico["inicio"]).dt.total_seconds() / 86400
    historico["diasExercicio"] = historico["dias"].where(historico["situacao"] == "EXERCÍCIO", 0)

    # Um novo período só começa quando há troca feita pelo deputado
    bloco = 0
    blocos = []
    siglaAnterior = None

    for _, linha in historico.iterrows():
        sigla = linha["siglaPartido"]

        if siglaAnterior is not None and sigla != siglaAnterior:
            dataMudanca = sucessao.get((siglaAnterior, sigla))
            automatica = dataMudanca is not None and linha["inicio"] >= dataMudanca - pd.Timedelta(days=30)

            if not automatica:
                bloco = bloco + 1

        blocos.append(bloco)
        siglaAnterior = sigla

    historico["bloco"] = blocos

    for numeroBloco, grupo in historico.groupby("bloco"):
        diasExercicio = grupo["diasExercicio"].sum()

        if diasExercicio > 0:
            periodos.append({
                "id": idDeputado,
                "nome": grupo["nome"].iloc[0],
                "siglaPartido": grupo["siglaPartido"].iloc[-1],
                "siglasNoPeriodo": " | ".join(dict.fromkeys(grupo["siglaPartido"])),
                "siglaUf": grupo["siglaUf"].iloc[0],
                "idLegislatura": 55,
                "dataInicio": grupo["inicio"].min().strftime("%Y-%m-%d"),
                "dataFim": grupo["fim"].max().strftime("%Y-%m-%d"),
                "diasExercicio": round(diasExercicio),
            })


df = pd.DataFrame(periodos)
# Chave de agrupamento: une apenas renomeações (não fusões)
renomeacoes = {"PTN": "PODE", "PTdoB": "AVANTE", "PEN": "PATRI", "PMDB": "MDB",
               "PSDC": "DC", "SD": "SOLIDARIEDADE"}
df["partidoGrupo"] = df["siglaPartido"].replace(renomeacoes)
df.to_csv("historico_55.csv", index=False)

# Trocas reais: partidos diferentes, sem contar S.PART.
partidos = df[df["siglaPartido"] != "S.PART."].groupby("id")["siglaPartido"].nunique()

print("Total de períodos:", len(df))
print("Deputados:", df["id"].nunique())
print("Deputados que trocaram de partido:", (partidos > 1).sum())
print(df["siglaPartido"].value_counts())