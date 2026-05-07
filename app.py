import streamlit as st
import pandas as pd
import io

# Configuración de la pestaña del navegador con el nombre exacto solicitado
st.set_page_config(
    page_title="Sistema de Gestión Renal - Clínica Inmaculada", 
    layout="wide",
    page_icon="🏥"
)

# Estilo personalizado para un acabado más profesional y limpio (similar a un sistema de escritorio)
st.markdown("""
    <style>
    .main-title {
        color: #1F4E78;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
    .section-header {
        color: #2F5597;
        font-family: 'Segoe UI', sans-serif;
        border-bottom: 2px solid #2F5597;
        padding-bottom: 5px;
        margin-top: 20px;
    }
    </style>
""", unsafe_allowed_html=True)

st.markdown("<h1 class='main-title'>🏥 Sistema de Gestión Renal</h1>", unsafe_allowed_html=True)
st.markdown("<h4 style='text-align: center; color: #595959; margin-bottom: 30px;'>Clínica Inmaculada - Sullana</h4>", unsafe_allowed_html=True)

# --- PANEL LATERAL DE CARGA ---
st.sidebar.header("📁 Carga de Archivos Mensuales")
st.sidebar.markdown("Suba hasta 3 archivos por categoría para realizar el cruce consolidado.")

st.sidebar.subheader("1. Archivos de Diagnósticos")
archivos_dx = st.sidebar.file_uploader(
    "Seleccione archivos de Diagnóstico (DxMedSer)", 
    accept_multiple_files=True, 
    type=['txt', 'csv'],
    key="dx_files"
)

st.sidebar.subheader("2. Archivos de Resultados")
archivos_res = st.sidebar.file_uploader(
    "Seleccione archivos de Resultados (ResulExamDet)", 
    accept_multiple_files=True, 
    type=['txt', 'csv'],
    key="res_files"
)

# Restringir a máximo 3 archivos
if len(archivos_dx) > 3:
    st.sidebar.error("⚠️ Ha seleccionado más de 3 archivos de diagnóstico. Solo se procesarán los 3 primeros.")
    archivos_dx = archivos_dx[:3]

if len(archivos_res) > 3:
    st.sidebar.error("⚠️ Ha seleccionado más de 3 archivos de resultados. Solo se procesarán los 3 primeros.")
    archivos_res = archivos_res[:3]

# --- PANTALLA PRINCIPAL ---
st.markdown("<h3 class='section-header'>Procesamiento y Consolidación</h3>", unsafe_allowed_html=True)

if st.button("🚀 PROCESAR Y CRUZAR DATOS", use_container_width=True):
    if archivos_dx and archivos_res:
        with st.spinner("Procesando archivos, filtrando duplicados y cruzando información por DNI..."):
            try:
                # 1. PROCESAR DIAGNÓSTICOS
                list_df_dx = []
                for f in archivos_dx:
                    # Leemos con encoding latin-1 y separador '|'
                    df_temp = pd.read_csv(f, sep='|', encoding='latin-1', on_bad_lines='skip')
                    df_temp.columns = df_temp.columns.str.strip()
                    list_df_dx.append(df_temp)
                
                df_dx = pd.concat(list_df_dx).drop_duplicates()
                df_dx['DOC_PACIENTE'] = df_dx['DOC_PACIENTE'].astype(str).str.strip().str.split('.').str[0]

                # Base de Pacientes Únicos (DNI, Nombre, Edad, Sexo, Teléfono)
                pacientes = df_dx.groupby('DOC_PACIENTE').agg({
                    'PACIENTE': 'first',
                    'EDAD': 'first',
                    'SEXO': 'first',
                    'TELEF_MOVIL': 'first'
                }).reset_index()

                # Fechas de Diagnósticos prioritarios
                f_n189 = df_dx[df_dx['CODDX'].str.strip() == 'N18.9'].groupby('DOC_PACIENTE')['FECHATEN'].max().rename('FECHA_DX_N18.9')
                f_z712 = df_dx[df_dx['CODDX'].str.strip() == 'Z71.2'].groupby('DOC_PACIENTE')['FECHATEN'].max().rename('FECHA_DX_Z71.2')

                # 2. PROCESAR RESULTADOS
                list_df_res = []
                for f in archivos_res:
                    df_temp = pd.read_csv(f, sep='|', encoding='latin-1', on_bad_lines='skip')
                    df_temp.columns = df_temp.columns.str.strip()
                    list_df_res.append(df_temp)
                
                df_res = pd.concat(list_df_res).drop_duplicates()
                df_res['DNI_PACIENTE'] = df_res['DNI_PACIENTE'].astype(str).str.strip().str.split('.').str[0]

                # Resultados específicos de laboratorio (Creatinina: 82565 | Albúmina: 82043)
                creatinina = df_res[df_res['EXAMEN'].astype(str).str.strip() == '82565'].groupby('DNI_PACIENTE')['VALOR_RESULTADO'].first().rename('CREATININA')
                albumina = df_res[df_res['EXAMEN'].astype(str).str.strip() == '82043'].groupby('DNI_PACIENTE')['VALOR_RESULTADO'].first().rename('ALBUMINA')

                # 3. UNIÓN Y CRUCE FINAL POR DNI
                final = pacientes.merge(f_n189, left_on='DOC_PACIENTE', right_index=True, how='left')
                final = final.merge(f_z712, left_on='DOC_PACIENTE', right_index=True, how='left')
                final = final.merge(creatinina, left_on='DOC_PACIENTE', right_index=True, how='left')
                final = final.merge(albumina, left_on='DOC_PACIENTE', right_index=True, how='left')

                # Renombrar columnas para el Excel de exportación
                final.columns = ['DNI', 'PACIENTE', 'EDAD', 'SEXO', 'TELEFONO', 'FECHA_DX_N18.9', 'FECHA_DX_Z71.2', 'CREATININA', 'ALBUMINA']

                # Mostrar Tabla de Vista Previa
                st.success("✅ ¡Datos procesados y cruzados con éxito!")
                st.dataframe(final, use_container_width=True)

                # Generar archivo Excel en memoria para descarga instantánea
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    final.to_excel(writer, sheet_name='Consolidado Renal', index=False)
                
                buffer.seek(0)
                
                st.download_button(
                    label="📥 DESCARGAR CONSOLIDADO EXCEL",
                    data=buffer,
                    file_name="Consolidado_Gestión_Renal.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"Ocurrió un error al procesar los archivos: {str(e)}")
                st.info("Asegúrese de que los archivos cargados sean los correctos y tengan el formato '|' (delimitado por pipes).")
    else:
        st.warning("⚠️ Por favor, cargue al menos un archivo de Diagnósticos y uno de Resultados en la barra lateral para poder procesar.")

else:
    st.info("💡 Suba los archivos correspondientes en el panel de la izquierda y presione el botón para iniciar el cruce de datos.")
