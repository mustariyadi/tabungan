import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Tabungan Keluarga", page_icon="💰", layout="wide")

# --- 2. DATABASE (Session State) ---
if 'data_nasabah' not in st.session_state:
    st.session_state.data_nasabah = pd.DataFrame([
        {"Nama": "Ayah", "Username": "ayah123", "Password": "123", "Saldo": 500000},
        {"Nama": "Ibu", "Username": "ibu123", "Password": "123", "Saldo": 750000}
    ])

if 'log_transaksi' not in st.session_state:
    st.session_state.log_transaksi = pd.DataFrame(columns=["Tanggal", "Nama", "Tipe", "Nominal", "Saldo Akhir"])

if 'role' not in st.session_state:
    st.session_state.role = None
    st.session_state.user_now = None

def logout():
    st.session_state.role = None
    st.session_state.user_now = None
    st.rerun()

# --- 3. HALAMAN LOGIN ---
if st.session_state.role is None:
    st.title("🔐 Login Sistem Tabungan")
    col_l, _ = st.columns([1, 2])
    with col_l:
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type="password")
        if st.button("Masuk", use_container_width=True):
            if u_in == "admin" and p_in == "admin123":
                st.session_state.role = "admin"
                st.rerun()
            elif u_in in st.session_state.data_nasabah['Username'].values:
                idx = st.session_state.data_nasabah.index[st.session_state.data_nasabah['Username'] == u_in][0]
                if p_in == str(st.session_state.data_nasabah.at[idx, 'Password']):
                    st.session_state.role = "nasabah"
                    st.session_state.user_now = u_in
                    st.rerun()
            st.error("Username atau Password salah!")

# --- 4. HALAMAN ADMIN ---
elif st.session_state.role == "admin":
    st.sidebar.title("🚀 Panel Admin")
    if st.sidebar.button("Logout"): logout()
    
    st.title("🛠️ Manajemen Tabungan Keluarga")
    t1, t2, t3 = st.tabs(["👥 Data & Edit Nasabah", "💸 Input Transaksi", "📜 Semua Mutasi"])

    with t1:
        st.subheader("Daftar Nasabah")
        st.dataframe(st.session_state.data_nasabah, use_container_width=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📝 Edit / Reset Nasabah")
            if not st.session_state.data_nasabah.empty:
                list_n = st.session_state.data_nasabah['Nama'].tolist()
                pilih = st.selectbox("Pilih nasabah untuk diedit:", list_n)
                idx_e = st.session_state.data_nasabah.index[st.session_state.data_nasabah['Nama'] == pilih][0]
                
                edit_nama = st.text_input("Nama:", value=st.session_state.data_nasabah.at[idx_e, 'Nama'])
                edit_user = st.text_input("Username:", value=st.session_state.data_nasabah.at[idx_e, 'Username'])
                edit_pass = st.text_input("Password:", value=st.session_state.data_nasabah.at[idx_e, 'Password'])
                
                if st.button("Update Data"):
                    st.session_state.data_nasabah.at[idx_e, 'Nama'] = edit_nama
                    st.session_state.data_nasabah.at[idx_e, 'Username'] = edit_user
                    st.session_state.data_nasabah.at[idx_e, 'Password'] = edit_pass
                    st.success(f"Data {pilih} berhasil diperbarui!")
                    st.rerun()

        with c2:
            st.markdown("### ➕ Tambah Nasabah")
            t_nama = st.text_input("Nama Lengkap:")
            t_user = st.text_input("Username Baru:")
            t_pass = st.text_input("Password Awal:", value="123")
            if st.button("Daftarkan"):
                if t_nama and t_user:
                    baru = pd.DataFrame([{"Nama": t_nama, "Username": t_user, "Password": t_pass, "Saldo": 0}])
                    st.session_state.data_nasabah = pd.concat([st.session_state.data_nasabah, baru], ignore_index=True)
                    st.success("Berhasil didaftarkan!")
                    st.rerun()

    with t2:
        st.subheader("Input Setoran / Penarikan")
        target = st.selectbox("Pilih Anggota", st.session_state.data_nasabah['Nama'])
        aksi = st.radio("Jenis Transaksi", ["Setoran", "Penarikan"])
        nominal = st.number_input("Nominal (Rp)", min_value=0, step=5000)
        
        if st.button("Proses Transaksi"):
            idx_t = st.session_state.data_nasabah.index[st.session_state.data_nasabah['Nama'] == target][0]
            s_lama = st.session_state.data_nasabah.at[idx_t, 'Saldo']
            
            if aksi == "Setoran":
                s_baru = s_lama + nominal
            else:
                s_baru = s_lama - nominal
            
            if s_baru < 0:
                st.error("Maaf, saldo tidak cukup untuk penarikan!")
            else:
                st.session_state.data_nasabah.at[idx_t, 'Saldo'] = s_baru
                # Catat Mutasi
                log_baru = pd.DataFrame([{
                    "Tanggal": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Nama": target,
                    "Tipe": aksi,
                    "Nominal": nominal,
                    "Saldo Akhir": s_baru
                }])
                st.session_state.log_transaksi = pd.concat([st.session_state.log_transaksi, log_baru], ignore_index=True)
                st.success(f"Transaksi {aksi} {target} berhasil!")
                st.rerun()

    with t3:
        st.subheader("Riwayat Transaksi Keseluruhan")
        st.dataframe(st.session_state.log_transaksi, use_container_width=True)

# --- 5. HALAMAN NASABAH ---
elif st.session_state.role == "nasabah":
    st.sidebar.button("Logout", on_click=logout)
    u_idx = st.session_state.data_nasabah.index[st.session_state.data_nasabah['Username'] == st.session_state.user_now][0]
    u_nama = st.session_state.data_nasabah.at[u_idx, 'Nama']
    u_saldo = st.session_state.data_nasabah.at[u_idx, 'Saldo']
    
    st.title(f"Selamat Datang, {u_nama}!")
    st.metric("Saldo Anda Saat Ini", f"Rp {u_saldo:,}")
    
    st.divider()
    st.subheader("📋 Riwayat Mutasi Rekening")
    mutasi_user = st.session_state.log_transaksi[st.session_state.log_transaksi['Nama'] == u_nama]
    
    if not mutasi_user.empty:
        st.table(mutasi_user)
        csv = mutasi_user.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Mutasi (CSV)", data=csv, file_name=f"Mutasi_{u_nama}.csv", mime="text/csv")
    else:
        st.info("Belum ada riwayat transaksi.")
        st.write("Lokasi file saat ini:", os.getcwd())