import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="우리 가족 플래너", page_icon="👨‍👩‍👧‍👦", layout="wide")

st.markdown("""
<head>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="가족 플래너">
    <meta name="mobile-web-app-capable" content="yes">
</head>
""", unsafe_allow_html=True)

DB_URL = "https://familyplanners-a98b5-default-rtdb.firebaseio.com"

# ---------------------------------------------------------
# 1. 파이어베이스 데이터 연동
# ---------------------------------------------------------
def load_data_from_db():
    if 'data_loaded' not in st.session_state:
        res_t = requests.get(f"{DB_URL}/tasks.json")
        raw_tasks = res_t.json() if res_t.json() else {}
        for d, t_list in raw_tasks.items():
            for i, t in enumerate(t_list):
                if isinstance(t, str):
                    raw_tasks[d][i] = {"text": t, "done": False}
        st.session_state.tasks = raw_tasks
        
        res_s = requests.get(f"{DB_URL}/supplies.json")
        raw_supplies = res_s.json() if res_s.json() else {}
        for d, cats in raw_supplies.items():
            for c_name, items in cats.items():
                for i, item in enumerate(items):
                    if isinstance(item, str):
                        raw_supplies[d][c_name][i] = {"text": item, "done": False}
        st.session_state.supplies = raw_supplies
        
        res_n = requests.get(f"{DB_URL}/notes.json")
        raw_notes = res_n.json() if res_n.json() else {}
        if isinstance(raw_notes, str): 
            today_str = datetime.today().strftime("%Y-%m-%d")
            raw_notes = {today_str: raw_notes}
        st.session_state.notes = raw_notes
        
        res_tmpl = requests.get(f"{DB_URL}/templates.json")
        if res_tmpl.json():
            st.session_state.templates = res_tmpl.json()
        else:
            st.session_state.templates = {
                "🎒 아이 외출 가방 세트": ["기저귀 3장", "물티슈", "아이 간식", "물병", "여벌 옷"],
                "🛒 마트 장보기 세트": ["우유", "계란", "두부", "제철 과일", "세제"]
            }
            requests.put(f"{DB_URL}/templates.json", json=st.session_state.templates)
            
        st.session_state.data_loaded = True

def save_tasks_to_db(): requests.put(f"{DB_URL}/tasks.json", json=st.session_state.tasks)
def save_supplies_to_db(): requests.put(f"{DB_URL}/supplies.json", json=st.session_state.supplies)
def save_notes_to_db(): requests.put(f"{DB_URL}/notes.json", json=st.session_state.notes)
def save_templates_to_db(): requests.put(f"{DB_URL}/templates.json", json=st.session_state.templates)

load_data_from_db()

# ---------------------------------------------------------
# 2. 상태 관리 및 동작 함수들
# ---------------------------------------------------------
if 'view_mode' not in st.session_state: st.session_state.view_mode = '주간' 
if 'selected_weekly_date' not in st.session_state: st.session_state.selected_weekly_date = None
if 'week_offset' not in st.session_state: st.session_state.week_offset = 0 

def toggle_task(date_str, item_idx):
    st.session_state.tasks[date_str][item_idx]['done'] = not st.session_state.tasks[date_str][item_idx]['done']
    save_tasks_to_db()

def toggle_supply(date_str, cat_name, item_idx):
    st.session_state.supplies[date_str][cat_name][item_idx]['done'] = not st.session_state.supplies[date_str][cat_name][item_idx]['done']
    save_supplies_to_db()

def delete_task(date_str, task_index):
    st.session_state.tasks[date_str].pop(task_index)
    if not st.session_state.tasks[date_str]: del st.session_state.tasks[date_str]
    save_tasks_to_db()

def delete_supply_item(date_str, cat_name, item_index):
    st.session_state.supplies[date_str][cat_name].pop(item_index)
    if not st.session_state.supplies[date_str][cat_name]: del st.session_state.supplies[date_str][cat_name]
    if not st.session_state.supplies[date_str]: del st.session_state.supplies[date_str]
    save_supplies_to_db()

def add_supplies(date_str, tmpl_name, item_list):
    if date_str not in st.session_state.supplies: st.session_state.supplies[date_str] = {}
    if tmpl_name not in st.session_state.supplies[date_str]: st.session_state.supplies[date_str][tmpl_name] = []
    for item in item_list:
        existing_texts = [i['text'] for i in st.session_state.supplies[date_str][tmpl_name]]
        if item not in existing_texts:
            st.session_state.supplies[date_str][tmpl_name].append({"text": item, "done": False})
    save_supplies_to_db()

def toggle_view():
    st.session_state.view_mode = '월간' if st.session_state.view_mode == '주간' else '주간'

def change_week(offset):
    st.session_state.week_offset += offset
    st.session_state.selected_weekly_date = None

def select_weekly_date(date_str):
    st.session_state.selected_weekly_date = date_str

def render_task(d_str, j, task, prefix):
    c1, c2, c3 = st.columns([6.5, 1.5, 2.0])
    with c1:
        text = f"~~{task['text']}~~" if task['done'] else task['text']
        st.checkbox(text, value=task['done'], key=f"chk_{prefix}t_{d_str}_{j}", on_change=toggle_task, args=(d_str, j))
    with c2:
        if st.button("⭕", key=f"o_{prefix}t_{d_str}_{j}"):
            toggle_task(d_str, j)
            st.rerun()
    with c3:
        if st.button("🗑️", key=f"del_{prefix}t_{d_str}_{j}"):
            delete_task(d_str, j)
            st.rerun()

def render_supply(d_str, cat_name, j, item, prefix):
    c1, c2, c3 = st.columns([6.5, 1.5, 2.0])
    with c1:
        text = f"~~{item['text']}~~" if item['done'] else item['text']
        st.checkbox(text, value=item['done'], key=f"chk_{prefix}s_{d_str}_{cat_name}_{j}", on_change=toggle_supply, args=(d_str, cat_name, j))
    with c2:
        if st.button("⭕", key=f"o_{prefix}s_{d_str}_{cat_name}_{j}"):
            toggle_supply(d_str, cat_name, j)
            st.rerun()
    with c3:
        if st.button("🗑️", key=f"del_{prefix}s_{d_str}_{cat_name}_{j}"):
            delete_supply_item(d_str, cat_name, j)
            st.rerun()

# ---------------------------------------------------------
# 3. 상단 메뉴바
# ---------------------------------------------------------
col1, col2 = st.columns([8, 2])
with col1: st.title("우리 가족 플래너 👨‍👩‍👧‍👦")
with col2:
    st.write("") 
    btn_text = "📅 월간 달력" if st.session_state.view_mode == '주간' else "📝 주간 플래너"
    
    if st.session_state.view_mode != '설정':
        c2_1, c2_2 = st.columns(2)
        with c2_1:
            st.button(btn_text, on_click=toggle_view, use_container_width=True)
        with c2_2:
            if st.button("⚙️ 준비물 템플릿 설정", use_container_width=True):
                st.session_state.view_mode = '설정'
                st.rerun()
    else:
        if st.button("돌아가기", use_container_width=True):
            st.session_state.view_mode = '주간'
            st.rerun()
st.write("---")

# ---------------------------------------------------------
# 4. 화면 1: 주간 플래너
# ---------------------------------------------------------
if st.session_state.view_mode == '주간':
    
    today_in_view = datetime.today() + timedelta(weeks=st.session_state.week_offset)
    view_month = today_in_view.month
    
    def get_week_of_month(dt):
        first_day = dt.replace(day=1)
        adjusted_dom = dt.day + first_day.weekday()
        return int((adjusted_dom - 1) / 7) + 1
        
    week_num = get_week_of_month(today_in_view)
    
    nav_c1, nav_c2, nav_c3 = st.columns([1, 8, 1])
    with nav_c1: st.button("◀ 이전 주", on_click=change_week, args=(-1,), use_container_width=True)
    with nav_c2: st.subheader(f"📅 {view_month}월 {week_num}주차 플래너 & 할 일 목록", anchor=False)
    with nav_c3: st.button("다음 주 ▶", on_click=change_week, args=(1,), use_container_width=True)
    
    start_of_week = today_in_view - timedelta(days=today_in_view.weekday())
    day_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    days_data = []
    
    for i in range(7):
        dt = start_of_week + timedelta(days=i)
        d_str = dt.strftime("%Y-%m-%d")
        days_data.append({"dt": dt, "str": d_str, "display": dt.strftime("%m/%d"), "name": day_names[i]})
        
    real_today_str = datetime.today().strftime("%Y-%m-%d")
    total_items = 0
    done_items = 0
    
    for task in st.session_state.tasks.get(real_today_str, []):
        total_items += 1
        if task['done']: done_items += 1
    for cat_name, items in st.session_state.supplies.get(real_today_str, {}).items():
        for item in items:
            total_items += 1
            if item['done']: done_items += 1
            
    progress_percent = int((done_items / total_items) * 100) if total_items > 0 else 0
    
    st.markdown(f"**🌟 오늘의 목표 달성률 ({real_today_str}) : {progress_percent}%**")
    st.progress(progress_percent / 100.0)
    st.write("---")
    
    row1_c1, row1_c2, row1_c3, row1_c4 = st.columns(4)
    cols1 = [row1_c1, row1_c2, row1_c3]
    
    for i in range(3):
        with cols1[i]:
            with st.container(border=True):
                d_str = days_data[i]["str"]
                
                btn_type = "primary" if st.session_state.selected_weekly_date == d_str else "secondary"
                st.button(f"{days_data[i]['display']} {days_data[i]['name']}", key=f"btn_{d_str}", type=btn_type, use_container_width=True, on_click=select_weekly_date, args=(d_str,))
                
                for j, task in enumerate(st.session_state.tasks.get(d_str, [])):
                    render_task(d_str, j, task, "w1")
                
                day_sups = st.session_state.supplies.get(d_str, {})
                for cat_name, items in day_sups.items():
                    is_all_done = len(items) > 0 and all(item['done'] for item in items)
                    prefix = "🔵 " if is_all_done else ""
                    st.markdown(f"**{prefix}{cat_name}**")
                            
                with st.popover("+ 할 일 추가", use_container_width=True):
                    with st.form(key=f"form_{d_str}", clear_on_submit=True):
                        new_task = st.text_input("새로운 할 일 입력")
                        if st.form_submit_button("추가"):
                            if new_task:
                                if d_str not in st.session_state.tasks: st.session_state.tasks[d_str] = []
                                st.session_state.tasks[d_str].append({"text": new_task, "done": False})
                                save_tasks_to_db()
                                st.rerun()

    with row1_c4:
        with st.container(border=False):
            st.markdown("##### 🎒 선택한 날짜 준비물")
            sel_d = st.session_state.selected_weekly_date
            if not sel_d: 
                st.info("👈 날짜 버튼을 누르면 상세 리스트가 나타납니다.")
            else:
                day_sups = st.session_state.supplies.get(sel_d, {})
                if not day_sups:
                    st.write(f"{sel_d} 엔 챙길 준비물이 없습니다.")
                else:
                    st.caption(f"{sel_d} 상세 리스트")
                    for cat_name, items in day_sups.items():
                        is_all_done = len(items) > 0 and all(item['done'] for item in items)
                        prefix = "🔵 " if is_all_done else ""
                        st.write(f"**{prefix}{cat_name}**")
                        for j, item in enumerate(items):
                            render_supply(sel_d, cat_name, j, item, "w_sel")

    row2_c1, row2_c2, row2_c3, row2_c4 = st.columns(4)
    cols2 = [row2_c1, row2_c2]
    
    for i in range(2):
        day_idx = i + 3
        with cols2[i]:
            with st.container(border=True):
                d_str = days_data[day_idx]["str"]
                
                btn_type = "primary" if st.session_state.selected_weekly_date == d_str else "secondary"
                st.button(f"{days_data[day_idx]['display']} {days_data[day_idx]['name']}", key=f"btn_{d_str}", type=btn_type, use_container_width=True, on_click=select_weekly_date, args=(d_str,))
                
                for j, task in enumerate(st.session_state.tasks.get(d_str, [])):
                    render_task(d_str, j, task, "w2")
                
                day_sups = st.session_state.supplies.get(d_str, {})
                for cat_name, items in day_sups.items():
                    is_all_done = len(items) > 0 and all(item['done'] for item in items)
                    prefix = "🔵 " if is_all_done else ""
                    st.markdown(f"**{prefix}{cat_name}**")
                        
                with st.popover("+ 할 일 추가", use_container_width=True):
                    with st.form(key=f"form_{d_str}", clear_on_submit=True):
                        new_task = st.text_input("새로운 할 일 입력")
                        if st.form_submit_button("추가"):
                            if new_task:
                                if d_str not in st.session_state.tasks: st.session_state.tasks[d_str] = []
                                st.session_state.tasks[d_str].append({"text": new_task, "done": False})
                                save_tasks_to_db()
                                st.rerun()
                    
    with row2_c3:
        with st.container(border=True):
            sat_str = days_data[5]["str"]
            sat_type = "primary" if st.session_state.selected_weekly_date == sat_str else "secondary"
            st.button(f"{days_data[5]['display']} 토요일", key=f"btn_{sat_str}", type=sat_type, use_container_width=True, on_click=select_weekly_date, args=(sat_str,))
                
            for j, task in enumerate(st.session_state.tasks.get(sat_str, [])):
                render_task(sat_str, j, task, "w_sat")
            for cat_name, items in st.session_state.supplies.get(sat_str, {}).items():
                is_all_done = len(items) > 0 and all(item['done'] for item in items)
                prefix = "🔵 " if is_all_done else ""
                st.markdown(f"**{prefix}{cat_name}**")
                
            st.write("---") 
            
            sun_str = days_data[6]["str"]
            sun_type = "primary" if st.session_state.selected_weekly_date == sun_str else "secondary"
            st.button(f"{days_data[6]['display']} 일요일", key=f"btn_{sun_str}", type=sun_type, use_container_width=True, on_click=select_weekly_date, args=(sun_str,))
                
            for j, task in enumerate(st.session_state.tasks.get(sun_str, [])):
                render_task(sun_str, j, task, "w_sun")
            for cat_name, items in st.session_state.supplies.get(sun_str, {}).items():
                is_all_done = len(items) > 0 and all(item['done'] for item in items)
                prefix = "🔵 " if is_all_done else ""
                st.markdown(f"**{prefix}{cat_name}**")
                
            with st.popover("+ 주말 할 일 추가", use_container_width=True):
                with st.form(key="form_weekend", clear_on_submit=True):
                    new_sat = st.text_input("토요일 할 일")
                    new_sun = st.text_input("일요일 할 일")
                    if st.form_submit_button("추가"):
                        updated = False
                        if new_sat:
                            if sat_str not in st.session_state.tasks: st.session_state.tasks[sat_str] = []
                            st.session_state.tasks[sat_str].append({"text": new_sat, "done": False})
                            updated = True
                        if new_sun:
                            if sun_str not in st.session_state.tasks: st.session_state.tasks[sun_str] = []
                            st.session_state.tasks[sun_str].append({"text": new_sun, "done": False})
                            updated = True
                        if updated:
                            save_tasks_to_db()
                            st.rerun()
                
    with row2_c4:
        with st.container(border=False):
            sel_d = st.session_state.selected_weekly_date
            if not sel_d:
                st.markdown("##### 📝 요일별 메모장")
                st.info("👈 날짜 버튼을 누르면 해당 날짜의 메모를 띄워줍니다.")
            else:
                st.markdown(f"##### 📝 {sel_d} 메모장")
                note_content = st.session_state.notes.get(sel_d, "")
                def update_notes():
                    st.session_state.notes[sel_d] = st.session_state[f"note_{sel_d}"]
                    save_notes_to_db()
                st.text_area("자유롭게 적어주세요 (자동 저장)", value=note_content, key=f"note_{sel_d}", height=200, on_change=update_notes)

# ---------------------------------------------------------
# 5. 화면 2: 월간 달력
# ---------------------------------------------------------
elif st.session_state.view_mode == '월간':
    cal_events = []
    all_dates = set(st.session_state.tasks.keys()).union(set(st.session_state.supplies.keys()))
    
    for d_str in all_dates:
        t_count = len(st.session_state.tasks.get(d_str, []))
        if t_count > 0:
            cal_events.append({"title": f"📝 할일 {t_count}개", "start": d_str, "color": "#3B82F6", "allDay": True})
            
        day_sups = st.session_state.supplies.get(d_str, {})
        for cat_name, items in day_sups.items():
            is_all_done = len(items) > 0 and all(item['done'] for item in items)
            prefix = "🔵 " if is_all_done else "🎒 "
            cal_events.append({"title": f"{prefix}{cat_name}", "start": d_str, "color": "#10B981", "allDay": True})

    calendar_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""},
        "initialView": "dayGridMonth", "selectable": True, "height": 550,
        "timeZone": "Asia/Seoul", "locale": "ko" 
    }

    state = calendar(events=cal_events, options=calendar_options, key="family_calendar")
    st.write("---")
    
    clicked_date = None
    if state.get("callback") == "dateClick":
        clicked_date = state["dateClick"].get("dateStr", state["dateClick"]["date"].split("T")[0])
    elif state.get("callback") == "eventClick":
        clicked_date = state["eventClick"]["event"]["start"].split("T")[0]

    if clicked_date:
        st.subheader(f"✅ {clicked_date} 상세 일정")
        
        action_c1, action_c2 = st.columns(2)
        with action_c1:
            with st.popover("➕ 새로운 할 일 직접 입력", use_container_width=True):
                with st.form(key=f"form_month_{clicked_date}", clear_on_submit=True):
                    new_task = st.text_input("할 일을 입력하세요")
                    if st.form_submit_button("추가"):
                        if new_task:
                            if clicked_date not in st.session_state.tasks: st.session_state.tasks[clicked_date] = []
                            st.session_state.tasks[clicked_date].append({"text": new_task, "done": False})
                            save_tasks_to_db()
                            st.rerun()
        
        with action_c2:
            with st.popover("⚡ 준비물(템플릿) 불러오기", use_container_width=True):
                st.write("챙길 항목만 선택 후 **적용하기**를 누르세요.")
                for tmpl_name, tmpl_items in st.session_state.templates.items():
                    with st.expander(tmpl_name):
                        with st.form(f"form_{clicked_date}_{tmpl_name}"):
                            selected_items = []
                            for item in tmpl_items:
                                if st.checkbox(item, value=True, key=f"chk_{clicked_date}_{tmpl_name}_{item}"):
                                    selected_items.append(item)
                            
                            if st.form_submit_button("선택한 항목만 적용하기"):
                                add_supplies(clicked_date, tmpl_name, selected_items)
                                st.rerun()
        st.write("---")
        
        tasks_for_date = st.session_state.tasks.get(clicked_date, [])
        supplies_for_date = st.session_state.supplies.get(clicked_date, {})
        
        list_col1, list_col2 = st.columns(2)
        with list_col1:
            st.markdown("##### 📝 해야 할 일")
            if not tasks_for_date:
                st.write("등록된 할 일이 없습니다.")
            else:
                for i, task in enumerate(tasks_for_date):
                    render_task(clicked_date, i, task, "m")
                    
        with list_col2:
            st.markdown("##### 🎒 챙길 준비물")
            if not supplies_for_date:
                st.write("등록된 준비물이 없습니다.")
            else:
                for cat_name, items in supplies_for_date.items():
                    is_all_done = len(items) > 0 and all(item['done'] for item in items)
                    prefix = "🔵 " if is_all_done else ""
                    st.write(f"**{prefix}{cat_name}**") 
                    for i, sup in enumerate(items):
                        render_supply(clicked_date, cat_name, i, sup, "m")
                        
        st.write("---")
        st.markdown(f"##### 📝 {clicked_date} 메모장")
        m_note_content = st.session_state.notes.get(clicked_date, "")
        def update_m_notes():
            st.session_state.notes[clicked_date] = st.session_state[f"note_m_{clicked_date}"]
            save_notes_to_db()
        st.text_area("자유롭게 적어주세요 (자동 저장)", value=m_note_content, key=f"note_m_{clicked_date}", height=150, on_change=update_m_notes)
            
    else:
        st.info("👆 위 달력에서 날짜나 배지를 콕 클릭해 상세 일정을 관리하세요.")

# ---------------------------------------------------------
# 6. 화면 3: 템플릿 설정 페이지
# ---------------------------------------------------------
elif st.session_state.view_mode == '설정':
    st.subheader("⚙️ 준비물 템플릿 설정")
    st.write("자주 챙기는 준비물 세트를 내 마음대로 추가, 수정, 삭제할 수 있습니다.")
    st.write("---")
    
    with st.expander("➕ 새 템플릿 추가하기", expanded=False):
        with st.form("new_template_form"):
            new_tmpl_name = st.text_input("새 템플릿 이름 (예: 🏕️ 캠핑 준비물)")
            # 💡 [요청 반영] 띄어쓰기로 구분 안내
            new_tmpl_items = st.text_area("준비물 항목 (띄어쓰기로 구분하여 입력, 예: 텐트 랜턴 침낭)")
            if st.form_submit_button("추가하기"):
                if new_tmpl_name and new_tmpl_items:
                    # split()을 사용하여 여러 공백이나 줄바꿈도 완벽하게 단어로 쪼갭니다.
                    items_list = [item.strip() for item in new_tmpl_items.split() if item.strip()]
                    st.session_state.templates[new_tmpl_name] = items_list
                    save_templates_to_db()
                    st.success(f"'{new_tmpl_name}' 템플릿이 추가되었습니다!")
                    st.rerun()

    st.markdown("##### 📌 기존 템플릿 관리")
    for tmpl_name, items in list(st.session_state.templates.items()):
        with st.container(border=True):
            col1, col2 = st.columns([8, 2])
            with col1:
                st.markdown(f"**{tmpl_name}**")
                items_str = " ".join(items) # 보여줄 때도 띄어쓰기로 연결해서 보여줍니다.
                st.write(items_str)
            with col2:
                if st.button("🗑️ 삭제", key=f"del_tmpl_{tmpl_name}", use_container_width=True):
                    del st.session_state.templates[tmpl_name]
                    save_templates_to_db()
                    st.rerun()
                
            with st.popover("✏️ 항목 수정", use_container_width=True):
                with st.form(key=f"edit_tmpl_{tmpl_name}"):
                    edited_items_str = st.text_area("수정할 항목 (띄어쓰기로 구분)", value=items_str)
                    if st.form_submit_button("저장"):
                        new_list = [item.strip() for item in edited_items_str.split() if item.strip()]
                        st.session_state.templates[tmpl_name] = new_list
                        save_templates_to_db()
                        st.rerun()