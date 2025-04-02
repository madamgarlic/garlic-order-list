
import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="정제옵션 자동 생성기", layout="wide")
st.title("📦 발주서 옵션 자동 정제 시스템")

uploaded_files = st.file_uploader("발주서를 업로드하세요 (xlsx 형식)", type=["xlsx"], accept_multiple_files=True)

품종_키워드 = ['육쪽', '대서']
형태_키워드 = ['다진마늘', '깐마늘', '통마늘']
카테고리_키워드 = ['닭발', '빠삭이']
크기_키워드 = ['대', '중', '소']
업소용_키워드 = ['업소용', '영업용', '업용']

def parse_option(option_text):
    if pd.isna(option_text):
        return None, 1

    text = option_text.lower()
    품종 = 형태 = 크기 = None
    단위무게 = None
    포장수량 = 1
    업소용_표기 = ''

    for kw in 품종_키워드:
        if kw in text:
            품종 = kw
            break

    for kw in 형태_키워드 + 카테고리_키워드:
        if kw in text:
            형태 = kw
            break

    for kw in 크기_키워드:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            크기 = kw
            break

    match = re.search(r'(\d+)\s*(kg|g)', text)
    if match:
        weight = int(match.group(1))
        unit = match.group(2)
        단위무게 = f"{int(weight / 1000)}kg" if weight >= 1000 else f"{weight}g"

    if '빠삭이' in text and re.search(r'x\s*10(개|입|팩)', text):
        포장수량 = 1
    else:
        pack_match = re.search(r'[xX×]\s*(\d+)', text)
        if pack_match:
            포장수량 = int(pack_match.group(1))

    if any(kw in text for kw in 업소용_키워드):
        업소용_표기 = '** 업 소 용 ** '

    parts = [품종, 형태, 크기, 단위무게]
    parts = [p for p in parts if p]
    정제된옵션명 = 업소용_표기 + ' '.join(parts)

    return 정제된옵션명, 포장수량

if uploaded_files:
    for file in uploaded_files:
        st.subheader(f"📄 {file.name}")
        df = pd.read_excel(file)

        option_column = None
        for col in df.columns:
            if '옵션' in str(col) or '상품명' in str(col):
                option_column = col
                break

        if not option_column:
            st.warning("옵션 텍스트 컬럼을 찾을 수 없습니다.")
            continue

        df['정제된옵션명'], df['포장수량'] = zip(*df[option_column].map(parse_option))
        df['수량'] = df['수량'] if '수량' in df.columns else 1
        df['총수량'] = pd.to_numeric(df['수량'], errors='coerce').fillna(1) * df['포장수량']

        grouped = df.groupby('정제된옵션명', as_index=False)['총수량'].sum()
        st.dataframe(grouped)

        st.download_button(
            label="📥 정제된 파일 다운로드",
            data=grouped.to_csv(index=False).encode('utf-8-sig'),
            file_name=f"정제옵션_{file.name.replace('.xlsx', '')}.csv",
            mime="text/csv"
        )
