import pandas as pd


# ============================================================
# REQUIRED COLUMNS
# ============================================================

MASTER_COLUMNS = [
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


CUSTOMER_COLUMNS = [
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


# ============================================================
# VALIDATION
# ============================================================

def validate_columns(
    df: pd.DataFrame,
    data_type: str,
):
    """
    Memeriksa apakah kolom wajib tersedia.
    """

    if data_type == "master":

        required = MASTER_COLUMNS

    elif data_type == "customer":

        required = CUSTOMER_COLUMNS

    else:

        raise ValueError(
            "data_type harus 'master' atau 'customer'."
        )

    existing_columns = set(
        df.columns
    )

    missing = [
        col
        for col in required
        if col not in existing_columns
    ]

    return {
        "valid": len(missing) == 0,
        "missing": missing,
    }