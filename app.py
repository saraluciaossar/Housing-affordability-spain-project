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

st.set_page_config(page_title="Acceso a la vivienda en España", page_icon="🏠", layout="wide")


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
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


def col_graf_texto(fig, texto_md, key=None, on_select=False):
    """Layout estándar: gráfica a la izquierda, texto a la derecha. Devuelve evento de selección."""
    col_g, col_t = st.columns([2, 1], gap="large")
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
    fig.update_layout(xaxis_title="Precio (€)", legend=dict(orientation="h", y=-0.14, x=0))
    return style_fig(fig, height=560)


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


def fig_b2_m2_comarca():
    prov = load("b2_provincias.csv")
    disp = load("b2_dispersion_comarcas.csv").set_index("provincia")
    tope = prov["tope_vivienda"].iloc[0]
    orden = prov.sort_values("precio_m2_2024", ascending=False)["territorio"].tolist()
    fig = go.Figure()
    for p in orden:
        d = disp.loc[p]
        m2_mas, m2_menos = tope / d["precio_minimo"], tope / d["precio_maximo"]
        media = prov.loc[prov["territorio"] == p, "tope_m2_2024"].values[0]
        fig.add_trace(go.Scatter(x=[m2_menos, m2_mas], y=[p, p], mode="lines",
                                 line=dict(color=PROV[p], width=3), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=[m2_menos], y=[p], mode="markers+text",
                                 marker=dict(color=PROV[p], size=13, opacity=0.45),
                                 text=[f"{d['comarca_maximo']} · {m2_menos:.0f} m²"], textposition="bottom center",
                                 textfont=dict(size=10, color=TEXT), showlegend=False,
                                 hovertemplate=f"{p} · {d['comarca_maximo']} (más cara): {m2_menos:.0f} m²<extra></extra>"))
        fig.add_trace(go.Scatter(x=[m2_mas], y=[p], mode="markers+text",
                                 marker=dict(color=PROV[p], size=14),
                                 text=[f"{d['comarca_minimo']} · {m2_mas:.0f} m²"], textposition="top center",
                                 textfont=dict(size=10, color=TEXT), showlegend=False,
                                 hovertemplate=f"{p} · {d['comarca_minimo']} (más barata): {m2_mas:.0f} m²<extra></extra>"))
        fig.add_trace(go.Scatter(x=[media], y=[p], mode="markers",
                                 marker=dict(symbol="line-ns", color=TEXT, size=15, line=dict(width=2, color=TEXT)),
                                 showlegend=False, hovertemplate=f"{p} · media provincial: {media:.0f} m²<extra></extra>"))
    leyenda(fig, [(MERCADO, "Comarca más barata (más m²)", "circle"),
                  ("rgba(90,90,102,0.45)", "Comarca más cara (menos m²)", "circle"),
                  (TEXT, "Media provincial", "line-ns")])
    fig.update_yaxes(categoryorder="array", categoryarray=orden[::-1])
    fig.update_layout(xaxis_title="m² comprables con el tope (250.000 €)",
                      legend=dict(orientation="h", y=-0.16, x=0))
    fig.update_xaxes(range=[0, prov["tope_vivienda"].iloc[0] / disp["precio_minimo"].min() * 1.15])
    return style_fig(fig, height=460)


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
                                 hovertemplate=(f"{p}<br>{d['comarca_minimo']}: %{{x:,.0f}} €/m²"
                                                f"<br>{d['comarca_maximo']}<extra></extra>")))
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
    out = {}
    for nom, rate in [("Bajo", cagr - 1), ("Base", cagr), ("Alto", cagr + 1)]:
        out[nom] = (base * (1 + rate / 100) ** horizonte - hpo) * M2_REF
    return out


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
    st.write("")
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
    st.write("")
    with st.expander("Metodología"):
        st.markdown(
            "- **Capacidad de endeudamiento:** modelo hipotecario estándar — tipo 3,25 %, plazo 25 años, "
            "tasa de esfuerzo máx. 35 % sobre ingreso neto (Banco de España), factor neto 0,78. Las parejas "
            "asumen dos salarios medios a tiempo completo (escenario optimista).\n"
            "- **Proyección a 30 años (Bloque 3):** CAGR histórica provincial 2013-2024 como revalorización "
            "del mercado libre; IPC medio histórico (1,95 %) como techo HPO. Determinista, con sensibilidad ±1 pp.\n"
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
    st.header("Bloque 1 — Aval ICO")
    st.caption("H1: el tope ICO no cubre el precio real en los mercados más tensionados.")

    b24 = load("b1_brecha_ico.csv").query("año == 2024")
    cap = load("b1_capacidad.csv")
    peor = b24.loc[b24["brecha_ico"].idxmin()]
    m1, m2, m3 = st.columns(3)
    m1.metric("CCAA donde el tope no cubre (2024)", f"{int((b24['brecha_ico'] < 0).sum())} de {len(b24)}")
    m2.metric("Mayor brecha negativa", f"{peor['brecha_ico']:,.0f} €", peor["comunidad_autonoma"],
              delta_color="off")
    m3.metric("Mujer sola sin acceso", f"{int((cap['brecha_acceso_M'] < 0).sum())} de "
              f"{int(cap['brecha_acceso_M'].notna().sum())} CCAA")
    st.divider()

    st.markdown("##### Brecha entre tope ICO y precio medio por CCAA")
    año = st.radio("Año", [2024, 2025], horizontal=True, key="b1_año")
    col_graf_texto(
        fig_lollipop_ico(año),
        f"En **{año}**, la mayoría de CCAA quedan en verde (el tope cubre el precio medio), pero los "
        "mercados tensionados aparecen en rojo: el precio supera el tope y el aval no llega. La brecha "
        "se amplía de 2024 a 2025.", key=f"loll_{año}")
    st.divider()

    st.markdown("##### Dispersión provincial de precios vs. tope ICO (2024)")
    col_graf_texto(
        fig_range_ico(),
        "Cada barra va del precio mínimo al máximo provincial dentro de la CCAA; el punto hueco es el "
        "precio medio y la marca ámbar el tope ICO. Aun donde la media queda cubierta, la provincia más "
        "cara puede superar el tope (rojo). Madrid y Baleares, abajo, son los casos más tensionados.",
        key="range24")
    st.divider()

    st.markdown("##### Salario medio por sexo y CCAA (2024)")
    st.caption("Haz clic en una CCAA para ver el detalle.")
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

    st.markdown("##### Capacidad financiera por CCAA y perfil (2024)")
    col_graf_texto(
        fig_capacidad(),
        "Brecha de acceso (capacidad − precio medio) según el salario del perfil. En la zona roja "
        "(negativa) el perfil no puede financiar la vivienda media. Marcadores: círculo = individual, "
        "rombo = Pareja HM, cuadrado = Pareja MM, triángulo = Pareja HH.", key="capacidad")

elif seccion.startswith("Bloque 2"):
    st.header("Bloque 2 — Préstec Emancipació (Cataluña)")
    st.caption("H2: aunque el Préstec cubre el precio nominal, la hipoteca complementaria (200.000 €) "
               "es inaccesible para perfiles individuales.")

    p = load("b2_provincias.csv")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tope del Préstec", "250.000 €")
    m2.metric("Hipoteca necesaria", "200.000 €")
    m3.metric("Mujer sola alcanza", f"{p['hipoteca_max_M'].iloc[0]:,.0f} €",
              f"{p['hipoteca_max_M'].iloc[0] - 200000:,.0f} € vs. necesaria", delta_color="normal")
    m4.metric("Hombre solo alcanza", f"{p['hipoteca_max_H'].iloc[0]:,.0f} €",
              f"{p['hipoteca_max_H'].iloc[0] - 200000:,.0f} € vs. necesaria", delta_color="normal")
    st.divider()

    st.markdown("##### Precio €/m² por provincia y m² equivalentes al tope")
    col_graf_texto(
        fig_b2_precio_m2(),
        "El tope del Préstec (250.000 €) compra muy distinta superficie según la provincia: pocos m² "
        "donde el suelo es caro (Barcelona) y muchos más donde es barato (Lleida).", key="b2precio")
    st.divider()

    st.markdown("##### m² que compra el tope: comarca más barata vs. más cara")
    col_graf_texto(
        fig_b2_m2_comarca(),
        "El promedio provincial esconde fuertes diferencias internas: con el mismo tope se compran muchos "
        "más m² en la comarca más barata (punto sólido) que en la más cara (punto claro). La marca vertical "
        "es la media provincial.", key="b2m2")
    st.divider()

    st.markdown("##### Capacidad financiera por perfil de hogar")
    col_graf_texto(
        fig_b2_capacidad_hogar(),
        "Para comprar al tope hace falta una hipoteca de **200.000 €** (línea de referencia). Los perfiles "
        "individuales quedan en la zona roja: su hipoteca máxima no llega. Solo las parejas (dos salarios) "
        "superan el umbral.", key="b2cap")
    st.divider()

    st.markdown("##### Dispersión de precio €/m² por comarca")
    st.caption("Pasa el cursor para ver el precio; haz clic en una provincia para ver su detalle.")
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

elif seccion.startswith("Bloque 3"):
    st.header("Bloque 3 — Calificación HPO a 30 años")
    st.caption("H3: la calificación HPO permanente genera una pérdida patrimonial acumulada que supera "
               "el beneficio inicial del préstamo (50.000 €).")

    cg = load("b3_cagr_provincias.csv").set_index("provincia")
    ipc = float(load("b3_meta.csv")["ipc_medio_historico"].iloc[0])
    res = load("b3_resumen_provincias.csv").set_index("provincia")
    m1, m2, m3 = st.columns(3)
    m1.metric("IPC medio (techo HPO)", f"{ipc:.2f} %")
    m2.metric("CAGR Barcelona (mercado)", f"{cg.loc['Barcelona', 'cagr']:.2f} %")
    m3.metric(f"Brecha Barcelona · 30 a. ({M2_REF} m²)",
              f"{res.loc['Barcelona', 'brecha_m2'] * M2_REF:,.0f} €")
    st.divider()

    st.markdown("##### Proyección a 30 años: mercado libre vs. precio máximo HPO")
    c_prov, c_hor = st.columns([1, 2])
    provincia = c_prov.selectbox("Provincia", ["Barcelona", "Girona", "Tarragona", "Lleida"], key="b3prov")
    horizonte = c_hor.select_slider("Horizonte (años)", options=[5, 10, 15, 20, 25, 30], value=30, key="b3hor")
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
