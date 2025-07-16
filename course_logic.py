import pandas as pd
import numpy as np
from itertools import accumulate

# 對照表
WEEKDAY_MAPPING = {'M': 0, 'T': 1, 'W': 2, 'R': 3, 'F': 4, 'S': 5}
NUMBER_MAPPING = {'1': 0, '2': 1, '3': 2, '4': 3, 'n': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'a': 10, 'b': 11, 'c': 12}

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
    根據使用者設定，準備好所有可選課程、通識課程、ABCD類選修課程。
    """
    SelectNumberList = settings['SelectNumberList']
    EnglishNameList = settings['EnglishNameList']
    SelectType = settings['SelectType']
    unwanted_courses = settings.get('unwanted_courses', []) # 取得不想上的課程清單

    # 在最一開始就排除不想上的課程 ***
    if unwanted_courses:
        df = df[~df['中文課名'].isin(unwanted_courses)].copy()

    CSclassData = df[df['系所全名'] == '資訊工程學系'].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
    EECSclassData = df[df['系所全名'] == '電機資訊學院學士班'].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
    GEclassData = df[df['系所全名'] == '通識教育中心'].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
    LANGclassData = df[(df['系所全名'] == '英語教育中心(110起)') | (df['系所全名'] == '英語教育中心')].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
    CLclassData = df[(df['系所全名'] == '中國文學系') & (df['中文課名'] == '大學中文')].dropna(subset=['科號', '中文課名', '學分', '上課時間'])

    base_frames = [CSclassData, EECSclassData, GEclassData, LANGclassData, CLclassData]
    AllCoursesData = pd.concat(base_frames, ignore_index=True)

    listAdd = ['微積分Ｂ一','微積分Ｂ二','普通物理Ｂ一','普通物理Ｂ二','普通化學一','普通化學二','生命科學一','生命科學二']
    for course_name in listAdd:
        AddclassData = df[df['中文課名'] == course_name].dropna(subset=['科號', '系所全名', '學分'])
        AllCoursesData = pd.concat([AllCoursesData, AddclassData], ignore_index=True)

    if "1" in SelectNumberList:
        MATHclassData = df[df['系所全名'] == '數學系'].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
        AllCoursesData = pd.concat([AllCoursesData, MATHclassData], ignore_index=True)
    if "2" in SelectNumberList:
        PHYSclassData = df[df['系所全名'] == '物理學系'].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
        AllCoursesData = pd.concat([AllCoursesData, PHYSclassData], ignore_index=True)

    eng_map = {
        '1': '中高級選讀英文-演說與簡報', '2': '中高級選讀英文-新聞英文選讀', '3': '中高級選讀英文-短篇故事選讀',
        '4': '中高級選讀英文-影視英語聽講', '5': '中高級選讀英文-中英口譯', '6': '中高級選讀英文-職場英語寫作',
        '7': '中高級選讀英文-小說選讀', '8': '中高級選讀英文-中英文筆譯', '9': '中高級選讀英文-學術英語聽力',
        '10': '中高級選讀英文-職場英語口語表達'
    }
    for code in EnglishNameList:
        if code in eng_map:
            course_name = eng_map[code]
            LANGTmpclassData = df[df['中文課名'] == course_name].dropna(subset=['科號', '中文課名', '學分', '上課時間'])
            AllCoursesData = pd.concat([AllCoursesData, LANGTmpclassData], ignore_index=True)
            if course_name not in settings['EnglishCourseNames']:
                settings['EnglishCourseNames'].append(course_name)

    AllCoursesData['教師'] = AllCoursesData['教師'].fillna('')
    AllCoursesData['等級制'] = AllCoursesData['等級制'].fillna(0)
    AllCoursesData = AllCoursesData.drop_duplicates(subset=['科號', '上課時間']).reset_index(drop=True)
    
    Type = [
        ['常微分方程','訊號與系統','正規語言','數值最佳化','量子計算概論'], # A
        ['電路與電子學一','積體電路設計概論','嵌入式系統概論','編譯器設計','超大型積體電路系統設計'], # B
        ['計算機網路概論','軟體工程','密碼與網路安全概論','平行計算概論'], # C
        ['資料庫系統概論','人工智慧概論','多媒體技術概論','機器學習概論']  # D
    ]
    type_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    jump = type_map.get(SelectType, -1)
    
    AddCourseABCD = pd.DataFrame()
    listvisited = []

    for t in range(4):
        if t == jump: continue
        
        AddCourseS = pd.DataFrame()
        for course_name in Type[t]:
            if course_name in listvisited: continue
            
            AddclassData2 = df[df['中文課名'] == course_name].dropna(subset=['科號', '系所全名', '學分'])
            AddCourseS = pd.concat([AddCourseS, AddclassData2], ignore_index=True)
            
        AddCourseS = AddCourseS.nlargest(1, '等級制')
        if not AddCourseS.empty:
            listvisited.append(AddCourseS.iloc[0]['中文課名'])
            AddCourseABCD = pd.concat([AddCourseABCD, AddCourseS], ignore_index=True)

    remaining_courses_names = [c for group_idx, group in enumerate(Type) for c in group if c not in listvisited]
    AddCourseS_remaining = df[df['中文課名'].isin(remaining_courses_names)].dropna(subset=['科號', '系所全名', '學分'])
    AddCourseS_remaining = AddCourseS_remaining.nlargest(1, '等級制')
    AddCourseABCD = pd.concat([AddCourseABCD, AddCourseS_remaining], ignore_index=True)
    
    AddCourseABCD = AddCourseABCD.nlargest(4, '等級制').reset_index(drop=True)

    return AllCoursesData, GEclassData, AddCourseABCD


def get_recommended_schedule(settings, AllCoursesData, GEclassData, AddCourseABCD, cs_learn_df):
    """
    核心排課演算法
    """
    CreditList = settings['CreditList']
    SelectCourse = settings['SelectCourse']
    EnglishCourseNames = settings['EnglishCourseNames']

    # 初始化
    course_codes = np.full((8, 7, 13), None, dtype=object)
    credit = [0] * 8
    course_list = [pd.DataFrame() for _ in range(8)]
    result_df = pd.DataFrame()

    if EnglishCourseNames:
        eng_df = pd.DataFrame({
            '中文課名': EnglishCourseNames,
            '科號': ['-1'] * len(EnglishCourseNames),
            '類別': ['1'] * len(EnglishCourseNames)
        })
        cs_learn_df = pd.concat([cs_learn_df, eng_df], ignore_index=True)

    def is_conflict(semester, time_mapping):
        return any(course_codes[semester, t[0], t[1]] is not None for t in time_mapping)

    def try_schedule_course(course_df, semester):
        time_str = str(course_df['上課時間'].iloc[0]).replace(',', '')
        school_point = int(course_df['學分'].iloc[0])
        
        time_mapping = []
        is_valid_time = True
        if len(time_str) % 2 != 0:
            is_valid_time = False
        else:
            for i in range(0, len(time_str), 2):
                day_char = time_str[i]
                period_char = time_str[i+1]
                
                if day_char not in WEEKDAY_MAPPING or period_char not in NUMBER_MAPPING:
                    is_valid_time = False
                    break
                time_mapping.append([WEEKDAY_MAPPING[day_char], NUMBER_MAPPING[period_char]])

        if not is_valid_time:
            print(f"警告：課程 '{course_df['中文課名'].iloc[0]}' (科號: {course_df['科號'].iloc[0]}) 的上課時間 '{time_str}' 格式錯誤，將跳過此課程。")
            return False

        if (credit[semester] + school_point) > CreditList[semester] or is_conflict(semester, time_mapping):
            return False

        try:
            course_year = int(str(course_df['科號'].iloc[0])[-6])
            if course_year > 0 and 'GEC' not in str(course_df['科號'].iloc[0]) and course_year != (semester // 2) + 1:
                return False
        except (ValueError, IndexError):
            pass

        for t in time_mapping:
            course_codes[semester, t[0], t[1]] = course_df['中文課名'].iloc[0]
        credit[semester] += school_point
        course_list[semester] = pd.concat([course_list[semester], course_df], ignore_index=True)
        return True

    # 階段一: 處理必修和專業選修
    for type_val in range(3):
        MustclassData = pd.DataFrame()
        if type_val == 0: MustclassData = cs_learn_df[cs_learn_df['類別'] == '1'].dropna(subset=['中文課名', '科號'])
        elif type_val == 1: MustclassData = cs_learn_df[cs_learn_df['類別'] == SelectCourse].dropna(subset=['中文課名', '科號'])
        elif type_val == 2: MustclassData = AddCourseABCD

        for _, row in MustclassData.iterrows():
            if row['科號'] == '-1': temp_courses = AllCoursesData.loc[AllCoursesData['中文課名'] == row['中文課名']]
            else: temp_courses = AllCoursesData.loc[AllCoursesData['科號'].astype(str).str.contains(str(row['科號']))]
            
            temp_courses = temp_courses.sort_values(by='等級制', ascending=False)
            
            scheduled = False
            for _, course_to_schedule in temp_courses.iterrows():
                course_df = course_to_schedule.to_frame().T
                for semester in range(8):
                    if try_schedule_course(course_df, semester):
                        result_df = pd.concat([result_df, course_df], ignore_index=True)
                        scheduled = True
                        break
                if scheduled: break
    
    # 階段二: 處理通識 (GE)
    GE_Credit = 0
    GE_list = []
    for i in range(1, 5):
        core_ge = GEclassData[GEclassData['通識分類'].str.contains(f'核心通識CoreGEcourses{i}', na=False)].sort_values(by='等級制', ascending=False)
        for _, row in core_ge.iterrows():
            course_df = row.to_frame().T
            scheduled = False
            for sem in range(8):
                if try_schedule_course(course_df, sem):
                    GE_Credit += int(row['學分'])
                    GE_list.append(row['科號'])
                    result_df = pd.concat([result_df, course_df.drop(columns=['通識分類'], errors='ignore')], ignore_index=True)
                    scheduled = True
                    break
            if scheduled: break

    remaining_ge = GEclassData[~GEclassData['科號'].isin(GE_list)].sort_values(by='等級制', ascending=False)
    for _, row in remaining_ge.iterrows():
        if GE_Credit >= 20: break
        course_df = row.to_frame().T
        for sem in range(8):
            if try_schedule_course(course_df, sem):
                GE_Credit += int(row['學分'])
                GE_list.append(row['科號'])
                result_df = pd.concat([result_df, course_df.drop(columns=['通識分類'], errors='ignore')], ignore_index=True)
                break

    # 階段三: 處理電機資訊專業選修
    target_prefixes = ['EE', 'CS', 'ISA', 'COM']
    eecs_elective = AllCoursesData[AllCoursesData['科號'].str.contains('|'.join(target_prefixes), na=False)]
    eecs_elective = eecs_elective[~eecs_elective['科號'].isin(result_df['科號'])]
    eecs_elective = eecs_elective[~eecs_elective['中文課名'].str.contains('專題|書報討論', na=False)]
    eecs_elective = eecs_elective.sort_values(by='等級制', ascending=False)
    selected_eecs_credit = 0
    for _, row in eecs_elective.iterrows():
        if selected_eecs_credit >= 12: break
        course_df = row.to_frame().T
        for sem in range(8):
            if try_schedule_course(course_df, sem):
                selected_eecs_credit += int(row['學分'])
                result_df = pd.concat([result_df, course_df], ignore_index=True)
                break

    # 階段四: 處理其餘選修
    other_elective = AllCoursesData[~AllCoursesData['科號'].isin(result_df['科號'])]
    other_elective = other_elective.sort_values(by='等級制', ascending=False)
    for sem in range(8):
        while credit[sem] < CreditList[sem]:
            scheduled_in_sem = False
            for _, row in other_elective.iterrows():
                if row['科號'] in result_df['科號']: continue
                if try_schedule_course(row.to_frame().T, sem):
                     result_df = pd.concat([result_df, row.to_frame().T], ignore_index=True)
                     scheduled_in_sem = True
                     break
            if not scheduled_in_sem: break
    
    total_credits = sum(credit)
    
    return course_list, credit, total_credits