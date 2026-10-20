"""IMC em Dados — dashboard Streamlit independente.

O aplicativo usa os números e registros presentes no HTML de referência enviado
pela equipe. Indicadores dos modelos são resultados pré-calculados: mudar filtros
NÃO retreina nem reavalia regressão ou Random Forest.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="IMC em Dados | Painel da pesquisa",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Identidade visual inspirada no arquivo IMC_em_Dados.html, sem depender de HTML externo.
AZUL = "#2057BE"
AZUL_CLARO = "#61A5FA"
LARANJA = "#F08047"
VERDE = "#168977"
CINZA = "#8292AC"
ESCURO = "#15294E"
FUNDO = "#F1F5FB"

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
:root{color-scheme:light}
html, body, [class*="css"], [data-testid="stAppViewContainer"]{font-family:'DM Sans',system-ui,sans-serif}
[data-testid="stAppViewContainer"]{background:linear-gradient(135deg,#eef3fb 0%,#f8faff 67%,#eff4fd 100%)}
[data-testid="stMainBlockContainer"]{padding-top:1.2rem; max-width:1420px}
[data-testid="stSidebar"]{background:#fff;border-right:1px solid #e0e9f6}
h1,h2,h3{color:#15294e!important;letter-spacing:-.02em}
h1{font-size:2.05rem!important}
h2{font-size:1.25rem!important}
header[data-testid="stHeader"]{background:transparent}
.hero{padding:25px 30px;margin-bottom:17px;border-radius:21px;background:linear-gradient(125deg,#102d69,#2c61c7);color:#fff;box-shadow:0 12px 35px rgba(34,76,145,.12)}
.hero .eyebrow{font-size:.76rem;font-weight:800;letter-spacing:.14em;color:#c7d8ff}
.hero h1{color:#fff!important;margin:5px 0;font-size:2rem!important}
.hero p{margin:0;color:#e4eeff;font-size:.96rem}
.sectionline{display:flex;align-items:baseline;gap:9px;margin:16px 0 8px}
.sectionline b{color:#142e60;font-size:1.11rem}
.stat{padding:16px 18px;min-height:112px;background:#fff;border:1px solid #e1eaf7;border-radius:17px;box-shadow:0 4px 18px rgba(21,49,91,.045)}
.stat .top{font-size:.75rem;color:#657895;font-weight:700;letter-spacing:.015em}
.stat .number{font-size:1.95rem;font-weight:800;line-height:1.17;margin-top:9px;color:#245fc4}
.stat .hint{color:#71809b;font-size:.73rem;margin-top:3px}
.note{background:#fff;border-left:4px solid #286cdb;padding:11px 14px;border-radius:11px;color:#435775;font-size:.89rem;margin:8px 0 16px}
.result{padding:15px 19px;background:#fff;border:1px solid #e1eaf7;border-radius:17px}
.result h4{color:#15294e;margin:0 0 8px;font-size:1.03rem}
.result p{color:#4e607c;font-size:.9rem;margin:0}
[data-testid="stPlotlyChart"]{background:white;border:1px solid #e1eaf7;border-radius:17px;padding:5px 5px 0;box-shadow:0 2px 9px rgba(28,50,82,.035)}
[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden}
div[role="radiogroup"]{background:#fff;padding:8px 10px;border-radius:15px;border:1px solid #dfe8f7;margin:6px 0 15px}
div[role="radiogroup"] label{padding:3px 5px}
.stButton button[kind="primary"]{background:#245fc4!important;border-color:#245fc4!important}
footer{visibility:hidden}
@media(max-width:760px){.hero{padding:20px}.hero h1{font-size:1.55rem!important}.stat{min-height:92px}}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def carregar():
    arquivo = Path(__file__).with_name("dados_painel.json")
    if not arquivo.exists():
        raise FileNotFoundError("dados_painel.json não está ao lado de app.py")
    d = json.loads(arquivo.read_text(encoding="utf-8"))
    return d


def frame(conjunto: str) -> pd.DataFrame:
    return pd.DataFrame(DADOS[conjunto]).copy()


def indic(chave: str):
    return IND[chave]


def fmt_num(n, casas=0):
    return f"{n:,.{casas}f}".replace(",", "~").replace(".", ",").replace("~", ".")


def cartao(titulo: str, numero, dica: str = "", cor: str = AZUL):
    st.markdown(
        f'<div class="stat"><div class="top">{titulo}</div>'
        f'<div class="number" style="color:{cor}">{numero}</div>'
        f'<div class="hint">{dica}</div></div>', unsafe_allow_html=True
    )


def titulo(texto: str, descricao: str = ""):
    st.markdown(f'<div class="sectionline"><b>{texto}</b></div>', unsafe_allow_html=True)
    if descricao:
        st.caption(descricao)


def avisinho(texto: str):
    st.markdown(f'<div class="note">{texto}</div>', unsafe_allow_html=True)


def grafico(fig, altura: int = 340, chave: str | None = None):
    fig.update_layout(
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, Arial", color=ESCURO, size=12),
        margin=dict(l=23, r=20, t=48, b=30),
        colorway=[AZUL, LARANJA, VERDE, AZUL_CLARO, CINZA],
        legend=dict(orientation="h", y=-.22, x=0),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#edf1f8", zerolinecolor="#cdd7e6")
    fig.update_yaxes(showgrid=True, gridcolor="#edf1f8", zerolinecolor="#cdd7e6")
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False}, key=chave)


def donut(labels, values, cores=None, titulo_grafico=None):
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=.66, sort=False,
        marker=dict(colors=cores or [AZUL, LARANJA, VERDE, CINZA]),
        textinfo="percent", textfont=dict(size=12, color="white"),
        hovertemplate="%{label}: %{value} pessoas (%{percent})<extra></extra>",
    ))
    fig.update_layout(title=titulo_grafico, showlegend=True)
    return fig


DADOS = carregar()
IND = {item["id"]: item["valor"] for item in DADOS["indicadores"]}
PESSOAS = frame("pessoas")
PESSOAS["grupo_imc"] = np.where(PESSOAS["imc"] >= 25, "Com excesso", "Sem excesso")
PESSOAS["atividade"] = np.where(PESSOAS["atfis"] > 0, "Pratica", "Não pratica")

st.sidebar.markdown("### 📊 IMC em Dados")
st.sidebar.caption("Painel independente • pesquisa nutricional")
st.sidebar.divider()
st.sidebar.markdown("**Filtros de exploração**")
idade_min, idade_max = int(PESSOAS.idade.min()), int(PESSOAS.idade.max())
faixa = st.sidebar.slider("Idade (anos)", idade_min, idade_max, (idade_min, idade_max))
sexo = st.sidebar.selectbox("Sexo", ["Todos"] + sorted(PESSOAS.sexo.unique().tolist()))
grupo = st.sidebar.selectbox("Grupo do IMC", ["Todos", "Com excesso", "Sem excesso"])
atividade = st.sidebar.selectbox("Atividade física", ["Todos", "Pratica", "Não pratica"])

SEL = PESSOAS[PESSOAS["idade"].between(*faixa)].copy()
if sexo != "Todos":
    SEL = SEL[SEL.sexo == sexo]
if grupo != "Todos":
    SEL = SEL[SEL.grupo_imc == grupo]
if atividade != "Todos":
    SEL = SEL[SEL.atividade == atividade]
st.sidebar.caption(f"{len(SEL)} de {len(PESSOAS)} registros na seleção")
st.sidebar.info("Os filtros afetam apenas os gráficos exploratórios. Resultados dos modelos são os valores originais do relatório.", icon="ℹ️")

st.markdown(
    '<div class="hero"><div class="eyebrow">PROJETO DE SAÚDE NUTRICIONAL</div>'
    '<h1>IMC em Dados</h1><p>Da base de dados aos resultados de Regressão Linear e Random Forest</p></div>',
    unsafe_allow_html=True,
)

PAGINAS = ["Base de dados", "Participantes", "Exploração do IMC", "Regressão Linear", "Random Forest", "Conclusões"]
pagina = st.radio("Navegação", PAGINAS, horizontal=True, label_visibility="collapsed")


if pagina == "Base de dados":
    st.subheader("01 · Caracterização da base")
    c = st.columns(4)
    for col, titulo_k, num, hint, color in zip(
        c,
        ["Registros originais", "Prováveis respostas reais", "Sem repetição", "Adultos estudados"],
        ["2.111", "498", "488", "450"],
        ["base pública", "identificação por padrão de respostas", "deduplicação", "18 a 56 anos"],
        [AZUL, AZUL_CLARO, LARANJA, VERDE],
    ):
        with col: cartao(titulo_k, num, hint, color)
    a, b = st.columns([1.3, 1])
    with a:
        titulo("Caminho dos dados")
        df = frame("funil").sort_values("ordem", ascending=False)
        fig = px.bar(df, x="registros", y="etapa", orientation="h", text="registros", color="etapa",
                     color_discrete_sequence=[VERDE, AZUL_CLARO, AZUL, LARANJA], title="Da origem aos 450 participantes")
        fig.update_traces(textposition="outside", showlegend=False)
        fig.update_layout(showlegend=False, xaxis_title="Registros", yaxis_title="")
        grafico(fig, 355)
    with b:
        titulo("O que ficou de fora")
        r = frame("retirados").iloc[:4].sort_values("registros")
        fig = px.bar(r, y="motivo", x="registros", orientation="h", text="registros",
                     color_discrete_sequence=[LARANJA], title="Motivos e quantidades")
        fig.update_traces(textposition="outside")
        fig.update_layout(yaxis_title="", xaxis_title="Registros")
        grafico(fig, 355)
    avisinho("A distinção entre respostas reais e registros gerados por computador é uma <b>inferência da equipe</b> baseada nos padrões das respostas; não está identificada diretamente na base original.")
    titulo("Dicionário de variáveis", "O painel reproduz as informações presentes no HTML enviado.")
    vars_df = frame("variaveis").sort_values("ordem")
    st.dataframe(vars_df[["nome", "tipo", "descricao", "valores"]].rename(columns={"nome":"Variável","tipo":"Tipo","descricao":"O que indica","valores":"Categorias"}), hide_index=True, use_container_width=True, height=300)

elif pagina == "Participantes":
    st.subheader("02 · Perfil dos participantes")
    c = st.columns(4)
    with c[0]: cartao("Pessoas na seleção", fmt_num(len(SEL)), "filtros à esquerda", AZUL)
    with c[1]: cartao("Idade média", f"{fmt_num(SEL.idade.mean(),1)}" if len(SEL) else "—", "anos (seleção)", AZUL_CLARO)
    with c[2]: cartao("IMC mediano", f"{fmt_num(SEL.imc.median(),1)}" if len(SEL) else "—", "kg/m² (seleção)", VERDE)
    with c[3]: cartao("Com excesso", f"{fmt_num((SEL.imc>=25).mean()*100,1)}%" if len(SEL) else "—", "IMC ≥ 25 (seleção)", LARANJA)
    if SEL.empty:
        st.warning("Nenhum registro combina com os filtros escolhidos. Amplie a seleção na barra lateral.")
    else:
        a, b = st.columns([1.1, 1])
        with a:
            titulo("Idade dos participantes")
            fig=px.histogram(SEL,x="idade",nbins=min(30, max(8,int(SEL.idade.nunique()))),color_discrete_sequence=[AZUL], title="Distribuição etária")
            fig.update_layout(xaxis_title="Idade (anos)", yaxis_title="Número de pessoas", bargap=.06)
            grafico(fig,350)
        with b:
            titulo("Pessoas com e sem excesso de peso")
            s=SEL.grupo_imc.value_counts()
            grafico(donut(s.index.tolist(),s.tolist(),[LARANJA if v=="Com excesso" else AZUL for v in s.index], "IMC ≥ 25 x IMC < 25"),350)
        st.markdown("#### Hábitos e estilo de vida")
        a,b=st.columns([1,1])
        with a:
            eixo=st.selectbox("Explorar um hábito", ["lanches", "transporte", "alcool", "atividade", "veg", "agua", "refeic", "tela", "hist", "fuma"],
                              format_func=lambda v: {"lanches":"Lanches", "transporte":"Transporte", "alcool":"Álcool", "atividade":"Atividade física", "veg":"Vegetais (escala)", "agua":"Água (escala)", "refeic":"Refeições (escala)", "tela":"Tempo de tela (escala)", "hist":"Histórico familiar", "fuma":"Fumo"}[v])
            soma=SEL[eixo].astype(str).value_counts().reset_index()
            soma.columns=["Categoria", "Pessoas"]
            fig=px.bar(soma,x="Categoria",y="Pessoas", text="Pessoas", color_discrete_sequence=[AZUL_CLARO],title="Respostas selecionadas")
            fig.update_layout(xaxis_title="",yaxis_title="Número de pessoas")
            grafico(fig,330)
        with b:
            titulo("Sexo")
            sexo_cont=SEL.sexo.value_counts()
            grafico(donut(sexo_cont.index.tolist(),sexo_cont.tolist(),[AZUL,LARANJA],"Distribuição por sexo"),350)
        titulo("Registros para consulta")
        vista=SEL[["pessoa","idade","sexo","imc","grupo_imc","lanches","hist","atividade","transporte"]].rename(columns={"pessoa":"ID anônimo","idade":"Idade","sexo":"Sexo","imc":"IMC","grupo_imc":"Grupo IMC","lanches":"Lanches","hist":"Hist. familiar","atividade":"Atividade física","transporte":"Transporte"})
        st.dataframe(vista, use_container_width=True, hide_index=True, height=270)
        st.download_button("⬇️ Exportar registros filtrados (CSV)", data=vista.to_csv(index=False).encode("utf-8-sig"), file_name="imc_dados_filtrados.csv", mime="text/csv")

elif pagina == "Exploração do IMC":
    st.subheader("03 · Análise exploratória")
    avisinho("Gráficos calculados com os registros selecionados pelos filtros. As relações observadas <b>não provam causa</b>.")
    if len(SEL)<2:
        st.warning("Selecione pelo menos dois participantes nos filtros para comparar os dados.")
    else:
        c=st.columns(3)
        with c[0]: cartao("Pessoas selecionadas",fmt_num(len(SEL)),"exploração",AZUL)
        with c[1]: cartao("IMC médio",fmt_num(SEL.imc.mean(),1),"kg/m²",VERDE)
        with c[2]: cartao("Idade × IMC",fmt_num(SEL[["idade","imc"]].corr().iloc[0,1],2) if SEL.idade.nunique()>1 else "—","correlação na seleção",LARANJA)
        a,b=st.columns([1.4,1])
        with a:
            titulo("A idade acompanha o IMC?")
            fig=px.scatter(SEL,x="idade",y="imc",color="sexo",opacity=.7,
                           color_discrete_map={"Masculino":AZUL,"Feminino":LARANJA},
                           hover_data={"pessoa":True,"idade":True,"imc":":.2f","sexo":True},
                           title="Idade × IMC (cada ponto = uma pessoa)")
            if SEL.idade.nunique()>1:
                x=np.linspace(SEL.idade.min(),SEL.idade.max(),80)
                m,beta=np.polyfit(SEL.idade.to_numpy(),SEL.imc.to_numpy(),1)
                fig.add_trace(go.Scatter(x=x,y=m*x+beta,mode="lines",name="Tendência da seleção",line=dict(color=VERDE,width=3)))
            fig.update_layout(xaxis_title="Idade (anos)",yaxis_title="IMC (kg/m²)")
            grafico(fig,410)
        with b:
            titulo("IMC médio por atividade física")
            m=SEL.groupby("atividade",as_index=False).agg(imc=("imc","mean"), pessoas=("imc","size"))
            fig=px.bar(m,x="atividade",y="imc",text_auto=".1f",color="atividade",
                        color_discrete_map={"Pratica":VERDE,"Não pratica":LARANJA},title="Comparação dos grupos")
            fig.update_layout(showlegend=False,xaxis_title="",yaxis_title="IMC médio")
            grafico(fig,410)
        grupo_x=st.selectbox("Comparar o IMC por", ["sexo","hist","lanches","alcool","transporte","atfis"],
                            format_func=lambda x:{"sexo":"Sexo","hist":"Histórico familiar","lanches":"Lanches","alcool":"Álcool","transporte":"Transporte","atfis":"Atividade física (escala)"}[x])
        a,b=st.columns(2)
        with a:
            titulo("Distribuição do IMC por grupo")
            fig=px.box(SEL,x=grupo_x,y="imc",points="outliers",color=grupo_x,
                        color_discrete_sequence=[AZUL,LARANJA,VERDE,AZUL_CLARO,CINZA],title="Medianas e dispersão")
            fig.update_layout(showlegend=False,xaxis_title="",yaxis_title="IMC")
            grafico(fig,390)
        with b:
            titulo("Comparação de médias")
            avg=SEL.groupby(grupo_x,dropna=False,as_index=False).agg(imc=("imc","mean"),n=("imc","size"))
            fig=px.bar(avg,x=grupo_x,y="imc",text_auto=".1f",color_discrete_sequence=[AZUL_CLARO],title="Média por categoria")
            fig.update_layout(xaxis_title="",yaxis_title="IMC médio")
            grafico(fig,390)

elif pagina == "Regressão Linear":
    st.subheader("04 · Regressão Linear")
    c=st.columns(4)
    with c[0]: cartao("Pessoas no treino", "360", "80% dos dados")
    with c[1]: cartao("R² médio", "0,12", "validação cruzada", VERDE)
    with c[2]: cartao("Erro médio (MAE)", "3,39", "pontos de IMC", LARANJA)
    with c[3]: cartao("MAE no teste", "2,86", "90 pessoas não vistas", AZUL_CLARO)
    a,b=st.columns([1.1,1])
    with a:
        titulo("IMC previsto × verdadeiro")
        p=frame("previsoes_teste")
        fig=px.scatter(p,x="observado",y="previsto",color_discrete_sequence=[AZUL],opacity=.75,
                       title="Resultado do teste (90 pessoas)")
        rmin=min(p.observado.min(),p.previsto.min());rmax=max(p.observado.max(),p.previsto.max())
        fig.add_trace(go.Scatter(x=[rmin,rmax],y=[rmin,rmax],mode="lines",name="Previsão ideal",line=dict(color=LARANJA,dash="dash")))
        fig.update_layout(xaxis_title="IMC observado",yaxis_title="IMC previsto")
        grafico(fig,390)
    with b:
        titulo("Validação cruzada: erro médio")
        cv=frame("cv_regressao")
        fig=go.Figure()
        fig.add_bar(x=cv.rodada,y=cv.mae,name="Regressão",marker_color=AZUL)
        fig.add_bar(x=cv.rodada,y=cv.mae_chute,name="Prever a média",marker_color=LARANJA)
        fig.update_layout(barmode="group",title="MAE por rodada",xaxis_title="Rodada",yaxis_title="Erro (menor é melhor)")
        grafico(fig,390)
    titulo("Coeficientes e intervalos de confiança", "Azul: intervalo de 95% não cruza zero. Cinza: direção incerta.")
    coef=frame("coeficientes").copy()
    coef["clara"]=(coef.ic95_inferior*coef.ic95_superior>0)
    coef=coef.sort_values("coeficiente")
    fig=go.Figure()
    for claro, subset, cor, legenda in [(False,coef[~coef.clara],CINZA,"Direção incerta"),(True,coef[coef.clara],AZUL,"Direção clara")]:
        if not subset.empty:
            fig.add_trace(go.Scatter(
                x=subset.coeficiente,y=subset.variavel,mode="markers",name=legenda,
                marker=dict(color=cor,size=10),
                error_x=dict(type="data",symmetric=False,array=subset.ic95_superior-subset.coeficiente,arrayminus=subset.coeficiente-subset.ic95_inferior,thickness=1.5,color=cor),
                customdata=np.stack([subset.ic95_inferior.to_numpy(),subset.ic95_superior.to_numpy()],axis=1),
                hovertemplate="%{y}<br>Coef.: %{x:.2f}<br>IC95%: %{customdata[0]:.2f} a %{customdata[1]:.2f}<extra></extra>",
            ))
    fig.add_vline(x=0,line_color="#2C3C5D",line_dash="dash")
    fig.update_layout(title="Efeito associado ao IMC (mantendo as demais características constantes)",xaxis_title="Coeficiente (pontos de IMC por unidade/categoria)",yaxis_title="")
    grafico(fig, max(480,28*len(coef)+130))
    avisinho("Coeficientes têm <b>unidades e comparações diferentes</b> (por ano, por nível ou entre grupos). Não compare somente os tamanhos das barras. Associação não é causa.")

elif pagina == "Random Forest":
    st.subheader("05 · Random Forest")
    c=st.columns(4)
    with c[0]: cartao("Acerto médio", "67,5%", "5 rodadas de validação", AZUL)
    with c[1]: cartao("Comparação simples", "62,8%", "sempre o grupo majoritário", CINZA)
    with c[2]: cartao("Acerto no teste", "70,0%", "90 pessoas", VERDE)
    with c[3]: cartao("Excesso detectado", "42,6%", "média da validação", LARANJA)
    a,b=st.columns(2)
    with a:
        titulo("Matriz de confusão · teste")
        mx=frame("confusao").pivot(index="verdadeiro",columns="previsto",values="pessoas")
        ordem=["Excesso de peso","Sem excesso de peso"]
        mx=mx.reindex(index=ordem, columns=ordem)
        fig=go.Figure(go.Heatmap(z=mx.values,x=["Prev.: excesso","Prev.: sem excesso"],y=["Real: excesso","Real: sem excesso"],
                                 colorscale=[[0,"#edf4ff"],[1,AZUL]],showscale=False,hovertemplate="%{z} pessoas<extra></extra>"))
        for i in range(2):
            for j in range(2):
                fig.add_annotation(x=["Prev.: excesso","Prev.: sem excesso"][j],y=["Real: excesso","Real: sem excesso"][i],text=str(int(mx.iloc[i,j])),showarrow=False,font=dict(size=22,color="#14294e"))
        fig.update_layout(title="63 acertos e 27 erros em 90 pessoas",xaxis_title="Classificação prevista",yaxis_title="Grupo real",yaxis=dict(autorange="reversed"))
        grafico(fig,370)
    with b:
        titulo("A floresta supera o palpite simples?")
        v=frame("cv_floresta")
        fig=go.Figure()
        fig.add_bar(x=v.rodada,y=v.acertos_floresta,name="Random Forest",marker_color=AZUL)
        fig.add_bar(x=v.rodada,y=v.acertos_chute,name="Comparação simples",marker_color=LARANJA)
        fig.update_layout(barmode="group",title="Percentual de acertos nas cinco rodadas",xaxis_title="Rodada",yaxis_title="Acertos (%)",yaxis_range=[0,100])
        grafico(fig,370)
    titulo("Quais características a floresta usou mais?")
    imp=frame("importancia").sort_values("queda_acertos_pp")
    imp["cor"] = np.where(imp.queda_acertos_pp>3, "Destaque", "Outras")
    fig=px.bar(imp,x="queda_acertos_pp",y="variavel",orientation="h",color="cor",
               color_discrete_map={"Destaque":AZUL,"Outras":CINZA},title="Importância por permutação · variação de acertos (pontos percentuais)")
    fig.update_layout(xaxis_title="Queda nos acertos (p.p.)",yaxis_title="",showlegend=False)
    grafico(fig,max(490,imp.shape[0]*26+110))
    avisinho("Valores próximos de zero ou negativos podem refletir variação do teste. <b>Importância não indica causa nem direção</b>. O modelo acertou 100% do treino e 70% do teste (sobreajuste).")
    titulo("Desempenho por grupo")
    met=frame("metricas_rf")
    vis=met[met.metrica.isin(["precisao_exc","recall_exc","f1_exc","precisao_sem","recall_sem","f1_sem"])].copy()
    nomes={"precisao_exc":"Precisão · excesso","recall_exc":"Recall · excesso","f1_exc":"F1 · excesso","precisao_sem":"Precisão · sem excesso","recall_sem":"Recall · sem excesso","f1_sem":"F1 · sem excesso"}
    vis["Métrica"] = vis.metrica.map(nomes)
    vis=vis.rename(columns={"teste":"Teste (%)","cv_media":"Validação média (%)","cv_dp":"Desvio (p.p.)"})
    st.dataframe(vis[["Métrica","Teste (%)","Validação média (%)","Desvio (p.p.)"]],hide_index=True,use_container_width=True)

else:
    st.subheader("06 · Principais conclusões")
    c=st.columns(4)
    with c[0]: cartao("Participantes", "450", "adultos selecionados")
    with c[1]: cartao("Excesso de peso", "37,1%", "167 adultos",LARANJA)
    with c[2]: cartao("R² da regressão", "0,12", "média da validação",VERDE)
    with c[3]: cartao("Acertos da floresta", "67,5%", "média da validação",AZUL_CLARO)
    a,b=st.columns([1.1,1])
    with a:
        titulo("A origem dos dados muda a análise")
        orig=frame("comparacao_base")
        fig=px.bar(orig,y="base",x="imc_medio",orientation="h",text_auto=".1f",
                   color="base",color_discrete_sequence=[AZUL,LARANJA,VERDE],title="IMC médio por tipo de base")
        fig.update_layout(showlegend=False,yaxis_title="",xaxis_title="IMC médio")
        grafico(fig,370)
    with b:
        titulo("O que os dois modelos fazem?")
        st.markdown('<div class="result"><h4>Regressão Linear</h4><p>Mostra associações com o valor numérico do IMC. Explica cerca de 12% da variação.</p></div>',unsafe_allow_html=True)
        st.write("")
        st.markdown('<div class="result"><h4>Random Forest</h4><p>Classifica os grupos com e sem excesso. Acertou cerca de 5 pontos percentuais acima da referência.</p></div>',unsafe_allow_html=True)
        st.write("")
        st.markdown('<div class="result"><h4>Principal sinal: idade</h4><p>Foi a característica mais consistente nas duas análises, mas não comprova causalidade.</p></div>',unsafe_allow_html=True)
    titulo("Verificação dos números-chave")
    conf=frame("conferencia").rename(columns={"Indicador":"Indicador","Notebook":"Notebook","Este painel":"Painel","Confere?":"Conferência"})
    st.dataframe(conf, hide_index=True,use_container_width=True,height=260)
    avisinho("<b>Limitações:</b> amostra de adultos de uma base pública de México, Colômbia e Peru; autorrelato; seleção de respostas reais inferida; modelos com desempenho limitado. IMC é indicador de triagem, não diagnóstico.")
    st.markdown('**Próximo passo sugerido:** validar cuidadosamente em novos dados autorizados e verificar se os padrões se repetem.')

st.divider()
st.caption("IMC em Dados · versão Streamlit independente do NutriData · Fonte: dados e resultados incorporados ao HTML de referência enviado. Indicadores de modelagem são pré-calculados e não se alteram com filtros.")
