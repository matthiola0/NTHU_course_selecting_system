import pandas as pd
import numpy as np
from itertools import accumulate

# 對照表
WEEKDAY_MAPPING = {'M': 0, 'T': 1, 'W': 2, 'R': 3, 'F': 4, 'S': 5}
NUMBER_MAPPING = {'1': 0, '2': 1, '3': 2, '4': 3, 'n': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'a': 10, 'b': 11, 'c': 12}

# 課程替代規則字典
SUBSTITUTE_MAP = {
    '微積分Ｂ一': ['微積分一(數學系)', '微積分Ａ一'],
    '微積分Ｂ二': ['微積分二(數學系)', '微積分Ａ二'],
    '普通物理Ｂ一': ['普通物理一(物理系)', '普通物理Ａ一'],
    '普通物理Ｂ二': ['普通物理二(物理系)', '普通物理Ａ二'],
}
REVERSE_SUB_MAP = {sub: base for base, subs in SUBSTITUTE_MAP.items() for sub in subs}


def load_data():
    """載入所有需要的課程資料"""
    try:
        all_courses_df = pd.read_csv('./data/all_done.csv')
        cs_learn_df = pd.read_csv('./data/cslearn.csv')
        all_courses_df['上課時間'] = all_courses_df['上課時間'].astype(str).fillna('')
        return all_courses_df, cs_learn_df
    except FileNotFoundError:
        print("錯誤：找不到 'data/all_done.csv' 或 'data/cslearn.csv'。請確認資料檔案存在。")
        return None, None

def get_prepared_courses_and_settings(df, settings):
    """
    此函式整合了課程篩選和 ABCD 類選修的邏輯。
    """
    unwanted_courses = settings.get('unwanted_courses', [])
    if unwanted_courses:
        df = df[~df['中文課名'].isin(unwanted_courses)].copy()

    CSclassData = df[df['系所全名'] == '資訊工程學系'].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
    EECSclassData = df[df['系所全名'] == '電機資訊學院學士班'].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
    GEclassData = df[df['系所全名'] == '通識教育中心'].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
    LANGclassData = df[(df['系所全名'] == '英語教育中心(110起)') | (df['系所全名'] == '英語教育中心')].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
    CLclassData = df[(df['系所全名'] == '中國文學系') & (df['中文課名'] == '大學中文')].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
    base_frames = [CSclassData, EECSclassData, GEclassData, LANGclassData, CLclassData]
    AllCoursesData = pd.concat(base_frames, ignore_index=True)
    listAdd = ['微積分Ｂ一','微積分Ｂ二','普通物理Ｂ一','普通物理Ｂ二','普通化學一','普通化學二','生命科學一','生命科學二',
               '微積分一(數學系)', '微積分Ａ一', '微積分二(數學系)', '微積分Ａ二',
               '普通物理一(物理系)', '普通物理Ａ一', '普通物理二(物理系)', '普通物理Ａ二']
    for course_name in listAdd:
        AddclassData = df[df['中文課名'] == course_name].dropna(subset=['科號', '系所全名', '學分'])
        AllCoursesData = pd.concat([AllCoursesData, AddclassData], ignore_index=True)

    if "1" in settings['SelectNumberList']:
        MATHclassData = df[df['系所全名'] == '數學系'].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
        AllCoursesData = pd.concat([AllCoursesData, MATHclassData], ignore_index=True)
    if "2" in settings['SelectNumberList']:
        PHYSclassData = df[df['系所全名'] == '物理學系'].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
        AllCoursesData = pd.concat([AllCoursesData, PHYSclassData], ignore_index=True)

    eng_map = {'1': '演說與簡報', '2': '新聞英文選讀', '3': '短篇故事選讀', '4': '影視英語聽講','5': '中英口譯', '6': '職場英語寫作', '7': '小說選讀', '8': '中英文筆譯','9': '學術英語聽力', '10': '職場英語口語表達'}
    for code in settings['EnglishNameList']:
        if code in eng_map:
            course_name = eng_map[code]
            LANGTmpclassData = df[df['中文課名'] == course_name].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
            AllCoursesData = pd.concat([AllCoursesData, LANGTmpclassData], ignore_index=True)
            if course_name not in settings['EnglishCourseNames']:
                settings['EnglishCourseNames'].append(course_name)

    AllCoursesData['教師'] = AllCoursesData['教師'].fillna('')
    AllCoursesData['等級制'] = AllCoursesData['等級制'].fillna(0)
    AllCoursesData = AllCoursesData.drop_duplicates(subset=['科號', '上課時間']).reset_index(drop=True)
    
    Type = [['常微分方程','訊號與系統','正規語言','數值最佳化','量子計算概論'],['電路與電子學一','積體電路設計概論','嵌入式系統概論','編譯器設計','超大型積體電路系統設計'],['計算機網路概論','軟體工程','密碼與網路安全概論','平行計算概論'],['資料庫系統概論','人工智慧概論','多媒體技術概論','機器學習概論']]
    type_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}; jump = type_map.get(settings['SelectType'], -1)
    AddCourseABCD, listvisited = pd.DataFrame(), []

    for t in range(4):
        if t == jump: continue
        AddCourseS = df[df['中文課名'].isin(Type[t]) & ~df['中文課名'].isin(listvisited)].nlargest(1, '等級制')
        if not AddCourseS.empty:
            listvisited.append(AddCourseS.iloc[0]['中文課名'])
            AddCourseABCD = pd.concat([AddCourseABCD, AddCourseS], ignore_index=True)

    remaining_names = [c for g in Type for c in g if c not in listvisited]
    AddCourseS_remaining = df[df['中文課名'].isin(remaining_names)].nlargest(1, '等級制')
    AddCourseABCD = pd.concat([AddCourseABCD, AddCourseS_remaining], ignore_index=True)
    AddCourseABCD = AddCourseABCD.nlargest(4, '等級制').reset_index(drop=True)

    return AllCoursesData, GEclassData, AddCourseABCD


def get_recommended_schedule(settings, AllCoursesData, GEclassData, AddCourseABCD, cs_learn_df):
    """
    核心排課演算法
    """
    CreditList = settings['CreditList']
    wanted_courses_names = settings.get('wanted_courses', [])

    # 初始化
    course_codes = np.full((8, 7, 13), None, dtype=object)
    credit = [0] * 8
    course_list = [pd.DataFrame() for _ in range(8)]
    result_df = pd.DataFrame()
    fulfilled_requirements = set() # 用來記錄已被滿足的基礎必修要求

    def is_conflict(semester, time_mapping):
        return any(course_codes[semester, t[0], t[1]] is not None for t in time_mapping)

    def try_schedule_course(course_df, semester):
        time_str = str(course_df['上課時間'].iloc[0]).replace(',', '')
        school_point = int(course_df['學分'].iloc[0])

        time_mapping, is_valid_time = [], True
        if len(time_str) % 2 != 0: is_valid_time = False
        else:
            for i in range(0, len(time_str), 2):
                day, period = time_str[i], time_str[i+1]
                if day not in WEEKDAY_MAPPING or period not in NUMBER_MAPPING: is_valid_time = False; break
                time_mapping.append([WEEKDAY_MAPPING[day], NUMBER_MAPPING[period]])
        if not is_valid_time:
            # print(f"警告：課程 '{course_df['中文課名'].iloc[0]}' (科號: {course_df['科號'].iloc[0]}) 的上課時間 '{time_str}' 格式錯誤，跳過。")
            return False
        if (credit[semester] + school_point) > CreditList[semester] or is_conflict(semester, time_mapping): return False
        try:
            course_year = int(str(course_df['科號'].iloc[0])[-6])
            if course_year > 0 and 'GEC' not in str(course_df['科號'].iloc[0]) and course_year != (semester // 2) + 1: return False
        except (ValueError, IndexError): pass
        for t in time_mapping: course_codes[semester, t[0], t[1]] = course_df['中文課名'].iloc[0]
        credit[semester] += school_point
        course_list[semester] = pd.concat([course_list[semester], course_df], ignore_index=True)
        return True

    def schedule_best_available(course_names, current_result_df):
        if not current_result_df.empty and any(name in current_result_df['中文課名'].values for name in course_names): return True, current_result_df
        temp_courses = AllCoursesData[AllCoursesData['中文課名'].isin(course_names)].sort_values(by='等級制', ascending=False)
        for _, course_to_schedule in temp_courses.iterrows():
            course_df = course_to_schedule.to_frame().T
            for sem in range(8):
                if try_schedule_course(course_df, sem):
                    current_result_df = pd.concat([current_result_df, course_df], ignore_index=True)
                    return True, current_result_df
        print(f"警告：課程 '{course_names[0]}' (及其替代課程) 因衝堂或學分限制無法排入。")
        return False, current_result_df

    # --- 排課流程開始 ---
    # *** 階段零: 優先處理使用者想上的課程 ***
    GE_Credit = 0
    GE_list = []
    if wanted_courses_names:
        for course_name in wanted_courses_names:
            if not result_df.empty and course_name in result_df['中文課名'].values: continue

            # 檢查是否為通識課
            is_ge_course = not GEclassData[GEclassData['中文課名'] == course_name].empty
            
            # 排課
            scheduled, result_df = schedule_best_available([course_name], result_df)

            if scheduled:
                #  如果排入的是通識，則更新通識學分
                if is_ge_course:
                    scheduled_course_info = result_df[result_df['中文課名'] == course_name].iloc[-1]
                    GE_Credit += int(scheduled_course_info['學分'])
                    GE_list.append(scheduled_course_info['科號'])
                
                # 如果排入的是替代課程，則標記基礎必修已滿足
                if course_name in REVERSE_SUB_MAP:
                    base_req = REVERSE_SUB_MAP[course_name]
                    fulfilled_requirements.add(base_req)
                    print(f"資訊：已將 '{course_name}' 作為 '{base_req}' 的替代課程排入。")

    # 階段一: 處理必修和專業選修
    if settings['EnglishCourseNames']:
        eng_df = pd.DataFrame({'中文課名': settings['EnglishCourseNames'], '科號': ['-1']*len(settings['EnglishCourseNames']), '類別': ['1']*len(settings['EnglishCourseNames'])})
        cs_learn_df = pd.concat([cs_learn_df, eng_df], ignore_index=True)

    for type_val in range(3):
        MustclassData = pd.DataFrame()
        if type_val == 0: MustclassData = cs_learn_df[cs_learn_df['類別'] == '1']
        elif type_val == 1: MustclassData = cs_learn_df[cs_learn_df['類別'] == settings['SelectCourse']]
        elif type_val == 2: MustclassData = AddCourseABCD

        for _, row in MustclassData.iterrows():
            course_name = row['中文課名']
            
            # 檢查此必修要求是否已被替代課程滿足
            if course_name in fulfilled_requirements:
                continue

            course_options = [course_name] + SUBSTITUTE_MAP.get(course_name, [])
            scheduled, result_df = schedule_best_available(course_options, result_df)
            if scheduled:
                fulfilled_requirements.add(course_name)

    # 階段二: 處理通識 (GE)
    ge_courses = GEclassData[~GEclassData['科號'].isin(GE_list) & ~GEclassData['科號'].isin(result_df['科號'])].sort_values(by='等級制', ascending=False)
    for i in range(1, 5):
        core_ge = ge_courses[ge_courses['通識分類'].str.contains(f'核心通識CoreGEcourses{i}', na=False)]
        for _, row in core_ge.iterrows():
            course_df, scheduled = row.to_frame().T, False
            for sem in range(8):
                if try_schedule_course(course_df, sem):
                    GE_Credit += int(row['學分']); scheduled = True
                    result_df = pd.concat([result_df, course_df.drop(columns=['通識分類'], errors='ignore')], ignore_index=True)
                    break
            if scheduled: break
    
    remaining_ge = ge_courses[~ge_courses['通識分類'].str.contains('核心通識', na=False)]
    for _, row in remaining_ge.iterrows():
        if GE_Credit >= 20: break
        course_df = row.to_frame().T
        for sem in range(8):
            if try_schedule_course(course_df, sem):
                GE_Credit += int(row['學分'])
                result_df = pd.concat([result_df, course_df.drop(columns=['通識分類'], errors='ignore')], ignore_index=True)
                break

    # 階段三 & 四: 處理選修並補滿學分
    elective_courses = AllCoursesData[~AllCoursesData['科號'].isin(result_df['科號'])]
    target_prefixes = ['EE', 'CS', 'ISA', 'COM']
    eecs_elective = elective_courses[elective_courses['科號'].str.contains('|'.join(target_prefixes), na=False)]
    eecs_elective = eecs_elective[~eecs_elective['中文課名'].str.contains('專題|書報討論', na=False)].sort_values(by='等級制', ascending=False)
    selected_eecs_credit = 0
    for _, row in eecs_elective.iterrows():
        if selected_eecs_credit >= 12: break
        course_df = row.to_frame().T
        for sem in range(8):
            if try_schedule_course(course_df, sem):
                selected_eecs_credit += int(row['學分'])
                result_df = pd.concat([result_df, course_df], ignore_index=True)
                break
    other_elective = elective_courses[~elective_courses['科號'].isin(result_df['科號'])].sort_values(by='等級制', ascending=False)
    for sem in range(8):
        while credit[sem] < CreditList[sem]:
            scheduled_in_sem = False
            for _, row in other_elective.iterrows():
                if not result_df.empty and row['科號'] in result_df['科號'].values: continue
                if try_schedule_course(row.to_frame().T, sem):
                     result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True); scheduled_in_sem = True; break
            if not scheduled_in_sem: break
    
    total_credits = sum(credit)
    return course_list, credit, total_credits