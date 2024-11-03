# Import Libraries
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import folium_static

# Memuat Dataset
data_path = "dashboard/main_data.csv"  # Sesuaikan jika diperlukan
merged_data = pd.read_csv(data_path)

# Mengonversi kolom tanggal menjadi datetime
if 'review_answer_timestamp' in merged_data.columns:
    merged_data['review_answer_timestamp'] = pd.to_datetime(merged_data['review_answer_timestamp'], errors='coerce')

# Judul dan Pengantar
st.title("Dashboard Analisis Pelanggan dan Penjualan")
st.markdown("""
Dashboard ini menjawab pertanyaan bisnis berikut:
1. Bagaimana distribusi skor ulasan dari pelanggan, dan apakah terdapat pola hubungan antara skor ulasan dan harga produk?
2. Di wilayah (state) mana penjualan produk paling banyak terjadi, dan apakah wilayah ini memengaruhi biaya pengiriman?

Selain itu, kami juga melakukan Analisis RFM, Analisis Geospasial, dan Pengelompokan (Clustering) pada dataset ini.
""")

# Tinjauan Dataset
st.subheader("Tinjauan Dataset")
st.write(merged_data.head())
st.write("Kolom dalam dataset:", merged_data.columns.tolist())

# Pertanyaan 1: Analisis Skor Ulasan
st.subheader("Pertanyaan 1: Distribusi Skor Ulasan dan Hubungan dengan Harga Produk")
if 'review_score' in merged_data.columns and 'product_price' in merged_data.columns:
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))

    # Distribusi Skor Ulasan
    sns.countplot(data=merged_data, x='review_score', ax=ax[0])
    ax[0].set_title("Distribusi Skor Ulasan")
    ax[0].set_xlabel("Skor Ulasan")
    ax[0].set_ylabel("Jumlah")

    # Hubungan antara Skor Ulasan dan Harga Produk
    sns.boxplot(data=merged_data, x='review_score', y='product_price', ax=ax[1])
    ax[1].set_title("Hubungan Skor Ulasan dengan Harga Produk")
    ax[1].set_xlabel("Skor Ulasan")
    ax[1].set_ylabel("Harga Produk")

    st.pyplot(fig)
else:
    st.write("Kolom yang diperlukan untuk analisis ini tidak ditemukan.")

# Pertanyaan 2: Distribusi Penjualan dan Biaya Pengiriman Berdasarkan State
st.subheader("Pertanyaan 2: Distribusi Penjualan dan Biaya Pengiriman Berdasarkan State")
if 'seller_state' in merged_data.columns and 'freight_value' in merged_data.columns:
    sales_by_state = merged_data.groupby('seller_state').agg({
        'order_id': 'count',
        'freight_value': 'mean'
    }).rename(columns={'order_id': 'Total Penjualan', 'freight_value': 'Biaya Pengiriman Rata-rata'}).reset_index()

    # Visualisasi Peta
    m = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)  # Berpusat di Brasil
    for _, row in sales_by_state.iterrows():
        folium.Marker(
            location=[-14, -51],  # Ganti dengan koordinat yang relevan jika tersedia
            popup=f"{row['seller_state']}: {row['Total Penjualan']} penjualan, Biaya Rata-rata: ${row['Biaya Pengiriman Rata-rata']:.2f}",
            icon=folium.Icon(color="blue")
        ).add_to(m)

    folium_static(m)

    # Menampilkan Data sebagai Tabel
    st.write("Penjualan dan Biaya Pengiriman per State")
    st.dataframe(sales_by_state)
else:
    st.write("Kolom yang diperlukan untuk analisis ini tidak ditemukan.")

# Analisis RFM
st.subheader("Analisis RFM")
if 'customer_id' in merged_data.columns and 'review_answer_timestamp' in merged_data.columns and 'order_id' in merged_data.columns and 'payment_value' in merged_data.columns:
    end_date = merged_data['review_answer_timestamp'].max() + pd.Timedelta(days=1)
    
    rfm = merged_data.groupby('customer_id').agg({
        'review_answer_timestamp': lambda x: (end_date - x.max()).days,
        'order_id': 'count',
        'payment_value': 'sum'
    }).rename(columns={
        'review_answer_timestamp': 'Recency',
        'order_id': 'Frequency',
        'payment_value': 'Monetary'
    }).reset_index()
    
    st.write("Tabel RFM")
    st.dataframe(rfm.head())

    # Visualisasi RFM
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=rfm, x='Recency', y='Monetary', size='Frequency', sizes=(50, 500), alpha=0.5)
    plt.title("Analisis RFM: Recency vs Monetary")
    plt.xlabel("Recency (hari sejak pembelian terakhir)")
    plt.ylabel("Monetary (Total Pengeluaran)")
    st.pyplot(plt.gcf())
else:
    st.write("Kolom yang diperlukan untuk analisis RFM tidak ditemukan.")

# Analisis Clustering
st.subheader("Analisis Clustering")
## Pengelompokan Manual Berdasarkan Umur
if 'customer_age' in merged_data.columns:
    age_bins = [0, 30, 50, 70, 100]
    age_labels = ['0-30', '31-50', '51-70', '>70']
    merged_data['age_group'] = pd.cut(merged_data['customer_age'], bins=age_bins, labels=age_labels)

    # Pengeluaran Berdasarkan Kelompok Umur
    age_grouping = merged_data.groupby('age_group')['payment_value'].sum().reset_index()
    st.write("Pengeluaran Berdasarkan Kelompok Umur")
    st.bar_chart(age_grouping.set_index('age_group'))
else:
    st.write("Data umur pelanggan tidak tersedia untuk analisis clustering.")

## Binning Berdasarkan Pengeluaran
if 'payment_value' in merged_data.columns:
    bins = [0, 50, 150, 500, 1000, 5000]
    labels = ['Sangat Rendah', 'Rendah', 'Sedang', 'Tinggi', 'Sangat Tinggi']
    merged_data['spending_category'] = pd.cut(merged_data['payment_value'], bins=bins, labels=labels)

    # Analisis Kategori Pengeluaran
    spending_grouping = merged_data.groupby('spending_category')['order_id'].count().reset_index()
    st.write("Penjualan Berdasarkan Kategori Pengeluaran")
    st.bar_chart(spending_grouping.set_index('spending_category'))
else:
    st.write("Data pengeluaran tidak tersedia untuk analisis clustering.")
