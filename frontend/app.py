import streamlit as st
import requests
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from io import BytesIO

API_URL = "http://127.0.0.1:8000"

st.set_page_config(layout="wide")

# -----------------------------
# 상태 관리
# -----------------------------
if "selected_row" not in st.session_state:
    st.session_state.selected_row = None
if "mode" not in st.session_state:
    st.session_state.mode = None
if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = False

# -----------------------------
# 타이틀
# -----------------------------
st.markdown(""" <style> h1 a { display: none !important; } </style> """, unsafe_allow_html=True)
st.title("고객 관리 시스템")

# -----------------------------
# 사이드바
# -----------------------------
with st.sidebar:
    category = st.selectbox("카테고리", ["전체", "기업", "학교", "관공서"])
    search = st.text_input("검색")

# -----------------------------
# API 조회
# -----------------------------
if category == "전체":
    res = requests.get(f"{API_URL}/companies")
else:
    res = requests.get(f"{API_URL}/companies/{category}")

if res.status_code != 200:
    st.error("API 오류")
    st.stop()

data = res.json()

if search:
    data = [d for d in data if search.lower() in d["name"].lower()]

df = pd.DataFrame(data)

if df.empty:
    st.warning("데이터 없음")
    st.stop()

# -----------------------------
# 컬럼 정리
# -----------------------------
for col in ["contact_person", "email"]:
    if col not in df.columns:
        df[col] = ""

columns_order = ["id", "category", "name", "address", "tel", "homepage", "contact_person", "email"]
df = df[columns_order]

# -----------------------------
# 엑셀 다운로드
# -----------------------------
def to_excel(df):
    output = BytesIO()
    df_excel = df.drop(columns=["id"]).copy()  # 여기서만 id 제거
    df_excel["homepage"] = df_excel["homepage"].apply(lambda x: f"'{x}" if x else "")
    df_excel.columns = ["구분", "업체명", "주소", "전화번호", "홈페이지", "담당자", "이메일"]
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_excel.to_excel(writer, index=False)
    return output.getvalue()

# -----------------------------
# 버튼
# -----------------------------
with st.container():
    cols = st.columns([19,1,1])

    with cols[1]:
        if st.button("등록"):
            st.session_state.mode = "add"
            st.session_state.selected_row = None
            st.rerun()

    with cols[2]:
        st.download_button("엑셀", data=to_excel(df), file_name="company_list.xlsx")

# -----------------------------
# 모달 정의 (🔥 반드시 AgGrid보다 위)
# -----------------------------
@st.dialog("📌 업체 등록")
def add_dialog():
    name = st.text_input("업체명")
    category_input = st.selectbox("카테고리", ["기업", "학교", "관공서"])
    contact_person = st.text_input("담당자")
    email = st.text_input("이메일")
    address = st.text_input("주소")
    tel = st.text_input("전화번호")
    homepage = st.text_input("홈페이지")

    col1, col2, col3 = st.columns([2,1,2])
    with col2:
        submit = st.button("저장", use_container_width=True)

    if submit:
        if not name.strip() or not address.strip():
            st.error("업체명과 주소는 필수입니다.")
            return

        category_map = {"관공서": 1, "기업": 2, "학교": 3}

        payload = {
            "name": name.strip(),
            "category_id": category_map[category_input],
            "contact_person": contact_person or None,
            "email": email.strip() if email.strip() else None,
            "address": address.strip(),
            "tel": tel or None,
            "homepage": homepage or None
        }

        r = requests.post(f"{API_URL}/companies", json=payload)

        if r.status_code == 200:
            st.success("등록 완료")
            st.session_state.mode = None
            st.rerun()

        elif r.status_code == 422:
            st.error("올바른 이메일 형식이 아닙니다.")

        else:
            st.error("등록 실패")


# -----------------------------
# 업체 수정/삭제 모달
# -----------------------------
@st.dialog("📌 업체 수정/삭제")
def edit_dialog(selected_row):
    st.session_state.mode = "edit"

    # 기본 입력
    name = st.text_input("업체명", value=selected_row.get("name", ""))
    category_input = st.selectbox(
        "카테고리",
        ["기업", "학교", "관공서"],
        index=["기업","학교","관공서"].index(selected_row["category"])
    )
    contact_person = st.text_input("담당자", value=selected_row.get("contact_person", ""))
    email = st.text_input("이메일", value=selected_row.get("email", ""))
    address = st.text_input("주소", value=selected_row.get("address", ""))
    tel = st.text_input("전화번호", value=selected_row.get("tel", ""))
    homepage = st.text_input("홈페이지", value=selected_row.get("homepage", ""))

    # 버튼 중앙
    c1, c2, c3, c4, c5 = st.columns([1,1,1,1,1])
    with c2:
        submit = st.button("수정", key=f"edit_submit_{selected_row['id']}", use_container_width=True)
    with c4:
        delete = st.button("삭제", key=f"edit_delete_{selected_row['id']}", use_container_width=True)

    # -----------------------------
    # 수정 처리
    # -----------------------------
    if submit:
        if not name.strip() or not address.strip():
            st.error("업체명과 주소는 필수입니다.")
            return

        category_map = {"관공서": 1, "기업": 2, "학교": 3}
        payload = {
            "name": name.strip(),
            "category_id": category_map[category_input],
            "contact_person": contact_person or None,
            "email": email.strip() if email and email.strip() else None,
            "address": address.strip(),
            "tel": tel or None,
            "homepage": homepage or None
        }

        try:
            company_id = int(selected_row['id'])
            r = requests.put(f"{API_URL}/companies/{company_id}", json=payload)
            if r.status_code == 200:
                st.success("수정 완료")
                st.session_state.selected_row = None
                st.session_state.mode = None
                st.rerun()
            elif r.status_code == 422:
                st.error("올바른 이메일 형식이 아닙니다.")
            else:
                st.error(r.json().get("detail","수정 실패"))
        except Exception as e:
            st.error(f"수정 오류: {e}")

    # -----------------------------
    # 삭제 처리 (확인 없이 바로 삭제)
    # -----------------------------
    if delete:
        try:
            company_id = int(selected_row['id'])
            r = requests.delete(f"{API_URL}/companies/{company_id}")
            if r.status_code == 200:
                st.success("삭제 완료")
                st.session_state.selected_row = None
                st.session_state.mode = None
                st.rerun()
            else:
                st.error(r.json().get("detail","삭제 실패"))
        except Exception as e:
            st.error(f"삭제 오류: {e}")

# -----------------------------
# AgGrid
# -----------------------------
columns_map = {
    "category": "구분",
    "name": "업체명",
    "address": "주소",
    "tel": "전화번호",
    "homepage": "홈페이지",
    "contact_person": "담당자",
    "email": "이메일"
}

df_grid = df.copy()

gb = GridOptionsBuilder.from_dataframe(df_grid)
for col, display_name in columns_map.items():
    gb.configure_column(col, header_name=display_name)
gb.configure_selection("single", use_checkbox=False)
gridOptions = gb.build()
gridOptions["onGridSizeChanged"] = JsCode(""" function(params) { params.api.sizeColumnsToFit(); } """)

grid = AgGrid(
    df_grid,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.SELECTION_CHANGED,  # 🔥 핵심
    data_return_mode="FILTERED_AND_SORTED",        # 🔥 추가
    reload_data=True,                             # 🔥 핵심
    use_container_width=True,
    height=400,
    allow_unsafe_jscode=True,
)

# -----------------------------
# 선택 → 수정 모달
# -----------------------------
selected_rows = grid.get("selected_rows", [])

selected_row = None

# 🔥 DataFrame 대응
if isinstance(selected_rows, pd.DataFrame):
    if not selected_rows.empty:
        selected_row = selected_rows.iloc[0].to_dict()

# 🔥 list 대응
elif isinstance(selected_rows, list):
    if len(selected_rows) > 0:
        selected_row = selected_rows[0]

# -----------------------------
# 모달 실행
# -----------------------------
if selected_row:
    if st.session_state.get("selected_row") != selected_row:
        st.session_state.selected_row = selected_row
        edit_dialog(selected_row)

# -----------------------------
# 등록 모달 실행
# -----------------------------
if st.session_state.mode == "add":
    add_dialog()