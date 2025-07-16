import argparse
from course_logic import load_data, get_prepared_courses_and_settings, get_recommended_schedule

def main():
    parser = argparse.ArgumentParser(description="清大課程推薦系統 - 命令列工具")
    parser.add_argument('--credits', nargs=8, type=int, metavar='C',
                        default=[16, 16, 18, 20, 20, 20, 9, 9],
                        help='8個學期的期望學分 (預設: 16 16 18 20 20 20 9 9)')
    parser.add_argument('--extra-dept', nargs='*', choices=['1', '2'], default=[],
                        help="額外修習的科系 (1: 數學, 2: 物理)")
    parser.add_argument('--select-course', choices=['X', 'Y', 'Z'], default='X',
                        help="基礎科學課程 (X: 物理, Y: 化學, Z: 生科)")
    parser.add_argument('--avoid-type', choices=['A', 'B', 'C', 'D'], default='A',
                        help="不想優先修習的專業選修類別")
    parser.add_argument('--eng-type', nargs=2, default=['1', '2'],
                        help="想修習的2種選修英文代碼")
    
    args = parser.parse_args()

    # 收集設定
    user_settings = {
        "SelectNumberList": args.extra_dept,
        "EnglishNameList": args.eng_type,
        "EnglishCourseNames": [],
        "SelectCourse": args.select_course,
        "SelectType": args.avoid_type,
        "CreditList": args.credits,
    }
    
    print("設定:", user_settings)
    print("\n正在載入課程資料...")
    all_courses_df, cs_learn_df = load_data()
    if all_courses_df is None:
        return

    print("正在準備課程與設定...")
    AllCoursesData, GEclassData, AddCourseABCD = get_prepared_courses_and_settings(all_courses_df, user_settings)
    
    print("正在執行排課演算法...")
    course_lists, credits, total_credits = get_recommended_schedule(user_settings, AllCoursesData, GEclassData, AddCourseABCD, cs_learn_df)
    
    print("\n==================== 推薦課表結果 ====================")
    print(f"推薦總學分: {total_credits}\n")
    semesters = ["大一上", "大一下", "大二上", "大二下", "大三上", "大三下", "大四上", "大四下"]
    for i, sem in enumerate(semesters):
        print(f"--- {sem} ({credits[i]} 學分) ---")
        if not course_lists[i].empty:
            print(course_lists[i][['科號', '中文課名', '學分', '教師']].to_string(index=False))
        else:
            print("本學期沒有排課。")
        print("\n")

if __name__ == '__main__':
    main()