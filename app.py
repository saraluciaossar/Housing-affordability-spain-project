from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Paleta semántica del proyecto (coherente con los notebooks)
HOMBRE, MUJER = "#2C6FB0", "#E07B39"
PAREJA_HM, PAREJA_MM, PAREJA_HH = "#7E4DA0", "#D6457F", "#17A2B8"
CUBIERTO, NO_CUBIERTO = "#2E9E5B", "#D64545"
MERCADO, TOPE = "#5A5A66", "#E6A700"
SIN_DATO, CONJUNTO = "#B8BCC4", "#8C6D46"
TEXT, GRID = "#222222", "#E2E5E9"
PROV = {"Barcelona": "#16404D", "Girona": "#2E6E80", "Tarragona": "#6BA3B5", "Lleida": "#A9C5D1"}

DATA = Path(__file__).parent / "Data"

st.set_page_config(page_title="Acceso a la vivienda en España", page_icon="🏠", layout="wide")


@st.cache_data
def load(name):
    return pd.read_csv(DATA / name)


def style_fig(fig, height=480, money_x=False, money_y=False):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=TEXT, size=13),
        title=dict(font=dict(size=16)),
        margin=dict(l=10, r=10, t=70, b=10),
        height=height,
        legend=dict(bgcolor="white", bordercolor=GRID, borderwidth=1),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    if money_x:
        fig.update_xaxes(tickformat="~s", ticksuffix="€")
    if money_y:
        fig.update_yaxes(tickformat="~s", ticksuffix="€")
    return fig


def bloque(fig, texto_md):
    col_g, col_t = st.columns([2, 1])
    with col_g:
        st.plotly_chart(fig, use_container_width=True)
    with col_t:
        st.markdown(texto_md)


def leyenda(fig, items):
    for color, name, symbol in items:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=name,
                                 marker=dict(color=color, size=10, symbol=symbol)))


# ============================== BLOQUE 1 ==============================
def fig_lollipop_ico(year):
    df = load("b1_brecha_ico.csv")
    df = df[df["año"] == year].sort_values("brecha_ico")
    fig = go.Figure()
    for _, r in df.iterrows():
        color = NO_CUBIERTO if r["brecha_ico"] < 0 else CUBIERTO
        y = r["comunidad_autonoma"]
        fig.add_trace(go.Scatter(x=[0, r["brecha_ico"]], y=[y, y], mode="lines",
                                 line=dict(color=color, width=2.5), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=[r["brecha_ico"]], y=[y], mode="markers",
                                 marker=dict(color=color, size=12), showlegend=False,
                                 hovertemplate=f"{y}<br>Brecha: %{{x:,.0f}} €<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=TEXT, width=1, dash="dash"))
    leyenda(fig, [(NO_CUBIERTO, "Precio supera el tope ICO (brecha < 0)", "circle"),
                  (CUBIERTO, "El tope ICO cubre el precio (brecha > 0)", "circle")])
    fig.update_layout(title=f"Brecha entre tope ICO y precio medio por CCAA — {year}",
                      xaxis_title="Brecha en € (tope ICO − precio medio)",
                      legend=dict(orientation="h", y=-0.16, x=0))
    return style_fig(fig, height=560, money_x=True)


def fig_range_ico(year):
    df = load("b1_dispersion_provincial.csv")
    df = df[df["año"] == year].sort_values("precio_maximo")
    fig = go.Figure()
    for _, r in df.iterrows():
        color = CUBIERTO if r["precio_maximo"] <= r["tope_ico"] else NO_CUBIERTO
        y = r["comunidad_autonoma"]
        fig.add_trace(go.Scatter(
            x=[r["precio_minimo"], r["precio_maximo"]], y=[y, y], mode="lines+markers",
            line=dict(color=color, width=2.5), marker=dict(color=color, size=9), showlegend=False,
            hovertemplate=(f"{y}<br>mín {r['provincia_minimo']}: %{{x:,.0f}} €"
                           f"<br>máx {r['provincia_maximo']}<extra></extra>")))
        fig.add_trace(go.Scatter(x=[r["precio_medio_compraventa"]], y=[y], mode="markers",
                                 marker=dict(color="white", size=10, line=dict(color=MERCADO, width=2)),
                                 showlegend=False,
                                 hovertemplate=f"{y}<br>Precio medio CCAA: %{{x:,.0f}} €<extra></extra>"))
        fig.add_trace(go.Scatter(x=[r["tope_ico"]], y=[y], mode="markers",
                                 marker=dict(color=TOPE, size=16, symbol="line-ns",
                                             line=dict(color=TOPE, width=2.5)),
                                 showlegend=False,
                                 hovertemplate=f"Tope ICO: %{{x:,.0f}} €<extra></extra>"))
    leyenda(fig, [(CUBIERTO, "Máximo provincial cubierto", "circle"),
                  (NO_CUBIERTO, "Máximo provincial supera el tope", "circle"),
                  (MERCADO, "Precio medio CCAA", "circle-open"),
                  (TOPE, "Tope ICO", "line-ns")])
    fig.update_layout(title=f"Dispersión provincial de precios vs. tope ICO — {year}",
                      xaxis_title="Precio (€)", legend=dict(orientation="h", y=-0.16, x=0))
    return style_fig(fig, height=560, money_x=True)


def fig_genero():
    df = load("b1_salario_genero.csv").sort_values("salario_HyM")
    fig = go.Figure()
    for _, r in df.iterrows():
        y, h, m = r["comunidad_autonoma"], r["salario_H"], r["salario_M"]
        if pd.notna(h) and pd.notna(m):
            fig.add_trace(go.Scatter(x=[min(h, m), max(h, m)], y=[y, y], mode="lines",
                                     line=dict(color=GRID, width=2), showlegend=False, hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=[h], y=[y], mode="markers", marker=dict(color=HOMBRE, size=11),
                                     showlegend=False, hovertemplate=f"{y} · Hombre: %{{x:,.0f}} €<extra></extra>"))
            fig.add_trace(go.Scatter(x=[m], y=[y], mode="markers", marker=dict(color=MUJER, size=11),
                                     showlegend=False, hovertemplate=f"{y} · Mujer: %{{x:,.0f}} €<extra></extra>"))
        elif pd.isna(h) and pd.isna(m):
            fig.add_trace(go.Scatter(x=[r["salario_HyM"]], y=[y], mode="markers",
                                     marker=dict(color=SIN_DATO, size=12, symbol="diamond"), showlegend=False,
                                     hovertemplate=f"{y} · sin dato desagregado: %{{x:,.0f}} €<extra></extra>"))
        else:
            fig.add_trace(go.Scatter(x=[r["salario_HyM"]], y=[y], mode="markers",
                                     marker=dict(color=CONJUNTO, size=11), showlegend=False,
                                     hovertemplate=f"{y} · salario conjunto: %{{x:,.0f}} €<extra></extra>"))
    leyenda(fig, [(HOMBRE, "Hombre", "circle"), (MUJER, "Mujer", "circle"),
                  (CONJUNTO, "Salario conjunto (dato mujer no fiable)", "circle"),
                  (SIN_DATO, "Sin dato desagregado", "diamond")])
    fig.update_layout(title="Salario medio por sexo y CCAA (2024) — tramo 25-34 años",
                      xaxis_title="Salario bruto anual (€)", legend=dict(orientation="h", y=-0.16, x=0))
    return style_fig(fig, height=560, money_x=True)


def fig_capacidad():
    df = load("b1_capacidad.csv")
    # (nombre, color, símbolo): círculo para individuales; forma propia por tipo de pareja
    perfiles = {"brecha_acceso_H": ("Hombre", HOMBRE, "circle"),
                "brecha_acceso_M": ("Mujer", MUJER, "circle"),
                "brecha_acceso_pareja_HM": ("Pareja HM", PAREJA_HM, "diamond"),
                "brecha_acceso_pareja_MM": ("Pareja MM", PAREJA_MM, "square"),
                "brecha_acceso_pareja_HH": ("Pareja HH", PAREJA_HH, "triangle-up")}
    orden = df.sort_values("precio_medio_compraventa")["comunidad_autonoma"].tolist()
    xmin = float(df[list(perfiles)].min().min())
    fig = go.Figure()
    fig.add_vrect(x0=xmin * 1.05, x1=0, fillcolor=NO_CUBIERTO, opacity=0.06, line_width=0)
    for col, (name, color, symbol) in perfiles.items():
        sub = df[["comunidad_autonoma", col]].dropna()
        fig.add_trace(go.Scatter(x=sub[col], y=sub["comunidad_autonoma"], mode="markers",
                                 marker=dict(color=color, size=11, opacity=0.9, symbol=symbol), name=name,
                                 hovertemplate=f"%{{y}} · {name}: %{{x:,.0f}} €<extra></extra>"))
    fig.add_vline(x=0, line=dict(color=TEXT, width=1, dash="dash"))
    fig.update_yaxes(categoryorder="array", categoryarray=orden)
    fig.update_layout(title="Capacidad financiera por CCAA y perfil — Aval ICO (2024)",
                      xaxis_title="Brecha de acceso (€)   ← no puede acceder · puede acceder →",
                      legend=dict(orientation="h", y=-0.16, x=0))
    return style_fig(fig, height=600, money_x=True)


# ============================== BLOQUE 2 ==============================
def fig_b2_precio_m2():
    df = load("b2_provincias.csv").sort_values("precio_m2_2024", ascending=False)
    fig = go.Figure(go.Bar(
        x=df["territorio"], y=df["precio_m2_2024"], width=0.5,
        marker_color=[PROV[p] for p in df["territorio"]],
        text=[f"Tope: {m:.0f} m²" for m in df["tope_m2_2024"]], textposition="outside",
        textfont=dict(color=TEXT, size=12),
        hovertemplate="%{x}: %{y:,.0f} €/m²<extra></extra>"))
    fig.update_layout(title="Precio medio €/m² por provincia y m² equivalentes al tope (250.000 €)",
                      yaxis_title="€/m² (2024)", showlegend=False)
    fig.update_yaxes(range=[0, df["precio_m2_2024"].max() * 1.25], ticksuffix=" €")
    return style_fig(fig, height=500)


def fig_b2_m2_comarca():
    prov = load("b2_provincias.csv")
    disp = load("b2_dispersion_comarcas.csv").set_index("provincia")
    tope = prov["tope_vivienda"].iloc[0]
    orden = prov.sort_values("precio_m2_2024", ascending=False)["territorio"].tolist()
    m2_mas = [tope / disp.loc[p, "precio_minimo"] for p in orden]
    m2_menos = [tope / disp.loc[p, "precio_maximo"] for p in orden]
    media = [prov.loc[prov["territorio"] == p, "tope_m2_2024"].values[0] for p in orden]
    nom_mas = [disp.loc[p, "comarca_minimo"] for p in orden]
    nom_menos = [disp.loc[p, "comarca_maximo"] for p in orden]
    cols = [PROV[p] for p in orden]
    fig = go.Figure()
    fig.add_bar(x=orden, y=m2_mas, marker=dict(color=cols), showlegend=False,
                text=[f"{n}<br>{v:.0f} m²" for n, v in zip(nom_mas, m2_mas)], textposition="outside",
                hovertemplate="%{x} · más barata: %{y:.0f} m²<extra></extra>")
    fig.add_bar(x=orden, y=m2_menos, marker=dict(color=cols, opacity=0.45), showlegend=False,
                text=[f"{n}<br>{v:.0f} m²" for n, v in zip(nom_menos, m2_menos)], textposition="outside",
                hovertemplate="%{x} · más cara: %{y:.0f} m²<extra></extra>")
    fig.add_trace(go.Scatter(x=orden, y=media, mode="markers", name="Media provincial",
                             marker=dict(symbol="line-ew", color=TEXT, size=26, line=dict(width=2, color=TEXT))))
    fig.add_bar(x=[None], y=[None], marker=dict(color=MERCADO), name="Comarca más barata (más m²)")
    fig.add_bar(x=[None], y=[None], marker=dict(color=MERCADO, opacity=0.45), name="Comarca más cara (menos m²)")
    fig.update_layout(barmode="group", bargap=0.35, bargroupgap=0.08,
                      title="Con el mismo tope (250.000 €) se compran más m² donde la vivienda es más barata",
                      yaxis_title="m² comprables con el tope", legend=dict(orientation="h", y=-0.12, x=0))
    fig.update_yaxes(range=[0, max(m2_mas) * 1.22])
    return style_fig(fig, height=540)


def fig_b2_capacidad_hogar():
    df = load("b2_provincias.csv")
    perfiles = [("hipoteca_max_M", "Mujer sola", MUJER), ("hipoteca_max_H", "Hombre solo", HOMBRE),
                ("hipoteca_max_pareja_MM", "Pareja MM", PAREJA_MM),
                ("hipoteca_max_pareja_HM", "Pareja HM", PAREJA_HM),
                ("hipoteca_max_pareja_HH", "Pareja HH", PAREJA_HH)]
    vals = [df[c].iloc[0] for c, _, _ in perfiles]
    labels = [l for _, l, _ in perfiles]
    colors = [c for *_, c in perfiles]
    nec = 200000
    fig = go.Figure(go.Bar(y=labels, x=vals, orientation="h", marker_color=colors, width=0.62,
                           text=[f"{v:,.0f} €" for v in vals], textposition="outside",
                           hovertemplate="%{y}: %{x:,.0f} €<extra></extra>"))
    fig.add_vrect(x0=0, x1=nec, fillcolor=NO_CUBIERTO, opacity=0.06, line_width=0)
    fig.add_vline(x=nec, line=dict(color=TEXT, width=1.6, dash="dash"))
    fig.add_annotation(x=nec, y=labels[-1], text=f"Hipoteca necesaria: {nec:,.0f} €",
                       showarrow=False, xanchor="left", yshift=16, font=dict(color=TEXT, size=12))
    fig.update_layout(title="Capacidad financiera por perfil de hogar — Cataluña (25-34 años)",
                      xaxis_title="Hipoteca máxima financiable (€)", showlegend=False)
    fig.update_xaxes(range=[0, max(max(vals), nec) * 1.2], tickformat="~s", ticksuffix="€")
    return style_fig(fig, height=440)


def fig_b2_dispersion():
    prov = load("b2_provincias.csv")
    disp = load("b2_dispersion_comarcas.csv")
    orden = prov.sort_values("precio_m2_2024", ascending=False)["territorio"].tolist()
    fig = go.Figure()
    for p in orden:
        d = disp[disp["provincia"] == p].iloc[0]
        media = prov.loc[prov["territorio"] == p, "precio_m2_2024"].values[0]
        fig.add_trace(go.Scatter(x=[d["precio_minimo"], d["precio_maximo"]], y=[p, p], mode="lines+markers",
                                 line=dict(color=PROV[p], width=3), marker=dict(color=PROV[p], size=10),
                                 showlegend=False,
                                 hovertemplate=(f"{p}<br>{d['comarca_minimo']}: %{{x:,.0f}} €/m²"
                                                f"<br>{d['comarca_maximo']}<extra></extra>")))
        fig.add_trace(go.Scatter(x=[media], y=[p], mode="markers", showlegend=False,
                                 marker=dict(color="white", size=11, line=dict(color=PROV[p], width=2)),
                                 hovertemplate=f"{p} · media provincial: %{{x:,.0f}} €/m²<extra></extra>"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Media provincial",
                             marker=dict(color="white", size=10, line=dict(color=MERCADO, width=2))))
    fig.update_yaxes(categoryorder="array", categoryarray=orden[::-1])
    fig.update_layout(title="Dispersión de precio €/m² por comarca dentro de cada provincia (2024)",
                      xaxis_title="Precio €/m²", legend=dict(orientation="h", y=-0.2, x=0))
    fig.update_xaxes(ticksuffix=" €")
    return style_fig(fig, height=420)


# ============================== BLOQUE 3 ==============================
def fig_b3_curvas():
    df = load("b3_proyecciones.csv")
    cagr = load("b3_cagr_provincias.csv").set_index("provincia")["cagr"]
    provs = ["Barcelona", "Girona", "Lleida", "Tarragona"]
    fig = make_subplots(rows=2, cols=2, vertical_spacing=0.13, horizontal_spacing=0.08,
                        subplot_titles=[f"{p} · CAGR {cagr[p]:.2f}%" for p in provs])
    for idx, p in enumerate(provs):
        row, col = idx // 2 + 1, idx % 2 + 1
        d = df[df["provincia"] == p].sort_values("año_proyeccion")
        fig.add_trace(go.Scatter(x=d["año_proyeccion"], y=d["precio_mercado_m2"], mode="lines",
                                 line=dict(color=PROV[p], width=2.5), name="Precio mercado libre",
                                 legendgroup="m", showlegend=(idx == 0),
                                 hovertemplate="Año %{x}: %{y:,.0f} €/m²<extra></extra>"), row=row, col=col)
        fig.add_trace(go.Scatter(x=d["año_proyeccion"], y=d["precio_hpo_m2"], mode="lines",
                                 line=dict(color=TOPE, width=2, dash="dash"), name="Precio máximo HPO (IPC)",
                                 fill="tonexty", fillcolor="rgba(214,69,69,0.12)",
                                 legendgroup="h", showlegend=(idx == 0),
                                 hovertemplate="Año %{x}: %{y:,.0f} €/m²<extra></extra>"), row=row, col=col)
    fig.update_xaxes(title_text="Años desde la compra", gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, ticksuffix=" €")
    fig.update_layout(title="Proyección a 30 años: mercado libre vs. precio máximo HPO por provincia",
                      legend=dict(orientation="h", y=-0.08, x=0))
    return style_fig(fig, height=640)


def fig_b3_brecha():
    df = load("b3_resumen_provincias.csv").set_index("provincia")
    orden = ["Barcelona", "Girona", "Tarragona", "Lleida"]
    df = df.loc[orden].reset_index()
    m2, benef = 65, 50000
    df["brecha_total"] = df["brecha_m2"] * m2
    fig = go.Figure(go.Bar(
        x=df["provincia"], y=df["brecha_total"], width=0.55,
        marker_color=[PROV[p] for p in df["provincia"]],
        text=[f"{v:,.0f} €<br>{v/benef:.1f}× el beneficio" for v in df["brecha_total"]],
        textposition="outside", textfont=dict(color=TEXT, size=12),
        hovertemplate="%{x}: %{y:,.0f} €<extra></extra>"))
    fig.add_hline(y=benef, line=dict(color=NO_CUBIERTO, width=1.6, dash="dash"))
    fig.add_annotation(x=df["provincia"].iloc[-1], y=benef, yshift=15, xanchor="right", showarrow=False,
                       text=f"Beneficio inicial del Préstec: {benef:,.0f} €", font=dict(color=NO_CUBIERTO, size=12))
    fig.update_layout(title=f"Brecha patrimonial a 30 años vs. beneficio del Préstec — vivienda {m2} m²",
                      yaxis_title="€ (vivienda de 65 m²)", showlegend=False)
    fig.update_yaxes(range=[0, df["brecha_total"].max() * 1.2], tickformat="~s", ticksuffix="€")
    return style_fig(fig, height=520)


def fig_b3_sensibilidad():
    cg = load("b3_cagr_provincias.csv").set_index("provincia")
    ipc = float(load("b3_meta.csv")["ipc_medio_historico"].iloc[0])
    base, cagr = cg.loc["Barcelona", "precio_2024"], cg.loc["Barcelona", "cagr"]
    años = list(range(31))
    proj = lambda rate: [base * (1 + rate / 100) ** t for t in años]
    hpo = proj(ipc)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=años, y=hpo, mode="lines", line=dict(color=TOPE, width=2, dash="dash"),
                             name=f"Precio máximo HPO (IPC {ipc:.2f}%)"))
    for nom, rate, color in [("bajo", cagr - 1, "#C9B3DD"), ("base", cagr, "#8E5BAE"), ("alto", cagr + 1, "#5B2A86")]:
        merc = proj(rate)
        b30 = merc[30] - hpo[30]
        fig.add_trace(go.Scatter(x=años, y=merc, mode="lines", line=dict(color=color, width=2.6),
                                 name=f"Escenario {nom} (CAGR {rate:.2f}%) · brecha año 30: {b30:,.0f} €/m²"))
    fig.update_layout(title="Análisis de sensibilidad — Barcelona (3 escenarios de revalorización)",
                      xaxis_title="Años desde la compra", yaxis_title="€/m²",
                      legend=dict(orientation="h", y=-0.18, x=0))
    fig.update_yaxes(ticksuffix=" €")
    return style_fig(fig, height=560)


# ============================== NAVEGACIÓN ==============================
st.sidebar.title("🏠 Acceso a la vivienda")
st.sidebar.caption("Ayudas públicas a la primera vivienda en España y Cataluña")
seccion = st.sidebar.radio(
    "Navegación",
    ["Introducción", "Bloque 1 — Aval ICO", "Bloque 2 — Préstec Emancipació",
     "Bloque 3 — HPO 30 años", "Conclusiones"],
)

if seccion == "Introducción":
    st.title("Acceso a la vivienda en España")
    st.subheader("¿Están las ayudas públicas a la primera vivienda calibradas al mercado real?")
    st.markdown(
        "Análisis de dos programas públicos de acceso a la primera vivienda — el **aval ICO** "
        "(nacional) y el **Préstec Emancipació** (Cataluña) — frente al precio real de mercado.\n\n"
        "- **H1 · Bloque 1:** el tope ICO no cubre el precio real en los mercados más tensionados.\n"
        "- **H2 · Bloque 2:** aunque el Préstec cubre el precio nominal, la hipoteca complementaria "
        "(200.000 €) es inaccesible para perfiles individuales.\n"
        "- **H3 · Bloque 3:** la calificación HPO permanente genera una pérdida patrimonial acumulada "
        "que supera el beneficio inicial del préstamo (50.000 €).\n\n"
        "**Convención de signo:** brecha **negativa = rojo** (problema), **positiva = verde** (bien)."
    )
    with st.expander("Metodología"):
        st.markdown(
            "- **Capacidad de endeudamiento:** modelo hipotecario estándar — tipo 3,25 %, plazo 25 años, "
            "tasa de esfuerzo máx. 35 % sobre ingreso neto (Banco de España), factor neto 0,78. Las parejas "
            "asumen dos salarios medios a tiempo completo (escenario optimista).\n"
            "- **Proyección a 30 años (Bloque 3):** CAGR histórica provincial 2013-2024 como revalorización "
            "del mercado libre; IPC medio histórico (1,95 %) como techo HPO. Determinista, con análisis de "
            "sensibilidad ±1 pp.\n"
            "- **Limitación:** los precios son medias por CCAA/provincia, sin distribución ni percentiles → "
            "la brecha real en mercados tensionados puede estar subestimada."
        )
    with st.expander("Fuentes"):
        st.markdown(
            "Colegio de Registradores (precios de compraventa), Idescat (precios comarcales de Cataluña e "
            "IPC), INE — Encuesta Anual de Estructura Salarial (salarios 25-34 por sexo y CCAA), condiciones "
            "oficiales ICO / ICF."
        )

elif seccion.startswith("Bloque 1"):
    st.header("Bloque 1 — Aval ICO vs. precio de mercado por CCAA")
    st.markdown("**H1:** el tope ICO no cubre el precio real en los mercados más tensionados.")
    año = st.radio("Año de referencia", [2024, 2025], horizontal=True)

    bloque(fig_lollipop_ico(año),
           f"**Brecha tope ICO − precio medio ({año}).**\n\nLa mayoría de CCAA quedan en verde "
           "(el tope cubre el precio medio), pero los mercados tensionados aparecen en rojo: el precio "
           "supera el tope y el aval no llega. La brecha se amplía de 2024 a 2025.")

    bloque(fig_range_ico(año),
           f"**Dispersión provincial vs. tope ICO ({año}).**\n\nCada barra va del precio mínimo al máximo "
           "provincial dentro de la CCAA; el punto hueco es el precio medio y la marca ámbar el tope ICO. "
           "Aun donde la media queda cubierta, la provincia más cara puede superar el tope (rojo).")

    bloque(fig_genero(),
           "**Brecha salarial de género (25-34 años).**\n\nEl salario medio de la mujer (naranja) queda "
           "por debajo del hombre (azul) en casi todas las CCAA. La Rioja y Cantabria no tienen dato "
           "desagregado (diamante gris); Extremadura y P. Asturias usan el salario conjunto (marrón).")

    bloque(fig_capacidad(),
           "**Capacidad financiera por perfil.**\n\nBrecha de acceso (capacidad − precio medio) según el "
           "salario del perfil. En la zona roja (negativa) el perfil no puede financiar la vivienda media. "
           "Los perfiles individuales —y especialmente las mujeres— quedan excluidos en más territorios.")

elif seccion.startswith("Bloque 2"):
    st.header("Bloque 2 — Préstec Emancipació (Cataluña)")
    st.markdown("**H2:** aunque el Préstec cubre el precio nominal, la hipoteca complementaria "
                "(200.000 €) es inaccesible para perfiles individuales.")

    bloque(fig_b2_precio_m2(),
           "**Precio €/m² por provincia.**\n\nEl tope del Préstec (250.000 €) compra muy distinta "
           "superficie según la provincia: pocos m² donde el suelo es caro (Barcelona) y muchos más "
           "donde es barato (Lleida). La etiqueta indica los m² equivalentes al tope.")

    bloque(fig_b2_m2_comarca(),
           "**m² por comarca: extremos vs. media.**\n\nEl promedio provincial esconde fuertes "
           "diferencias internas: con el mismo tope se compran muchos más m² en la comarca más barata "
           "que en la más cara (p. ej. Lluçanès vs. Barcelonès). El tono fuerte es la comarca más barata; "
           "el claro, la más cara.")

    bloque(fig_b2_capacidad_hogar(),
           "**Capacidad financiera por perfil de hogar.**\n\nPara comprar al tope (250.000 €) hace falta "
           "una hipoteca de **200.000 €** (línea de referencia). Los perfiles individuales —mujer y hombre "
           "solos— quedan en la zona roja: su hipoteca máxima no llega. Solo las parejas (dos salarios) "
           "superan el umbral.")

    bloque(fig_b2_dispersion(),
           "**Dispersión comarcal de precio €/m².**\n\nRango de precio entre la comarca más barata y la "
           "más cara de cada provincia; el punto hueco es la media provincial. Muestra cuánta variación "
           "territorial queda oculta tras la media.")

elif seccion.startswith("Bloque 3"):
    st.header("Bloque 3 — Calificación HPO permanente a 30 años")
    st.markdown("**H3:** la calificación HPO permanente genera una pérdida patrimonial acumulada "
                "que supera el beneficio inicial del préstamo (50.000 €).")

    bloque(fig_b3_curvas(),
           "**Proyección a 30 años.**\n\nEl precio de mercado libre crece según la CAGR histórica "
           "(2013-2024) de cada provincia; el precio máximo HPO solo crece con el IPC (1,95 %). El área "
           "roja es la brecha patrimonial: la plusvalía que la vivienda HPO no acumula frente al mercado.")

    bloque(fig_b3_brecha(),
           "**Brecha patrimonial vs. beneficio del préstamo.**\n\nPérdida de plusvalía a 30 años para una "
           "vivienda de **65 m²** (el mínimo que el tope compra en la comarca más cara). La línea roja marca "
           "los 50.000 € de beneficio inicial; la etiqueta indica cuántas veces lo supera cada provincia.")

    bloque(fig_b3_sensibilidad(),
           "**Sensibilidad (Barcelona).**\n\nTres escenarios de revalorización (CAGR −1 pp / base / +1 pp) "
           "frente al techo HPO. La conclusión sobre la magnitud de la brecha depende del ritmo de "
           "revalorización; el análisis acota ese rango.")

elif seccion == "Conclusiones":
    st.header("Conclusiones")
    st.markdown(
        "Los dos programas comparten un mismo punto ciego: **se calibran sobre precios medios, "
        "no sobre el mercado real al que se enfrenta el comprador.**\n\n"
        "- **H1 — Aval ICO:** el tope cubre el precio medio en la mayoría de CCAA, pero **no en los "
        "mercados tensionados** (Madrid, Baleares), donde el precio lo supera y la brecha se amplía.\n"
        "- **H2 — Préstec Emancipació:** aunque el tope cubre el precio nominal, la **hipoteca "
        "complementaria de 200.000 € es inaccesible para perfiles individuales**; solo las parejas con "
        "dos salarios llegan.\n"
        "- **H3 — HPO a 30 años:** la calificación permanente traslada al beneficiario una **pérdida "
        "patrimonial** que, en mercados como Barcelona, **multiplica el beneficio inicial del préstamo**.\n\n"
        "**Limitación:** los precios son medias por CCAA/provincia, sin distribución ni percentiles, por lo "
        "que la brecha real en los mercados más tensionados puede estar **subestimada**."
    )
