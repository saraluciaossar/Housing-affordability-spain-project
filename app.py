from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Paleta semántica del proyecto (coherente con los notebooks)
HOMBRE, MUJER = "#2C6FB0", "#E07B39"
PAREJA_HM, PAREJA_MM, PAREJA_HH = "#7E4DA0", "#D6457F", "#17A2B8"
CUBIERTO, NO_CUBIERTO = "#2E9E5B", "#D64545"
MERCADO, TOPE = "#5A5A66", "#E6A700"
SIN_DATO, CONJUNTO = "#B8BCC4", "#8C6D46"
TEXT, GRID = "#222222", "#E2E5E9"
PROV = {"Barcelona": "#16404D", "Girona": "#2E6E80", "Tarragona": "#6BA3B5", "Lleida": "#A9C5D1"}

DATA = Path(__file__).parent / "Data"
M2_REF = 65  # vivienda de referencia (m²) — mínimo que el tope compra en la comarca más cara

st.set_page_config(page_title="Acceso a la vivienda en España", layout="wide")


@st.cache_data
def load(name):
    return pd.read_csv(DATA / name)


def style_fig(fig, height=460):
    fig.update_layout(
        template="plotly_white", paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color=TEXT, size=13),
        margin=dict(l=10, r=10, t=30, b=10), height=height,
        legend=dict(bgcolor="rgba(255,255,255,0.6)", bordercolor=GRID, borderwidth=1),
        hoverlabel=dict(bgcolor="white", bordercolor=GRID),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, automargin=True)
    return fig


def col_graf_texto(fig, texto_md, key=None, on_select=False):
    col_g, col_t = st.columns([2, 1], gap="large", vertical_alignment="center")
    ev = None
    with col_g:
        if on_select:
            ev = st.plotly_chart(fig, use_container_width=True, key=key, on_select="rerun")
        else:
            st.plotly_chart(fig, use_container_width=True, key=key)
    with col_t:
        st.markdown(texto_md)
    return ev


def selected_y(ev):
    try:
        pts = ev["selection"]["points"]
        return pts[0]["y"] if pts else None
    except (TypeError, KeyError, IndexError):
        return None


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
    fig.update_layout(xaxis_title="Brecha en € (tope ICO − precio medio)",
                      legend=dict(orientation="h", y=-0.14, x=0))
    return style_fig(fig, height=560)


def fig_range_ico():
    df = load("b1_dispersion_provincial.csv")
    df = df[df["año"] == 2024].sort_values("precio_maximo", ascending=False)
    orden = df["comunidad_autonoma"].tolist()
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
                                 showlegend=False, hovertemplate=f"Tope ICO: %{{x:,.0f}} €<extra></extra>"))
    leyenda(fig, [(CUBIERTO, "Máximo provincial cubierto", "circle"),
                  (NO_CUBIERTO, "Máximo provincial supera el tope", "circle"),
                  (MERCADO, "Precio medio CCAA", "circle-open"), (TOPE, "Tope ICO", "line-ns")])
    fig.update_yaxes(categoryorder="array", categoryarray=orden)
    fig.update_layout(xaxis_title="Precio (€)", legend=dict(orientation="h", y=-0.08, x=0))
    fig = style_fig(fig, height=780)
    fig.update_layout(margin=dict(l=10, r=10, t=20, b=80))
    return fig


def fig_genero():
    df = load("b1_salario_genero.csv").sort_values("salario_HyM")
    fig = go.Figure()
    for _, r in df.iterrows():
        y, h, m = r["comunidad_autonoma"], r["salario_H"], r["salario_M"]
        if pd.notna(h) and pd.notna(m):
            brecha = h - m
            fig.add_trace(go.Scatter(x=[min(h, m), max(h, m)], y=[y, y], mode="lines",
                                     line=dict(color=GRID, width=2), showlegend=False, hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=[h], y=[y], mode="markers", marker=dict(color=HOMBRE, size=11),
                                     showlegend=False,
                                     hovertemplate=f"{y} · Hombre: {h:,.0f} €<br>Brecha H−M: {brecha:,.0f} €<extra></extra>"))
            fig.add_trace(go.Scatter(x=[m], y=[y], mode="markers", marker=dict(color=MUJER, size=11),
                                     showlegend=False,
                                     hovertemplate=f"{y} · Mujer: {m:,.0f} €<br>Brecha H−M: {brecha:,.0f} €<extra></extra>"))
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
    fig.update_layout(xaxis_title="Salario bruto anual (€)", legend=dict(orientation="h", y=-0.14, x=0))
    return style_fig(fig, height=560)


def fig_capacidad():
    df = load("b1_capacidad.csv")
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
    fig.update_layout(xaxis_title="Brecha de acceso (€)   ← no puede acceder · puede acceder →",
                      legend=dict(orientation="h", y=-0.14, x=0))
    return style_fig(fig, height=600)


# ============================== BLOQUE 2 ==============================
def fig_b2_precio_m2():
    df = load("b2_provincias.csv").sort_values("precio_m2_2024", ascending=False)
    fig = go.Figure(go.Bar(
        x=df["territorio"], y=df["precio_m2_2024"], width=0.5,
        marker_color=[PROV[p] for p in df["territorio"]],
        text=[f"Tope: {m:.0f} m²" for m in df["tope_m2_2024"]], textposition="outside",
        textfont=dict(color=TEXT, size=12), hovertemplate="%{x}: %{y:,.0f} €/m²<extra></extra>"))
    fig.update_layout(yaxis_title="€/m² (2024)", showlegend=False)
    fig.update_yaxes(range=[0, df["precio_m2_2024"].max() * 1.25], ticksuffix=" €")
    return style_fig(fig, height=470)


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
    fig.add_annotation(x=nec, xref="x", yref="paper", y=1.0, yanchor="bottom", xanchor="center",
                       showarrow=False, text=f"Hipoteca necesaria · {nec:,.0f} €",
                       font=dict(color=TEXT, size=12))
    fig.update_layout(xaxis_title="Hipoteca máxima financiable (€)", showlegend=False)
    fig.update_xaxes(range=[0, max(max(vals), nec) * 1.18], tickformat="~s", ticksuffix="€")
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
                                 hovertemplate=(f"{p}<br>mín {d['comarca_minimo']}: %{{x:,.0f}} €/m²"
                                                f"<br>máx {d['comarca_maximo']}<extra></extra>")))
        fig.add_trace(go.Scatter(x=[media], y=[p], mode="markers", showlegend=False,
                                 marker=dict(color="white", size=11, line=dict(color=PROV[p], width=2)),
                                 hovertemplate=f"{p} · media provincial: %{{x:,.0f}} €/m²<extra></extra>"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Media provincial",
                             marker=dict(color="white", size=10, line=dict(color=MERCADO, width=2))))
    fig.update_yaxes(categoryorder="array", categoryarray=orden[::-1])
    fig.update_layout(xaxis_title="Precio €/m²", legend=dict(orientation="h", y=-0.22, x=0))
    fig.update_xaxes(ticksuffix=" €")
    return style_fig(fig, height=420)


# ============================== BLOQUE 3 ==============================
def fig_b3_curva(provincia, horizonte):
    df = load("b3_proyecciones.csv")
    d = df[(df["provincia"] == provincia) & (df["año_proyeccion"] <= horizonte)].sort_values("año_proyeccion")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["año_proyeccion"], y=d["precio_mercado_m2"], mode="lines",
                             line=dict(color=PROV[provincia], width=2.8), name="Precio mercado libre",
                             hovertemplate="Año %{x}: %{y:,.0f} €/m²<extra></extra>"))
    fig.add_trace(go.Scatter(x=d["año_proyeccion"], y=d["precio_hpo_m2"], mode="lines",
                             line=dict(color=TOPE, width=2, dash="dash"), name="Precio máximo HPO (IPC)",
                             fill="tonexty", fillcolor="rgba(214,69,69,0.12)",
                             hovertemplate="Año %{x}: %{y:,.0f} €/m²<extra></extra>"))
    fig.update_layout(xaxis_title="Años desde la compra", yaxis_title="€/m²",
                      legend=dict(orientation="h", y=-0.16, x=0))
    fig.update_yaxes(ticksuffix=" €")
    return style_fig(fig, height=470)


def _b3_barcelona():
    cg = load("b3_cagr_provincias.csv").set_index("provincia")
    ipc = float(load("b3_meta.csv")["ipc_medio_historico"].iloc[0])
    return cg.loc["Barcelona", "precio_2024"], cg.loc["Barcelona", "cagr"], ipc


def fig_b3_sensibilidad(horizonte):
    base, cagr, ipc = _b3_barcelona()
    años = list(range(horizonte + 1))
    proj = lambda rate: [base * (1 + rate / 100) ** t for t in años]
    hpo = proj(ipc)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=años, y=hpo, mode="lines", line=dict(color=TOPE, width=2, dash="dash"),
                             name=f"Precio máximo HPO (IPC {ipc:.2f}%)"))
    for nom, rate, color in [("bajo", cagr - 1, "#C9B3DD"), ("base", cagr, "#8E5BAE"), ("alto", cagr + 1, "#5B2A86")]:
        fig.add_trace(go.Scatter(x=años, y=proj(rate), mode="lines", line=dict(color=color, width=2.6),
                                 name=f"Escenario {nom} (CAGR {rate:.2f}%)",
                                 hovertemplate="Año %{x}: %{y:,.0f} €/m²<extra></extra>"))
    fig.update_layout(xaxis_title="Años desde la compra", yaxis_title="€/m²",
                      legend=dict(orientation="h", y=-0.18, x=0))
    fig.update_yaxes(ticksuffix=" €")
    return style_fig(fig, height=520)


def b3_brecha_escenarios(horizonte):
    base, cagr, ipc = _b3_barcelona()
    hpo = base * (1 + ipc / 100) ** horizonte
    return {nom: (base * (1 + rate / 100) ** horizonte - hpo) * M2_REF
            for nom, rate in [("Bajo", cagr - 1), ("Base", cagr), ("Alto", cagr + 1)]}


# ============================== APP ==============================
st.title("Acceso a la vivienda en España")
st.markdown(
    "<p style='font-size:1.5rem; color:#555; font-weight:400; margin-top:-0.6rem;'>"
    "¿Están las ayudas públicas a la primera vivienda calibradas al mercado real?</p>",
    unsafe_allow_html=True)

tab_intro, tab1, tab2, tab3, tab_concl = st.tabs(
    ["Introducción", "Bloque 1 — Aval ICO", "Bloque 2 — Préstec Emancipació",
     "Bloque 3 — HPO 30 años", "Conclusiones e insights"])

# ------------------------------ Introducción ------------------------------
with tab_intro:
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(
            "Este proyecto evalúa si dos programas públicos de acceso a la primera vivienda están bien "
            "calibrados al mercado real.\n\n"
            "**Aval ICO** (nacional) — el Estado avala hasta el 20 % de la hipoteca para que jóvenes y "
            "familias compren su primera vivienda sin ahorro previo para la entrada, hasta un tope de "
            "precio por CCAA.  \n"
            "🔗 [Línea de avales ICO](https://www.ico.es/linea-avales-hipoteca-primera-vivienda)\n\n"
            "**Préstec Emancipació** (Cataluña, ICF) — préstamo que cubre el 20 % de la entrada (máx. "
            "50.000 €) para vivienda de hasta 250.000 €; el 80 % restante se financia con hipoteca "
            "bancaria convencional.  \n"
            "🔗 [ICF Habitatge Emancipació](https://www.icf.cat/es/prestecs/habitatge/icf-habitatge-emancipacio)\n\n"
            "**Las tres hipótesis:**\n"
            "- **H1 · Bloque 1:** el tope ICO no cubre el precio real en los mercados más tensionados.\n"
            "- **H2 · Bloque 2:** la hipoteca complementaria (200.000 €) es inaccesible para perfiles "
            "individuales.\n"
            "- **H3 · Bloque 3:** la calificación HPO permanente genera una pérdida patrimonial que supera "
            "el beneficio inicial del préstamo (50.000 €).\n\n"
            "**Convención de signo:** brecha **negativa = rojo** (problema), **positiva = verde** (bien)."
        )
        st.subheader("Metodología")
        st.markdown(
            "- **Capacidad de endeudamiento:** modelo hipotecario estándar — tipo 3,25 %, plazo 25 años, "
            "tasa de esfuerzo máx. 35 % sobre ingreso neto (Banco de España), factor neto 0,78. Las parejas "
            "asumen dos salarios medios a tiempo completo (escenario optimista).\n"
            "- **Proyección a 30 años (Bloque 3):** CAGR histórica provincial 2013-2024 como revalorización "
            "del mercado libre; IPC medio histórico como techo HPO. Determinista, con sensibilidad ±1 pp.\n"
            "- **Limitación:** los precios son medias por CCAA/provincia, sin distribución ni percentiles → "
            "la brecha real en mercados tensionados puede estar subestimada."
        )
        st.subheader("Fuentes")
        st.markdown(
            "- [Colegio de Registradores — compraventas de inmuebles uso residencial por provincia]"
            "(https://opendata.registradores.org/dataset/dataset/compraventas-de-inmuebles-uso-residencial-por-provincia/resource/b779dd2c-db5c-4771-9a50-571bf04ecb15)\n"
            "- [Idescat — preu mitjà de venda d'habitatges (comarques i províncies)]"
            "(https://www.idescat.cat/indicadors/?id=aec&n=15707)\n"
            "- [Idescat — IPC](https://www.idescat.cat/indicadors/?id=basics&n=10261)\n"
            "- [INE — Encuesta Anual de Estructura Salarial](https://www.ine.es) (salarios 25-34 por sexo y CCAA)\n"
            "- [ICO — precios máximos por CCAA (PDF oficial)]"
            "(https://www.ico.es/documents/20124/777320/Precios+maximos+CCAA-+avales-jovenes-familias.pdf/ecedf846-95a6-66d4-99f4-4941e5bec442?t=1715080874074)"
        )

# ------------------------------ Bloque 1 ------------------------------
with tab1:
    st.caption("H1: el tope ICO no cubre el precio real en los mercados más tensionados.")
    año = st.radio("Año de referencia (cobertura ICO)", [2024, 2025], horizontal=True, key="b1_año")
    bsel = load("b1_brecha_ico.csv").query("año == @año")
    peor = bsel.loc[bsel["brecha_ico"].idxmin()]
    m1, m2 = st.columns(2)
    m1.metric(f"CCAA donde el tope no cubre ({año})", f"{int((bsel['brecha_ico'] < 0).sum())} de {len(bsel)}")
    m2.metric("Mayor brecha negativa", f"{peor['brecha_ico']:,.0f} €", peor["comunidad_autonoma"],
              delta_color="off")
    st.divider()

    st.markdown("##### Brecha entre tope ICO y precio medio por CCAA")
    col_graf_texto(
        fig_lollipop_ico(año),
        f"En **{año}**, la mayoría de CCAA quedan en verde (el tope cubre el precio medio), pero los "
        "mercados tensionados aparecen en rojo: el precio supera el tope y el aval no llega. La brecha "
        "se amplía de 2024 a 2025.", key=f"loll_{año}")
    st.divider()

    st.markdown("##### Dispersión provincial de precios vs. tope ICO (2024)")
    st.markdown(
        "Cada barra va del precio mínimo al máximo provincial dentro de la CCAA; el punto hueco es el "
        "precio medio y la marca ámbar el tope ICO. Aun donde la media queda cubierta, la provincia más "
        "cara puede superar el tope (rojo). **Madrid y Baleares, abajo, son los casos más tensionados.**")
    st.plotly_chart(fig_range_ico(), use_container_width=True, key="range24")
    st.divider()

    st.markdown("##### Salario medio por sexo y CCAA (2024)")
    st.caption("Pasa el cursor sobre los círculos para ver el salario y la brecha entre hombres y mujeres.")
    ev = col_graf_texto(
        fig_genero(),
        "El salario medio de la mujer (naranja) queda por debajo del hombre (azul) en casi todas las CCAA. "
        "La Rioja y Cantabria no tienen dato desagregado (diamante gris); Extremadura y P. Asturias usan el "
        "salario conjunto (marrón).", key="genero", on_select=True)
    sel = selected_y(ev)
    if sel:
        g = load("b1_salario_genero.csv")
        row = g[g["comunidad_autonoma"] == sel]
        if not row.empty:
            row = row.iloc[0]
            st.markdown(f"**{sel}**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Salario hombre", f"{row['salario_H']:,.0f} €" if pd.notna(row["salario_H"]) else "—")
            c2.metric("Salario mujer", f"{row['salario_M']:,.0f} €" if pd.notna(row["salario_M"]) else "—")
            if pd.notna(row["salario_H"]) and pd.notna(row["salario_M"]):
                brecha = row["salario_H"] - row["salario_M"]
                c3.metric("Brecha (H − M)", f"{brecha:,.0f} €", f"{brecha / row['salario_H'] * 100:.1f} %",
                          delta_color="off")
            else:
                c3.metric("Brecha (H − M)", "sin dato")
    st.divider()

    st.markdown(
        "Para estimar si cada perfil puede acceder a la hipoteca, se aplicó un modelo estándar de capacidad "
        "de endeudamiento: tipo de interés 3,25 % anual, plazo 25 años, tasa de esfuerzo máxima del 35 % "
        "sobre ingresos netos (criterio del Banco de España). El salario bruto se convierte a neto aplicando "
        "un factor de 0,78. La hipoteca máxima financiable resulta de la fórmula de anualidad: cuota mensual "
        "máxima × factor de descuento del préstamo. Para las parejas se suman los dos salarios medios del "
        "tramo 25–34 años (escenario optimista: ambos a tiempo completo)."
    )
    st.markdown("##### Capacidad financiera por CCAA y perfil (2024)")
    col_graf_texto(
        fig_capacidad(),
        "Brecha de acceso (capacidad − precio medio) según el salario del perfil. En la zona roja "
        "(negativa) el perfil no puede financiar la vivienda media. Marcadores: círculo = individual, "
        "rombo = Pareja HM, cuadrado = Pareja MM, triángulo = Pareja HH.", key="capacidad")

# ------------------------------ Bloque 2 ------------------------------
with tab2:
    st.caption("H2: aunque el Préstec cubre el precio nominal, la hipoteca complementaria (200.000 €) "
               "es inaccesible para perfiles individuales.")
    p = load("b2_provincias.csv")
    hip_m, hip_h = p["hipoteca_max_M"].iloc[0], p["hipoteca_max_H"].iloc[0]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tope del Préstec", "250.000 €")
    m2.metric("Hipoteca necesaria", "200.000 €")
    m3.metric("Mujer sola alcanza", f"{hip_m:,.0f} €".replace(",", "."),
              f"{hip_m - 200000:,.0f} € por debajo del mínimo necesario".replace(",", "."))
    m4.metric("Hombre solo alcanza", f"{hip_h:,.0f} €".replace(",", "."),
              f"{hip_h - 200000:,.0f} € por debajo del mínimo necesario".replace(",", "."))
    st.divider()

    st.markdown("##### Precio €/m² por provincia y m² equivalentes al tope")
    col_graf_texto(
        fig_b2_precio_m2(),
        "El tope del Préstec (250.000 €) compra muy distinta superficie según la provincia: pocos m² "
        "donde el suelo es caro (Barcelona) y muchos más donde es barato (Lleida).", key="b2precio")
    st.divider()

    st.markdown("##### Capacidad financiera por perfil de hogar")
    col_graf_texto(
        fig_b2_capacidad_hogar(),
        "Para comprar al tope hace falta una hipoteca de **200.000 €** (línea de referencia). Los perfiles "
        "individuales quedan en la zona roja: su hipoteca máxima no llega. Solo las parejas (dos salarios) "
        "superan el umbral.\n\n"
        "_Nota metodológica: la capacidad de endeudamiento de las parejas se calcula asumiendo que ambas "
        "personas perciben el salario medio del tramo 25–34 años reportado por el INE y trabajan a tiempo "
        "completo. Es el escenario optimista._", key="b2cap")
    st.divider()

    st.markdown("##### Dispersión de precio €/m² por comarca")
    st.caption("Pasa el cursor sobre los puntos para ver el precio mínimo y máximo de cada provincia y las "
               "comarcas en esos extremos.")
    ev = col_graf_texto(
        fig_b2_dispersion(),
        "Rango de precio entre la comarca más barata y la más cara de cada provincia; el punto hueco es la "
        "media provincial.", key="b2disp", on_select=True)
    sel = selected_y(ev)
    if sel:
        d = load("b2_dispersion_comarcas.csv")
        d = d[d["provincia"] == sel]
        if not d.empty:
            d = d.iloc[0]
            media = p.loc[p["territorio"] == sel, "precio_m2_2024"].values[0]
            st.markdown(f"**{sel}**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Precio medio provincial", f"{media:,.0f} €/m²")
            c2.metric(f"Máximo · {d['comarca_maximo']}", f"{d['precio_maximo']:,.0f} €/m²")
            c3.metric(f"Mínimo · {d['comarca_minimo']}", f"{d['precio_minimo']:,.0f} €/m²")

# ------------------------------ Bloque 3 ------------------------------
with tab3:
    cg = load("b3_cagr_provincias.csv").set_index("provincia")
    ipc = float(load("b3_meta.csv")["ipc_medio_historico"].iloc[0])
    res = load("b3_resumen_provincias.csv").set_index("provincia")

    st.caption("H3: la calificación HPO permanente genera una pérdida patrimonial acumulada que supera "
               "el beneficio inicial del préstamo (50.000 €).")
    st.markdown(
        "La proyección usa la **CAGR** (Compound Annual Growth Rate) histórica provincial del período "
        "2013–2024 como tasa de revalorización del mercado libre, y el IPC medio histórico del mismo "
        f"período (**{ipc:.2f} % anual**) como techo de revalorización del precio máximo HPO.\n\n"
        "**Fórmula aplicada:**\n"
        "- Precio mercado año *n* = Precio₀ × (1 + CAGR)ⁿ\n"
        "- Precio HPO año *n* = Precio₀ × (1 + IPC)ⁿ\n"
        "- Brecha año *n* = (Precio mercado − Precio HPO) × 65 m²\n\n"
        "Se usa **65 m²** como superficie de referencia porque es el tamaño mínimo que se podría adquirir "
        "hoy al precio medio de la provincia de Barcelona con el tope del Préstec (250.000 €). Los "
        "resultados se expresan en euros totales para esa vivienda tipo."
    )
    st.divider()

    st.markdown("##### Proyección a 30 años: mercado libre vs. precio máximo HPO")
    c_prov, c_hor = st.columns([1, 2])
    provincia = c_prov.selectbox("Provincia", ["Barcelona", "Girona", "Tarragona", "Lleida"], key="b3prov")
    horizonte = c_hor.select_slider("Horizonte (años)", options=[5, 10, 15, 20, 25, 30], value=30, key="b3hor")

    k1, k2, k3 = st.columns(3)
    k1.metric("IPC medio (techo HPO)", f"{ipc:.2f} %")
    k2.metric(f"CAGR {provincia} (mercado)", f"{cg.loc[provincia, 'cagr']:.2f} %")
    k3.metric(f"Brecha {provincia} · 30 a. ({M2_REF} m²)",
              f"{res.loc[provincia, 'brecha_m2'] * M2_REF:,.0f} €")

    col_graf_texto(
        fig_b3_curva(provincia, horizonte),
        "El mercado libre crece según la CAGR histórica de la provincia; el precio máximo HPO solo crece "
        "con el IPC. El área roja es la brecha patrimonial: la plusvalía que la vivienda HPO no acumula "
        "frente al mercado.", key=f"b3curva_{provincia}_{horizonte}")
    st.divider()

    st.markdown("##### Análisis de sensibilidad — Barcelona")
    hor_s = st.select_slider("Horizonte (años)", options=[5, 10, 15, 20, 25, 30], value=30, key="b3sens_hor")
    esc = b3_brecha_escenarios(hor_s)
    cA, cB, cC = st.columns(3)
    cA.metric(f"Escenario bajo · {hor_s} a.", f"{esc['Bajo']:,.0f} €", f"vivienda {M2_REF} m²", delta_color="off")
    cB.metric(f"Escenario base · {hor_s} a.", f"{esc['Base']:,.0f} €", f"vivienda {M2_REF} m²", delta_color="off")
    cC.metric(f"Escenario alto · {hor_s} a.", f"{esc['Alto']:,.0f} €", f"vivienda {M2_REF} m²", delta_color="off")
    col_graf_texto(
        fig_b3_sensibilidad(hor_s),
        "Tres escenarios de revalorización (CAGR −1 pp / base / +1 pp) frente al techo HPO. Las tarjetas "
        f"muestran la brecha patrimonial acumulada al año {hor_s} para una vivienda de {M2_REF} m².",
        key=f"b3sens_{hor_s}")

# ------------------------------ Conclusiones e insights ------------------------------
with tab_concl:
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown(
            "Los tres bloques apuntan al mismo diagnóstico: **ambos programas trasladan al individuo riesgos "
            "que son de naturaleza estructural.**\n\n"
            "**H1 — Aval ICO:** el tope cubre el precio medio en **17 de 19** comunidades autónomas, pero "
            "falla exactamente donde más importa: **Madrid e Illes Balears**, los mercados más tensionados. "
            "Sus topes estáticos no se actualizan con el mercado — la brecha se amplía año a año.\n\n"
            "**H2 — Préstec Emancipació:** el tope de 250.000 € cubre el precio nominal en las cuatro "
            "provincias catalanas, pero el programa exige una hipoteca complementaria de 200.000 €. Con los "
            "salarios medios del tramo 25–34 años, **ningún perfil individual — ni hombre ni mujer — puede "
            "financiarla**. Solo las parejas con dos salarios llegan.\n\n"
            "**H3 — Calificación HPO permanente:** quien accede al Préstec asume una pérdida patrimonial "
            "acumulada a 30 años que en Barcelona **supera los 232.000 € para una vivienda de 65 m² — 4,6 "
            "veces el beneficio inicial** del préstamo. En el escenario más conservador (CAGR −1 pp), la "
            "pérdida sigue siendo de 89.000 €. La HPO permanente hace que el beneficiario pague el coste de "
            "mantener el stock de vivienda asequible durante toda su vida hipotecaria."
        )
        st.subheader("Tres recomendaciones")
        st.markdown(
            "1. **Actualizar los topes del ICO anualmente** con referencia a precios de mercado real y con "
            "mayor granularidad geográfica — idealmente provincial.\n"
            "2. **Incorporar un criterio de viabilidad financiera mínima** en ambos programas: no solo un "
            "tope máximo de ingresos, sino una capacidad de endeudamiento verificada sobre la hipoteca "
            "complementaria.\n"
            "3. **Sustituir la calificación HPO permanente** por fórmulas temporales o mecanismos de "
            "compensación de plusvalía que preserven la accesibilidad sin transferir al individuo el coste "
            "del mantenimiento del parque asequible."
        )
        st.subheader("Línea de análisis futura")
        st.markdown(
            "Estos programas están diseñados para menores de 35 años — el Préstec amplió recientemente el "
            "límite hasta los 40. Sin embargo, según datos de Idealista, la edad media de firma de hipoteca "
            "en España ronda los 40 años. Esto sugiere que el **perfil objetivo del programa puede no "
            "coincidir con el perfil real del mercado** — una hipótesis que abre una línea de trabajo "
            "relevante."
        )
        st.subheader("Relevancia para el sector privado")
        st.markdown(
            "- **Fintechs hipotecarias:** los perfiles individuales que no acceden al ICO ni al Préstec son "
            "clientes potenciales para productos hipotecarios alternativos.\n"
            "- **Fondos de inversión en vivienda asequible:** el modelo de brecha patrimonial HPO es el tipo "
            "de análisis que usan para valorar activos regulados.\n"
            "- **Consultoras inmobiliarias:** saber qué mercados no están cubiertos por el programa público "
            "define dónde hay demanda embalsada sin cobertura.\n"
            "- **Administraciones públicas:** el análisis identifica exactamente dónde fallan los programas y "
            "propone correcciones concretas."
        )
