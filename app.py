
import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="🧄 마늘귀신 자동 패킹리스트 시스템 v5.2", layout="wide")
st.title("🧄 마늘귀신 자동 패킹리스트 시스템 v5.2")

uploaded_files = st.file_uploader("📤 발주서를 업로드하세요 (.xlsx)", type=["xlsx"], accept_multiple_files=True)

# 컬럼 자동 인식 함수
def find_column(df, candidates):
    for col in df.columns:
        col_clean = col.replace(" ", "").lower()
        for c in candidates:
            if c in col_clean:
                return col
    return None

# 무게 추출
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

# 옵션 정제
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

final_list = []

if uploaded_files:
    for file in uploaded_files:
        st.markdown(f"### 📄 처리 중: `{file.name}`")
        try:
            df = pd.read_excel(file, engine="openpyxl")
            option_col = find_column(df, ["옵션명", "옵션", "옵션정보", "상품옵션", "선택옵션"])
            qty_col = find_column(df, ["수량", "수량개", "주문수량", "구매수량", "qty"])

            if option_col and qty_col:
                df["정제옵션"] = df[option_col].apply(clean_option)
                df["정제무게"] = df[option_col].apply(extract_weight)
                df["총중량"] = df["정제무게"] * df[qty_col]

                final_list.append(df[["정제옵션", qty_col, "정제무게", "총중량"]])

                st.dataframe(df[[option_col, qty_col, "정제옵션", "정제무게", "총중량"]])

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
                st.warning("❗ 옵션명 또는 수량 컬럼을 찾을 수 없습니다. 컬럼명을 확인해주세요.")
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")

    # 최종 합산 패킹시트 처리
    if final_list:
        combined_df = pd.concat(final_list, ignore_index=True)
        grouped = combined_df.groupby("정제옵션").agg(
            총수량=pd.NamedAgg(column=qty_col, aggfunc="sum"),
            총중량=pd.NamedAgg(column="총중량", aggfunc="sum")
        ).reset_index()

        st.subheader("📦 최종 합산 패킹리스트")
        st.dataframe(grouped)

        output_final = io.BytesIO()
        with pd.ExcelWriter(output_final, engine="xlsxwriter") as writer:
            grouped.to_excel(writer, index=False, sheet_name="패킹리스트")
        st.download_button(
            label="📥 최종 패킹리스트 다운로드",
            data=output_final.getvalue(),
            file_name="최종_패킹리스트_v52.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
