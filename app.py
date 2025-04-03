
import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="발주서 옵션 자동 정제 시스템", layout="wide")
st.title("📦 발주서 옵션 자동 정제 시스템")

uploaded_files = st.file_uploader("발주서를 업로드하세요 (xlsx 형식)", type=["xlsx"], accept_multiple_files=True)

# 기준 키워드
품종_키워드 = ['육쪽', '대서']
형태_키워드 = ['다진마늘', '깐마늘', '통마늘']
크기_키워드 = ['대', '중', '소']
업소용_키워드 = ['업소용', '영업용', '업용', '대용량']

all_rows = []

# 정제 로직
def parse_option(option_text):
    if pd.isna(option_text):
        return None, 1, None

    text = option_text.lower()
    품종 = 형태 = 크기 = 꼭지 = None
    단위무게 = None
    포장수량 = 1
    업소용_표기 = ''

    # 꼭지
    if '꼭지제거' in text:
        꼭지 = '꼭지제거'
    elif '꼭지포함' in text:
        꼭지 = '꼭지포함'

    # 품종
    for kw in 품종_키워드:
        if kw in text:
            품종 = kw
            break

    # 형태
    if '닭발' in text:
        형태 = '무뼈닭발'
    elif '빠삭이' in text:
        형태 = '마늘빠삭이'
    else:
        for kw in 형태_키워드:
            if kw in text:
                형태 = kw
                break

    # 품종이 없고 형태가 마늘류일 경우
    if not 품종 and 형태 in 형태_키워드:
        품종 = '대서'

    # 크기
    for kw in 크기_키워드:
        if re.search(r'\b' + re.escape(kw) + r'\b', text):
            크기 = kw
            break

    # 단위무게
    match = re.search(r'(\d+)\s*(kg|g)', text)
    if match:
        weight = int(match.group(1))
        unit = match.group(2)
        단위무게 = weight * 1000 if unit == 'kg' else weight
    elif '닭발' in text:
        단위무게 = 200
    elif '빠삭이' in text:
        단위무게 = 350

    # 포장수량
    if '빠삭이' in text and re.search(r'x\s*10(개|입|팩)', text):
        포장수량 = 1
    else:
        pack_match = re.search(r'[xX×]\s*(\d+)', text)
        if pack_match:
            포장수량 = int(pack_match.group(1))

    # 업소용 여부
    if any(kw in text for kw in 업소용_키워드):
        업소용_표기 = '** 업 소 용 ** '

    # 최종 정제 옵션명 구성
    parts = [품종, 형태, 꼭지, 크기]
    parts = [p for p in parts if p]
    if 단위무게:
        parts.append(f"{int(단위무게/1000)}kg" if 단위무게 >= 1000 else f"{단위무게}g")

    정제된옵션명 = 업소용_표기 + ' '.join(parts)
    return 정제된옵션명, 포장수량, 단위무게

if uploaded_files:
    for file in uploaded_files:
        st.subheader(f"📄 {file.name}")
        df = pd.read_excel(file)

        option_column = None
        for col in df.columns:
            if any(k in str(col).lower() for k in ['옵션', '옵션명', '옵션정보']):
                option_column = col
                break

        if not option_column:
            st.warning(f"❗ 옵션 컬럼을 찾을 수 없습니다: {file.name}")
            continue

        df['정제된옵션명'], df['포장수량'], df['단위무게(g)'] = zip(*df[option_column].map(parse_option))
        df['수량'] = pd.to_numeric(df['수량'], errors='coerce').fillna(1)
        df['총수량'] = df['수량'] * df['포장수량']
        df['총중량(kg)'] = df.apply(
            lambda row: (row['총수량'] * row['단위무게(g)'] / 1000)
            if any(x in str(row['정제된옵션명']) for x in ['깐마늘', '다진마늘', '통마늘']) else None,
            axis=1
        )

        all_rows.append(df[['정제된옵션명', '총수량', '총중량(kg)', '단위무게(g)']])

        # 개별 파일 다운로드
        df_download = df.copy()
        df_download[option_column] = df_download['정제된옵션명']
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_download.drop(columns=['정제된옵션명', '포장수량', '단위무게(g)', '총중량(kg)']).to_excel(writer, index=False)
        st.download_button(
            label=f"⬇ {file.name.replace('.xlsx','')}_정제.xlsx 다운로드",
            data=buffer.getvalue(),
            file_name=f"{file.name.replace('.xlsx','')}_정제.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # 합산 패킹리스트
    if all_rows:
        df_all = pd.concat(all_rows, ignore_index=True)
        df_sum = df_all.groupby('정제된옵션명', as_index=False).agg({
            '총수량': 'sum',
            '총중량(kg)': 'sum',
            '단위무게(g)': 'first'
        })
        df_sum = df_sum.rename(columns={
            '총수량': '🔢 총수량',
            '총중량(kg)': '📦 총중량(kg)',
            '단위무게(g)': '단위무게(g, 참고)'
        })

        st.markdown("### ✅ 최종 패킹리스트 (합산)")
        st.dataframe(df_sum)

        buffer2 = io.BytesIO()
        with pd.ExcelWriter(buffer2, engine='openpyxl') as writer:
            df_sum.to_excel(writer, index=False, sheet_name='패킹리스트')
        st.download_button(
            label="⬇ 패킹리스트_합산.xlsx 다운로드",
            data=buffer2.getvalue(),
            file_name="패킹리스트_합산.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
