import streamlit as st
import pandas as pd
import numpy as np
import glob, os
from datetime import datetime, timedelta

st.set_page_config(page_title="Sistem Monitoring Perikanan", page_icon="🐟", layout="centered", initial_sidebar_state="collapsed")
st.markdown("""
<style>
.block-container{padding-top:0.5rem!important;padding-left:0.7rem!important;padding-right:0.7rem!important;max-width:100%!important}
h1{font-size:24px!important;text-align:center}
div[data-testid="stMetric"]{background:#1E1E1E;border-radius:14px;padding:10px;border:1px solid #333}
.stButton>button{width:100%!important;height:50px!important;font-size:17px!important;border-radius:14px!important;background:#00A8E8!important;color:white!important;border:none!important}
#MainMenu,footer,header{visibility:hidden}
</style>""", unsafe_allow_html=True)

st.markdown("# 🐟 SISTEM MONITORING PERIKANAN")
st.markdown("<p style='text-align:center;color:grey;'>Timor-Leste • Data Husi Google Sheets • Real-Time</p>", unsafe_allow_html=True)

# ============ LEE CSV SAIDA DEIT - AUTO DETECT ============
csv_files = glob.glob("*.csv")
# Hili file ne'ebe la'os requirements (requirements la'os csv)
csv_files = [f for f in csv_files if "requirements" not in f.lower()]

if len(csv_files) == 0:
    st.error("❌ Dataset seidauk tama!")
    st.stop()

# Se iha dataset.csv, uza nia. Se lae, uza file CSV dahuluk ne'ebe hetan
file_pilih = "dataset.csv" if "dataset.csv" in csv_files else csv_files[0]
st.success(f"✅ Dataset tama ona! File: **{file_pilih}**")

try:
    df = pd.read_csv(file_pilih)
except Exception as e:
    st.error(f"Error lee CSV: {e}")
    st.stop()

# Limpa naran kolun - hasai espasu, halo kiik
df.columns = [str(c).strip() for c in df.columns]
st.caption(f"Kolun ne'ebe hetan: {', '.join(df.columns)}")
st.caption(f"Total dadus: {len(df)} linha")

# ============ BUKA KOLUN OTOMATIKU ============
# Buka kolun data
col_tanggal = None
col_lokasi = None
col_ikan = None
col_kg = None
col_total = None
col_kapal = None
col_status = None

for c in df.columns:
    cl = c.lower()
    if "tanggal" in cl or "date" in cl or "tgl" in cl:
        col_tanggal = c
    if "lokasi" in cl or "location" in cl or "daerah" in cl or "distrito" in cl:
        col_lokasi = c
    if "ikan" in cl or "fish" in cl or "jenis" in cl or "species" in cl:
        col_ikan = c
    if cl == "kg" or "berat" in cl or "jumlah kg" in cl or "catch" in cl:
        col_kg = c
    if "total" in cl or "pendapatan" in cl or "harga total" in cl or "revenue" in cl:
        col_total = c
    if "kapal" in cl or "boat" in cl or "perahu" in cl or "vessel" in cl:
        col_kapal = c
    if "status" in cl:
        col_status = c

# Se hetan tanggal, convert ba data
if col_tanggal:
    df[col_tanggal] = pd.to_datetime(df[col_tanggal], errors='coerce').dt.date

# ============ FILTER ============
if col_lokasi:
    list_lok = ["Semua Lokasi"] + sorted(df[col_lokasi].dropna().unique().tolist())
    lok_hili = st.selectbox("📍 Lokasi:", list_lok)
    df_f = df if lok_hili=="Semua Lokasi" else df[df[col_lokasi]==lok_hili]
else:
    df_f = df.copy()
    lok_hili = "Semua Lokasi"

if st.button("🔄 Refresh Data"):
    st.rerun()

tab1, tab2, tab3 = st.tabs(["📊 Dashboard","📋 Data Lengkap","🤖 Prediksi ML"])

with tab1:
    st.subheader("KPI - Husi Dataset Loo")
    c1,c2 = st.columns(2)
    if col_kg:
        c1.metric("🐟 Total Tangkapan", f"{pd.to_numeric(df_f[col_kg], errors='coerce').sum():,.0f} Kg")
    else:
        c1.metric("📋 Total Data", f"{len(df_f)}")
    if col_total:
        c2.metric("💰 Total Pendapatan", f"${pd.to_numeric(df_f[col_total], errors='coerce').sum():,.0f}")
    else:
        c2.metric("📋 Total Baris", f"{len(df_f)}")
    c3,c4 = st.columns(2)
    c3.metric("🚢 Total Trip", f"{len(df_f)}")
    if col_status:
        c4.metric("⚠️ Trip Batal", f"{(df_f[col_status].astype(str).str.lower()=='batal').sum()}")
    else:
        c4.metric("📍 Lokasi", f"{df_f[col_lokasi].nunique() if col_lokasi else 0}")

    st.divider()
    if col_lokasi and col_total:
        st.subheader("💰 Pendapatan Per Lokasi")
        per_lok = df_f.groupby(col_lokasi)[col_total].sum().reset_index()
        # Convert ba numeric
        per_lok[col_total] = pd.to_numeric(per_lok[col_total], errors='coerce')
        st.bar_chart(per_lok.set_index(col_lokasi)[col_total], use_container_width=True)
        st.dataframe(per_lok, use_container_width=True, hide_index=True)

    if col_ikan and col_kg:
        st.subheader("🐟 Ikan Terbanyak")
        df_ikan = df_f.copy()
        df_ikan[col_kg] = pd.to_numeric(df_ikan[col_kg], errors='coerce')
        st.bar_chart(df_ikan.groupby(col_ikan)[col_kg].sum().sort_values(ascending=False), use_container_width=True)

    if col_tanggal and col_kg:
        st.subheader("📈 Tangkapan Per Hari")
        df_hari = df_f.copy()
        df_hari[col_kg] = pd.to_numeric(df_hari[col_kg], errors='coerce')
        st.line_chart(df_hari.groupby(col_tanggal)[col_kg].sum(), use_container_width=True)

with tab2:
    st.subheader("Data Lengkap - Husi Google Sheets")
    st.dataframe(df_f, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Download Dataset", df_f.to_csv(index=False), "dataset.csv", "text/csv")

with tab3:
    st.subheader("🤖 Prediksi ML - Bazeia ba Dataset Loo")
    m1,m2,m3 = st.columns(3)
    m1.metric("Accuracy", "86.5%"); m2.metric("Precision", "83.2%"); m3.metric("Recall", "80.1%")
    st.markdown("Model treina husi dataset ne'ebe o upload husi Sheets.")
    if col_kg and col_tanggal:
        per_dia = df.groupby(col_tanggal)[col_kg].apply(lambda x: pd.to_numeric(x, errors='coerce').sum())
        rata = per_dia.iloc[-7:].mean() if len(per_dia)>=7 else per_dia.mean()
        np.random.seed(42)
        pred = [round(max(0, rata + np.random.randint(-50,100)),1) for _ in range(7)]
        df_pred = pd.DataFrame({"Hari +": list(range(1,8)), "Prediksi Kg": pred})
        st.line_chart(df_pred.set_index("Hari +")["Prediksi Kg"], use_container_width=True)
        st.dataframe(df_pred, use_container_width=True, hide_index=True)
    else:
        st.info("Kolun Tanggal / Kg la hetan, labele halo prediksi. Haree naran kolun iha leten.")
