import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import time

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Tabungan Keluarga Digital", page_icon="💰", layout="wide")

# --- 2. KONEKSI GOOGLE SHEETS ---
# Koneksi ini membaca data dari link yang Anda simpan di Streamlit Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def fetch_data():
    # Membaca tab data_nasabah dan data_mutasi dengan TTL=0 agar selalu update
    df_n = conn.read(worksheet="data_nasabah", ttl=0)
    df_m = conn.read(worksheet="data_mutasi", ttl=0)
    # Pastikan kolom Saldo adalah angka
    df_n['Saldo'] = pd.to_numeric(df_n['Saldo'])
    return df_n, df_m

# Inisialisasi Data ke Session State (Memori Sementara Browser)
if 'data_nasabah' not in st.session_state:
    n, m = fetch_data()
    st.session_state.data_nasabah = n
    st.session_state.log_transaksi = m

if 'role' not in st.session_state:
    st.session_state.role = None
    st.session_state.user_now = None

# Fungsi Simpan Permanen ke Google Sheets
def save_permanently():
    conn.update(worksheet="data_nasabah", data=st.session_state.data_nasabah)
    conn.update(worksheet="data_mutasi", data=st.session_state.log_transaksi)
    st.cache_data.clear() # Reset cache agar data terbaru langsung terbaca

# --- 3. LOGIKA LOGIN & LOGOUT ---
def logout():
    st.session_state.role = None
    st.session_state.user_now = None
    st.rerun()

if st.session_state.role is None:
    st.title("🔐 Login Sistem Tabungan")
    col_login, _ = st.columns([1, 2])
    with col_login:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Masuk", use_container_width=True):
            # Cek Login Admin
            if u == "admin" and p == "admin123":
                st.session_state.role = "admin"
                st.rerun()
            # Cek Login Nasabah (Keluarga)
            elif u in st.session_state.data_nasabah['Username'].values:
                idx = st.session_state.data_nasabah.index[st.session_state.data_nasabah['Username'] == u][0]
                if str(p) == str(st.session_state.data_nasabah.at[idx, 'Password']):
                    st.session_state.role = "nasabah"
                    st.session_state.user_now = u
                    st.rerun()
            st.error("Login Gagal! Periksa Username dan Password.")

# --- 4. HALAMAN ADMIN (ORANG TUA) ---
elif st.session_state.role == "admin":
    st.sidebar.header(f"Admin: Pusat Kontrol")
    st.sidebar.button("Keluar / Logout", on_click=logout)
    
    st.title("🛠️ Panel Administrasi Tabungan")
    
    tab1, tab2, tab3 = st.tabs(["👥 Data Anggota", "💸 Input Transaksi", "📜 Seluruh Mutasi"])

    with tab1:
        st.subheader("Daftar Saldo Keluarga")
        st.dataframe(st.session_state.data_nasabah, use_container_width=True, hide_index=True)
        
        with st.expander("➕ Tambah Anggota Keluarga Baru"):
            new_nama = st.text_input("Nama Lengkap")
            new_user = st.text_input("Username Baru")
            new_pass = st.text_input("Password Baru", value="123")
            if st.button("Daftarkan Anggota"):
                if new_nama and new_user:
                    new_row = pd.DataFrame([{"Nama": new_nama, "Username": new_user, "Password": new_pass, "Saldo": 0}])
                    st.session_state.data_nasabah = pd.concat([st.session_state.data_nasabah, new_row], ignore_index=True)
                    save_permanently()
                    st.success(f"Anggota {new_nama} berhasil didaftarkan!")
                    time.sleep(1)
                    st.rerun()

    with tab2:
        st.subheader("Catat Setoran / Penarikan")
        target = st.selectbox("Pilih Nama Anggota", st.session_state.data_nasabah['Nama'])
        aksi = st.radio("Jenis Transaksi", ["Setoran", "Penarikan"], horizontal=True)
        nominal = st.number_input("Jumlah Uang (Rp)", min_value=0, step=1000)
        
        if st.button("Simpan Transaksi Ke Cloud", type="primary"):
            idx_t = st.session_state.data_nasabah.index[st.session_state.data_nasabah['Nama'] == target][0]
            
            # Update Saldo
            if aksi == "Setoran":
                st.session_state.data_nasabah.at[idx_t, 'Saldo'] += nominal
            else:
                if st.session_state.data_nasabah.at[idx_t, 'Saldo'] < nominal:
                    st.error("❌ Saldo tidak mencukupi untuk penarikan ini!")
                    st.stop()
                st.session_state.data_nasabah.at[idx_t, 'Saldo'] -= nominal
            
            # Catat ke Mutasi
            new_log = pd.DataFrame([{
                "Tanggal": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Nama": target,
                "Tipe": aksi,
                "Nominal": f"Rp {nominal:,}",
                "Saldo Akhir": f"Rp {st.session_state.data_nasabah.at[idx_t, 'Saldo']:,}"
            }])
            st.session_state.log_transaksi = pd.concat([st.session_state.log_transaksi, new_log], ignore_index=True)
            
            # SIMPAN KE GOOGLE SHEETS
            with st.spinner("Sedang menyimpan ke Google Sheets..."):
                save_permanently()
            
            st.success(f"✅ Berhasil! {aksi} untuk {target} sebesar Rp {nominal:,} telah tersimpan.")
            st.balloons()
            time.sleep(2)
            st.rerun()

    with tab3:
        st.subheader("Riwayat Transaksi Global")
        st.dataframe(st.session_state.log_transaksi, use_container_width=True, hide_index=True)

# --- 5. HALAMAN NASABAH (ANGGOTA KELUARGA) ---
elif st.session_state.role == "nasabah":
    st.sidebar.button("Logout", on_click=logout)
    
    # Cari data user yang login
    u_idx = st.session_state.data_nasabah.index[st.session_state.data_nasabah['Username'] == st.session_state.user_now][0]
    nama_user = st.session_state.data_nasabah.at[u_idx, 'Nama']
    saldo_user = st.session_state.data_nasabah.at[u_idx, 'Saldo']
    
    st.title(f"Selamat Datang, {nama_user}! 👋")
    
    col_saldo, _ = st.columns([1, 1])
    with col_saldo:
        st.metric("Saldo Tabungan Anda", f"Rp {saldo_user:,}")
    
    st.divider()
    st.subheader("📊 Riwayat Tabungan Saya")
    
    # Filter log hanya untuk user ini
    filter_log = st.session_state.log_transaksi[st.session_state.log_transaksi['Nama'] == nama_user]
    
    if not filter_log.empty:
        st.table(filter_log.iloc[::-1]) # Tampilkan dari yang terbaru (dibalik)
    else:
        st.info("Belum ada riwayat transaksi masuk.")
