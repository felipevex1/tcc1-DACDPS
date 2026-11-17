import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Eficiência do Mandato - 55ª", layout="wide")

# Renomeações dentro da 55ª (PMDB e MDB contam como o mesmo partido nos filtros)
renomeacoes = {"PTN": "PODE", "PTdoB": "AVANTE", "PEN": "PATRI", "PMDB": "MDB",
               "PSDC": "DC", "SD": "SOLIDARIEDADE"}


# =============================================
# 1. CARREGAR DADOS (fica em cache)
# =============================================

@st.cache_data
def carregar():
    indice = pd.read_csv("indice_55.csv")
    historico = pd.read_csv("historico_55.csv")

    # Partido principal: maior número de dias em exercício, sem S.PART.
    h = historico[historico["siglaPartido"] != "S.PART."].copy()
    h["partido"] = h["siglaPartido"].replace(renomeacoes)
    dias = h.groupby(["id", "partido"])["diasExercicio"].sum().reset_index()
    principal = dias.sort_values("diasExercicio", ascending=False).drop_duplicates("id")

    uf = historico.drop_duplicates("id")[["id", "siglaUf"]]

    indice = indice.merge(principal[["id", "partido"]], on="id", how="left")
    indice = indice.merge(uf, on="id", how="left")
    indice["partido"] = indice["partido"].fillna("S.PART.")
    indice["situacao"] = "Classificado"
    indice.loc[indice["elegivel"] & indice["camada"].isna(), "situacao"] = "Sem entrega registrada"
    indice.loc[~indice["elegivel"], "situacao"] = "Menos de 6 meses de exercício"
    return indice, historico


indice, historico = carregar()
elegiveis = indice[indice["elegivel"]]

# Medianas fixas da legislatura (não mudam com os filtros)
medEntrega = elegiveis["entrega"].median()
medGasto = elegiveis["gastoMensalProporcional"].median()


# =============================================
# 2. FILTROS
# =============================================

st.sidebar.header("Filtros")
partidos = st.sidebar.multiselect("Partido", sorted(indice["partido"].unique()))
ufs = st.sidebar.multiselect("UF", sorted(indice["siglaUf"].dropna().unique()))
quadrantes = st.sidebar.multiselect("Quadrante", sorted(elegiveis["quadrante"].dropna().unique()))
busca = st.sidebar.text_input("Buscar deputado")

filtrado = indice.copy()
if partidos:
    filtrado = filtrado[filtrado["partido"].isin(partidos)]
if ufs:
    filtrado = filtrado[filtrado["siglaUf"].isin(ufs)]
if quadrantes:
    filtrado = filtrado[filtrado["quadrante"].isin(quadrantes)]
if busca:
    filtrado = filtrado[filtrado["nome"].str.contains(busca, case=False)]

st.title("Eficiência do mandato parlamentar — 55ª legislatura (2015–2019)")
st.caption("Medida relativa, construída a partir dos dados abertos da Câmara dos Deputados. "
           "Não representa uma avaliação definitiva do mandato.")

aba1, aba2, aba3, aba4 = st.tabs(["Visão geral", "Entrega × custo", "Deputado", "Metodologia"])


# =============================================
# 3. VISÃO GERAL
# =============================================

with aba1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Deputados", len(filtrado))
    c2.metric("Na fronteira (camada 1)", int((filtrado["camada"] == 1).sum()))
    c3.metric("Gasto mensal mediano", f"R$ {filtrado['gastoMensalProporcional'].median():,.0f}".replace(",", "."))
    c4.metric("Sem entrega registrada", int((filtrado["situacao"] == "Sem entrega registrada").sum()))

    tabela = filtrado.sort_values(["camada", "entrega"], ascending=[True, False])
    st.dataframe(
        tabela[["nome", "partido", "siglaUf", "camada", "quadrante", "lesb",
                "coautoriasInterpartidarias", "gastoMensalProporcional", "entrega", "situacao"]]
        .rename(columns={"siglaUf": "UF", "camada": "Camada", "quadrante": "Quadrante",
                         "lesb": "LESb", "coautoriasInterpartidarias": "Coautorias interpartidárias",
                         "gastoMensalProporcional": "Gasto mensal (R$)", "entrega": "Entrega",
                         "situacao": "Situação"}),
        use_container_width=True, hide_index=True)


# =============================================
# 4. GRÁFICO ENTREGA x CUSTO
# =============================================

with aba2:
    pontos = filtrado[filtrado["elegivel"]].copy()
    pontos["fronteira"] = pontos["camada"] == 1

    dispersao = alt.Chart(pontos).mark_circle(size=60, opacity=0.7).encode(
        x=alt.X("gastoMensalProporcional", title="Gasto mensal da cota (R$)"),
        y=alt.Y("entrega", title="Entrega (efetividade + articulação)"),
        color=alt.Color("quadrante", title="Quadrante"),
        tooltip=["nome", "partido", "siglaUf", "camada", "lesb",
                 "coautoriasInterpartidarias", "gastoMensalProporcional"])

    fronteira = alt.Chart(pontos[pontos["fronteira"]]).mark_point(
        size=200, color="black", filled=False).encode(
        x="gastoMensalProporcional", y="entrega", tooltip=["nome"])

    linhaX = alt.Chart(pd.DataFrame({"x": [medGasto]})).mark_rule(strokeDash=[4, 4]).encode(x="x")
    linhaY = alt.Chart(pd.DataFrame({"y": [medEntrega]})).mark_rule(strokeDash=[4, 4]).encode(y="y")

    st.altair_chart((dispersao + fronteira + linhaX + linhaY).properties(height=550),
                    use_container_width=True)
    st.caption("Linhas tracejadas: medianas da legislatura. Círculos pretos: fronteira de eficiência "
               "(nenhum outro deputado entrega mais gastando menos).")


# =============================================
# 5. FICHA DO DEPUTADO
# =============================================

with aba3:
    nome = st.selectbox("Deputado", sorted(filtrado["nome"].unique()))
    dep = indice[indice["nome"] == nome].iloc[0]

    st.subheader(f"{dep['nome']} — {dep['partido']}/{dep['siglaUf']}")
    st.write("Situação:", dep["situacao"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("LESb", f"{dep['lesb']:.2f}")
    c2.metric("Coautorias interpartidárias", int(dep["coautoriasInterpartidarias"]))
    c3.metric("Gasto mensal", f"R$ {dep['gastoMensalProporcional']:,.0f}".replace(",", "."))
    c4.metric("Camada", "—" if pd.isna(dep["camada"]) else int(dep["camada"]))

    if dep["elegivel"]:
        st.write("Quadrante:", dep["quadrante"])

    st.markdown("**Partidos ao longo da legislatura**")
    st.dataframe(historico[historico["id"] == dep["id"]]
                 [["siglaPartido", "dataInicio", "dataFim", "diasExercicio"]],
                 use_container_width=True, hide_index=True)


# =============================================
# 6. METODOLOGIA
# =============================================

with aba4:
    st.markdown(f"""
- **Efetividade (LESb):** avanço das proposições do deputado por cinco estágios de tramitação,
  com pesos por tipo (PEC 5, PLP 3, PL 2, PDL/PDC 1). A média da legislatura é igual a 1.
- **Articulação:** número de proposições coassinadas com deputados de outros partidos (sem PECs).
- **Entrega:** média entre efetividade e articulação, após transformação logarítmica e normalização de 0 a 1.
- **Custo:** gasto da cota parlamentar dividido pelos meses em exercício.
- **Quadrantes:** comparação com as medianas da legislatura
  (entrega {medEntrega:.3f}; gasto R$ {medGasto:,.0f}).
- **Camadas:** a camada 1 reúne deputados que nenhum outro supera ao mesmo tempo em entrega e em custo.
  Deputados na mesma camada não são ordenados entre si.

**Limitações:** a articulação é uma aproximação; o LESb usa o último status da proposição e não
capta influência informal; deputados com menos de 6 meses de exercício não são classificados.
""")