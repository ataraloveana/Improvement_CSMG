import pandas as pd


# ============================================================
# HELPER
# ============================================================

def build_unique_lookup(
    df: pd.DataFrame,
    keys: list,
    value_column: str,
):
    """
    Membuat lookup berdasarkan kombinasi keys.

    Jika satu kombinasi keys memiliki lebih dari satu Route,
    maka dipilih Route dengan jumlah data paling sedikit.

    Contoh:

        Cycle + Jalan + Blok
        ---------------------
        1 + Mawar + A1 -> Route 01 = 50 data
        1 + Mawar + A1 -> Route 02 = 35 data
        1 + Mawar + A1 -> Route 03 = 42 data

    Maka hasil lookup:
        (1, mawar, a1) -> Route 02

    Jika hanya terdapat satu Route, Route tersebut langsung digunakan.
    """

    lookup = {}

    valid_df = df.copy()

    # ========================================================
    # PASTIKAN SELURUH KEY TERSEDIA
    # ========================================================

    for key in keys:

        if key not in valid_df.columns:

            raise ValueError(
                f"Kolom '{key}' tidak ditemukan."
            )

    if value_column not in valid_df.columns:

        raise ValueError(
            f"Kolom '{value_column}' tidak ditemukan."
        )

    # ========================================================
    # BUANG BARIS YANG KEY-NYA KOSONG
    # ========================================================

    for key in keys:

        valid_df = valid_df[
            valid_df[key]
            .fillna("")
            .astype(str)
            .str.strip()
            != ""
        ]

    # ========================================================
    # BERSIHKAN ROUTE
    # ========================================================

    valid_df[value_column] = (
        valid_df[value_column]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Buang Route kosong
    valid_df = valid_df[
        valid_df[value_column] != ""
    ]

    # ========================================================
    # GROUP BERDASARKAN KEYS + ROUTE
    # ========================================================

    route_counts = (
        valid_df
        .groupby(
            keys + [value_column],
            dropna=False,
        )
        .size()
        .reset_index(
            name="jumlah_data"
        )
    )

    # ========================================================
    # PILIH ROUTE DENGAN JUMLAH DATA TERKECIL
    # ========================================================

    for key_values, group in route_counts.groupby(
        keys,
        dropna=False,
    ):

        # ----------------------------------------------------
        # Jika hanya satu Route
        # ----------------------------------------------------

        if not isinstance(
            key_values,
            tuple,
        ):

            key_values = (
                key_values,
            )

        # ----------------------------------------------------
        # Urutkan berdasarkan jumlah data terkecil
        # ----------------------------------------------------

        group = group.sort_values(
            by="jumlah_data",
            ascending=True,
        )

        # ----------------------------------------------------
        # Ambil Route dengan jumlah paling sedikit
        # ----------------------------------------------------

        selected_route = group.iloc[0][
            value_column
        ]

        lookup[key_values] = selected_route

    return lookup

# ============================================================
# ROUTE ASSIGNMENT
# ============================================================

def assign_route(
    master_df: pd.DataFrame,
    customer_df: pd.DataFrame,
):
    """
    Menentukan Route berdasarkan:

    PRIORITAS 1:
        Cycle + Jalan + Blok

    PRIORITAS 2:
        Cycle + Jalan + RT + RW

    Prioritas 2 digunakan jika:
        - Blok kosong
        ATAU
        - kombinasi Cycle + Jalan + Blok tidak ditemukan.
    """

    master_df = master_df.copy()
    customer_df = customer_df.copy()

    # ========================================================
    # LOOKUP 1
    # Cycle + Jalan + Blok
    # ========================================================

    lookup_block = build_unique_lookup(
        master_df,
        [
            "Cycle",
            "__jalan",
            "__blok",
        ],
        "Route",
    )

    # ========================================================
    # LOOKUP 2
    # Cycle + Jalan + RT + RW
    # ========================================================

    lookup_rtrw = build_unique_lookup(
        master_df,
        [
            "Cycle",
            "__jalan",
            "__rt",
            "__rw",
        ],
        "Route",
    )

    # ========================================================
    # PROSES CUSTOMER
    # ========================================================

    routes = []

    for _, row in customer_df.iterrows():

        cycle = (
            str(row["Cycle"]).strip()
            if not pd.isna(row["Cycle"])
            else ""
        )

        jalan = (
            str(row["__jalan"]).strip()
            if not pd.isna(row["__jalan"])
            else ""
        )

        blok = (
            str(row["__blok"]).strip()
            if not pd.isna(row["__blok"])
            else ""
        )

        rt = (
            str(row["__rt"]).strip()
            if not pd.isna(row["__rt"])
            else ""
        )

        rw = (
            str(row["__rw"]).strip()
            if not pd.isna(row["__rw"])
            else ""
        )

        route = None

        # ====================================================
        # VALIDASI MINIMAL
        # ====================================================

        if cycle == "" or jalan == "":

            routes.append(pd.NA)
            continue

        # ====================================================
        # PRIORITAS 1
        # Cycle + Jalan + Blok
        # ====================================================

        if blok != "":

            key_block = (
                cycle,
                jalan,
                blok,
            )

            route = lookup_block.get(
                key_block
            )

        # ====================================================
        # PRIORITAS 2
        # Cycle + Jalan + RT + RW
        # ====================================================

        if route is None:

            if (
                rt != ""
                and rw != ""
            ):

                key_rtrw = (
                    cycle,
                    jalan,
                    rt,
                    rw,
                )

                route = lookup_rtrw.get(
                    key_rtrw
                )

        # ====================================================
        # SIMPAN
        # ====================================================

        routes.append(route)

    # ========================================================
    # ASSIGN ROUTE
    # ========================================================

    customer_df["Route"] = pd.Series(
        routes,
        index=customer_df.index,
        dtype="object",
    )

    # ========================================================
    # KOSONG -> NA
    # ========================================================

    customer_df["Route"] = (
        customer_df["Route"]
        .replace("", pd.NA)
    )

    return customer_df