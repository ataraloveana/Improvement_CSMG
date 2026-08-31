import pandas as pd


# ============================================================
# KONFIGURASI
# ============================================================

MIN_SEQ = 1


# ============================================================
# NORMALISASI ROUTE
# ============================================================

def normalize_route(route):
    """
    Menyamakan format Route agar pencocokan antara
    Master Data dan Customer Data lebih konsisten.

    Contoh:
        " R001 " -> "R001"
        "r001"   -> "r001"

    Catatan:
    Tidak mengubah angka menjadi numeric karena Route
    dapat memiliki leading zero, misalnya "001".
    """

    if pd.isna(route):
        return None

    route = str(route).strip()

    if route == "":
        return None

    return route


# ============================================================
# BUILD SEQUENCE STATE
# ============================================================

def build_sequence_state(
    master_df: pd.DataFrame,
):
    """
    Membuat state sequence berdasarkan Route.

    Struktur hasil:

    {
        "R001": {
            "used": {2, 3, 4},
            "min": 1,
            "max": 4
        },

        "R002": {
            "used": {1, 2, 3},
            "min": 1,
            "max": 3
        }
    }

    Aturan:
    - MIN_SEQ selalu dimulai dari 1.
    - Sequence yang tidak valid diabaikan.
    - MAX adalah sequence terbesar yang terdapat
      pada Master Data untuk Route tersebut.
    """

    state = {}

    # --------------------------------------------------------
    # Pastikan kolom tersedia
    # --------------------------------------------------------

    required_columns = [
        "Route",
        "Seq",
    ]

    for column in required_columns:

        if column not in master_df.columns:

            raise ValueError(
                f"Kolom '{column}' tidak ditemukan "
                "pada Master Data."
            )

    # --------------------------------------------------------
    # Copy data
    # --------------------------------------------------------

    valid_master = master_df.copy()

    # --------------------------------------------------------
    # Normalisasi Route
    # --------------------------------------------------------

    valid_master["_route_normalized"] = (
        valid_master["Route"]
        .apply(normalize_route)
    )

    # --------------------------------------------------------
    # Konversi Seq menjadi numeric
    # --------------------------------------------------------

    valid_master["_seq_numeric"] = pd.to_numeric(
        valid_master["Seq"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Hanya gunakan data dengan:
    #
    # - Route valid
    # - Seq valid
    # --------------------------------------------------------

    valid_master = valid_master[
        valid_master["_route_normalized"].notna()
        &
        valid_master["_seq_numeric"].notna()
    ].copy()

    # --------------------------------------------------------
    # Sequence harus berupa bilangan bulat
    # --------------------------------------------------------

    valid_master["_seq_numeric"] = (
        valid_master["_seq_numeric"]
        .astype(int)
    )

    # --------------------------------------------------------
    # Sequence 0 atau negatif tidak digunakan
    #
    # Karena minimum sequence kita adalah 1.
    # --------------------------------------------------------

    valid_master = valid_master[
        valid_master["_seq_numeric"] >= MIN_SEQ
    ].copy()

    # --------------------------------------------------------
    # Group berdasarkan Route
    # --------------------------------------------------------

    for route, group in valid_master.groupby(
        "_route_normalized",
        dropna=False,
    ):

        # ----------------------------------------------------
        # Ambil seluruh sequence unik
        # ----------------------------------------------------

        seq_values = (
            group["_seq_numeric"]
            .dropna()
            .astype(int)
            .tolist()
        )

        if not seq_values:
            continue

        # ----------------------------------------------------
        # Sequence yang sudah digunakan
        # ----------------------------------------------------

        used = set(seq_values)

        # ----------------------------------------------------
        # Sequence maksimum
        # ----------------------------------------------------

        max_seq = max(used)

        # ----------------------------------------------------
        # Simpan state
        # ----------------------------------------------------

        state[route] = {
            "used": used,
            "min": MIN_SEQ,
            "max": max_seq,
        }

    return state


# ============================================================
# GET NEXT SEQUENCE
# ============================================================

def get_next_sequence(
    route,
    state,
):
    """
    Menentukan sequence berikutnya berdasarkan Route.

    Aturan:
    1. Jika Route belum ada:
       Seq pertama = 1.

    2. Jika Seq 1 belum digunakan:
       gunakan Seq 1 terlebih dahulu.

    3. Setelah Seq 1 terisi, cari gap terkecil
       mulai dari 1 sampai MAX.

    4. Jika tidak ada gap:
       gunakan MAX + 1.

    5. Seq yang baru diberikan langsung dimasukkan
       ke dalam used agar tidak diberikan kembali.
    """

    # --------------------------------------------------------
    # Normalisasi Route
    # --------------------------------------------------------

    route = normalize_route(route)

    if route is None:
        return None

    # --------------------------------------------------------
    # Route belum ada di state
    # --------------------------------------------------------

    if route not in state:

        state[route] = {
            "used": set(),
            "min": 1,
            "max": 0,
        }

    route_state = state[route]

    used = route_state["used"]

    # ========================================================
    # PRIORITAS UTAMA: CEK SEQ 1
    # ========================================================

    if 1 not in used:

        used.add(1)

        # Jadikan 1 sebagai minimum
        route_state["min"] = 1

        # Jika sebelumnya max = 0,
        # sekarang max menjadi 1
        if route_state["max"] < 1:
            route_state["max"] = 1

        return 1

    # ========================================================
    # SEQ 1 SUDAH ADA
    # Lanjut mencari gap
    # ========================================================

    min_seq = route_state["min"]

    max_seq = route_state["max"]

    # --------------------------------------------------------
    # Cari gap terkecil
    # --------------------------------------------------------

    for seq in range(
        min_seq,
        max_seq + 1,
    ):

        if seq not in used:

            used.add(seq)

            return seq

    # ========================================================
    # Tidak ada gap
    # Gunakan MAX + 1
    # ========================================================

    next_seq = max_seq + 1

    used.add(next_seq)

    route_state["max"] = next_seq

    return next_seq

# ============================================================
# ASSIGN SEQUENCE
# ============================================================

def assign_sequence(
    master_df: pd.DataFrame,
    customer_df: pd.DataFrame,
):
    """
    Menentukan Seq untuk Customer Data berdasarkan Route.

    Sequence diberikan secara berurutan dan setiap sequence
    yang sudah diberikan langsung dianggap terpakai.

    Contoh:

    Master Route R001:
        Seq = 2
        Seq = 3
        Seq = 4

    Customer baru:

        Customer A -> Seq 1
        Customer B -> Seq 5
        Customer C -> Seq 6
        Customer D -> Seq 7
    """

    master_df = master_df.copy()
    customer_df = customer_df.copy()

    # --------------------------------------------------------
    # Validasi kolom
    # --------------------------------------------------------

    if "Route" not in master_df.columns:

        raise ValueError(
            "Kolom 'Route' tidak ditemukan pada Master Data."
        )

    if "Seq" not in master_df.columns:

        raise ValueError(
            "Kolom 'Seq' tidak ditemukan pada Master Data."
        )

    if "Route" not in customer_df.columns:

        raise ValueError(
            "Kolom 'Route' tidak ditemukan pada Customer Data."
        )

    # --------------------------------------------------------
    # Build state dari Master
    # --------------------------------------------------------

    state = build_sequence_state(
        master_df
    )

    # --------------------------------------------------------
    # List hasil sequence
    # --------------------------------------------------------

    assigned_sequences = []

    # --------------------------------------------------------
    # Proses customer satu per satu
    # --------------------------------------------------------

    for _, row in customer_df.iterrows():

        route = normalize_route(
            row["Route"]
        )

        # ----------------------------------------------------
        # Jika Route kosong
        # ----------------------------------------------------

        if route is None:

            assigned_sequences.append(
                pd.NA
            )

            continue

        # ----------------------------------------------------
        # Ambil sequence berikutnya
        # ----------------------------------------------------

        next_seq = get_next_sequence(
            route,
            state,
        )

        assigned_sequences.append(
            next_seq
        )

    # --------------------------------------------------------
    # Simpan hasil
    # --------------------------------------------------------

    customer_df["Seq"] = pd.Series(
        assigned_sequences,
        index=customer_df.index,
        dtype="Int64",
    )

    return customer_df