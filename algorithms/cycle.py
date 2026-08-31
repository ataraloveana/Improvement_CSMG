import pandas as pd


# ============================================================
# BUILD CYCLE LOOKUP
# ============================================================

def build_cycle_lookup(
    master_df: pd.DataFrame,
):
    """
    Membuat lookup Cycle berdasarkan 3 tingkat:

    Level 1:
        Jalan

    Level 2:
        Jalan + Kecamatan

    Level 3:
        Jalan + Kecamatan + Desa

    Logika:
        Jalan
            ↓
        jika >1 Cycle
            ↓
        Jalan + Kecamatan
            ↓
        jika >1 Cycle
            ↓
        Jalan + Kecamatan + Desa
    """

    master = master_df.copy()

    # ========================================================
    # VALIDASI
    # ========================================================

    required_columns = [
        "__jalan",
        "__kecamatan",
        "__desa",
        "Cycle",
    ]

    for col in required_columns:

        if col not in master.columns:

            raise ValueError(
                f"Kolom '{col}' tidak ditemukan "
                "pada Master Data."
            )

    # ========================================================
    # NORMALISASI TAMBAHAN
    # ========================================================

    for col in [
        "__jalan",
        "__kecamatan",
        "__desa",
        "Cycle",
    ]:

        master[col] = (
            master[col]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # ========================================================
    # LEVEL 1
    # JALAN
    # ========================================================

    lookup_level_1 = {}

    valid = master[
        (master["__jalan"] != "")
        &
        (master["Cycle"] != "")
    ]

    grouped = valid.groupby(
        "__jalan"
    )

    for jalan, group in grouped:

        cycles = (
            group["Cycle"]
            .dropna()
            .unique()
            .tolist()
        )

        lookup_level_1[jalan] = cycles

    # ========================================================
    # LEVEL 2
    # JALAN + KECAMATAN
    # ========================================================

    lookup_level_2 = {}

    valid = master[
        (master["__jalan"] != "")
        &
        (master["__kecamatan"] != "")
        &
        (master["Cycle"] != "")
    ]

    grouped = valid.groupby(
        [
            "__jalan",
            "__kecamatan",
        ]
    )

    for key, group in grouped:

        cycles = (
            group["Cycle"]
            .dropna()
            .unique()
            .tolist()
        )

        lookup_level_2[key] = cycles

    # ========================================================
    # LEVEL 3
    # JALAN + KECAMATAN + DESA
    # ========================================================

    lookup_level_3 = {}

    valid = master[
        (master["__jalan"] != "")
        &
        (master["__kecamatan"] != "")
        &
        (master["__desa"] != "")
        &
        (master["Cycle"] != "")
    ]

    grouped = valid.groupby(
        [
            "__jalan",
            "__kecamatan",
            "__desa",
        ]
    )

    for key, group in grouped:

        cycles = (
            group["Cycle"]
            .dropna()
            .unique()
            .tolist()
        )

        lookup_level_3[key] = cycles

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "level_1": lookup_level_1,
        "level_2": lookup_level_2,
        "level_3": lookup_level_3,
    }


# ============================================================
# FIND CYCLE
# ============================================================

def find_cycle(
    row,
    lookup,
):
    """
    Menentukan Cycle dengan metode bertingkat:

    Level 1:
        Jalan

    Level 2:
        Jalan + Kecamatan

    Level 3:
        Jalan + Kecamatan + Desa

    Semakin tinggi level, semakin spesifik pencarian.
    """

    jalan = str(
        row["__jalan"]
    ).strip()

    kecamatan = str(
        row["__kecamatan"]
    ).strip()

    desa = str(
        row["__desa"]
    ).strip()

    # ========================================================
    # LEVEL 1
    # JALAN
    # ========================================================

    if jalan != "":

        cycles = lookup[
            "level_1"
        ].get(
            jalan,
            []
        )

        # ----------------------------------------------------
        # Hanya 1 Cycle
        # ----------------------------------------------------

        if len(cycles) == 1:

            return (
                cycles[0],
                "Level 1 - Jalan",
                "Matched",
            )

        # ----------------------------------------------------
        # Lebih dari 1 Cycle
        # Lanjut Level 2
        # ----------------------------------------------------

        # Tidak perlu return di sini.
        # Program otomatis lanjut ke Level 2.

    # ========================================================
    # LEVEL 2
    # JALAN + KECAMATAN
    # ========================================================

    if (
        jalan != ""
        and kecamatan != ""
    ):

        key = (
            jalan,
            kecamatan,
        )

        cycles = lookup[
            "level_2"
        ].get(
            key,
            []
        )

        # ----------------------------------------------------
        # Hanya 1 Cycle
        # ----------------------------------------------------

        if len(cycles) == 1:

            return (
                cycles[0],
                "Level 2 - Jalan + Kecamatan",
                "Matched",
            )

        # ----------------------------------------------------
        # Lebih dari 1 Cycle
        # Lanjut Level 3
        # ----------------------------------------------------

    # ========================================================
    # LEVEL 3
    # JALAN + KECAMATAN + DESA
    # ========================================================

    if (
        jalan != ""
        and kecamatan != ""
        and desa != ""
    ):

        key = (
            jalan,
            kecamatan,
            desa,
        )

        cycles = lookup[
            "level_3"
        ].get(
            key,
            []
        )

        # ----------------------------------------------------
        # Hanya 1 Cycle
        # ----------------------------------------------------

        if len(cycles) == 1:

            return (
                cycles[0],
                "Level 3 - Jalan + Kecamatan + Desa",
                "Matched",
            )

        # ----------------------------------------------------
        # Lebih dari 1 Cycle
        # ----------------------------------------------------

        if len(cycles) > 1:

            return (
                pd.NA,
                "Level 3 - Jalan + Kecamatan + Desa",
                "Ambiguous",
            )

    # ========================================================
    # NOT FOUND
    # ========================================================

    return (
        pd.NA,
        "Tidak ditemukan",
        "Not Found",
    )


# ============================================================
# ASSIGN CYCLE
# ============================================================

def assign_cycle(
    master_df: pd.DataFrame,
    customer_df: pd.DataFrame,
):
    """
    Menentukan Cycle pelanggan baru.

    Prioritas pencarian:

        1. Jalan
        2. Jalan + Kecamatan
        3. Jalan + Kecamatan + Desa

    Jika suatu level hanya menghasilkan 1 Cycle,
    maka Cycle tersebut langsung digunakan.

    Jika menghasilkan lebih dari 1 Cycle,
    pencarian dilanjutkan ke level berikutnya.
    """

    master_df = master_df.copy()
    customer_df = customer_df.copy()

    # ========================================================
    # BUILD LOOKUP
    # ========================================================

    lookup = build_cycle_lookup(
        master_df
    )

    # ========================================================
    # FIND CYCLE
    # ========================================================

    results = customer_df.apply(
        lambda row: find_cycle(
            row,
            lookup,
        ),
        axis=1,
        result_type="expand",
    )

    results.columns = [
        "__calculated_cycle",
        "Cycle_Matching_Level",
        "Cycle_Matching_Status",
    ]

    # ========================================================
    # SIMPAN CYCLE
    # ========================================================

    customer_df["Cycle"] = (
        results[
            "__calculated_cycle"
        ]
    )

    # ========================================================
    # SIMPAN INFORMASI MATCHING
    # ========================================================

    customer_df[
        "Cycle_Matching_Level"
    ] = results[
        "Cycle_Matching_Level"
    ]

    customer_df[
        "Cycle_Matching_Status"
    ] = results[
        "Cycle_Matching_Status"
    ]

    return customer_df