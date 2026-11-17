import pandas as pd
import streamlit as st

from generate_data import BANK_COLS, PLATFORM_COLS, generate
from reconcile import reconcile, to_display

st.set_page_config(page_title="Payments Reconciliation", layout="wide")
st.title("Month-end payments reconciliation")
st.caption("Platform ledger vs bank settlements - find out why the books don't balance.")

mode = st.sidebar.radio("Data source", ["Generate synthetic data", "Upload CSVs"])
year = st.sidebar.number_input("Year", 2000, 2100, 2026)
month = st.sidebar.number_input("Month", 1, 12, 10)

if mode == "Generate synthetic data":
    seed = st.sidebar.number_input("Seed", 0, 99999, 42)
    n = st.sidebar.slider("Transactions", 100, 2000, 400, 50)
    platform, bank, truth = generate(seed=int(seed), n=n, year=int(year), month=int(month))
    p_df = pd.DataFrame(platform, columns=PLATFORM_COLS)
    b_df = pd.DataFrame(bank, columns=BANK_COLS)
    with st.sidebar.expander("Planted gaps (answer key)"):
        st.json({k: len(v) for k, v in truth.items()})
else:
    up_p = st.sidebar.file_uploader("Platform CSV", type="csv")
    up_b = st.sidebar.file_uploader("Bank CSV", type="csv")
    if not (up_p and up_b):
        st.info("Upload both files. Columns - platform: " + ", ".join(PLATFORM_COLS)
                + " | bank: " + ", ".join(BANK_COLS))
        st.stop()
    p_df = pd.read_csv(up_p, dtype=str, keep_default_na=False)
    b_df = pd.read_csv(up_b, dtype=str, keep_default_na=False)

res = reconcile(p_df, b_df, int(year), int(month))
c1, c2, c3, c4 = st.columns(4)
c1.metric("Platform total", f"{res['platform_total']:,.3f}")
c2.metric("Bank total", f"{res['bank_total']:,.3f}")
c3.metric("Gap", f"{res['gap']:,.3f}")
c4.metric("Unexplained", f"{res['residual']:,.3f}",
          help="0 means every rupee of the gap is attributed to a named cause")

st.subheader("Bridge: how the gap breaks down")
st.dataframe(to_display(res["bridge"]), hide_index=True, use_container_width=True)

st.subheader("Where the gaps are")
f = to_display(res["findings"])
pick = st.multiselect("Filter category", sorted(f["category"].unique()),
                      default=sorted(f["category"].unique()))
view = f[f["category"].isin(pick)]
st.dataframe(view, hide_index=True, use_container_width=True)
st.download_button("Download findings CSV", view.to_csv(index=False), "findings.csv", "text/csv")
