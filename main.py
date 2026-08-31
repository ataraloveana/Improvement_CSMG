import io

import pandas as pd
import streamlit as st
import altair as alt

from algorithms.cycle import assign_cycle
from algorithms.route import assign_route
from algorithms.sequence import assign_sequence
from utils.validation import validate_columns
from utils.export import dataframe_to_excel
from algorithms.preprocessing import (
    preprocess_data,  
    remove_internal_columns,
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="MARS - Meter Assignment & Routing System",
    page_icon="☄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 15px;
        color: #6b7280;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 21px;
        font-weight: 600;
        margin-top: 15px;
        margin-bottom: 10px;
    }


    .amras-card {
        background-color: #1f2937;
        border: 1px solid #374151;
        border-radius: 14px;
        padding: 24px;
        min-height: 130px;
        margin-bottom: 20px;
    }

    .amras-card-title {
        font-size: 16px;
        font-weight: 600;
        color: #d1d5db;
        margin-bottom: 12px;
    }

    .amras-card-value {
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.2;
    }

    .amras-card-description {
        font-size: 13px;
        color: #9ca3af;
        margin-top: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Dashboard"

if "master_df" not in st.session_state:
    st.session_state.master_df = None

if "customer_df" not in st.session_state:
    st.session_state.customer_df = None

if "result_df" not in st.session_state:
    st.session_state.result_df = None

if "processing_done" not in st.session_state:
    st.session_state.processing_done = False

# ============================================================
# HELPER FUNCTION
# ============================================================

def read_uploaded_file(uploaded_file):
    """
    Membaca file CSV atau Excel sebagai teks.
    Menjaga leading zero pada ID Pelanggan, RT, RW, Blok, dll.
    """

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):

        return pd.read_csv(
            uploaded_file,
            sep=";",
            dtype=str,
            keep_default_na=False,
        )

    elif file_name.endswith(".xlsx"):

        return pd.read_excel(
            uploaded_file,
            dtype=str,
            keep_default_na=False,
        )

    elif file_name.endswith(".xls"):

        return pd.read_excel(
            uploaded_file,
            dtype=str,
            keep_default_na=False,
        )

    else:

        raise ValueError(
            "Format file tidak didukung."
        )


def reset_session():
    """
    Menghapus seluruh data yang tersimpan pada session.
    """

    keys_to_clear = [
        "master_df",
        "customer_df",
        "result_df",
        "processing_done",
    ]

    for key in keys_to_clear:
        st.session_state[key] = None

    st.session_state.processing_done = False

    st.session_state.current_page = "🏠 Dashboard"


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">☄️ MARS</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
        Meter Assignment & Routing System<br>
        Automated Cycle • Route • Sequence Assignment
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("☄️MARS")

    menu_options = [
        "🏠 Dashboard",
        "🗃️ Data Upload & Processing",
        "📋 Result",
    ]

    current_index = menu_options.index(
        st.session_state.current_page
    )

    page = st.radio(
        "Menu",
        menu_options,
        index=current_index,
    )

# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.subheader("Dashboard")

    master_rows = (
        len(st.session_state.master_df)
        if st.session_state.master_df is not None
        else 0
    )

    customer_rows = (
        len(st.session_state.customer_df)
        if st.session_state.customer_df is not None
        else 0
    )

    result_rows = (
        len(st.session_state.result_df)
        if st.session_state.result_df is not None
        else 0
    )

    master_count = 0
    customer_count = 0
    result_count = 0

    if st.session_state.get("master_df") is not None:
        master_count = len(st.session_state.master_df)

    if st.session_state.get("customer_df") is not None:
        customer_count = len(st.session_state.customer_df)

    if st.session_state.get("result_df") is not None:
        result_count = len(st.session_state.result_df)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f"""
            <div class="amras-card">
                <div class="amras-card-title">🗂️ Master Data</div>
                <div class="amras-card-value">{master_count:,}</div>
                <div class="amras-card-description">Total data master</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="amras-card">
                <div class="amras-card-title">👤 Customer Baru</div>
                <div class="amras-card-value">{customer_count:,}</div>
                <div class="amras-card-description">Data pelanggan baru</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="amras-card">
                <div class="amras-card-title">⚙️ Hasil Processing</div>
                <div class="amras-card-value">{result_count:,}</div>
                <div class="amras-card-description">Data berhasil diproses</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    st.subheader("Workflow")

    st.markdown(
        """
        **① Upload Master Data**

        ↓

        **② Upload Data Pelanggan Baru**

        ↓

        **③ Preprocessing**

        ↓

        **④ Penentuan Cycle**

        ↓

        **⑤ Penentuan Route**

        ↓

        **⑥ Penentuan Sequence**

        ↓

        **⑦ Review Hasil**

        ↓

        **⑧ Export CSV / Excel**
        """
    )

    st.info(
        """
        Data yang di-upload digunakan hanya untuk proses
        pada session aplikasi. Tidak ada database permanen
        yang digunakan pada versi ini.
        """
    )


# ============================================================
# UPLOAD DATA + PROCESSING
# ============================================================

elif page == "🗃️ Data Upload & Processing":

    # ========================================================
    # INFORMASI FORMAT DATA
    # ========================================================

    st.markdown("### 📋 Format Data yang Dibutuhkan")

    st.info(
        """
        **Sebelum melakukan upload, pastikan file Master Data dan
        Data Pelanggan Baru memiliki judul kolom berikut:**
        """
    )

    required_upload_columns = [
        "ID Pelanggan",
        "Cycle",
        "route baca",
        "sequence",
        "Area Revised",
        "Blok Revised",
        "Rt Revised",
        "Rw Revised",
        "Kecamatan",
        "Nama Desa",
    ]

    # --------------------------------------------------------
    # TAMPILKAN DAFTAR KOLOM
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
            **Kolom Identitas & Routing**
            """
        )

        st.markdown(
            """
            - `ID Pelanggan`
            - `Cycle`
            - `route baca`
            - `sequence`
            - `Area Revised`
            """
        )

    with col2:

        st.markdown(
            """
            **Kolom Lokasi**
            """
        )

        st.markdown(
            """
            - `Blok Revised`
            - `Rt Revised`
            - `Rw Revised`
            - `Kecamatan`
            - `Nama Desa`
            """
        )

    st.warning(
        """
        ⚠️ **Penting:** Nama judul kolom harus sama persis dengan
        format di atas. `ID Pelanggan`, `Rt Revised`, dan `Rw Revised`
        akan dibaca sebagai **teks** sehingga angka 0 di depan tetap dipertahankan.
        """
    )

    st.divider()

    # ========================================================
    # UPLOAD MASTER DATA
    # ========================================================

    st.markdown("### 📑 Master Data")

    master_file = st.file_uploader(
        "Upload Master Data",
        type=["csv", "xlsx"],
        key="master_uploader",
    )

    # ========================================================
    # UPLOAD CUSTOMER DATA
    # ========================================================

    st.markdown("### 📑 Data Pelanggan Baru")

    customer_file = st.file_uploader(
        "Upload Data Pelanggan Baru",
        type=["csv", "xlsx"],
        key="customer_uploader",
    )

    # ========================================================
    # BACA MASTER DATA
    # ========================================================

    if master_file is not None:

        try:

            master_df = read_uploaded_file(master_file)

            st.session_state.master_df = master_df

            st.success(
                f"✅ Master Data berhasil dibaca: "
                f"{len(master_df):,} rows"
            )

        except Exception as e:

            st.error(
                f"❌ Gagal membaca Master Data: {e}"
            )

    # ========================================================
    # BACA CUSTOMER DATA
    # ========================================================

    if customer_file is not None:

        try:

            customer_df = read_uploaded_file(customer_file)

            st.session_state.customer_df = customer_df

            st.success(
                f"✅ Data Pelanggan Baru berhasil dibaca: "
                f"{len(customer_df):,} rows"
            )

        except Exception as e:

            st.error(
                f"❌ Gagal membaca Data Pelanggan Baru: {e}"
            )

    # ========================================================
    # CEK DATA
    # ========================================================

    master_df = st.session_state.master_df
    customer_df = st.session_state.customer_df

    if (
        master_df is not None
        and customer_df is not None
    ):

        st.divider()

        st.subheader(
            "📝 Data Siap Diproses"
        )

        col1, col2 = st.columns(2)

        with col1:

            st.info(
                f"🗃️ **Master Data**\n\n"
                f"{len(master_df):,} rows"
            )

        with col2:

            st.info(
                f"👥 **Pelanggan Baru**\n\n"
                f"{len(customer_df):,} rows"
            )

        # ====================================================
        # PREVIEW DATA
        # ====================================================

        with st.expander(
            "👁️ Preview Data"
        ):

            tab1, tab2 = st.tabs(
                [
                    "Master Data",
                    "Pelanggan Baru",
                ]
            )

            with tab1:

                st.dataframe(
                    master_df.head(100),
                    use_container_width=True,
                    height=350,
                )

            with tab2:

                st.dataframe(
                    customer_df.head(100),
                    use_container_width=True,
                    height=350,
                )

        st.divider()

        # ====================================================
        # PROCESSING
        # ====================================================

        st.subheader(
            "⚙️ Processing"
        )

        if st.button(
            "🚀 MULAI PROCESSING",
            type="primary",
            use_container_width=True,
        ):

            progress = st.progress(0)

            status = st.empty()

            try:

                # ------------------------------------------------
                # STEP 1
                # ------------------------------------------------

                status.info(
                    "Step 1/4 — Preprocessing..."
                )

                master_clean, customer_clean = (
                    preprocess_data(
                        master_df.copy(),
                        customer_df.copy(),
                    )
                )

                progress.progress(25)

                # ------------------------------------------------
                # STEP 2
                # ------------------------------------------------

                status.info(
                    "Step 2/4 — Menentukan Cycle..."
                )

                customer_clean = assign_cycle(
                    master_clean,
                    customer_clean,
                )

                progress.progress(50)

                # ------------------------------------------------
                # STEP 3
                # ------------------------------------------------

                status.info(
                    "Step 3/4 — Menentukan Route..."
                )

                customer_clean = assign_route(
                    master_clean,
                    customer_clean,
                )

                progress.progress(75)

                # ------------------------------------------------
                # STEP 4
                # ------------------------------------------------

                status.info(
                    "Step 4/4 — Menentukan Sequence..."
                )

                customer_clean = assign_sequence(
                    master_clean,
                    customer_clean,
                )

                progress.progress(100)

                # ------------------------------------------------
                # REMOVE INTERNAL COLUMNS
                # ------------------------------------------------

                customer_clean = (
                    remove_internal_columns(
                        customer_clean
                    )
                )

                # ------------------------------------------------
                # SAVE RESULT
                # ------------------------------------------------

                st.session_state.result_df = (
                    customer_clean
                )

                st.session_state.processing_done = True

                status.success(
                    "✅ Processing berhasil!"
                )

                st.success(
                    f"{len(customer_clean):,} data berhasil diproses."
                )

            except Exception as e:

                st.error(
                    f"❌ Processing gagal: {e}"
                )

        # ============================================================
        # LIHAT RESULT
        # ============================================================

        if st.session_state.processing_done:

            st.divider()

            st.success(
                "Data sudah berhasil diproses dan siap ditampilkan."
            )

            if st.button(
                "📋 Lihat Result",
                type="primary",
                use_container_width=True,
            ):

                st.session_state.current_page = (
                    "📋 Result"
                )

                st.rerun()

# ============================================================
# RESULT
# ============================================================

elif page == "📋 Result":

    st.subheader("📋 Processing Result")

    # ========================================================
    # AMBIL RESULT DATA
    # ========================================================

    result_df = st.session_state.result_df

    if result_df is None:

        st.warning(
            "⚠️ Belum ada hasil processing."
        )

        st.info(
            "Silakan upload data dan jalankan processing "
            "terlebih dahulu."
        )

        st.stop()

    # --------------------------------------------------------
    # Copy agar data asli di session tidak berubah
    # --------------------------------------------------------

    df = result_df.copy()

    # ========================================================
    # VALIDASI KOLOM
    # ========================================================

    required_result_columns = [
        "Cycle",
        "route baca",
        "sequence",
    ]

    missing_columns = [
        col
        for col in required_result_columns
        if col not in df.columns
    ]

    if missing_columns:

        st.error(
            "❌ Kolom hasil processing tidak lengkap."
        )

        st.write(
            "Kolom yang tidak ditemukan:"
        )

        st.code(
            "\n".join(missing_columns)
        )

        st.write(
            "Kolom yang tersedia pada result:"
        )

        st.code(
            "\n".join(df.columns.tolist())
        )

        st.stop()

    # ========================================================
    # NORMALISASI DATA UNTUK ANALISIS
    # ========================================================

    # --------------------------------------------------------
    # Cycle
    # --------------------------------------------------------

    cycle_series = (
    df["Cycle"]
    .astype("string")
    .fillna("")
    .str.strip()
    )

    # --------------------------------------------------------
    # Route
    # --------------------------------------------------------

    route_series = (
    df["route baca"]
    .astype("string")
    .fillna("")
    .str.strip()
    )

    # --------------------------------------------------------
    # Sequence
    # --------------------------------------------------------

    sequence_series = (
    df["sequence"]
    .astype("string")
    .fillna("")
    .str.strip()
    )

    # ========================================================
    # METRICS
    # ========================================================

    total_customer = len(df)

    cycle_filled = (
        cycle_series != ""
    ).sum()

    route_filled = (
        route_series != ""
    ).sum()

    sequence_filled = (
        sequence_series != ""
    ).sum()

    cycle_unique = (
        cycle_series[
            cycle_series != ""
        ]
        .nunique()
    )

    route_unique = (
        route_series[
            route_series != ""
        ]
        .nunique()
    )

    sequence_unique = (
        sequence_series[
            sequence_series != ""
        ]
        .nunique()
    )

    # ========================================================
    # METRIC CARDS
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            label="👥 Total Customer",
            value=f"{total_customer:,}",
        )

    with col2:

        st.metric(
            label="🔵 Cycle",
            value=f"{cycle_filled:,}",
            delta=f"{cycle_unique:,} Cycle unik",
        )

    with col3:

        st.metric(
            label="🟢 Route",
            value=f"{route_filled:,}",
            delta=f"{route_unique:,} Route unik",
        )

    with col4:

        st.metric(
            label="🟠 Sequence",
            value=f"{sequence_filled:,}",
            delta=f"{sequence_unique:,} Sequence unik",
        )

    st.divider()

    # ========================================================
    # VISUALIZATION
    # ========================================================

    st.subheader("📊 Result Visualization")

    st.caption(
        "Visualisasi berikut menunjukkan distribusi dan "
        "keberhasilan penentuan Cycle, Route, dan Sequence "
        "untuk data pelanggan baru."
    )

    # ========================================================
    # CHART 1
    # DISTRIBUSI CYCLE
    # ========================================================

    st.markdown(
        "### 1️⃣ Distribusi Pelanggan Baru berdasarkan Cycle"
    )

    st.caption(
        "Chart menunjukkan jumlah pelanggan baru "
        "yang masuk ke masing-masing Cycle."
    )

    # ========================================================
    # SIAPKAN DATA CYCLE
    # ========================================================

    cycle_chart_data = (
        cycle_series
        .replace("", "Belum Ditentukan")
        .value_counts()
        .reset_index()
    )

    cycle_chart_data.columns = [
        "Cycle",
        "Jumlah Customer",
    ]


    # ========================================================
    # FUNGSI SORTING CYCLE
    # ========================================================

    def cycle_sort_key(value):

        value = str(value).strip()

        if value.isdigit():
            return (0, int(value))

        return (1, value)


    # ========================================================
    # URUTKAN CYCLE
    # ========================================================

    cycle_order = sorted(
        cycle_chart_data["Cycle"].unique(),
        key=cycle_sort_key,
    )


    # ========================================================
    # TAMPILKAN CHART
    # ========================================================

    if not cycle_chart_data.empty:

        chart_cycle = (
            alt.Chart(cycle_chart_data)
            .mark_bar()
            .encode(
                x=alt.X(
                    "Jumlah Customer:Q",
                    title="Jumlah Customer",
                    axis=alt.Axis(
                        format="d",
                        grid=True,
                    ),
                ),

                y=alt.Y(
                    "Cycle:N",
                    title="Cycle",
                    sort=cycle_order,
                    axis=alt.Axis(
                        labelAngle=0,
                        labelLimit=150,
                        titlePadding=15,
                    ),
                ),

                tooltip=[
                    alt.Tooltip(
                        "Cycle:N",
                        title="Cycle",
                    ),
                    alt.Tooltip(
                        "Jumlah Customer:Q",
                        title="Jumlah Customer",
                        format="d",
                    ),
                ],
            )
            .properties(
                height=max(
                    350,
                    len(cycle_order) * 45,
                )
            )
        )

        st.altair_chart(
            chart_cycle,
            use_container_width=True,
        )

    else:

        st.info(
            "Belum terdapat data Cycle."
        )


    st.caption(
        "Jumlah pelanggan ditampilkan berdasarkan masing-masing Cycle."
    )

    st.divider()

    # ========================================================
    # CHART 2
    # SUMMARY STATUS PENENTUAN
    # ========================================================

    st.markdown(
        "### 2️⃣ Summary Status Penentuan"
    )

    st.caption(
        "Persentase keberhasilan penentuan Cycle, Route, "
        "dan Sequence pada data pelanggan baru."
    )

    # ========================================================
    # HITUNG STATUS
    # ========================================================

    summary_data = pd.DataFrame(
        {
            "Variabel": [
                "Cycle",
                "Route",
                "Sequence",
            ],
            "Terisi": [
                cycle_filled,
                route_filled,
                sequence_filled,
            ],
            "Belum Terisi": [
                total_customer - cycle_filled,
                total_customer - route_filled,
                total_customer - sequence_filled,
            ],
        }
    )

    # ========================================================
    # HITUNG PERSENTASE
    # ========================================================

    summary_data["Persentase"] = (
        summary_data["Terisi"]
        / total_customer
        * 100
    ).fillna(0)

    summary_data["Persentase"] = (
        summary_data["Persentase"]
        .clip(0, 100)
    )

    # ========================================================
    # TAMPILKAN SUMMARY
    # ========================================================

    for _, row in summary_data.iterrows():

        variable = row["Variabel"]
        terisi = int(row["Terisi"])
        belum_terisi = int(row["Belum Terisi"])
        percentage = row["Persentase"]

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        col1, col2 = st.columns(
            [2, 1]
        )

        with col1:

            st.markdown(
                f"""
                <div style="
                    font-size: 17px;
                    font-weight: 600;
                    margin-bottom: 5px;
                ">
                    {variable}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:

            st.markdown(
                f"""
                <div style="
                    text-align: right;
                    font-size: 17px;
                    font-weight: 700;
                    margin-bottom: 5px;
                ">
                    {percentage:.1f}%
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------
        # PROGRESS BAR
        # ----------------------------------------------------

        st.progress(
            int(round(percentage))
        )

        # ----------------------------------------------------
        # DETAIL
        # ----------------------------------------------------

        detail_col1, detail_col2 = st.columns(2)

        with detail_col1:

            st.caption(
                f"✓ {terisi:,} Terisi"
            )

        with detail_col2:

            st.markdown(
                f"<div style='text-align:right;'>"
                f"{belum_terisi:,} Belum Terisi"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ========================================================
    # CHART 3
    # CYCLE VS ROUTE
    # ========================================================

    st.markdown(
        "### 3️⃣Distribusi Pelanggan berdasarkan Cycle dan Route"
    )

    st.caption(
    "Setiap bar menunjukkan jumlah pelanggan pada masing-masing "
    "Cycle, sedangkan warna menunjukkan pembagian berdasarkan Route."
    )

    # ========================================================
    # SIAPKAN DATA
    # ========================================================

    cycle_route_df = pd.DataFrame(
        {
            "Cycle": cycle_series.replace(
                "",
                "Belum Ditentukan",
            ),
            "Route": route_series.replace(
                "",
                "Belum Ditentukan",
            ),
        }
    )

    # ========================================================
    # AGREGASI DATA
    # ========================================================

    cycle_route_data = (
        cycle_route_df
        .groupby(
            [
                "Cycle",
                "Route",
            ],
            as_index=False,
        )
        .size()
        .rename(
            columns={
                "size": "Jumlah Customer"
            }
        )
    )

    # ========================================================
    # URUTAN CYCLE
    # ========================================================

    def cycle_sort_key(value):

        value = str(value).strip()

        if value.isdigit():
            return (
                0,
                int(value),
            )

        return (
            1,
            value,
        )


    cycle_order = sorted(
        cycle_route_data["Cycle"].unique(),
        key=cycle_sort_key,
    )

    # ========================================================
    # BUAT HORIZONTAL STACKED BAR
    # ========================================================

    if not cycle_route_data.empty:

        chart = (
            alt.Chart(
                cycle_route_data
            )
            .mark_bar()
            .encode(

                # --------------------------------------------
                # X = JUMLAH CUSTOMER
                # --------------------------------------------

                x=alt.X(
                    "Jumlah Customer:Q",
                    title="Jumlah Customer",
                    axis=alt.Axis(
                        format="d",
                        grid=True,
                    ),
                ),

                # --------------------------------------------
                # Y = CYCLE
                # --------------------------------------------

                y=alt.Y(
                    "Cycle:N",
                    title="Cycle",
                    sort=cycle_order,
                    axis=alt.Axis(
                        labelAngle=0,
                        labelLimit=150,
                        titlePadding=15,
                    ),
                ),

                # --------------------------------------------
                # COLOR = ROUTE
                # --------------------------------------------

                color=alt.Color(
                    "Route:N",
                    title="Route",
                    legend=alt.Legend(
                        orient="bottom",
                        columns=6,
                        titleFontSize=14,
                        labelFontSize=13,
                    ),
                ),

                # --------------------------------------------
                # TOOLTIP
                # --------------------------------------------

                tooltip=[
                    alt.Tooltip(
                        "Cycle:N",
                        title="Cycle",
                    ),
                    alt.Tooltip(
                        "Route:N",
                        title="Route",
                    ),
                    alt.Tooltip(
                        "Jumlah Customer:Q",
                        title="Jumlah Customer",
                        format="d",
                    ),
                ],
            )
            .properties(
                height=max(
                    300,
                    len(cycle_order) * 55,
                ),
            )
        )

        st.altair_chart(
            chart,
            use_container_width=True,
        )

    else:

        st.info(
            "Data Cycle dan Route belum tersedia."
        )

    st.caption(
        "Panjang total setiap bar menunjukkan jumlah pelanggan "
        "pada Cycle tersebut, sedangkan setiap warna menunjukkan "
        "jumlah pelanggan berdasarkan Route."
    )

    st.divider()

    # ========================================================
    # FILTER
    # ========================================================

    st.subheader("🔎 Filter Result")

    st.caption(
        "Gunakan filter berikut untuk mencari dan "
        "menampilkan data tertentu."
    )

    filter_col1, filter_col2, filter_col3 = (
        st.columns(3)
    )

    # ========================================================
    # SEARCH CUSTOMER
    # ========================================================

    with filter_col1:

        search_column = None

        # Prioritas menggunakan No.Pelanggan
        if "No.Pelanggan" in df.columns:

            search_column = "No.Pelanggan"

        # Alternatif jika menggunakan ID Pelanggan
        elif "ID Pelanggan" in df.columns:

            search_column = "ID Pelanggan"

        if search_column is not None:

            search = st.text_input(
                "💡 No. Pelanggan",
                placeholder=(
                    "Masukkan nomor pelanggan..."
                ),
            )

        else:

            search = ""

            st.info(
                "Kolom No.Pelanggan tidak tersedia."
            )

    # ========================================================
    # FILTER CYCLE
    # ========================================================

    with filter_col2:

        cycle_options = sorted(
            [
                value
                for value in cycle_series.unique()
                if value != ""
            ]
        )

        selected_cycle = st.multiselect(
            "🔵 Cycle",
            options=cycle_options,
            placeholder="Pilih Cycle...",
        )

    # ========================================================
    # FILTER ROUTE
    # ========================================================

    with filter_col3:

        route_options = sorted(
            [
                value
                for value in route_series.unique()
                if value != ""
            ]
        )

        selected_route = st.multiselect(
            "🟢 Route",
            options=route_options,
            placeholder="Pilih Route...",
        )

    # ========================================================
    # APPLY FILTER
    # ========================================================

    filtered_df = df.copy()

    # --------------------------------------------------------
    # Search No. Pelanggan
    # --------------------------------------------------------

    if search:

        if search_column is not None:

            filtered_df = filtered_df[
                filtered_df[search_column]
                .astype(str)
                .str.contains(
                    search,
                    case=False,
                    na=False,
                )
            ]

    # --------------------------------------------------------
    # Filter Cycle
    # --------------------------------------------------------

    if selected_cycle:

        filtered_df = filtered_df[
            filtered_df["Cycle"]
            .fillna("")
            .astype(str)
            .str.strip()
            .isin(selected_cycle)
        ]

    # --------------------------------------------------------
    # Filter Route
    # --------------------------------------------------------

    if selected_route:

        filtered_df = filtered_df[
            filtered_df["route baca"]
            .fillna("")
            .astype(str)
            .str.strip()
            .isin(selected_route)
        ]

    # ========================================================
    # RESULT COUNT
    # ========================================================

    st.divider()

    st.caption(
        f"Menampilkan "
        f"**{len(filtered_df):,}** data "
        f"dari total **{total_customer:,}** data pelanggan."
    )

    # ========================================================
    # DATA RESULT
    # ========================================================

    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=600,
        hide_index=True,
    )

    # ========================================================
    # EXPORT
    # ========================================================

    st.divider()

    st.subheader("📥 Export Result")

    st.caption(
        "Download hasil processing dalam format CSV atau Excel."
    )

    col1, col2 = st.columns(2)

    # --------------------------------------------------------
    # CSV
    # --------------------------------------------------------

    csv_data = result_df.to_csv(
        index=False,
        encoding="utf-8-sig",
    )

    with col1:

        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name="MARS_Result.csv",
            mime="text/csv",
            use_container_width=True,
        )


    # --------------------------------------------------------
    # EXCEL
    # --------------------------------------------------------

    excel_buffer = dataframe_to_excel(
        result_df
    )

    with col2:

        st.download_button(
            label="📊 Download Excel",
            data=excel_buffer,
            file_name="MARS_Result.xlsx",
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            use_container_width=True,
        )


    # ========================================================
    # CLEAR SESSION
    # ========================================================

    st.divider()

    st.warning(
        """
        Setelah selesai menggunakan aplikasi, gunakan tombol
        di bawah untuk menghapus seluruh data dari session aplikasi.
        """
    )

    if st.button(
        "🗑️ Hapus Semua Data Session",
        type="secondary",
        use_container_width=True,
    ):

        reset_session()

        st.success(
            "Semua data session telah dihapus."
        )

        st.rerun()