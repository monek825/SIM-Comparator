# 📶 SIM Comparator

Streamlit app to compare SIM card data between Iluvatrack’s internal database and Telkomsel billing files.

## Features
- Compare both directions:
  - Telkomsel → Iluvatrack (find unused SIMs still billed)
  - Iluvatrack → Telkomsel (find unbilled SIMs)
- Supports multiple Iluvatrack files & multiple Telkomsel sheets
- Download results as Excel or JSON

## Usage
1. Upload Iluvatrack database file(s)
2. Upload Jakarta, Kalimantan, and any extra Telkomsel sheets
3. Select comparison mode
4. Click **Compare**
5. Download results

## Deployment
- Powered by [Streamlit](https://streamlit.io/)
- To run locally:  
  ```bash
  pip install -r requirements.txt
  streamlit run sim_comparator_gui.py
