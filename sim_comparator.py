import streamlit as st
import pandas as pd
import json
from io import BytesIO

# --- Helpers ---
def normalize_sim(sim):
    if pd.isna(sim):
        return None
    sim = str(sim).strip().replace(".0", "")
    sim = "".join(filter(str.isdigit, sim))
    if sim.startswith("62"):
        return "0" + sim[2:]
    elif sim.startswith("8"):
        return "0" + sim
    elif sim.startswith("0"):
        return sim
    return None

def load_iluvatrack(file):
    """Load Iluvatrack database and normalize SIM numbers."""
    df = pd.read_excel(file)
    df["phone_number"] = df["Sim Card"].apply(normalize_sim)
    return set(df["phone_number"].dropna()), df

def load_telkomsel(file, region):
    """Load Telkomsel billing data and normalize SIM numbers."""
    df = pd.read_excel(file)
    df["phone_number"] = df["MSISDN"].apply(normalize_sim)
    df["price"] = pd.to_numeric(df["TAGIHAN"], errors="coerce").fillna(0).astype(int)
    df["status"] = df["STATUS_LAYANAN"].astype(str).str.strip().str.upper()
    df = df.dropna(subset=["phone_number"])
    df = df[df["status"] != "C"]  # Ignore cancelled
    df["region"] = region
    return df[["phone_number", "price", "status", "region"]].drop_duplicates()

def to_excel_file(df):
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return output

# --- UI ---
st.title("📶 SIM Comparison Tool")

mode = st.selectbox("Select comparison mode:", [
    "Telkomsel → Iluvatrack (find unused / still billed)",
    "Iluvatrack → Telkomsel (find missing / unbilled)"
])

# Upload Iluvatrack database
iluva_files = st.file_uploader(
    "Upload Iluvatrack Database (1 or more files)",
    type=["xlsx"],
    accept_multiple_files=True
)

# Upload Telkomsel sheets
st.markdown("**Telkomsel Provider Sheets**")
jakarta_file = st.file_uploader("Upload Jakarta Telkomsel Sheet", type=["xlsx"], key="jakarta")
kalimantan_file = st.file_uploader("Upload Kalimantan Telkomsel Sheet", type=["xlsx"], key="kalimantan")
extra_files = st.file_uploader("Add More Telkomsel Sheets (Optional)", type=["xlsx"], accept_multiple_files=True, key="extra")

if st.button("Compare"):
    if not iluva_files or not jakarta_file or not kalimantan_file:
        st.error("❌ Please upload at least Iluvatrack + Jakarta + Kalimantan sheets.")
    else:
        try:
            # Combine Iluvatrack SIMs
            iluva_sims = set()
            for f in iluva_files:
                sims, _ = load_iluvatrack(f)
                iluva_sims |= sims

            # Combine Telkomsel SIMs
            telkomsel_dfs = []
            telkomsel_dfs.append(load_telkomsel(jakarta_file, "Jakarta"))
            telkomsel_dfs.append(load_telkomsel(kalimantan_file, "Kalimantan"))
            for i, f in enumerate(extra_files):
                telkomsel_dfs.append(load_telkomsel(f, f"Extra-{i+1}"))

            telkomsel_df = pd.concat(telkomsel_dfs, ignore_index=True)
            telkomsel_sims = set(telkomsel_df["phone_number"].dropna())

            # Comparison logic
            if mode.startswith("Telkomsel"):
                unmatched_df = telkomsel_df[~telkomsel_df["phone_number"].isin(iluva_sims)]
                st.success(f"✅ Found {len(unmatched_df)} Telkomsel SIMs still billed but not in Iluvatrack.")
            else:
                unmatched_df = pd.DataFrame(
                    {"phone_number": list(iluva_sims - telkomsel_sims)}
                )
                st.success(f"✅ Found {len(unmatched_df)} Iluvatrack SIMs missing from Telkomsel billing.")

            # Show table
            st.dataframe(unmatched_df)

            # Download buttons
            st.download_button(
                label="⬇️ Download JSON",
                data=json.dumps(unmatched_df.to_dict(orient="records"), indent=2),
                file_name="unmatched_sims.json",
                mime="application/json"
            )

            st.download_button(
                label="⬇️ Download Excel",
                data=to_excel_file(unmatched_df),
                file_name="unmatched_sims.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
