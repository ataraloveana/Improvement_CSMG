import io

import pandas as pd


def dataframe_to_excel(
    df: pd.DataFrame,
):
    """
    Mengubah DataFrame menjadi Excel dalam memory.

    Tidak membuat file permanen di server.
    """

    buffer = io.BytesIO()

    with pd.ExcelWriter(
        buffer,
        engine="openpyxl",
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Result",
        )

    buffer.seek(0)

    return buffer