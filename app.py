
import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="🧄 마늘귀신 자동 패킹리스트 시스템 v5.0", layout="wide")
st.title("🧄 마늘귀신 자동 패킹리스트 시스템 v5.0")

uploaded_files = st.file_uploader("📤 발주서를 업로드하세요 (.xlsx)", type=["xlsx"], accept_multiple_files=True)

# 키워드 기반 정제 함수들
def extract_weight(text):
    try:
        text = str(text)
        if "총" in text:
            total_match = re.search(r"총\s*(\d+(?:\.\d+)?)(kg|g)", text, flags=re.IGNORECASE)
            if total_match:
                value, unit = total_match.groups()
                return float(value) if unit.lower() == "kg" else float(value) / 1000
        weights = re.findall(r'(\d+(?:\.\d+)?)(kg|g)', text, flags=re.IGNORECASE)
        if weights:
            value, unit = weights[-1]
            return float(value) if unit.lower() == "kg" else float(value) / 1000
    except:
        return 0
    return 0

def clean_option(option):
    try:
        option = str(option)
        if ':' in option:
            option = option.split(':')[-1]
        if '/' in option:
            option = option.split('/')[0]
        return option.strip()
    except:
        return option

def generate_filename(file):
    name = file.name.replace(".xlsx", "")
    return f"정제_{name}.xlsx"

# 처리 시작
if uploaded_files:
    for file in uploaded_files:
        st.markdown(f"### 📄 처리 중: `{file.name}`")
        try:
            df = pd.read_excel(file, engine="openpyxl")
            if "옵션명" in df.columns and "수량" in df.columns:
                df["정제옵션"] = df["옵션명"].apply(clean_option)
                df["정제무게"] = df["옵션명"].apply(extract_weight)
                df["총중량"] = df["정제무게"] * df["수량"]

                st.dataframe(df[["정제옵션", "수량", "정제무게", "총중량"]])

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False, sheet_name="정제발주서")

                st.download_button(
                    label=f"📥 {file.name} - 정제 발주서 다운로드",
                    data=output.getvalue(),
                    file_name=generate_filename(file),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("⚠️ '옵션명' 및 '수량' 컬럼이 있어야 정제가 가능합니다.")
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
