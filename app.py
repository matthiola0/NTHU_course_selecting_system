import streamlit as st
import pandas as pd
import time
from course_logic import load_data, get_prepared_courses_and_settings, get_recommended_schedule, process_past_courses

def set_null_time_schedule():
    schedule_data = {'M': ['-'] * 13, 'T': ['-'] * 13, 'W': ['-'] * 13, 'R': ['-'] * 13, 'F': ['-'] * 13, 'S': ['-'] * 13}
    new_index = ['1', '2', '3', '4', 'n', '5', '6', '7', '8', '9', 'a', 'b', 'c']
    return pd.DataFrame(schedule_data, index=new_index)

def fill_in_time_schedule(dataframe, result_df):
    if result_df.empty: return dataframe
    weekday_map = {'M': 'M', 'T': 'T', 'W': 'W', 'R': 'R', 'F': 'F', 'S': 'S'}
    for _, row in result_df.iterrows():
        course_time = str(row['上課時間']).replace(',', '')
        for i in range(0, len(course_time), 2):
            day, period = weekday_map.get(course_time[i]), course_time[i+1]
            if day and period in dataframe.index:
                dataframe.loc[period, day] = f"{row['中文課名']}<br>{row['教師']}"
    return dataframe

# --- 主應用程式介面 ---
def main_app():
    st.set_page_config(page_title="清大課程推薦系統", page_icon="🎓", layout="wide")
    st.title("🎓 清華大學課程推薦系統")
    st.info("本系統旨在幫助資工系學生根據畢業門檻和個人偏好，智慧推薦未來的修課排程。")

    all_courses_df, cs_learn_df = load_data()
    if all_courses_df is None or cs_learn_df is None:
        st.error("嚴重錯誤：無法載入課程資料，請檢查 `data` 資料夾。")
        return

    # --- 側邊欄 UI ---
    with st.sidebar:
        st.header("⚙️ 個人化設定")

        # 選擇已完成學期數
        completed_semesters = st.slider(
            "請選擇您已完成的學期數",
            min_value=0, max_value=7, value=0,
            help="如果您是大一新生，請選0。如果您剛完成大二下，請選4。"
        )

        # 選擇已修過的課程
        all_course_names = sorted(all_courses_df['中文課名'].unique().tolist())
        past_courses = st.multiselect(
            "請選擇您已修過的課程",
            options=all_course_names,
            help="系統將會自動辨識這些課程的學分屬性。"
        )

        initial_state_suggestion = process_past_courses(past_courses, all_courses_df, cs_learn_df, all_courses_df[all_courses_df['系所全名'] == '通識教育中心'])

        st.header("未來學期設定")
        st.subheader("英語課程設定")
        eng_req_completed = initial_state_suggestion['eng_req_completed'] >= 2
        eng_elec_completed = initial_state_suggestion['eng_elec_completed'] >= 2
        eng_level_index = 1 if '中高級英文（三）' in past_courses or '中高級英文（四）' in past_courses else 0
        english_level = st.radio("1. 您的英文能力分級", ["前標", "頂標"], index=eng_level_index, disabled=eng_req_completed)
        if eng_req_completed: st.success("已滿足必修英文要求！")
            
        elec_eng_option = st.radio("2. 選修英文/外語 (2門)", ["請推薦2門「選修英文」", "請用2門「外語課」代替", "我已滿足此要求"], index=2 if eng_elec_completed else 0)
        if elec_eng_option == "我已滿足此要求" and not eng_elec_completed:
            st.warning("提醒：分析您已修的課程後，似乎尚未滿足2門選修英文/外語的要求。")

        st.subheader("其他設定")
        SelectNumberList = st.multiselect("選擇額外想修的科系", ['1', '2'], format_func=lambda x: {'1': '數學系', '2': '物理系'}.get(x))
        SelectCourse = st.radio("選擇基礎科學系列課程", ['X', 'Y', 'Z'], format_func=lambda x: {'X':'普通物理B','Y':'普通化學','Z':'生命科學'}.get(x))
        SelectType = st.selectbox("選擇不想優先修習的專業選修類別", ['A', 'B', 'C', 'D'], format_func=lambda x: f"{x} 類")
        wanted_courses = st.multiselect("選擇想優先修習的特定課程", all_course_names)
        unwanted_courses = st.multiselect("選擇不想上的特定課程", all_course_names)
        
        st.write("---")
        st.write("未來各學期期望學分")
        CreditList = []
        semesters_all = ["大一上", "大一下", "大二上", "大二下", "大三上", "大三下", "大四上", "大四下"]
        default_credits = [20, 20, 20, 20, 12, 12, 12, 12]
        cols = st.columns(2)
        for i in range(8):
            is_future_sem = (i >= completed_semesters)
            CreditList.append(cols[i%2].number_input(semesters_all[i], 0, 30, default_credits[i], key=f"credit_{i}", disabled=not is_future_sem))
        
        start_button = st.button("開始產生推薦課表", use_container_width=True)

    if start_button:
        with st.spinner('正在為您分析與排程... 請稍候...'):
            user_settings = {
                "completed_semesters": completed_semesters, "past_courses": past_courses,
                "english_level": english_level, "elec_eng_option": elec_eng_option,
                "SelectNumberList": SelectNumberList, "SelectCourse": SelectCourse, "SelectType": SelectType,
                "CreditList": CreditList, "unwanted_courses": unwanted_courses, "wanted_courses": wanted_courses,
            }
            AllCoursesData, GEclassData, AddCourseABCD = get_prepared_courses_and_settings(all_courses_df, user_settings)
            course_lists, credits, total_credits, initial_state = get_recommended_schedule(user_settings, AllCoursesData, GEclassData, AddCourseABCD, cs_learn_df)
                
        st.success("課表產生成功！")
        
        # 顯示已修課程的學分統計
        st.subheader("已修課程學分分析")
        cols = st.columns(5)
        cols[0].metric("已滿足必修要求", f"{len(initial_state['fulfilled_reqs'])} 項")
        cols[1].metric("必修英文", f"{initial_state['eng_req_completed']} / 2 門")
        cols[2].metric("選修英文/外語", f"{initial_state['eng_elec_completed']} / 2 門")
        cols[3].metric("通識學分", f"{initial_state['ge_credits']} / 20 學分")
        cols[4].metric("電資專業選修", f"{initial_state['eecs_credits']} / 12 學分")

        st.subheader("未來學期推薦課表")
        for i in range(completed_semesters, 8):
            sem_name = semesters_all[i]
            with st.expander(f"📚 **{sem_name}** - 推薦課表 ( {int(credits[i])} 學分 )", expanded=True):
                if not course_lists[i].empty:
                    schedule_df_filled = set_null_time_schedule()
                    schedule_df_filled = fill_in_time_schedule(schedule_df_filled, course_lists[i])
                     
                    st.markdown("##### 視覺化課表")
                    st.write(schedule_df_filled.to_html(escape=False), unsafe_allow_html=True)
                    st.markdown("##### 課程清單")
                    st.dataframe(course_lists[i][['科號', '中文課名', '學分', '教師', '上課時間']])
                else:
                    st.write("本學期沒有排課。")
    else:
        st.info("請在左方側邊欄完成您的個人化設定後，點擊按鈕開始產生課表。")

if __name__ == "__main__":
    main_app()