
import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="🧄 마늘귀신 자동 패킹리스트 시스템 v6.2", layout="wide")
st.title("🧄 마늘귀신 자동 패킹리스트 시스템 v6.2")

uploaded_files = st.file_uploader("📤 발주서를 업로드하세요 (.xlsx)", type=["xlsx"], accept_multiple_files=True)

품종_키워드 = ["육쪽", "대서"]
형태_키워드 = ["다진마늘", "깐마늘", "통마늘"]
크기_키워드 = ["소", "중", "대"]
꼭지_키워드 = ["꼭지제거", "꼭지포함"]
업소용_키워드 = ["업소", "대용량"]

def find_column(df, candidates):
    for col in df.columns:
        col_clean = col.replace(" ", "").lower()
        for c in candidates:
            if c in col_clean:
                return col
    return None

def extract_weight(text):
    try:
        text = str(text)
        main_text = re.split(r'\(', text)[0]
        first_match = re.search(r'(\d+(\.\d+)?)(kg|g)', main_text, flags=re.IGNORECASE)
        if first_match:
            value, unit = first_match.groups()[0], first_match.groups()[-1]
            return f"{int(float(value))}kg" if unit.lower() == "kg" else f"{int(float(value)/1000)}kg"
        total_match = re.search(r'총\s*(\d+(\.\d+)?)(kg|g)', text, flags=re.IGNORECASE)
        if total_match:
            value, unit = total_match.groups()[0], total_match.groups()[-1]
            return f"{int(float(value))}kg" if unit.lower() == "kg" else f"{int(float(value)/1000)}kg"
        weights = re.findall(r'(\d+(?:\.\d+)?)(kg|g)', text, flags=re.IGNORECASE)
        if weights:
            value, unit = weights[-1]
            return f"{int(float(value))}kg" if unit.lower() == "kg" else f"{int(float(value)/1000)}kg"
    except:
        return ""
    return ""

def extract_unit(option):
    if "무뼈닭발" in option:
        return "팩"
    elif "마늘빠삭이" in option:
        return "박스"
    else:
        return "kg"

def refine_option(option):
    option = str(option)
    is_dajin = "다진마늘" in option
    is_dakbal = "무뼈닭발" in option
    is_bbasaki = "마늘빠삭이" in option

    if is_dakbal:
        base = "무뼈닭발"
    elif is_bbasaki:
        base = "마늘빠삭이"
    else:
        품종 = next((k for k in 품종_키워드 if k in option), None)
        형태 = next((k for k in 형태_키워드 if k in option), None)
        크기 = next((k for k in 크기_키워드 if re.search(rf"\({k}\)", option)), None)
        꼭지 = next((k for k in 꼭지_키워드 if k in option), None)
        무게 = extract_weight(option)
        parts = [p for p in [품종, 형태, 크기 if not (형태 == "다진마늘") else None, 꼭지, 무게] if p]
        base = " ".join(parts)

    if any(k in option for k in 업소용_키워드):
        return "** 업 소 용 ** " + base
    return base

def calculate_quantity(option, base_qty):
    option = str(option)
    if "무뼈닭발" in option:
        weight = extract_weight(option)
        grams = int(weight.replace("kg", "")) * 1000 if "kg" in weight else 0
        return int((grams / 200) * base_qty) if grams > 0 else base_qty
    elif "마늘빠삭이" in option:
        return base_qty
    else:
        return base_qty

def generate_filename(file):
    name = file.name.replace(".xlsx", "")
    return f"정제_{name}.xlsx"

all_refined = []
packing_items = []

if uploaded_files:
    for file in uploaded_files:
        st.markdown(f"### 📄 처리 중: `{file.name}`")
        try:
            df = pd.read_excel(file, engine="openpyxl")
            option_col = find_column(df, ["옵션", "옵션명", "옵션정보", "선택옵션"])
            qty_col = find_column(df, ["수량", "주문수량", "qty"])

            if option_col and qty_col:
                df["정제옵션"] = df[option_col].apply(refine_option)
                df["단위"] = df[option_col].apply(extract_unit)
                df["수량계산"] = df.apply(lambda x: calculate_quantity(x[option_col], x[qty_col]), axis=1)

                refined = df.copy()
                refined[option_col] = df["정제옵션"]
                all_refined.append(refined)

                packing_items.append(df[["단위", "정제옵션", "수량계산"]])
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                    refined.to_excel(writer, index=False, sheet_name="정제발주서")
                st.download_button(
                    label=f"📥 {file.name} - 정제 발주서 다운로드",
                    data=output.getvalue(),
                    file_name=generate_filename(file),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("❗ 옵션명 또는 수량 컬럼이 없습니다.")
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")

    if packing_items:
        combined_df = pd.concat(packing_items, ignore_index=True)
        combined_df["정제옵션패킹"] = combined_df["정제옵션"].apply(
            lambda x: "무뼈닭발" if "무뼈닭발" in x else ("마늘빠삭이" if "마늘빠삭이" in x else x)
        )
        grouped = combined_df.groupby(["단위", "정제옵션패킹"]).agg(총수량=pd.NamedAgg(column="수량계산", aggfunc="sum")).reset_index()
        grouped.columns = ["단위", "정제옵션", "총수량"]

        st.subheader("📦 최종 합산 패킹리스트")
        st.dataframe(grouped)

        output_final = io.BytesIO()
        with pd.ExcelWriter(output_final, engine="xlsxwriter") as writer:
            grouped.to_excel(writer, index=False, sheet_name="패킹리스트")
        st.download_button(
            label="📥 최종 패킹리스트 다운로드",
            data=output_final.getvalue(),
            file_name="최종_패킹리스트_v62.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
