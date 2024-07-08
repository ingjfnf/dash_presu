import io
from babel.dates import format_date
import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime
import warnings
import emoji
warnings.filterwarnings('ignore')

st.set_page_config(page_title="PLANNING & REPORTING!!!", page_icon=":bar_chart:", layout="wide")

# URL de la imagen del logo en GitHub
logo_url = "https://raw.githubusercontent.com/ingjfnf/dash_presu/main/logo.jpg"


# Inicializamos el estado de sesión
if 'show_dataframe' not in st.session_state:
    st.session_state.show_dataframe = False


def generate_scroller_html(df):
    items = []
    for index, row in df.iterrows():
        if row['VARIACION'] < 0:
            items.append(f"<span>{row['CONCEPTO']} <span style='color:red;'>&#9660;</span> {row['VARIACION']}% &nbsp;&nbsp;&nbsp;&nbsp;</span>")
        else:
            items.append(f"<span>{row['CONCEPTO']} <span style='color:green;'>&#9650;</span> {row['VARIACION']}% &nbsp;&nbsp;&nbsp;&nbsp;</span>")
    
    items_html = ''.join(items)
    items_html_double = items_html + items_html  # Duplicamos los elementos para el scroller continuo
    
    
    html_content = f"""
    <div id="scroller" style="white-space: nowrap; overflow: hidden; width: 92.5%; height: 37px; position: fixed;background-color: white; 
    color: black; z-index: 2000; display: flex; align-items: center;">
        <div id="scrolling-text" style="display: inline-block;">
            {items_html_double}
        </div>
    </div>
    <hr class="scroller-divider">
    <style>
    #scroller {{
        overflow: hidden;
        position: relative;
        margin-bottom: 0px;  /* Asegúrate de que no haya margen debajo del scroller */
        display: flex;
        align-items: center;
    }}
    #scrolling-text {{
        display: inline-block;
        white-space: nowrap;
        position: relative;
        animation: scroll 110s linear infinite;
        font-weight: bold;
        padding: 0 10px;
    }}
    @keyframes scroll {{
        0% {{ transform: translateX(0); }}
        100% {{ transform: translateX(-50%); }}
    }}
    .scroller-divider {{
        border: 0;
        height: 1px;
        background: #444;
        margin-top: 0;  /* Sin margen superior */
        margin-bottom: 2rem;  /* Puedes ajustar el margen inferior si necesitas más espacio antes del siguiente contenido */
    }}
    #scroller:hover #scrolling-text {{
        animation-play-state: paused;
    }}
    </style>
    """
    
    return html_content


# Función para transformar los datos
def arreglos(preclosing_df, simulacion_df, actual, historico_df):
    preclosing_df['PRESUPUESTO'] = preclosing_df['PRESUPUESTO'].fillna(0).round().astype('int64')
    preclosing_df = preclosing_df.rename(columns={"PRESUPUESTO": "VALOR"})
    preclosing_df["ANALISIS"] = "BUDGET"

    simulacion_df['VALOR'] = simulacion_df['VALOR'].fillna(0).round().astype('int64')
    simulacion_df["ANALISIS"] = "FORECAST"

    actual_tendencia = actual[["FECHA", "CONCEPTO", "EJECUCIÓN"]].rename(columns={"EJECUCIÓN": "VALOR"})
    actual_tendencia["ANALISIS"] = "ACTUAL"

    historico_df = historico_df.rename(columns={"EJECUCIÓN": "VALOR"})
    historico_df['FECHA'] = pd.to_datetime(historico_df['FECHA'], dayfirst=True)
    historico_df['AÑO'] = historico_df['FECHA'].dt.year
    dataframes_por_año = {año: historico_df[historico_df['AÑO'] == año].reset_index(drop=True) for año in historico_df['AÑO'].unique()}

    for año, df in dataframes_por_año.items():
        df["ANALISIS"] = f"Historico_{año}"
        df.drop(columns="AÑO", inplace=True)

    preclosing_df['FECHA'] = pd.to_datetime(preclosing_df['FECHA'], dayfirst=True)
    simulacion_df['FECHA'] = pd.to_datetime(simulacion_df['FECHA'], dayfirst=True)
    actual_tendencia['FECHA'] = pd.to_datetime(actual_tendencia['FECHA'], dayfirst=True)

    conjunto_total = pd.concat([preclosing_df, simulacion_df, actual_tendencia] + list(dataframes_por_año.values()))
    return conjunto_total

def format_currency(value):
    if isinstance(value, (int, float)):
        return f"${value:,.0f}".replace(",", ".").replace("$", "$ ")
    return value

def format_percentage(value):
    return f"{value:.2f}%"


def style_dataframe(df):
    df_formatted = df.copy()
    for col in df.columns:
        if col not in ['PORCENTAJE_ACUMULADO', 'FECHA_MAX_DIFF']:
            df_formatted[col] = df_formatted[col].apply(format_currency)
        elif col == 'PORCENTAJE_ACUMULADO':
            df_formatted[col] = df_formatted[col].apply(format_percentage)
    
    styled_df = df_formatted.style.set_table_styles(
        [
            {
                'selector': 'th',
                'props': [('background-color', '#1F77B4'), ('color', 'white'), ('font-size', "14px"), ('text-align', 'center')]
            },
            {
                'selector': 'td',
                'props': [('font-size', "12px"), ('text-align', 'center'), ('white-space', 'nowrap')]
            },
            {
                'selector': 'td.col0',
                'props': [('font-weight', 'bold')]
            }
        ]
    ).set_properties(**{'border': '1px solid white','width': '70px'})
    
    return styled_df


def style_dataframe_filtered(df):
    df_formatted = df.copy()
    for col in df.columns:
        if col == 'VALOR':
            df_formatted[col] = df_formatted[col].apply(format_currency)
    
    styled_df = df_formatted.style.set_table_styles(
        [
            {
                'selector': 'th',
                'props': [('background-color', '#1F77B4'), ('color', 'white'), ('font-size', '14px'), ('text-align', 'center')]
            },
            {
                'selector': 'td',
                'props': [('font-size', '12px'), ('text-align', 'center'), ('white-space', 'nowrap')]
            },
            {
                'selector': 'td.col0',
                'props': [('font-weight', 'bold')]
            }
        ]
    ).set_properties(**{'border': '1px solid white', 'width': '70px'})
    
    return styled_df


def style_tabla_filtro(df):
    df_formatted = df.copy()
    for col in df.columns:
        if col != 'CONCEPTO' or col != 'MES':
            df_formatted[col] = df_formatted[col].apply(format_currency)
    
    styled_df = df_formatted.style.set_table_styles(
        [
            {
                'selector': 'th',
                'props': [('background-color', '#1F77B4'), ('color', 'white'), ('font-size', '14px'), ('text-align', 'center')]
            },
            {
                'selector': 'td',
                'props': [('font-size', '12px'), ('text-align', 'center'), ('white-space', 'nowrap')]
            },
            {
                'selector': 'td.col0',
                'props': [('font-weight', 'bold')]
            }
        ]
    ).set_properties(**{'border': '1px solid white', 'width': '70px'})
    
    return styled_df

def pareto_auto(traza_df):
    traza_df['PRESUPUESTO'] = traza_df['PRESUPUESTO'].fillna(0)
    traza_df['PRESUPUESTO'] = traza_df['PRESUPUESTO'].round().astype('int64')
    traza_df['EJECUCIÓN'] = traza_df['EJECUCIÓN'].fillna(0)
    traza_df['EJECUCIÓN'] = traza_df['EJECUCIÓN'].round().astype('int64')
    traza_original = traza_df.copy()

    traza_original['DIFERENCIA'] = traza_original.apply(lambda x: x["EJECUCIÓN"] - x['PRESUPUESTO'], axis=1)
    traza_original['DIFERENCIA_ABS'] = traza_original['DIFERENCIA'].abs()

    traza_df = traza_df.groupby(["CONCEPTO"]).agg({"PRESUPUESTO": "sum", "EJECUCIÓN": "sum"}).reset_index()
    traza_df['DIFERENCIA'] = traza_df.apply(lambda x: x["EJECUCIÓN"] - x['PRESUPUESTO'], axis=1)
    traza_df['DIFERENCIA_ABS'] = traza_df['DIFERENCIA'].abs()
    traza_df_ordenado = traza_df.sort_values(by='DIFERENCIA_ABS', ascending=False)
    traza_df_ordenado = traza_df_ordenado[traza_df_ordenado["DIFERENCIA_ABS"] > 0]
    traza_df_ordenado = traza_df_ordenado.copy()
    traza_df_ordenado['SUMA_ACUMULADA'] = traza_df_ordenado['DIFERENCIA_ABS'].cumsum()
    traza_df_ordenado['PORCENTAJE_ACUMULADO'] = traza_df_ordenado['SUMA_ACUMULADA'] / traza_df_ordenado['DIFERENCIA_ABS'].sum() * 100

    pareto = traza_df_ordenado['PORCENTAJE_ACUMULADO'].searchsorted(80) + 1
    pareto_valores = traza_df_ordenado.iloc[:pareto]
    paretofinal = pareto_valores[['CONCEPTO', 'PRESUPUESTO', 'EJECUCIÓN', 'DIFERENCIA_ABS', 'PORCENTAJE_ACUMULADO']]
    paretofinal = paretofinal.rename(columns={"DIFERENCIA_ABS": "DIFERENCIA_ABSOLUTO"})

    traza_df_media = traza_original.groupby(["CONCEPTO"]).agg({"DIFERENCIA_ABS": "mean"}).reset_index()
    traza_df_max = traza_original.groupby(["CONCEPTO"]).agg({"DIFERENCIA_ABS": "max"}).reset_index()

    paretofinal = paretofinal.copy()
    paretofinal = pd.merge(paretofinal, traza_df_media, how="left", on="CONCEPTO")

    paretofinal['DIFERENCIA_ABS'] = paretofinal['DIFERENCIA_ABS'].fillna(0)
    paretofinal['DIFERENCIA_ABS'] = paretofinal['DIFERENCIA_ABS'].round().astype('int64')
    paretofinal = paretofinal.rename(columns={"DIFERENCIA_ABS": "MEDIA_DIFERENCIA_ABS"})

    paretofinal = pd.merge(paretofinal, traza_df_max, how="left", on="CONCEPTO")
    paretofinal = paretofinal.rename(columns={"DIFERENCIA_ABS": "MAX_DIFERENCIA_ABS"})

    paretofinal["LLAVE"] = paretofinal["CONCEPTO"] + paretofinal["MAX_DIFERENCIA_ABS"].astype(str)
    traza_original["llav"] = traza_original["CONCEPTO"] + traza_original["DIFERENCIA_ABS"].astype(str)
    paretofinal["FECHA_MAX_DIFF"] = pd.merge(paretofinal, traza_original, how="left", left_on="LLAVE", right_on="llav")["FECHA"]

    del paretofinal["LLAVE"]

    return paretofinal

def distributivo(df,modelo):
    distri = df[(df["ANALISIS"] == "Historico_2022") | (df["ANALISIS"] == "Historico_2023") | (df["ANALISIS"] == "ACTUAL")]
    distri = distri.copy()
    distri["absoluto"] = distri["VALOR"].abs()
    actual = distri[distri["ANALISIS"] == "ACTUAL"]
    promedio_por_concepto = actual.groupby('CONCEPTO')['absoluto'].mean()
    promedio_por_concepto_anual = promedio_por_concepto * 12
    actual = actual.copy()
    actual['TOTAL CONCEPTO PROMEDIO'] = actual['CONCEPTO'].map(promedio_por_concepto_anual)
    actual['TOTAL CONCEPTO PROMEDIO'] = actual['TOTAL CONCEPTO PROMEDIO'].astype("int64")
    actual['PESO PONDERADO PROMEDIO'] = actual.apply(
        lambda x: round((x["absoluto"] / x['TOTAL CONCEPTO PROMEDIO']) * 100, 2) if x['TOTAL CONCEPTO PROMEDIO'] != 0 else 0,
        axis=1
    )
    historia_22 = distri[distri["ANALISIS"] == "Historico_2022"]
    suma_por_concepto = historia_22.groupby('CONCEPTO')['absoluto'].sum()
    historia_22 = historia_22.copy()
    historia_22['TOTAL CONCEPTO'] = historia_22['CONCEPTO'].map(suma_por_concepto)
    historia_22['TOTAL CONCEPTO'] = historia_22['TOTAL CONCEPTO'].astype("int64")
    historia_22['PESO PONDERADO PROMEDIO'] = historia_22.apply(
        lambda x: round((x["absoluto"] / x['TOTAL CONCEPTO']) * 100, 2) if x['TOTAL CONCEPTO'] != 0 else 0,
        axis=1
    )
    historia_23 = distri[distri["ANALISIS"] == "Historico_2023"]
    suma_por_concepto = historia_23.groupby('CONCEPTO')['absoluto'].sum()
    historia_23 = historia_23.copy()
    historia_23['TOTAL CONCEPTO'] = historia_23['CONCEPTO'].map(suma_por_concepto)
    historia_23['TOTAL CONCEPTO'] = historia_23['TOTAL CONCEPTO'].astype("int64")
    historia_23['PESO PONDERADO PROMEDIO'] = historia_23.apply(
        lambda x: round((x["absoluto"] / x['TOTAL CONCEPTO']) * 100, 2) if x['TOTAL CONCEPTO'] != 0 else 0,
        axis=1
    )
    Distribucion_23 = historia_23[["FECHA", "CONCEPTO", "PESO PONDERADO PROMEDIO", "ANALISIS"]]
    Distribucion_22 = historia_22[["FECHA", "CONCEPTO", "PESO PONDERADO PROMEDIO", "ANALISIS"]]
    Distribucion_actual = actual[["FECHA", "CONCEPTO", "PESO PONDERADO PROMEDIO", "ANALISIS"]]
    salida_total = pd.concat([Distribucion_23, Distribucion_22, Distribucion_actual], ignore_index=True)

    df_transpuesto = modelo.melt(id_vars=['CONCEPTO COSTO', 'CONCEPTO COSTO HOMOLOGADO'], var_name='mensualidad', value_name='Valor')
    del df_transpuesto["CONCEPTO COSTO"]
    def convertir_fecha(fecha):
        meses = {
            'ene': '01', 'feb': '02', 'mar': '03', 'abr': '04', 
            'may': '05', 'jun': '06', 'jul': '07', 'ago': '08', 
            'sep': '09', 'oct': '10', 'nov': '11', 'dic': '12'
        }
        mes, año = fecha.split('-')
        año = '20' + año  
        mes = meses[mes.lower()]  
        return f'{año}-{mes}-01'

    df_transpuesto['FECHA'] = df_transpuesto['mensualidad'].apply(convertir_fecha)
    del df_transpuesto['mensualidad']
    df_transpuesto = df_transpuesto.rename(columns={"CONCEPTO COSTO HOMOLOGADO": "CONCEPTO", "Valor": "PESO"})
    df_transpuesto = df_transpuesto[["FECHA", "CONCEPTO", "PESO"]]
    df_transpuesto["PESO PONDERADO PROMEDIO"] = df_transpuesto.apply(lambda x: round(x["PESO"] * 100, 2), axis=1)
    del df_transpuesto["PESO"]
    df_transpuesto["ANALISIS"] = "MODELO"
    df_transpuesto['FECHA'] = pd.to_datetime(df_transpuesto['FECHA'])
    distribucion_final = pd.concat([salida_total, df_transpuesto], ignore_index=True)

    return distribucion_final


def pareto_filtro(traza_df):
    traza_df['PRESUPUESTO'] = traza_df['PRESUPUESTO'].fillna(0)
    traza_df['PRESUPUESTO'] = traza_df['PRESUPUESTO'].round().astype('int64')
    traza_df['EJECUCIÓN'] = traza_df['EJECUCIÓN'].fillna(0)
    traza_df['EJECUCIÓN'] = traza_df['EJECUCIÓN'].round().astype('int64')
    traza_original = traza_df.copy()

    traza_original['DIFERENCIA'] = traza_original.apply(lambda x: x["EJECUCIÓN"] - x['PRESUPUESTO'], axis=1)
    traza_original['DIFERENCIA_ABS'] = traza_original['DIFERENCIA'].abs()

    traza_df = traza_df.groupby(["CONCEPTO"]).agg({"PRESUPUESTO": "sum", "EJECUCIÓN": "sum"}).reset_index()
    traza_df['DIFERENCIA'] = traza_df.apply(lambda x: x["EJECUCIÓN"] - x['PRESUPUESTO'], axis=1)
    traza_df['DIFERENCIA_ABS'] = traza_df['DIFERENCIA'].abs()
    traza_df_ordenado = traza_df.sort_values(by='DIFERENCIA_ABS', ascending=False)
    traza_df_ordenado = traza_df_ordenado[traza_df_ordenado["DIFERENCIA_ABS"] > 0]
    traza_df_ordenado = traza_df_ordenado.copy()
    traza_df_ordenado['SUMA_ACUMULADA'] = traza_df_ordenado['DIFERENCIA_ABS'].cumsum()
    traza_df_ordenado['PORCENTAJE_ACUMULADO'] = traza_df_ordenado['SUMA_ACUMULADA'] / traza_df_ordenado['DIFERENCIA_ABS'].sum() * 100

    pareto = traza_df_ordenado['PORCENTAJE_ACUMULADO'].searchsorted(80) + 1
    pareto_valores = traza_df_ordenado.iloc[:pareto]
    paretofinal = pareto_valores[['CONCEPTO', 'PRESUPUESTO', 'EJECUCIÓN', 'DIFERENCIA_ABS', 'PORCENTAJE_ACUMULADO']]
    paretofinal = paretofinal.rename(columns={"DIFERENCIA_ABS": "DIFERENCIA_ABSOLUTO"})

    traza_df_media = traza_original.groupby(["CONCEPTO"]).agg({"DIFERENCIA_ABS": "mean"}).reset_index()
    traza_df_max = traza_original.groupby(["CONCEPTO"]).agg({"DIFERENCIA_ABS": "max"}).reset_index()

    paretofinal = paretofinal.copy()
    paretofinal = pd.merge(paretofinal, traza_df_media, how="left", on="CONCEPTO")

    paretofinal['DIFERENCIA_ABS'] = paretofinal['DIFERENCIA_ABS'].fillna(0)
    paretofinal['DIFERENCIA_ABS'] = paretofinal['DIFERENCIA_ABS'].round().astype('int64')
    paretofinal = paretofinal.rename(columns={"DIFERENCIA_ABS": "MEDIA_DIFERENCIA_ABS"})

    paretofinal = pd.merge(paretofinal, traza_df_max, how="left", on="CONCEPTO")
    paretofinal = paretofinal.rename(columns={"DIFERENCIA_ABS": "MAX_DIFERENCIA_ABS"})

    paretofinal["LLAVE"] = paretofinal["CONCEPTO"] + paretofinal["MAX_DIFERENCIA_ABS"].astype(str)
    traza_original["llav"] = traza_original["CONCEPTO"] + traza_original["DIFERENCIA_ABS"].astype(str)
    paretofinal["FECHA_MAX_DIFF"] = pd.merge(paretofinal, traza_original, how="left", left_on="LLAVE", right_on="llav")["FECHA"]

    del paretofinal["LLAVE"]

    return paretofinal

def detectar_outliers(df, columna_valor):
    Q1 = df[columna_valor].quantile(0.25)
    Q3 = df[columna_valor].quantile(0.75)
    IQR = Q3 - Q1
    outliers = df[(df[columna_valor] < (Q1 - 1.5 * IQR)) | (df[columna_valor] > (Q3 + 1.5 * IQR))]
    return outliers

def salida_out(df):  
    outliers_df = pd.DataFrame()
    for concepto in df['CONCEPTO'].unique():
        for analisis in df['ANALISIS'].unique():
            subset = df[(df['CONCEPTO'] == concepto) & (df['ANALISIS'] == analisis)]
            if not subset.empty:
                outliers = detectar_outliers(subset, 'VALOR')
                outliers_df = pd.concat([outliers_df, outliers])
    return outliers_df

def maquillaje(df):
    df['PRESUPUESTO'] = df['PRESUPUESTO'].fillna(0).round().astype('int64')
    df['EJECUCIÓN'] = df['EJECUCIÓN'].fillna(0).round().astype('int64')
    df = df.groupby(["CONCEPTO"]).agg({"PRESUPUESTO": "sum", "EJECUCIÓN": "sum"}).reset_index()
    df['DIFERENCIA'] = df.apply(lambda x: x["EJECUCIÓN"] - x['PRESUPUESTO'], axis=1)
    df = df[df['PRESUPUESTO'] > 0]
    df['VARIACION'] = df.apply(lambda x: round((((x["DIFERENCIA"] / x['PRESUPUESTO']) * 100) * -1), 2), axis=1)
    return df

if st.session_state.show_dataframe:

    # Cargamos los datos desde el estado de sesión
    preclosing_df = pd.read_excel(st.session_state.preclosing)
    simulacion_df = pd.read_excel(st.session_state.simulacion)
    historico_df = pd.read_excel(st.session_state.historico)
    actual = pd.read_excel(st.session_state.traza,sheet_name="SEGUIMIENTO")
    distribucion = pd.read_excel(st.session_state.traza,sheet_name="DISTRIBUCION")

    
    df_final = arreglos(preclosing_df, simulacion_df, actual, historico_df)
    st.session_state.df_final = df_final  # Guardamos el DataFrame final en el estado de sesión

    fecha_hoy = datetime.now()
    fecha_formateada = format_date(fecha_hoy, format='d', locale='es_ES')
    fecha_mes = format_date(fecha_hoy, format='MMMM', locale='es_ES')
    fecha_año = format_date(fecha_hoy, format='y', locale='es_ES')
    #scroll
    scrolll=maquillaje(actual)
    html_content = generate_scroller_html(scrolll)
    st.markdown(html_content, unsafe_allow_html=True)   
    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; position: relative;">
        <img src="{logo_url}" alt="Logo de la empresa" style="top: 0; width: 180px; height: auto;"/>
        <h1 style="text-align: right;">E.D.A. PLANNING & REPORTING !!! </h1>
        <span style="font-size: 3rem; margin-left: 2rem;">📊</span>
    </div>
    <style>
        div.block-container {{
            padding-top: 3rem;
        }}
        .styled-table {{
            width: 70% !important;  /* Ajusta el ancho aquí */
            margin: auto;
        }}
        th {{
            background-color: #1F77B4 !important;
            color: white !important;
            text-align: center !important;
            font-size: 14px !important;  /* Reduce el tamaño de la letra del encabezado */
        }}
        td {{
            text-align: center !important;
            font-size: 13px !important;  /* Reduce el tamaño de la letra de las celdas */
            white-space: nowrap;
        }}
        .concepto-col {{
            font-weight: bold !important;
        }}
        hr.divider {{
            border: 0;
            height: 1px;
            background: #444;
            margin: 2rem 0;
        }}
        .custom-select-container {{
            display: flex; justify-content: center;
            font-size: 1.2rem;
        }}
        .custom-select {{
            width: 150px !important;
        }}
        .small-font {{
            font-size: 12px !important;  /* Reduce el tamaño de la letra */
        }}
    </style>
    
""", unsafe_allow_html=True)


    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    # TABLA PARETO 2
    
    st.subheader(":point_right: Análisis de Pareto de la Ejecución Actual al: " + fecha_formateada + " de " + fecha_mes + " de " + fecha_año)
        
    
    pareto_uno = actual.copy()

    grafica_1 = pareto_auto(pareto_uno)
    styled_df = style_dataframe(grafica_1)

    st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
    st.write(styled_df.set_table_attributes('class="styled-table"').hide(axis="index").to_html(), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)


    # TABLA PARETO 2
    st.subheader(":point_right: Análisis de Pareto Dinámico")

    st.markdown('<div class="custom-select-container">', unsafe_allow_html=True)
    st.markdown('<span style="font-size: 1.3rem;">Selecciona las fechas de corte</span>', unsafe_allow_html=True)
    selected_conceptos = st.multiselect(
        '',
        options=pareto_uno['FECHA'].unique(),
        key="custom-select"
    )
    st.markdown('</div>', unsafe_allow_html=True)

    
    filtered_df = pareto_uno[pareto_uno['FECHA'].isin(selected_conceptos)]

    grafica_2 = pareto_filtro(filtered_df)
    styled_df_2 = style_dataframe(grafica_2)

    st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
    st.write(styled_df_2.set_table_attributes('class="styled-table small-font"').hide(axis="index").to_html(), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
   
    #GRÁFICA DE TENDENCIAS
    

    st.subheader(":point_right: Análisis Gráfico de Tendencias para Escenarios Presupuestales")
  
    # Utilizamos el DataFrame final guardado en el estado de sesión
    df = st.session_state.df_final.copy()
    df['FECHA'] = pd.to_datetime(df['FECHA'])
    
    
    df['Mes'] = df['FECHA'].dt.strftime('%b')
    df['Año'] = df['FECHA'].dt.year
    
    
    meses_ingles = {'ene.': 'Jan', 'feb.': 'Feb', 'mar.': 'Mar', 'abr.': 'Apr', 'may.': 'May', 'jun.': 'Jun',
                    'jul.': 'Jul', 'ago.': 'Aug', 'sep.': 'Sep', 'oct.': 'Oct', 'nov.': 'Nov', 'dic.': 'Dec'}
    df['Mes'] = df['Mes'].replace(meses_ingles)
    
    df['EJECUCIÓN_MIL_MILLONES'] = df['VALOR'] / 1e9
    
    
    df['Mes'] = pd.Categorical(df['Mes'], categories=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], ordered=True)

    conceptos_unicos = df['CONCEPTO'].unique().tolist()
    conceptos_opciones = ['TODAS'] + conceptos_unicos

    
    col1, col2 = st.columns(2)
    with col1:
        conceptos_seleccionados = st.multiselect('Selecciona los conceptos', options=conceptos_opciones, default=[])
    with col2:
        analisis = st.multiselect('Selecciona el tipo de análisis', options=df['ANALISIS'].unique(), default=[])

    
    if 'TODAS' in conceptos_seleccionados:
        conceptos_seleccionados = conceptos_unicos

    if conceptos_seleccionados and analisis:
        
        df_filtered = df[(df['CONCEPTO'].isin(conceptos_seleccionados)) & (df['ANALISIS'].isin(analisis))]

        
        if not df_filtered.empty:
            df_grouped = df_filtered.groupby(['Mes', 'Año', 'ANALISIS'], as_index=False)['EJECUCIÓN_MIL_MILLONES'].sum()

            
            df_grouped = df_grouped[df_grouped['EJECUCIÓN_MIL_MILLONES'] != 0]

            
            fig = px.line(
                df_grouped,
                x='Mes',
                y='EJECUCIÓN_MIL_MILLONES',
                color='ANALISIS',  #
                title="COMPARACIÓN DE ESCENARIOS PRESUPUESTALES",
                labels={'EJECUCIÓN_MIL_MILLONES': 'Ejecución (Mil Millones de COP)', 'ANALISIS': 'Tipo de Análisis'},
                markers=True
            )

            
            for trace in fig.data:
                trace.update(name=trace.name.split(',')[0])  
                trace.update(line=dict(dash=None))  

            
            unique_colors = px.colors.qualitative.Plotly
            color_mapping = {name: unique_colors[i % len(unique_colors)] for i, name in enumerate(df['ANALISIS'].unique())}
            for trace in fig.data:
                trace.update(line=dict(color=color_mapping[trace.name]))

            
            for trace in fig.data:
                trace.update(
                    hovertemplate='<b>Mes</b>: %{x}<br>' +
                    '<b>Ejecución</b>: $%{y:.2f} Mil Millones<br>' +
                    '<b>Análisis</b>: ' + trace.name + '<br>'
                )

            
            fig.update_layout(
                width=1250,
                height=730,
                title={
                    'text': "COMPARACIÓN DE ESCENARIOS PRESUPUESTALES",
                    'y':0.9,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': dict(size=24)
                },
                xaxis=dict(showgrid=False), 
                   yaxis=dict(
                    showgrid=True,
                    gridwidth=0.5,
                    gridcolor='rgba(255, 255, 255, 0.1)'),  
                    
                plot_bgcolor='rgba(0, 0, 0, 0)'  

            )

            st.plotly_chart(fig)
       
            def descargar_excel(dataframe):
                if 'FECHA' in dataframe.columns:
                    dataframe['FECHA'] = dataframe['FECHA'].dt.date
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    dataframe.to_excel(writer, index=False, sheet_name='Sheet1')
                processed_data = output.getvalue()
                return processed_data
                                
            
            excel_data = descargar_excel(df_final)
            st.download_button(
                label="Descargar Datos",
                data=excel_data,
                file_name="df_final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            #TABLA EXPANSORA
            
            expansor = df_final.copy()

            expansor['FECHA'] = pd.to_datetime(expansor['FECHA'], errors='coerce')
            expansor['MES'] = expansor['FECHA'].dt.strftime('%B')
            analisis_options = ['Seleccione una opción'] + list(expansor['ANALISIS'].unique())

            with st.expander(":point_right: TABLA DINÁMICA: CÁLCULO DE DIFERENCIAS POR ESCENARIO"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    escenario_1 = st.selectbox("Escenario 1", options=analisis_options, key="escenario_1")
                with col2:
                    escenario_2 = st.selectbox("Escenario 2", options=analisis_options, key="escenario_2")
                with col3:
                    conceptos_seleccionados = st.multiselect("Conceptos", options=expansor['CONCEPTO'].unique(), key="conceptos_seleccionados")
                with col4:
                    fechas_seleccionadas = st.multiselect("Meses", options=expansor['MES'].unique(), key="fechas_seleccionadas")

                
                total_escenario = [escenario_1, escenario_2]
                if 'Seleccione una opción' in total_escenario:
                    st.warning("Por favor, seleccione opciones válidas para los escenarios.")
                else:
                    
                    filtro = expansor[
                        (expansor['ANALISIS'].isin(total_escenario)) & 
                        (expansor['CONCEPTO'].isin(conceptos_seleccionados)) & 
                        (expansor['MES'].isin(fechas_seleccionadas))
                    ]

                    if filtro.empty:
                        st.warning("No hay datos que coincidan con los filtros seleccionados.")
                    else:
                        df_pivot = filtro.pivot_table(index=['CONCEPTO', 'MES'], columns='ANALISIS', values='VALOR').reset_index()
                        meses_ls = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
                        df_pivot['MES'] = pd.Categorical(df_pivot['MES'], categories=meses_ls, ordered=True)
                        dfsalida = df_pivot.sort_values(by=['CONCEPTO', 'MES'])
                        dfsalida["DIFERENCIA"] = dfsalida.apply(lambda x: abs(x[dfsalida.columns[-2]] - x[dfsalida.columns[-1]]), axis=1)
                        styled_filtrado = style_tabla_filtro(dfsalida)
                        st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
                        st.write(styled_filtrado.set_table_attributes('class="styled-table"').hide(axis="index").to_html(), unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.markdown('<p style="font-size:24px; color:orange;">No hay datos disponibles para los filtros seleccionados.</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p style="font-size:24px; color:orange;">Por favor, selecciona al menos un concepto y un tipo de análisis para visualizar la gráfica.</p>', unsafe_allow_html=True)
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # OUTLIERS
    st.subheader(":point_right: Análisis dinámico de Outliers por Escenarios Presupuestales")


    df_outlier = st.session_state.df_final.copy()

    df_out=salida_out(df_outlier)
    
    df_out['FECHA'] = pd.to_datetime(df_out['FECHA'])

    df_out['FECHA'] = df_out['FECHA'].dt.date

     
    df_out = df_out.reset_index(drop=True)
    df_out.columns = pd.Index([f"{col}_{i}" if list(df_out.columns).count(col) > 1 else col for i, col in enumerate(df_out.columns)])

    
    col1, col2 = st.columns([1, 3])

    with col1:
        
        conceptos = df_out['CONCEPTO'].unique()
    
        
        selected_conceptos = st.multiselect('Selecciona los conceptos', conceptos)

    with col2:
        
        df_filtered = df_out[df_out['CONCEPTO'].isin(selected_conceptos)]

        
        styled_df_3 = style_dataframe_filtered(df_filtered)

        
        st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
        st.write(styled_df_3.set_table_attributes('class="styled-table"').hide(axis="index").to_html(), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    #DISTRIBUCION_GRAFI
    df_distri = df_final.copy()
    df_distribucion= distributivo(df_distri,distribucion)
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.subheader(":point_right: Análisis de Distribución de Costos Mensuales por Concepto")
   
    # Variable selector
    st.markdown('<div class="custom-select-container">', unsafe_allow_html=True)
    st.markdown('<span style="font-size: 1.3rem;">Selecciona el concepto para analizar</span>', unsafe_allow_html=True)
    seleccion_conceptos = st.multiselect(
        '',
        options=df_distribucion['CONCEPTO'].unique(),
        key="custom-selector-conceptos"
    )    
    df_filtrado= df_distribucion[df_distribucion['CONCEPTO'].isin(seleccion_conceptos)].copy()

    if not df_filtrado.empty:
        df_filtrado['FECHA'] = pd.to_datetime(df_filtrado['FECHA'])
        df_filtrado['Mes'] = df_filtrado['FECHA'].dt.strftime('%B')
        df_filtrado['PESO PONDERADO PROMEDIO'] = df_filtrado['PESO PONDERADO PROMEDIO'].round(2)

        # Definir el orden de los meses en inglés
        meses_ordenados = ['January', 'February', 'March', 'April', 'May', 'June', 
                        'July', 'August', 'September', 'October', 'November', 'December']
        df_filtrado['Mes'] = pd.Categorical(df_filtrado['Mes'], categories=meses_ordenados, ordered=True)

        fig = px.line(
            df_filtrado,
            x='Mes',
            y='PESO PONDERADO PROMEDIO',
            color='ANALISIS',
            title="DISTRIBUCIÓN MENSUAL DE COSTOS",
            labels={'PESO PONDERADO PROMEDIO': 'DISTRIBUCIÓN PORCENTUAL %', 'ANALISIS': 'Tipo de Análisis'},
            markers=True
        )

        for trace in fig.data:
            trace.update(name=trace.name.split(',')[0])
            trace.update(line=dict(dash=None))

        unique_colors = px.colors.qualitative.Plotly
        color_mapping = {name: unique_colors[i % len(unique_colors)] for i, name in enumerate(df_filtrado['ANALISIS'].unique())}
        for trace in fig.data:
            trace.update(line=dict(color=color_mapping[trace.name]))

        for trace in fig.data:
            trace.update(
                hovertemplate='<b>Mes</b>: %{x}<br>' +
                '<b>Distribución Porcentual</b>: %{y:.2f}%<br>' +
                '<b>Análisis</b>: ' + trace.name + '<br>'
            )

        fig.update_layout(
            width=1250,
            height=730,
            title={
                'text': "DISTRIBUCIÓN MENSUAL DE COSTOS",
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=24)
            },
            xaxis=dict(showgrid=False, categoryorder='array', categoryarray=meses_ordenados),
            yaxis=dict(
                tickformat=".0f",  
                showgrid=True,
                gridwidth=0.5,
                gridcolor='rgba(255, 255, 255, 0.1)',
            ),
            plot_bgcolor='rgba(0, 0, 0, 0)'
        )

        st.plotly_chart(fig)
    else:
        st.markdown('<p style="font-size:24px; color:orange;">Por favor, selecciona al menos un concepto para visualizar la gráfica.</p>', unsafe_allow_html=True)

    
else:
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; position: relative;">
        <img src="{logo_url}" alt="Logo de la empresa" style="top: 0; width: 180px; height: auto;"/>
        <h1 style="text-align: right;">E.D.A. PLANNING & REPORTING !!! </h1>
        <span style="font-size: 3rem; margin-left: 2rem;">📊</span>
    </div>
    <style>
        div.block-container {{
            padding-top: 3rem;
        }}
        .styled-table {{
            width: 70% !important;  /* Ajusta el ancho aquí */
            margin: auto;
        }}
        th {{
            background-color: #1F77B4 !important;
            color: white !important;
            text-align: center !important;
            font-size: 14px !important;  /* Reduce el tamaño de la letra del encabezado */
        }}
        td {{
            text-align: center !important;
            font-size: 13px !important;  /* Reduce el tamaño de la letra de las celdas */
            white-space: nowrap;
        }}
        .concepto-col {{
            font-weight: bold !important;
        }}
        hr.divider {{
            border: 0;
            height: 1px;
            background: #444;
            margin: 2rem 0;
        }}
        .custom-select-container {{
            display: flex; justify-content: center;
            font-size: 1.2rem;
        }}
        .custom-select {{
            width: 150px !important;
        }}
        .small-font {{
            font-size: 12px !important;  /* Reduce el tamaño de la letra */
        }}
    </style>
    <hr class='divider'>
""", unsafe_allow_html=True)
    


    col1, col2 = st.columns(2)
    
    folder_emoji = emoji.emojize(':file_folder:')
    with col1:
        preclosing = st.file_uploader(f"{folder_emoji} CARGUE DE ARCHIVO PRECLOSING", type=["csv", "txt", "xlsx", "xls"], key="preclosing_upload")
        simulacion = st.file_uploader(f"{folder_emoji} CARGUE DE ARCHIVO SIMULACIÓN ESCENARIOS", type=["csv", "txt", "xlsx", "xls"], key="simulacion_upload")

    with col2:
        historico = st.file_uploader(f"{folder_emoji} CARGUE DE ARCHIVO HISTÓRICO DE EJECUCIONES", type=["csv", "txt", "xlsx", "xls"], key="historico_upload")
        traza = st.file_uploader(f"{folder_emoji} CARGUE DE ARCHIVO DE EJECUCIÓN ACTUAL", type=["csv", "txt", "xlsx", "xls"], key="traza_upload")

    if preclosing is not None:
        st.session_state.preclosing = preclosing
    if simulacion is not None:
        st.session_state.simulacion = simulacion
    if historico is not None:
        st.session_state.historico = historico
    if traza is not None:
        st.session_state.traza = traza

    if 'preclosing' in st.session_state and 'simulacion' in st.session_state and 'historico' in st.session_state and 'traza' in st.session_state:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown('<p style="font-size:24px; color:green;">Todos los archivos han sido cargados correctamente.</p>', unsafe_allow_html=True)
        with col2:
            if st.button('Siguiente', key="next_button"):
                st.session_state.show_dataframe = True
                st.experimental_rerun()
    else:
        st.markdown('<p style="font-size:24px; color:red;">DEBEN SER CARGADOS LOS 4 ARCHIVOS PARA EL TABLERO, DE LO CONTRARIO NO ES POSIBLE CONTINUAR.</p>', unsafe_allow_html=True)
