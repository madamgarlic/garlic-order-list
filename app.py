
import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="🧄 마늘귀신 자동 패킹리스트 시스템 v4.3", layout="wide")
st.title("🧄 마늘귀신 자동 패킹리스트 시스템 v4.3")

uploaded_file = st.file_uploader("📤 발주서를 업로드하세요 (.xlsx)", type=["xlsx"])

def parse_weight(text):
    try:
        text = str(text)
        weights = re.findall(r'(\d+(?:\.\d+)?)(kg|g)', text, flags=re.IGNORECASE)
        if "총" in text:
            match = re.search(r'총\s*(\d+(?:\.\d+)?)(kg|g)', text, flags=re.IGNORECASE)
            if match:
                value, unit = match.groups()
                return float(value) if unit.lower() == "kg" else float(value) / 1000
        if weights:
            value, unit = weights[-1]
            return float(value) if unit.lower() == "kg" else float(value) / 1000
    except:
        return 0
    return 0

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("파일이 업로드되었습니다!")

        if "옵션명" in df.columns and "수량" in df.columns:
            df["정제무게"] = df["옵션명"].apply(parse_weight)
            df["총중량"] = df["정제무게"] * df["수량"]

            st.subheader("📄 정제된 발주서 미리보기")
            st.dataframe(df[["옵션명", "수량", "정제무게", "총중량"]])

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="정제발주서")
            st.download_button(
                label="📥 정제된 발주서 다운로드",
                data=output.getvalue(),
                file_name="정제_발주서_v43.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("⚠️ '옵션명' 및 '수량' 컬럼이 포함된 엑셀 파일을 업로드해주세요.")
    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")
