
import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="발주서 옵션 자동 정제 시스템", layout="wide")
st.title("📦 발주서 옵션 자동 정제 시스템")

uploaded_files = st.file_uploader("발주서를 업로드하세요 (xlsx 형식)", type=["xlsx"], accept_multiple_files=True)

# 키워드 정의
품종_키워드 = ['육쪽', '대서']
형태_키워드 = ['다진마늘', '깐마늘', '통마늘']
카테고리_키워드 = ['닭발', '빠삭이', '마늘쫑']
크기_키워드 = ['대', '중', '소']
업소용_키워드 = ['업소용', '영업용', '업용', '대용량']

all_rows = []

def parse_option(option_text):
    if pd.isna(option_text):
        return None, 1, None, None, None, None

    text = option_text.lower()
    품종 = 형태 = 크기 = 꼭지 = None
    단위무게 = None
    포장수량 = 1
    업소용_표기 = ''
    is_업소용 = False
    카테고리 = '기타'

    for kw in 품종_키워드:
        if kw in text:
            품종 = kw
            break
    for kw in 형태_키워드 + 카테고리_키워드:
        if kw in text:
            형태 = kw
            if kw in ['빠삭이', '닭발']:
                카테고리 = kw
            elif kw == '마늘쫑':
                카테고리 = '마늘쫑'
            else:
                카테고리 = '마늘'
            break
    for kw in 크기_키워드:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            크기 = kw
            break
    for kw in ['꼭지제거', '꼭지포함']:
        if kw in text:
            꼭지 = kw
            break

    match = re.search(r'(\d+)\s*(kg|g)', text)
    if match:
        weight = int(match.group(1))
        unit = match.group(2)
        단위무게 = weight * 1000 if unit == 'kg' else weight
    else:
        if '닭발' in text:
            단위무게 = 200
        elif '빠삭이' in text:
            단위무게 = 350

    if '빠삭이' in text and re.search(r'x\s*10(개|입|팩)', text):
        포장수량 = 1
    else:
        pack_match = re.search(r'[xX×]\s*(\d+)', text)
        if pack_match:
            포장수량 = int(pack_match.group(1))

    if any(kw in text for kw in 업소용_키워드):
        업소용_표기 = '** 업 소 용 ** '
        is_업소용 = True

    # 품종 누락 시 기본값 대서 사용 (마늘류 한정)
    if not 품종 and 카테고리 == '마늘':
        품종 = '대서'

    parts = [품종, 형태, 크기, 꼭지]
    parts = [p for p in parts if p]

    정제된옵션명 = 업소용_표기 + ' '.join(parts)
    return 정제된옵션명.strip(), 포장수량, 단위무게, is_업소용, 카테고리

def get_단위표시(카테고리):
    if 카테고리 in ['마늘', '마늘쫑']:
        return 'kg'
    elif 카테고리 == '닭발':
        return '팩 (200g)'
    elif 카테고리 == '빠삭이':
        return '박스 (10개입)'
    return '단위'

if uploaded_files:
    st.markdown("### 📁 개별 정제 발주서 다운로드 + 최종 패킹리스트 합산")

    for file in uploaded_files:
        st.subheader(f"📄 {file.name}")
        df = pd.read_excel(file)

        옵션후보 = ['옵션', '옵션명', '옵션정보', '옵션내용', '상세옵션']
        option_column = next((col for col in df.columns if any(k in str(col).lower() for k in 옵션후보)), None)
        if not option_column:
            st.warning(f"❗ 옵션 컬럼을 찾을 수 없습니다: {file.name}")
            continue

        df['정제된옵션명'], df['포장수량'], df['단위무게(g)'], df['is_업소용'], df['카테고리'] = zip(*df[option_column].map(parse_option))
        df['수량'] = pd.to_numeric(df['수량'], errors='coerce').fillna(1)
        df['총수량'] = df['수량'] * df['포장수량']
        df['총중량(kg)'] = df['총수량'] * df['단위무게(g)'] / 1000
        all_rows.append(df[['정제된옵션명', '총수량', '총중량(kg)', '카테고리']])

        df_download = df.copy()
        df_download[option_column] = df_download['정제된옵션명']
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_download.drop(columns=['정제된옵션명', '포장수량', '단위무게(g)', '총중량(kg)', '카테고리']).to_excel(writer, index=False)
        st.download_button(
            label=f"⬇ {file.name.replace('.xlsx','')}_정제.xlsx 다운로드",
            data=buffer.getvalue(),
            file_name=f"{file.name.replace('.xlsx','')}_정제.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if all_rows:
        df_all = pd.concat(all_rows, ignore_index=True)

        summaries = []
        for category in ['마늘', '마늘쫑', '닭발', '빠삭이']:
            group_col = '총중량(kg)' if category in ['마늘', '마늘쫑'] else '총수량'
            grouped = df_all[df_all['카테고리'] == category].groupby('정제된옵션명', as_index=False).agg({
                group_col: 'sum'
            })
            grouped['단위'] = get_단위표시(category)
            grouped['수량'] = grouped[group_col].round(2).astype(int)
            summaries.append(grouped[['정제된옵션명', '단위', '수량']])

        summary_df = pd.concat(summaries, ignore_index=True)

        st.markdown("### ✅ 최종 패킹리스트")
        st.dataframe(summary_df)

        buffer2 = io.BytesIO()
        with pd.ExcelWriter(buffer2, engine='openpyxl') as writer:
            summary_df.to_excel(writer, index=False, sheet_name='패킹리스트')
        st.download_button(
            label="⬇ 최종 패킹리스트 다운로드",
            data=buffer2.getvalue(),
            file_name="패킹리스트_합산.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
