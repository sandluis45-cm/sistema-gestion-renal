import streamlit as st
import pandas as pd
import io

# Configuración de la pestaña
st.set_page_config(page_title="Sistema de Gestión Renal - Clínica Inmaculada", layout="wide")

st.title("🏥 Sistema de Gestión Renal - Clínica Inmaculada")
st.subheader("Consolidación Mensual de Diagnósticos y Laboratorio")

# --- CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1:
    st.info("📂 ARCHIVOS DE DIAGNÓSTICO")
    files_dx = st.file_uploader("Sube archivos de Diagnóstico", accept_multiple_files=True, type=['txt'], key="dx")
with col2:
    st.success("🧪 ARCHIVOS DE RESULTADOS")
    files_res = st.file_uploader("Sube archivos de Resultados", accept_multiple_files=True, type=['txt'], key="res")

if st.button("🚀 PROCESAR Y CRUZAR DATOS POR DNI"):
    if files_dx and files_res:
        try:
            # Procesar DX
            df_dx = pd.concat([pd.read_csv(f, sep='|', encoding='latin-1', on_bad_lines='skip') for f in files_dx]).drop_duplicates()
            df_dx.columns = df_dx.columns.str.strip()
            df_dx['DOC_PACIENTE'] = df_dx['DOC_PACIENTE'].astype(str).str.split('.').str[0]

            pacientes = df_dx.groupby('DOC_PACIENTE').agg({
                'PACIENTE': 'first', 'EDAD': 'first', 'SEXO': 'first', 'TELEF_MOVIL': 'first'
            }).reset_index()

            f_n189 = df_dx[df_dx['CODDX'] == 'N18.9'].groupby('DOC_PACIENTE')['FECHATEN'].max().rename('FECHA_N18.9')
            f_z712 = df_dx[df_dx['CODDX'] == 'Z71.2'].groupby('DOC_PACIENTE')['FECHATEN'].max().rename('FECHA_Z71.2')

            # Procesar RES
            df_res = pd.concat([pd.read_csv(f, sep='|', encoding='latin-1', on_bad_lines='skip') for f in files_res]).drop_duplicates()
            df_res.columns = df_res.columns.str.strip()
            df_res['DNI_PACIENTE'] = df_res['DNI_PACIENTE'].astype(str).str.split('.').str[0]

            crea = df_res[df_res['EXAMEN'].astype(str).str.contains('82565')].groupby('DNI_PACIENTE')['VALOR_RESULTADO'].first().rename('CREATININA')
            albu = df_res[df_res['EXAMEN'].astype(str).str.contains('82043')].groupby('DNI_PACIENTE')['VALOR_RESULTADO'].first().rename('ALBUMINA')

            # Unir
            final = pacientes.merge(f_n189, left_on='DOC_PACIENTE', right_index=True, how='left')
            final = final.merge(f_z712, left_on='DOC_PACIENTE', right_index=True, how='left')
            final = final.merge(crea, left_on='DOC_PACIENTE', right_index=True, how='left')
            final = final.merge(albu, left_on='DOC_PACIENTE', right_index=True, how='left')

            st.write("### Vista Previa")
            st.dataframe(final)

            # DESCARGA EN CSV (Esto no falla nunca y Excel lo abre igual)
            csv = final.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Descargar Reporte (Formato Excel/CSV)", data=csv, file_name="Reporte_Clinica.csv", mime='text/csv')
            
        except Exception as e:
            st.error(f"Error: {e}")
