import streamlit as st
import pandas as pd
import time
from course_logic import load_data, get_prepared_courses_and_settings, get_recommended_schedule

# --- 輔助函式 (維持不變) ---

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
    
    weekday_map = {'M': 'M', 'T': 'T', 'W': 'W', 'R': 'R', 'F': 'F', 'S': 'S'}
    
    for _, row in result_df.iterrows():
        course_time = str(row['上課時間']).replace(',', '')
        for i in range(0, len(course_time), 2):
            day = weekday_map.get(course_time[i])
            period = course_time[i+1]
            if day and period in dataframe.index:
                dataframe.loc[period, day] = f"{row['中文課名']}<br>{row['教師']}"
    return dataframe

# --- 主應用程式介面 ---

def main_app():
    """課程推薦系統的主介面"""
    st.set_page_config(page_title="清大課程推薦系統", page_icon="🎓", layout="wide")
    
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
        
        # 選擇不想上的課程 ***
        all_courses_df, _ = load_data()
        if all_courses_df is not None:
            # 取得所有不重複的課程名稱並排序
            all_course_names = sorted(all_courses_df['中文課名'].unique().tolist())
            unwanted_courses = st.multiselect(
                "選擇不想上的特定課程 (可多選)",
                options=all_course_names,
                help="在此選擇的課程將不會出現在推薦課表中。"
            )
        else:
            unwanted_courses = []
        
        st.write("---")
        st.write("各學期期望學分")
        CreditList = []
        semesters = ["大一上", "大一下", "大二上", "大二下", "大三上", "大三下", "大四上", "大四下"]
        default_credits = [20, 20, 20, 20, 12, 12, 12, 12]
        cols = st.columns(2)
        for i, sem in enumerate(semesters):
            CreditList.append(cols[i%2].number_input(sem, min_value=0, max_value=30, value=default_credits[i], key=f"credit_{i}"))

        st.write("---")
        start_button = st.button("🚀 開始產生推薦課表", use_container_width=True)

    # --- 主頁面邏輯 ---
    if start_button:
        if len(EnglishNameList) != 2:
            st.error("輸入錯誤：請務必選擇 2 種不同的選修英文類型。")
        elif sum(CreditList) < 128:
            st.error(f"輸入錯誤：期望總學分 ({sum(CreditList)}) 不可低於 128。")
        else:
            with st.spinner('AI 助教正在根據您的設定，排千萬種可能... 請稍候...'):
                # 重新載入以確保拿到最新的資料
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
                        "unwanted_courses": unwanted_courses # 將不想上的課程傳入設定
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
if __name__ == "__main__":
    main_app()