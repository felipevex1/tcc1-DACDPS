import pandas as pd

INICIO_LEG = "2015-02-01"
FIM_LEG = "2019-01-31"

pesos = {"PEC": 5, "PLP": 3, "PL": 2, "PDL": 1, "PDC": 1}

situacoesSenado = ["Aguardando Apreciação pelo Senado Federal", "Vetado totalmente",
                   "Aguardando Apreciação do Veto", "Aguardando Autógrafos na Mesa"]

situacoesPlenario = ["Aguardando Deliberação de Recurso", "Aguardando Envio à Redação Final"]   # AJUSTE

situacoesComissao = ["Aguardando Parecer", "Aguardando Recurso", "Aguardando Análise de Parecer",   # AJUSTE
                     "Aguardando Designação - Aguardando Devolução de Relator(a) que deixou de ser Membro"]

situacoesInicio = ["Arquivada", "Tramitando em Conjunto", "Aguardando Designação de Relator(a)",
                   "Retirado pelo(a) Autor(a)", "Devolvida ao(à) Autor(a)",
                   "Aguardando Criação de Comissão Temporária", "Aguardando Constituição de Comissão Temporária",
                   "Aguardando Definição Encaminhamento", "Aguardando Autorização do Despacho",
                   "Aguardando Despacho do Presidente da Câmara dos Deputados", "Aguardando Apensação",
                   "Transformado em nova proposição", "<Não Definido>",
                   "Aguardando Encaminhamento",                                                  # AJUSTE
                   "Aguardando Despacho do Presidente da Câmara dos Deputados (Chancela)"]       # AJUSTE


def classificarEstagio(linha):
    situacao = linha["ultimoStatus_descricaoSituacao"]
    orgao = linha["ultimoStatus_siglaOrgao"]

    if situacao == "Transformado em Norma Jurídica":
        return "LEI"
    if situacao in situacoesSenado:
        return "SEN"
    if situacao in situacoesPlenario:
        return "PLE"
    if situacao in ["Pronta para Pauta", "Aguardando Deliberação"]:
        if orgao == "PLEN":
            return "PLE"
        return "COM"
    if situacao in situacoesComissao:
        return "COM"
    return "INI"


todasProposicoes = []

for ano in [2015, 2016, 2017, 2018, 2019]:
    url = f"https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-{ano}.csv"
    proposicoesAno = pd.read_csv(url, sep=";", encoding="utf-8-sig", low_memory=False)

    proposicoesAno = proposicoesAno[proposicoesAno["siglaTipo"].isin(pesos.keys())]
    proposicoesAno = proposicoesAno[(proposicoesAno["dataApresentacao"] >= INICIO_LEG) &
                                    (proposicoesAno["dataApresentacao"] <= FIM_LEG + "T23:59")]

    todasProposicoes.append(proposicoesAno)
    print("Ano", ano, "-", len(proposicoesAno), "proposições da 55ª")

proposicoes = pd.concat(todasProposicoes)

# Situações que não estão em nenhuma lista (para revisão)
conhecidas = (situacoesSenado + situacoesPlenario + situacoesComissao + situacoesInicio +
              ["Transformado em Norma Jurídica", "Pronta para Pauta", "Aguardando Deliberação"])
novas = proposicoes[~proposicoes["ultimoStatus_descricaoSituacao"].isin(conhecidas)]
print("\nSituações não mapeadas (foram para INI):")
print(novas["ultimoStatus_descricaoSituacao"].value_counts().to_string())

proposicoes["estagio"] = proposicoes.apply(classificarEstagio, axis=1)
proposicoes["peso"] = proposicoes["siglaTipo"].map(pesos)

proposicoes = proposicoes[["id", "siglaTipo", "numero", "ano", "ementa", "dataApresentacao",
                           "ultimoStatus_descricaoSituacao", "ultimoStatus_siglaOrgao",
                           "estagio", "peso"]]

proposicoes.to_csv("proposicoes_55.csv", index=False)

print("\nTotal:", len(proposicoes))
print(proposicoes["estagio"].value_counts())