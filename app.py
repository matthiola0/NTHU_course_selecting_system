import streamlit as st
import pandas as pd
import time
from course_logic import load_data, get_prepared_courses_and_settings, get_recommended_schedule

# --- 輔助函式 ---

def set_null_time_schedule():
    """設定一個空的時間表 DataFrame"""
    schedule_data = {
        'M': ['-'] * 13, 'T': ['-'] * 13, 'W': ['-'] * 13,
        'R': ['-'] * 13, 'F': ['-'] * 13, 'S': ['-'] * 13
    }
    new_index = ['1', '2', '3', '4', 'n', '5', '6', '7', '8', '9', 'a', 'b', 'c']
    df_schedule = pd.DataFrame(schedule_data, index=new_index)
    return df_schedule

def fill_in_time_schedule(dataframe, result_df):
    """將排課結果填入課表"""
    if result_df.empty:
        return dataframe
    
    # 對照表
    weekday_map = {'M': 'M', 'T': 'T', 'W': 'W', 'R': 'R', 'F': 'F', 'S': 'S'}
    
    for _, row in result_df.iterrows():
        course_time = str(row['上課時間']).replace(',', '')
        for i in range(0, len(course_time), 2):
            day = weekday_map.get(course_time[i])
            period = course_time[i+1]
            if day and period in dataframe.index:
                dataframe.loc[period, day] = f"{row['中文課名']}<br>{row['教師']}"
    return dataframe

# --- 登入邏輯 ---

def check_login():
    """顯示登入表單並驗證"""
    st.set_page_config(page_title="登入 - 課程推薦系統", layout="centered")
    st.title("🎓 清華大學課程推薦系統")
    
    # 模擬的用戶資料庫
    VALID_USERS = {
        "testuser": "password123",
        "nthucs": "cs"
    }

    with st.form("login_form"):
        username = st.text_input("學號 (Username)")
        password = st.text_input("密碼 (Password)", type="password")
        submitted = st.form_submit_button("登入")

        if submitted:
            if username in VALID_USERS and VALID_USERS[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.rerun()  # 重新執行腳本以進入主應用
            else:
                st.error("帳號或密碼錯誤！")

# --- 主應用程式介面 ---

def main_app():
    """課程推薦系統的主介面"""
    st.set_page_config(page_title="清大課程推薦系統", page_icon="🎓", layout="wide")
    
    st.sidebar.header(f"👋 你好, {st.session_state['username']}")
    st.sidebar.write("---")

    st.title("🎓 清華大學課程推薦系統")
    st.info("本系統旨在幫助資工系學生根據畢業門檻和個人偏好，智慧推薦未來四年的修課排程。")

    # --- 側邊欄 UI ---
    with st.sidebar:
        st.header("⚙️ 排課設定")
        
        # 選擇科系
        SelectNumberList = st.multiselect(
            "選擇額外修習的科系",
            options=['1', '2'],
            format_func=lambda x: {'1': '數學系', '2': '物理系'}.get(x),
            help="預設已包含資工、電資學院、通識、英文、大學中文。可多選。"
        )

        # 選擇課程 (物理/化學/生科)
        SelectCourse = st.radio(
            "選擇基礎科學系列課程",
            options=['X', 'Y', 'Z'],
            format_func=lambda x: {'X': '普通物理B', 'Y': '普通化學', 'Z': '生命科學'}.get(x)
        )

        # 選擇不想要的專業選修類別
        SelectType = st.selectbox(
            "選擇**不**想優先修習的專業選修類別",
            options=['A', 'B', 'C', 'D'],
            format_func=lambda x: f"{x} 類"
        )

        # 選擇選修英文
        eng_options = {
            '1': '演說與簡報', '2': '新聞英文選讀', '3': '短篇故事選讀',
            '4': '影視英語聽講', '5': '中英口譯', '6': '職場英語寫作',
            '7': '小說選讀', '8': '中英文筆譯', '9': '學術英語聽力',
            '10': '職場英語口語表達'
        }
        EnglishNameList = st.multiselect(
            "請選擇 2 種想修習的選修英文類型",
            options=list(eng_options.keys()),
            format_func=lambda x: eng_options.get(x)
        )
        
        st.write("---")
        st.write("各學期期望學分 (總和須 >= 128)")
        CreditList = []
        semesters = ["大一上", "大一下", "大二上", "大二下", "大三上", "大三下", "大四上", "大四下"]
        cols = st.columns(2)
        for i, sem in enumerate(semesters):
            CreditList.append(cols[i%2].number_input(sem, min_value=0, max_value=30, value=16, key=f"credit_{i}"))

        st.write("---")
        # 開始按鈕
        start_button = st.button("🚀 開始產生推薦課表", use_container_width=True)
        # 登出按鈕
        if st.button("登出", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()


    # --- 主頁面邏輯 ---
    if start_button:
        # 驗證輸入
        if len(EnglishNameList) != 2:
            st.error("輸入錯誤：請務必選擇 2 種不同的選修英文類型。")
        elif sum(CreditList) < 128:
            st.error(f"輸入錯誤：期望總學分 ({sum(CreditList)}) 不可低於 128。")
        else:
            with st.spinner('AI 助教正在根據您的設定，排千萬種可能... 請稍候...'):
                # 載入資料
                all_courses_df, cs_learn_df = load_data()
                if all_courses_df is None:
                    st.error("嚴重錯誤：無法載入課程資料，請檢查 `data` 資料夾。")
                else:
                    # 收集所有設定
                    user_settings = {
                        "SelectNumberList": SelectNumberList,
                        "EnglishNameList": EnglishNameList,
                        "EnglishCourseNames": [], 
                        "SelectCourse": SelectCourse,
                        "SelectType": SelectType,
                        "CreditList": CreditList,
                    }
                    
                    # 執行後端邏輯
                    AllCoursesData, GEclassData, AddCourseABCD = get_prepared_courses_and_settings(all_courses_df, user_settings)
                    course_lists, credits, total_credits = get_recommended_schedule(user_settings, AllCoursesData, GEclassData, AddCourseABCD, cs_learn_df)
            
            st.success(f"課表產生成功！推薦總學分：**{int(total_credits)}** 學分")
            
            # 顯示結果
            for i, sem in enumerate(semesters):
                with st.expander(f"📚 **{sem}** - 推薦課表 ( {int(credits[i])} 學分 )", expanded=(i < 2)):
                    if not course_lists[i].empty:
                        schedule_df = set_null_time_schedule()
                        schedule_df_filled = fill_in_time_schedule(schedule_df, course_lists[i])
                        
                        st.markdown("##### 視覺化課表")
                        st.write(schedule_df_filled.to_html(escape=False), unsafe_allow_html=True)
                        st.markdown("##### 課程清單")
                        st.dataframe(course_lists[i][['科號', '中文課名', '學分', '教師', '上課時間']])
                    else:
                        st.write("本學期沒有排課。")
    else:
        st.info("請在左方側邊欄完成所有設定後，點擊按鈕開始產生課表。")


# ---程式進入點---
# 檢查 session_state 中是否有登入標記
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# 根據登入狀態顯示不同頁面
if st.session_state["logged_in"]:
    main_app()
else:
    check_login()