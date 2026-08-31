import pandas as pd


# ============================================================
# HELPER
# ============================================================

def clean_text(series: pd.Series) -> pd.Series:
    """
    Membersihkan text untuk kebutuhan matching.

    - NaN -> ""
    - menghapus BOM
    - mengubah non-breaking space
    - lowercase
    - menghapus seluruh spasi/whitespace
    """

    return (
        series
        .fillna("")
        .astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.replace("\u00a0", " ", regex=False)
        .str.lower()
        .str.replace(r"\s+", "", regex=True)
    )

def clean_code(series: pd.Series) -> pd.Series:
    """
    Membersihkan kode seperti RT, RW, Blok, dll.

    Semua nilai diperlakukan sebagai TEXT sehingga
    leading zero tetap dipertahankan.
    """

    return (
        series
        .fillna("")
        .astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.replace("\u00a0", " ", regex=False)
        .str.strip()
        .str.lower()
    )

def clean_id_pelanggan(series: pd.Series) -> pd.Series:
    """
    Membersihkan ID Pelanggan sebagai teks.

    Tujuan:
    - Memastikan ID Pelanggan bertipe string
    - Mempertahankan angka 0 di depan
    - Menghapus spasi di awal/akhir
    - Menghapus BOM dan non-breaking space
    """

    return (
        series
        .fillna("")
        .astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.replace("\u00a0", " ", regex=False)
        .str.strip()
    )

# ============================================================
# MAIN PREPROCESSING
# ============================================================

def preprocess_data(
    master_df: pd.DataFrame,
    customer_df: pd.DataFrame,
):
    """
    Melakukan preprocessing Master Data dan Customer Data.

    Kolom internal:
        __jalan
        __blok
        __rt
        __rw
        __kecamatan
        __desa

    Kolom asli tetap dipertahankan.
    """

    master_df = master_df.copy()
    customer_df = customer_df.copy()

    # --------------------------------------------------------
    # Pastikan kolom wajib tersedia
    # --------------------------------------------------------

    required_columns = [
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

    for col in required_columns:

        if col not in master_df.columns:
            raise ValueError(
                f"Kolom '{col}' tidak ditemukan pada Master Data."
            )

        if col not in customer_df.columns:
            raise ValueError(
                f"Kolom '{col}' tidak ditemukan pada Data Pelanggan Baru."
            )

    # --------------------------------------------------------
    # ID Pelanggan
    # --------------------------------------------------------

    if "ID Pelanggan" in master_df.columns:
        master_df["ID Pelanggan"] = clean_id_pelanggan(
            master_df["ID Pelanggan"]
        )

    if "ID Pelanggan" in customer_df.columns:
        customer_df["ID Pelanggan"] = clean_id_pelanggan(
            customer_df["ID Pelanggan"]
        )

    # --------------------------------------------------------
    # Cleaning jalan
    # --------------------------------------------------------

    master_df["__jalan"] = clean_text(
        master_df["Area Revised"]
    )

    customer_df["__jalan"] = clean_text(
        customer_df["Area Revised"]
    )

    # --------------------------------------------------------
    # Cleaning kecamatan
    # --------------------------------------------------------
    
    master_df["__kecamatan"] = clean_text(
        master_df["Kecamatan"]
    )

    customer_df["__kecamatan"] = clean_text(
        customer_df["Kecamatan"]
    )

    # --------------------------------------------------------
    # Cleaning desa
    # --------------------------------------------------------
    
    master_df["__desa"] = clean_text(
        master_df["Nama Desa"]
    )

    customer_df["__desa"] = clean_text(
        customer_df["Nama Desa"]
    )

    # --------------------------------------------------------
    # Cleaning blok
    # --------------------------------------------------------

    master_df["__blok"] = clean_code(
        master_df["Blok Revised"]
    )

    customer_df["__blok"] = clean_code(
        customer_df["Blok Revised"]
    )

    # --------------------------------------------------------
    # Cleaning RT
    # --------------------------------------------------------

    master_df["__rt"] = clean_code(
        master_df["Rt Revised"]
    )

    customer_df["__rt"] = clean_code(
        customer_df["Rt Revised"]
    )

    # --------------------------------------------------------
    # Cleaning RW
    # --------------------------------------------------------

    master_df["__rw"] = clean_code(
        master_df["Rw Revised"]
    )

    customer_df["__rw"] = clean_code(
        customer_df["Rw Revised"]
    )

    # --------------------------------------------------------
    # Cycle
    # --------------------------------------------------------

    master_df["Cycle"] = (
        master_df["Cycle"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    customer_df["Cycle"] = (
        customer_df["Cycle"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Route
    # --------------------------------------------------------

    master_df["Route"] = (
        master_df["route baca"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    customer_df["Route"] = (
        customer_df["route baca"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Sequence
    # --------------------------------------------------------

    master_df["Seq"] = pd.to_numeric(
        master_df["sequence"],
        errors="coerce",
    )

    customer_df["Seq"] = pd.to_numeric(
        customer_df["sequence"],
        errors="coerce",
    )

    return master_df, customer_df

def remove_internal_columns(df):
    """
    Menyiapkan DataFrame untuk hasil akhir.

    Hasil dari algoritma internal:
        Route -> route baca
        Seq   -> sequence

    Kemudian menghapus seluruh kolom internal.
    """

    df = df.copy()

    # ========================================================
    # KEMBALIKAN HASIL ROUTE
    # ========================================================

    if "Route" in df.columns:

        df["route baca"] = df["Route"]

    # ========================================================
    # KEMBALIKAN HASIL SEQUENCE
    # ========================================================

    if "Seq" in df.columns:

        df["sequence"] = df["Seq"]

    # ========================================================
    # HAPUS KOLOM INTERNAL
    # ========================================================

    internal_columns = [
        "__jalan",
        "__blok",
        "__rt",
        "__rw",
        "__kecamatan",
        "__desa",
        "Route",
        "Seq",
    ]

    return df.drop(
        columns=[
            col
            for col in internal_columns
            if col in df.columns
        ]
    )