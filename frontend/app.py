import streamlit as st
import requests
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
from io import BytesIO

API_URL = "http://127.0.0.1:8000"

st.set_page_config(layout="wide")

# 🔥 타이틀 링크 제거
st.markdown("""
<style>
h1 a { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.title("업체 관리 시스템")

# -----------------------------
# 상태 관리
# -----------------------------
if "mode" not in st.session_state:
    st.session_state.mode = None

if "selected_row" not in st.session_state:
    st.session_state.selected_row = None

# -----------------------------
# 사이드바
# -----------------------------
with st.sidebar:
    category = st.selectbox("카테고리", ["전체", "기업", "학교", "관공서"], key="sidebar_category")
    search = st.text_input("검색", key="sidebar_search")

# -----------------------------
# 데이터 조회
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

# 컬럼 순서
df = df[["category", "name", "address", "tel", "homepage", "id"]]

# -----------------------------
# AgGrid 설정
# -----------------------------
gb = GridOptionsBuilder.from_dataframe(df)

gb.configure_default_column(resizable=True, sortable=True, filter=True)

gb.configure_column("id", hide=True)
gb.configure_column("category", header_name="구분", maxWidth=120)
gb.configure_column("name", header_name="업체명", flex=1)
gb.configure_column("address", header_name="주소", flex=2)
gb.configure_column("tel", header_name="전화번호", flex=1)
gb.configure_column("homepage", header_name="홈페이지", flex=1)

# 🔥 안정적인 체크박스
gb.configure_selection("single", use_checkbox=True)

gridOptions = gb.build()

# 🔥 빈 컬럼 방지
gridOptions["onGridSizeChanged"] = JsCode("""
function(params) {
    params.api.sizeColumnsToFit();
}
""")

# -----------------------------
# 테이블 출력
# -----------------------------
grid = AgGrid(
    df,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    use_container_width=True,
    allow_unsafe_jscode=True,
    height=400
)

selected = grid["selected_rows"]

if selected:
    st.session_state.selected_row = selected[0]
else:
    st.session_state.selected_row = None

selected_row = st.session_state.selected_row

# -----------------------------
# 엑셀 다운로드
# -----------------------------
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_excel = df.drop(columns=["id"])
        df_excel.columns = ["구분", "업체명", "주소", "전화번호", "홈페이지"]
        df_excel.to_excel(writer, index=False)
    return output.getvalue()

# -----------------------------
# 버튼 영역
# -----------------------------
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("등록", key="btn_add"):
        st.session_state.mode = "add"

with col2:
    if st.button("수정", key="btn_edit", disabled=(selected_row is None)):
        st.session_state.mode = "edit"

with col3:
    if st.button("삭제", key="btn_delete", disabled=(selected_row is None)):
        st.session_state.mode = "delete"

with col4:
    st.download_button(
        "엑셀 다운로드",
        data=to_excel(df),
        file_name="company_list.xlsx",
        key="btn_excel"
    )

# -----------------------------
# 등록
# -----------------------------
if st.session_state.mode == "add":
    st.markdown("### 📌 업체 등록")

    with st.form("form_add"):
        name = st.text_input("업체명")
        category_input = st.selectbox("카테고리", ["기업", "학교", "관공서"])
        address = st.text_input("주소")
        tel = st.text_input("전화번호")
        homepage = st.text_input("홈페이지")

        c1, c2 = st.columns(2)

        with c1:
            submit = st.form_submit_button("저장", key="add_submit")
        with c2:
            cancel = st.form_submit_button("취소", key="add_cancel")

        if cancel:
            st.session_state.mode = None
            st.rerun()

        if submit:
            if not name.strip() or not address.strip():
                st.error("업체명과 주소는 필수입니다.")
            else:
                category_map = {"관공서": 1, "기업": 2, "학교": 3}

                res = requests.post(f"{API_URL}/companies", json={
                    "name": name,
                    "category_id": category_map[category_input],
                    "address": address,
                    "tel": tel,
                    "homepage": homepage
                })

                if res.status_code == 200:
                    st.success("등록 완료")
                    st.session_state.mode = None
                    st.rerun()

# -----------------------------
# 수정
# -----------------------------
if st.session_state.mode == "edit" and selected_row:
    st.markdown("### ✏️ 업체 수정")

    with st.form("form_edit"):
        name = st.text_input("업체명", value=selected_row["name"])
        category_input = st.selectbox("카테고리", ["기업", "학교", "관공서"])
        address = st.text_input("주소", value=selected_row["address"])
        tel = st.text_input("전화번호", value=selected_row["tel"])
        homepage = st.text_input("홈페이지", value=selected_row["homepage"])

        c1, c2 = st.columns(2)

        with c1:
            submit = st.form_submit_button("저장", key="edit_submit")
        with c2:
            cancel = st.form_submit_button("취소", key="edit_cancel")

        if cancel:
            st.session_state.mode = None
            st.rerun()

        if submit:
            category_map = {"관공서": 1, "기업": 2, "학교": 3}

            res = requests.put(
                f"{API_URL}/companies/{selected_row['id']}",
                json={
                    "name": name,
                    "category_id": category_map[category_input],
                    "address": address,
                    "tel": tel,
                    "homepage": homepage
                }
            )

            if res.status_code == 200:
                st.success("수정 완료")
                st.session_state.mode = None
                st.rerun()

# -----------------------------
# 삭제
# -----------------------------
if st.session_state.mode == "delete" and selected_row:
    st.warning(f"정말 '{selected_row['name']}' 삭제하시겠습니까?")

    c1, c2 = st.columns(2)

    with c1:
        if st.button("삭제", key="confirm_delete"):
            requests.delete(f"{API_URL}/companies/{selected_row['id']}")
            st.success("삭제 완료")
            st.session_state.mode = None
            st.rerun()

    with c2:
        if st.button("취소", key="cancel_delete"):
            st.session_state.mode = None