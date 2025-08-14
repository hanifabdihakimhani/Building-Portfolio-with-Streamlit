import streamlit as st
import pandas as pd
import plotly.express as px

# ---- set konfigurasi halaman ----
st.set_page_config(
    page_title='Dashboard Analisis Penjualan',
    layout='wide',
    initial_sidebar_state='expanded'
)

# -- fungsi untuk memuat data --
@st.cache_data
def load_data():
    return pd.read_csv("data/ecommerce_data.csv")

# load data penjualan
df_sales = load_data()
df_sales[['InvoiceDate']] = df_sales[['InvoiceDate']].apply(pd.to_datetime)

# judul dashboard 
st.markdown("<h1 style='text-align: center;'>Dashboard Analisis Penjualan</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Dashboard interaktif ini menyediakan gambaran umum performa penjualan.</h3>", unsafe_allow_html=True)

# Sidebar Navigation
min_date = df_sales['InvoiceDate'].min().date()
max_date = df_sales['InvoiceDate'].max().date()

date_range = st.sidebar.date_input(
    "Pilih Rentang Tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date_filter = pd.to_datetime(date_range[0])
    end_date_filter = pd.to_datetime(date_range[1])
    filtered_df = df_sales[(df_sales['InvoiceDate'] >= start_date_filter) &
                           (df_sales['InvoiceDate'] <= end_date_filter)]
else: 
    # kalau filter date-nya belum tuntas
    filtered_df = df_sales 

page = st.sidebar.selectbox(
    "Pilih Halaman:",
    ["Performa Penjualan", "Analisis Produk", "Analisis Waktu"]
)

st.markdown("<h4>KPI Penjualan</h4>", unsafe_allow_html=True)

total_sales = filtered_df['TotalPrice'].sum()
total_orders = filtered_df['InvoiceNo'].nunique()
avg_order_value = total_sales / total_orders if total_orders > 0 else 0 # handle kalau total order 0
total_products_sold = filtered_df['Quantity'].sum()

# KPI
kpi = st.container() 
with kpi:
    
    col1, col2, col3, col4 = st.columns(4)  
    
    with col1:
        st.metric(label="Total Penjualan", value=f"$ {total_sales:,.2f}")
    with col2:
        st.metric(label="Jumlah Pesanan", value=f"{total_orders:}") 
    with col3:
        st.metric(label="Rata-Rata Nilai Pesanan", value=f"$ {avg_order_value:,.2f}")
    with col4:
        st.metric(label="Jumlah Produk Terjual", value=f"{total_products_sold:}")
    
# --- Tampilan Berdasarkan Halaman yang Dipilih ---
if page == "Performa Penjualan":
    tab_transaction_by_country, tab_total_sales_by_country = st.tabs(["Total Transaksi Tiap Negara", "Total Penjualan Tiap Negara"])
    
    country_stats = filtered_df.groupby('Country').agg({
            'InvoiceNo': 'nunique',
            'TotalPrice': 'sum'
        }).rename(columns={
            'InvoiceNo': 'Total_Transactions',
            'TotalPrice': 'Total_Sales'
        }).sort_values(by='Total_Sales', ascending=False).head(10)
        
    with tab_transaction_by_country:
        fig_transaction_by_country = px.bar(
            country_stats,  
            x=country_stats.index,  
            y='Total_Transactions',  
            title="Total Transaksi Tiap Negara",
            labels={'Total_Transactions': 'Total Transaksi', 'Country': 'Negara'}
        )

        st.plotly_chart(fig_transaction_by_country, use_container_width=True)
        
    with tab_total_sales_by_country:
        fig_total_sales_by_country = px.bar(
            country_stats,
            x=country_stats.index,
            y='Total_Sales',
            title="Total Sales Tiap Negara",
            labels={'Total_Sales': 'Total Penjualan', 'Country': 'Negara'}
        )
    
        st.plotly_chart(fig_total_sales_by_country, use_container_width=True)
    
elif page == "Analisis Produk":
    col_top_product, col_favorite_product = st.columns(2)
    
    # --- Top 10 Produk ---
    with col_top_product:
        st.write("### Top 10 Produk Terlaris")
        top_product_sold = filtered_df.groupby('Description')['Quantity'].sum().nlargest(10).sort_values(ascending=True).reset_index() # agregasi

        # bar chart
        fig_top_products = px.bar(
          top_product_sold,
          x='Quantity',
          y='Description',
          orientation='h'
        )

        st.plotly_chart(fig_top_products, use_container_width=True)
    
    # --- Favorite Product ---
    with col_favorite_product:
        st.write("### Produk Favorite Tiap Negara")
        top_products_per_country = (
            filtered_df.groupby(['Country', 'Description'])['Quantity']
            .sum()
            .reset_index()
            .sort_values(['Quantity'], ascending=[False])
            .groupby('Country')
            .head(1)
            .reset_index(drop=True)
        )

        top_products_per_country = top_products_per_country.nlargest(10, 'Quantity').sort_values(by='Quantity', ascending=True)
        
        # bar chart
        fig_top_products_per_country = px.bar(
          top_products_per_country,
          x='Quantity',
          y='Description',
          color='Country',
          orientation='h'
        )

        st.plotly_chart(fig_top_products_per_country, use_container_width=True)
        
elif page == "Analisis Waktu":
    filtered_df['InvoiceMonth'] = filtered_df['InvoiceDate'].dt.strftime('%Y-%m')
    
    sales_by_month = filtered_df.groupby('InvoiceMonth')['TotalPrice'].sum().reset_index()
    
    fig_monthly_sales = px.line(
        sales_by_month,
        x='InvoiceMonth', 
        y='TotalPrice',
        markers=True,
        title="Total Penjualan Bulanan",
        labels={'InvoiceMonth': 'Bulan', 'TotalPrice': 'Total Penjualan'},
        hover_name='InvoiceMonth'  
    )
    
    st.plotly_chart(fig_monthly_sales, use_container_width=True)

