import streamlit as st
import pandas as pd
import plotly.express as px
import os
import psycopg2

# ==========================================
# 1. KONEKSI DATABASE (DARI DATABASE.PY)
# ==========================================
def get_connection():
    # Streamlit Cloud akan membaca dari st.secrets
    return psycopg2.connect(
        host=st.secrets.get("DB_HOST", "localhost"),
        port=st.secrets.get("DB_PORT", "5432"),
        database=st.secrets.get("DB_NAME", "fisheries_db"),
        user=st.secrets.get("DB_USER", "fisheries_user"),
        password=st.secrets.get("DB_PASSWORD", "fisheries_pass")
    )

def get_monthly_species_percentage():
    try:
        conn = get_connection()
        query = """
            WITH monthly_catch AS (
                SELECT TO_CHAR(DATE_TRUNC('month', timestamp), 'YYYY-MM') as month_year, species, SUM(weight_kg) as total_weight
                FROM catch_reports GROUP BY DATE_TRUNC('month', timestamp), species
            ),
            total_per_month AS (
                SELECT month_year, SUM(total_weight) as grand_total FROM monthly_catch GROUP BY month_year
            )
            SELECT mc.month_year, mc.species, mc.total_weight, ROUND(((mc.total_weight / tp.grand_total) * 100)::numeric, 2) as percentage
            FROM monthly_catch mc JOIN total_per_month tp ON mc.month_year = tp.month_year
            ORDER BY mc.month_year DESC, mc.total_weight DESC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error Database Bulanan: {e}")
        return pd.DataFrame()

def get_daily_cpue():
    try:
        conn = get_connection()
        query = """
            SELECT DATE(timestamp) as date, vessel_id, SUM(weight_kg) as daily_catch, COUNT(*) as species_count, SUM(weight_kg) / 8.0 as cpue
            FROM catch_reports GROUP BY DATE(timestamp), vessel_id ORDER BY date DESC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error Database Harian: {e}")
        return pd.DataFrame()

# ==========================================
# 2. TAMPILAN DASHBOARD (DARI WEB_GALERI.PY)
# ==========================================
st.set_page_config(page_title="Dashboard Monitorizasaun Peskas", layout="wide")
st.title("🐟 Dashboard Monitorizasaun Peskas")

# CSS atu kontrol imajen
st.markdown("""
    <style>
    div[data-testid="stImage"] img { max-height: 300px; max-width: 100%; object-fit: contain; border-radius: 10px; }
    div[data-testid="stImage"] > img { max-height: 80vh; width: auto; }
    </style>
""", unsafe_allow_html=True)

# Kamus
kamus_ikan = {
    'Tuna': 'Tuna', 'Tongkol': 'Mackerel Tuna', 'Cakalang': 'Skipjack Tuna',
    'Kakap': 'Snapper', 'Kerapu': 'Grouper', 'Bandeng': 'Milkfish',
    'Gurita': 'Octopus', 'Udang': 'Shrimp', 'Barakuda': 'Barracuda',
    'Kepiting': 'Crab', 'Cumi-cumi': 'Squid', 'Sardin': 'Sardine',
    'Nila': 'Tilapia', 'Kerang': 'Shellfish', 'Salem': 'Trevally'
}

# --- PARTE 1: GRÁFIKU PERSENTAJEN IKAN ---
st.header("📊 Persentajen Tipu Ikan Per Fulan")

df_monthly = get_monthly_species_percentage()

if not df_monthly.empty:
    df_monthly['species_en'] = df_monthly['species'].map(kamus_ikan).fillna(df_monthly['species'])
    
    list_bulan = df_monthly['month_year'].unique()
    selected_month = st.selectbox("Hili Fulan (Formatu: Tinan-Fulan):", list_bulan)
    df_filtered = df_monthly[df_monthly['month_year'] == selected_month]
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pie = px.pie(
            df_filtered, values='percentage', names='species_en', hole=0.4, 
            title=f"Fish Percentage ({selected_month})", 
            color_discrete_sequence=px.colors.qualitative.Pastel,
            labels={'percentage': 'Percentage (%)', 'species_en': 'Fish Species'}
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col2:
        fig_bar = px.bar(
            df_filtered, x='species_en', y='total_weight', color='species_en', 
            title=f"Total Fish Weight (kg) in {selected_month}", text='total_weight',
            labels={'total_weight': 'Total Weight (kg)', 'species_en': 'Fish Species'}
        )
        fig_bar.update_traces(texttemplate='%{text:.1f} kg', textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    st.subheader(f"Tabela Dadus Persentajen - {selected_month}")
    df_tampil = df_filtered[['species_en', 'total_weight', 'percentage']].copy()
    df_tampil.columns = ['Fish Species', 'Total Weight (kg)', 'Percentage (%)']
    st.dataframe(df_tampil, use_container_width=True, hide_index=True)
else:
    st.warning("Seidauk iha dadus peskas iha database. Favor hatama dadus uluk.")

# --- PARTE 2: DADUS LORON-LORON (CPUE) ---
st.divider()
st.header("📅 Dadus Loron-Loron (CPUE)")
st.write("Hatudu dadus performansu kapal loroloron.")

df_daily = get_daily_cpue()
if not df_daily.empty:
    df_daily_tampil = df_daily.copy()
    df_daily_tampil.columns = ['Data', 'ID Kapal', 'Kaptura Loron (kg)', 'Númeru Espésie', 'CPUE']
    st.dataframe(df_daily_tampil, use_container_width=True, hide_index=True)
else:
    st.info("Seidauk iha dadus CPUE loroloron iha database.")

# --- PARTE 3: GALERIA ESPÉSIE IKAN ---
st.divider()
st.header("🖼️ Galeria Espésie Ikan")
st.write("Hatudu foto no informasaun ba espécie ikan sira ne'ebé iha sistema.")

if not df_monthly.empty:
    df_foto = df_filtered.sort_values(by='percentage', ascending=False)
    cols = st.columns(5) 
    
    for index, row in df_foto.iterrows():
        species_tetun = row['species'] 
        percentage = row['percentage']
        weight = row['total_weight']
        img_path = f"images/{species_tetun}.jpg" 
        
        with cols[index % 5]:
            try:
                if os.path.exists(img_path):
                    st.image(img_path, width=120) 
                else:
                    st.image("https://via.placeholder.com/120x100?text=No+Image", width=120)
            except Exception:
                st.image("https://via.placeholder.com/120x100?text=Error+Image", width=120)
                
            st.markdown(f"**{species_tetun}**") 
            st.write(f"Persentajen: **{percentage}%**")
            st.write(f"Totál: **{weight:,.1f} kg**")
            st.write("---")
else:
    st.info("Seidauk iha dadus atu hatudu foto.")
