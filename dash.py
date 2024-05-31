import io
import locale
import streamlit as st
import plotly.express as px
import pandas as pd
import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="PLANNING & REPORTING!!!", page_icon=":bar_chart:", layout="wide")

# URL de la imagen del logo en GitHub
logo_url = "https://raw.githubusercontent.com/ingjfnf/dash_presu/main/logo.jpg"

st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; position: relative;">
        <img src="{logo_url}" alt="Logo de la empresa" style="position: absolute; left: 0; top: 0; width: 200px; height: auto;"/>
        <span style="font-size: 2rem; margin-right: 0.5rem;">📊</span>
        <h1 style="text-align: center;">E.D.A. PLANNING & REPORTING !!!</h1>
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

# Inicializar el estado de sesión
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
    items_html_double = items_html + items_html  # Duplicar los elementos para un scroller continuo
    
    html_content = f"""
    <div id="scroller" style="white-space: nowrap; overflow: hidden; width: 100%; height: 50px; position: relative;">
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
    }}
    #scrolling-text {{
        display: inline-block;
        white-space: nowrap;
        position: relative;
        animation: scroll 110s linear infinite;
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
    preclosing_df = preclosing_df[["FECHA", "Campo homologado", "total_presupuesto"]].copy()
    preclosing_df['total_presupuesto'] = preclosing_df['total_presupuesto'].fillna(0).round().astype('int64')
    preclosing_df = preclosing_df.rename(columns={"Campo homologado": "CONCEPTO", "total_presupuesto": "VALOR"})
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

    # Cargar los datos desde el estado de sesión
    preclosing_df = pd.read_excel(st.session_state.preclosing)
    simulacion_df = pd.read_excel(st.session_state.simulacion)
    historico_df = pd.read_excel(st.session_state.historico)
    actual = pd.read_excel(st.session_state.traza)

    # Transformar los datos
    df_final = arreglos(preclosing_df, simulacion_df, actual, historico_df)
    st.session_state.df_final = df_final  # Guardar el DataFrame final en el estado de sesión

    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    fecha_hoy = datetime.datetime.now()
    fecha_formateada = fecha_hoy.strftime("%d de %B de %Y")
    #scroll
    scrolll=maquillaje(actual)
    html_content = generate_scroller_html(scrolll)
    st.markdown(html_content, unsafe_allow_html=True)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    
    # TABLA PARETO 2
    
    st.subheader(":point_right: Análisis de Pareto de la Ejecución Actual al: " + fecha_formateada)
        
    fecha_formateada = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
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
    # Obtener lista de conceptos con la opción "TODAS"

    st.subheader(":point_right: Análisis Gráfico de Tendencias para Escenarios Presupuestales")
  
    # Utilizar el DataFrame final guardado en el estado de sesión
    df = st.session_state.df_final.copy()
    df['FECHA'] = pd.to_datetime(df['FECHA'])
    
    # Asignar correctamente los meses
    df['Mes'] = df['FECHA'].dt.strftime('%b')
    df['Año'] = df['FECHA'].dt.year
    
    # Convertir los nombres de los meses a inglés
    meses_ingles = {'ene.': 'Jan', 'feb.': 'Feb', 'mar.': 'Mar', 'abr.': 'Apr', 'may.': 'May', 'jun.': 'Jun',
                    'jul.': 'Jul', 'ago.': 'Aug', 'sep.': 'Sep', 'oct.': 'Oct', 'nov.': 'Nov', 'dic.': 'Dec'}
    df['Mes'] = df['Mes'].replace(meses_ingles)
    
    df['EJECUCIÓN_MIL_MILLONES'] = df['VALOR'] / 1e9
    
    # Ordenar los meses correctamente
    df['Mes'] = pd.Categorical(df['Mes'], categories=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], ordered=True)

    conceptos_unicos = df['CONCEPTO'].unique().tolist()
    conceptos_opciones = ['TODAS'] + conceptos_unicos

    # Colocar los selectores arriba de la gráfica
    col1, col2 = st.columns(2)
    with col1:
        conceptos_seleccionados = st.multiselect('Selecciona los conceptos', options=conceptos_opciones, default=[])
    with col2:
        analisis = st.multiselect('Selecciona el tipo de análisis', options=df['ANALISIS'].unique(), default=[])

    # Si se selecciona "TODAS", seleccionar todos los conceptos
    if 'TODAS' in conceptos_seleccionados:
        conceptos_seleccionados = conceptos_unicos

    if conceptos_seleccionados and analisis:
        # Filtrar y agrupar los datos por mes y tipo de análisis, sumando solo los existentes
        df_filtered = df[(df['CONCEPTO'].isin(conceptos_seleccionados)) & (df['ANALISIS'].isin(analisis))]

        # Verificar si el DataFrame filtrado no está vacío
        if not df_filtered.empty:
            df_grouped = df_filtered.groupby(['Mes', 'Año', 'ANALISIS'], as_index=False)['EJECUCIÓN_MIL_MILLONES'].sum()

            # Filtrar valores cero
            df_grouped = df_grouped[df_grouped['EJECUCIÓN_MIL_MILLONES'] != 0]

            # Ajustar las leyendas y asegurarse de que las líneas sean continuas
            fig = px.line(
                df_grouped,
                x='Mes',
                y='EJECUCIÓN_MIL_MILLONES',
                color='ANALISIS',  # Asegurando que se muestre el tipo de análisis
                title="COMPARACIÓN DE ESCENARIOS PRESUPUESTALES",
                labels={'EJECUCIÓN_MIL_MILLONES': 'Ejecución (Mil Millones de COP)', 'ANALISIS': 'Tipo de Análisis'},
                markers=True
            )

            # Actualizar trazos para eliminar los nombres de los años y las líneas discontinuas
            for trace in fig.data:
                trace.update(name=trace.name.split(',')[0])  # Eliminar el año de la leyenda
                trace.update(line=dict(dash=None))  # Asegurar que las líneas sean continuas

            # Asignar colores únicos a cada línea
            unique_colors = px.colors.qualitative.Plotly
            color_mapping = {name: unique_colors[i % len(unique_colors)] for i, name in enumerate(df['ANALISIS'].unique())}
            for trace in fig.data:
                trace.update(line=dict(color=color_mapping[trace.name]))

            # Actualizar el hovertemplate para mostrar información correcta
            for trace in fig.data:
                trace.update(
                    hovertemplate='<b>Mes</b>: %{x}<br>' +
                    '<b>Ejecución</b>: $%{y:.2f} Mil Millones<br>' +
                    '<b>Análisis</b>: ' + trace.name + '<br>'
                )

            # Configurar el título centrado y con un tamaño de letra más grande
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
                }
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
                                
            # Agregar el botón de descarga debajo de la gráfica
            excel_data = descargar_excel(df_final)
            st.download_button(
                label="Descargar Datos",
                data=excel_data,
                file_name="df_final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
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

     # Asegurarse de que el índice y las columnas sean únicos
    df_out = df_out.reset_index(drop=True)
    df_out.columns = pd.Index([f"{col}_{i}" if list(df_out.columns).count(col) > 1 else col for i, col in enumerate(df_out.columns)])

    # Crear dos columnas: una para el selector y otra para la tabla
    col1, col2 = st.columns([1, 3])

    with col1:
        # Obtener los valores únicos de la columna "CONCEPTO"
        conceptos = df_out['CONCEPTO'].unique()
    
        # Agregar un multiselect para seleccionar conceptos
        selected_conceptos = st.multiselect('Selecciona los conceptos', conceptos)

    with col2:
        # Filtrar el DataFrame según los conceptos seleccionados
        df_filtered = df_out[df_out['CONCEPTO'].isin(selected_conceptos)]

        # Aplicar estilo al DataFrame filtrado
        styled_df_3 = style_dataframe_filtered(df_filtered)

        # Mostrar el DataFrame estilizado en Streamlit
        st.markdown("<div style='display: flex; justify-content: center;'>", unsafe_allow_html=True)
        st.write(styled_df_3.set_table_attributes('class="styled-table"').hide(axis="index").to_html(), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

else:
    col1, col2 = st.columns(2)

    with col1:
        preclosing = st.file_uploader(":file_folder: CARGUE DE ARCHIVO PRECLOSING", type=["csv", "txt", "xlsx", "xls"], key="preclosing_upload")
        simulacion = st.file_uploader(":file_folder: CARGUE DE ARCHIVO SIMULACIÓN ESCENARIOS", type=["csv", "txt", "xlsx", "xls"], key="simulacion_upload")

    with col2:
        historico = st.file_uploader(":file_folder: CARGUE DE ARCHIVO HISTÓRICO DE EJECUCIONES", type=["csv", "txt", "xlsx", "xls"], key="historico_upload")
        traza = st.file_uploader(":file_folder: CARGUE DE ARCHIVO DE EJECUCIÓN ACTUAL", type=["csv", "txt", "xlsx", "xls"], key="traza_upload")

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
