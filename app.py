
import streamlit as st
import pandas as pd
import re
import io

st.set_page_config(page_title="마늘귀신 자동 패킹리스트 시스템 v3", layout="wide")
st.title("🧄 마늘귀신 자동 패킹리스트 시스템 v3")

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
    "무뼈닭발": ["무뼈닭발"],
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

def parse_option(option):
    if pd.isna(option):
        return None, 1, 0, None, None, False

    original_text = str(option)

    # ':' 기준 오른쪽만 사용
    if ":" in original_text:
        text = original_text.rsplit(":", 1)[-1].strip().lower()
    else:
        text = original_text.lower()

    # '/' 뒤 제거
    if "/" in text:
        text = text.split("/", 1)[0].strip()

    text = text.replace(" ", "")

    품종 = next((p for p in 설정["품종"] if p in text), None)
    형태 = next((f for f in 설정["형태"] if f in text), None)
    크기 = next((k for k in 설정["크기"] if k in text), None)
    꼭지 = next((k for k in 설정["꼭지"] if k in text), None)
    is_업소용 = any(k in text for k in 설정["업소용"])
    category = detect_category(text)

    if not 품종 and category == "마늘":
        품종 = "대서"

    if category in ["마늘빠삭이", "무뼈닭발"]:
        parts = [형태] if 형태 else []
    else:
        parts = [품종, 형태, 크기, 꼭지]
        parts = [p for p in parts if p]

    # 무게 추출
    match = re.search(r'(\d+)\s*(kg|g)', original_text, re.IGNORECASE)
    if match:
        무게 = int(match.group(1))
        단위 = match.group(2).lower()
        단위무게 = 무게 * 1000 if 단위 == "kg" else 무게
    else:
        단위무게 = 200 if category == "무뼈닭발" else 350 if category == "마늘빠삭이" else 1000

    # 포장수량
    pack_match = re.search(r'[x×]\s*(\d+)', original_text)
    포장수량 = int(pack_match.group(1)) if pack_match else 1

    if category not in ["무뼈닭발", "마늘빠삭이"]:
        parts.append(f"{int(단위무게 / 1000)}kg")

    정제명 = ("** 업 소 용 ** " if is_업소용 else "") + " ".join(parts)

    return 정제명.strip(), 포장수량, 단위무게, category, is_업소용
