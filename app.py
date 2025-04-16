
import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="마늘귀신 자동 패킹리스트 시스템 v5.3", layout="wide")
st.title("🧄 마늘귀신 자동 패킹리스트 시스템 v5.3")

설정 = {
    "품종": ["육쪽", "대서"],
    "형태": ["다진마늘", "깐마늘", "통마늘", "무뼈닭발", "마늘빠삭이", "마늘쫑"],
    "크기": ["특", "대", "중", "소"],
    "꼭지": ["꼭지제거", "꼭지포함"],
    "업소용": ["업소용", "영업용", "업용", "대용량"]
}

카테고리_정의 = {
    "마늘": ["다진마늘", "깐마늘", "통마늘"],
    "마늘쫑": ["마늘쫑"],
    "무뼈닭발": ["무뼈닭발", "무뼈 닭발", "닭발"],
    "마늘빠삭이": ["마늘빠삭이"]
}

단위표기 = {
    "마늘": "kg",
    "마늘쫑": "kg",
    "무뼈닭발": "팩 (200g)",
    "마늘빠삭이": "박스 (10개입)"
}

def detect_category(text):
    for cat, items in 카테고리_정의.items():
        for item in items:
            if item in text:
                return cat
    return "기타"

def extract_weight(text):
    if pd.isna(text):
        return 1000
    text = str(text).lower()
    total_match = re.search(r'총\s*(\d+)\s*(kg|g)', text)
    if total_match:
        value, unit = total_match.groups()
        return int(value) * 1000 if unit == 'kg' else int(value)
    match = re.search(r'(\d+)\s*(kg|g)', text)
    if match:
        value, unit = match.groups()
        return int(value) * 1000 if unit == 'kg' else int(value)
    return 1000

def parse_option(option):
    if pd.isna(option):
        return None, 1, 1000, None, None, None

    original_text = str(option).strip()
    text = original_text.lower().replace(" ", "")
    품종 = next((p for p in 설정["품종"] if p in text), None)
    형태 = next((f for f in 설정["형태"] if f in text), None)
    크기 = next((k for k in 설정["크기"] if k in text), None)
    꼭지 = next((k for k in 설정["꼭지"] if k in text), None)
    is_업소용 = any(k in text for k in 설정["업소용"])
    category = detect_category(text)

    if 꼭지 == "꼭지포함":
        꼭지 = "* 꼭 지 포 함 *"

    단위무게 = extract_weight(original_text)
    포장수량_match = re.search(r'[x×]\s*(\d+)', original_text)
    포장수량 = int(포장수량_match.group(1)) if 포장수량_match else 1

    if category == "무뼈닭발":
        total_weight = extract_weight(original_text)
        count_match = re.search(r'(\d+)\s*팩', original_text)
        if count_match:
            pack_count = int(count_match.group(1))
        else:
            pack_count = total_weight // 200
        정제명 = f"무뼈닭발 {pack_count}팩"
        패킹표기 = "무뼈닭발"

    elif category == "마늘빠삭이":
        count_match = re.search(r'(\d+)\s*개입', original_text)
        if not count_match:
            count_match = re.search(r'\(\s*\d+\s*g\s*[x×]\s*(\d+)\s*개?\s*\)', original_text.lower())
        if count_match:
            count = count_match.group(1) + "개입"
        else:
            count = "10개입"
        정제명 = f"마늘빠삭이 {count}".strip()
        패킹표기 = "마늘빠삭이"

    else:
        parts = [품종, 형태, None if 형태 == "다진마늘" else 크기, 꼭지, f"{int(단위무게/1000)}kg"]
        정제명 = " ".join([p for p in parts if p])
        패킹표기 = 정제명

    if is_업소용:
        정제명 = "** 업 소 용 ** " + 정제명

    return 정제명, 포장수량, 단위무게, category, is_업소용, 패킹표기

    original_text = str(option).strip()
    text = original_text.lower().replace(" ", "")
    품종 = next((p for p in 설정["품종"] if p in text), None)
    형태 = next((f for f in 설정["형태"] if f in text), None)
    크기 = next((k for k in 설정["크기"] if k in text), None)
    꼭지 = next((k for k in 설정["꼭지"] if k in text), None)
    is_업소용 = any(k in text for k in 설정["업소용"])
    category = detect_category(text)

    단위무게 = extract_weight(original_text)
    포장수량_match = re.search(r'[x×]\s*(\d+)', original_text)
    포장수량 = int(포장수량_match.group(1)) if 포장수량_match else 1

    if category == "무뼈닭발":
        total_weight = extract_weight(original_text)
        count_match = re.search(r'(\d+)\s*팩', original_text)
        if count_match:
            pack_count = int(count_match.group(1))
        else:
            pack_count = total_weight // 200  # 무조건 내림 처리
        정제명 = f"무뼈닭발 {pack_count}팩"
        패킹표기 = "무뼈닭발"
    elif category == "마늘빠삭이":
        count_match = re.search(r'(\d+)\s*개입', original_text)
        if not count_match:
            count_match = re.search(r'\(\s*\d+\s*g\s*[x×]\s*(\d+)\s*개?\s*\)', original_text.lower())
        if count_match:
            count = count_match.group(1) + "개입"
        else:
            count = "10개입"
        정제명 = f"마늘빠삭이 {count}".strip()
        패킹표기 = "마늘빠삭이"
    else:
        parts = [품종, 형태, None if 형태 == "다진마늘" else 크기, 꼭지, f"{int(단위무게/1000)}kg"]
        정제명 = " ".join([p for p in parts if p])
        패킹표기 = 정제명

    if is_업소용:
        정제명 = "** 업 소 용 ** " + 정제명

    return 정제명, 포장수량, 단위무게, category, is_업소용, 패킹표기

uploaded_files = st.file_uploader("발주서 파일(.xlsx)을 업로드하세요", type=["xlsx"], accept_multiple_files=True)

정제_전체 = []

if uploaded_files:
    for file in uploaded_files:
        df = pd.read_excel(file)
        옵션컬럼 = next((col for col in df.columns if "옵션" in col.lower()), None)
        if not 옵션컬럼:
            st.warning(f"{file.name}에서 옵션 컬럼을 찾을 수 없습니다.")
            continue

        result = df[옵션컬럼].map(parse_option)
        df["정제된옵션명"], df["포장수량"], df["단위무게(g)"], df["카테고리"], df["is_업소용"], df["패킹표기"] = zip(*result)

        df["수량"] = pd.to_numeric(df.get("수량", 1), errors="coerce").fillna(1)
        df["총수량"] = df["수량"] * df["포장수량"]
        df["총중량(kg)"] = df["총수량"] * df["단위무게(g)"] / 1000

        정제_전체.append(df[["패킹표기", "정제된옵션명", "수량", "총수량", "총중량(kg)", "카테고리", "is_업소용"]])

        df_export = df.copy()
        df_export[옵션컬럼] = df_export["정제된옵션명"]
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_export.to_excel(writer, index=False)
        st.download_button(
            label=f"⬇ {file.name.replace('.xlsx','')}_정제.xlsx 다운로드",
            data=buffer.getvalue(),
            file_name=f"{file.name.replace('.xlsx','')}_정제.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if 정제_전체:
        st.markdown("### 📦 최종 패킹리스트 (합산)")
        df_all = pd.concat(정제_전체, ignore_index=True)
        df_all = df_all[df_all["패킹표기"].notna()]
        df_all = df_all[df_all["패킹표기"] != ""]

        grouped = {}
        for _, row in df_all.iterrows():
            key = (row["패킹표기"], 단위표기.get(row["카테고리"], "단위"))
            if row["카테고리"] == "마늘빠삭이":
                qty = row["수량"]
            elif row["is_업소용"]:
                qty = row["총수량"]
            elif row["카테고리"] in ["마늘", "마늘쫑"]:
                qty = row["총중량(kg)"]
            else:
                qty = row["총수량"]
            grouped[key] = grouped.get(key, 0) + qty

        df_summary = pd.DataFrame(
            [(unit, opt, round(qty)) for (opt, unit), qty in grouped.items()],
            columns=["단위", "정제된 옵션명", "수량"]
        )
            [(opt, unit, round(qty)) for (opt, unit), qty in grouped.items()],
            columns=["정제된 옵션명", "단위", "수량"]
        )

        st.dataframe(df_summary)

        buffer2 = io.BytesIO()
        with pd.ExcelWriter(buffer2, engine="openpyxl") as writer:
            df_summary.to_excel(writer, index=False, sheet_name="패킹리스트")
        st.download_button(
            label="⬇ 패킹리스트_합산.xlsx 다운로드",
            data=buffer2.getvalue(),
            file_name="패킹리스트_합산.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )