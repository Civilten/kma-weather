import streamlit as st
import pandas as pd
import requests
import io
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import plotly.graph_objects as go

# Page Config
st.set_page_config(page_title="기상청 기상상태 분석", layout="wide")

# Hide default Streamlit style
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
.stAppDeployButton {display:none;}
footer {visibility: hidden;}
[data-testid="stStatusWidget"] {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- API Key Management ---
def get_api_key():
    return st.session_state.get('api_key', 'fFr5k0SuRyia-ZNErlcoHA')

# Variable Mapping (Updated for Monthly APIs)
VAR_MAPPING = {
    'avgtamax': '평균최고기온 (℃)',
    'avgtamin': '평균최저기온 (℃)',
    'taavg': '평균기온 (℃)',
    'tamax': '최고기온 (℃)',
    'tamin': '최저기온 (℃)',
    'avghm': '평균상대습도 (%)',
    'rn_day': '강수량 (mm)', 
    'ws': '평균풍속 (m/s)',
    'ws_max': '최대풍속 (m/s)',
    'rn': '강수량 평년차 (mm)',
    'max_rn_day': '일최다강수량 (mm)',
    'avgcatot': '평균전운량 (1/10)',
    'sumssday': '일조시간 합계 (hr)',
    'daydur': '가조시간 (hr)',
    'stn_ko': '지점명',
    'stn_id': '지점번호',
    'year': '연도',
    'month': '월'
}

# --- State Management ---
# --- State Management ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'selection'
if 'raw_monthly_df' not in st.session_state:
    st.session_state['raw_monthly_df'] = None
if 'fetched_start_val' not in st.session_state:
    st.session_state['fetched_start_val'] = None
if 'fetched_end_val' not in st.session_state:
    st.session_state['fetched_end_val'] = None

def go_to_result():
    st.session_state['page'] = 'result'

def go_to_selection():
    st.session_state['page'] = 'selection'
    st.session_state['raw_monthly_df'] = None 
    st.session_state['fetched_start_val'] = None
    st.session_state['fetched_end_val'] = None
    st.session_state['region_sel'] = []
    st.session_state['station_sel'] = []

def on_region_change():
    curr = st.session_state.get('region_sel', [])
    if '전체 (모든 지역)' in curr:
        # If 'All' was just added as the last item, clear everything else
        if curr[-1] == '전체 (모든 지역)' and len(curr) > 1:
            st.session_state['region_sel'] = ['전체 (모든 지역)']
        # If 'All' was already there and something else was added, remove 'All'
        elif curr[0] == '전체 (모든 지역)' and len(curr) > 1:
            curr.remove('전체 (모든 지역)')
            st.session_state['region_sel'] = curr

def on_station_change():
    curr = st.session_state.get('station_sel', [])
    if '전체 (모든 관측소)' in curr:
        if curr[-1] == '전체 (모든 관측소)' and len(curr) > 1:
            st.session_state['station_sel'] = ['전체 (모든 관측소)']
        elif curr[0] == '전체 (모든 관측소)' and len(curr) > 1:
            curr.remove('전체 (모든 관측소)')
            st.session_state['station_sel'] = curr

# --- Data Functions ---

@st.cache_data
def load_station_list(tm_str, api_key):
    url = f"https://apihub.kma.go.kr/api/typ01/url/stn_inf.php?inf=SFC&stn=&tm={tm_str}&help=1&authKey={api_key}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'euc-kr' 
        
        df = pd.read_csv(io.StringIO(response.text), 
                         sep=r"\s+", 
                         comment="#", 
                         header=None,
                         on_bad_lines='skip')
        
        if len(df.columns) > 15:
            df.rename(columns={0: 'STN_ID', 10: 'STN_NAME', 15: 'REGION'}, inplace=True)
            df['STN_ID'] = df['STN_ID'].astype(str)
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

@st.cache_data
def fetch_single_month_api(api_url):
    try:
        response = requests.get(api_url, timeout=15)
        root = ET.fromstring(response.text)
        infos = root.findall(".//info")
        data_list = []
        for info in infos:
            row = {}
            for child in info:
                row[child.tag] = child.text
            data_list.append(row)
        return pd.DataFrame(data_list)
    except:
        return pd.DataFrame()

def fetch_monthly_data(year, month, api_key):
    month_str = f"{month:02d}"
    url1 = f"https://apihub.kma.go.kr/api/typ02/openApi/SfcMtlyInfoService/getMmSumry?pageNo=1&numOfRows=999&dataType=XML&year={year}&month={month_str}&authKey={api_key}"
    url2 = f"https://apihub.kma.go.kr/api/typ02/openApi/SfcMtlyInfoService/getMmSumry2?pageNo=1&numOfRows=999&dataType=XML&year={year}&month={month_str}&authKey={api_key}"
    
    df1 = fetch_single_month_api(url1)
    df2 = fetch_single_month_api(url2)
    
    if df1.empty and df2.empty:
        return pd.DataFrame()
        
    # Standardize STN_ID
    if not df1.empty and 'stnid' in df1.columns:
        df1.rename(columns={'stnid': 'stn_id'}, inplace=True)
    if not df2.empty and 'stn_id' not in df2.columns and 'stnid' in df2.columns:
        df2.rename(columns={'stnid': 'stn_id'}, inplace=True)
        
    # Merge
    if not df1.empty and not df2.empty:
        merged_df = pd.merge(df1, df2, on='stn_id', how='outer', suffixes=('', '_y'))
        
        # Handle stn_ko collision carefully
        if 'stn_ko' in merged_df.columns and 'stnko' in merged_df.columns:
            # Drop the alternate one if both exist
            merged_df.drop(columns=['stnko'], inplace=True)
        elif 'stnko' in merged_df.columns:
            merged_df.rename(columns={'stnko': 'stn_ko'}, inplace=True)
            
    elif not df1.empty:
        merged_df = df1
        if 'stnko' in merged_df.columns:
            merged_df.rename(columns={'stnko': 'stn_ko'}, inplace=True)
    else:
        merged_df = df2
        
    # Clean up and add temporal columns
    merged_df['year'] = year
    merged_df['month'] = month
    merged_df['time_val'] = year * 12 + month
    
    # Needs float conversion for aggregation later
    numeric_cols = ['avgtamax', 'avgtamin', 'taavg', 'tamax', 'tamin', 'avghm', 'rn_day', 'ws', 'ws_max',
                    'rn', 'max_rn_day', 'avgcatot', 'sumssday', 'daydur']
    for col in numeric_cols:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
            
    return merged_df

def fetch_date_range(start_val, end_val, selected_ids, api_key, progress_bar=None, status_text=None):
    all_months_df = []
    total_months_cnt = end_val - start_val + 1
    curr_cnt = 0
    
    for val in range(start_val, end_val + 1):
        y = (val - 1) // 12
        m = (val - 1) % 12 + 1
        
        if status_text:
            status_text.text(f"{y}년 {m}월 데이터를 불러오는 중...")
            
        df_month = fetch_monthly_data(y, m, api_key)
        if not df_month.empty and 'stn_id' in df_month.columns:
            df_month['stn_id'] = df_month['stn_id'].astype(str)
            current_selected_ids = [str(x) for x in selected_ids]
            
            filtered = df_month[df_month['stn_id'].isin(current_selected_ids)]
            all_months_df.append(filtered)
            
        curr_cnt += 1
        if progress_bar:
            progress_bar.progress(curr_cnt / total_months_cnt)
            
    if all_months_df:
        return pd.concat(all_months_df, ignore_index=True)
    return pd.DataFrame()


# --- UI: Selection Screen ---
def render_selection_screen():
    st.title("📅 기상청 기상상태 (월자료 기반) 분석")
    st.markdown("관측소를 선택하고 분석 기간(년/월)을 설정하세요.")
    
    # Sidebar - API Key Input
    with st.sidebar:
        st.header("🔑 설정")
        current_key = get_api_key()
        new_key = st.text_input("API Key 입력", value=current_key, type="password", help="기상청 API key 신청  https://apihub.kma.go.kr/")
        st.session_state['api_key'] = new_key
            
        # Add Footer Info
        st.sidebar.markdown('---')
        st.sidebar.markdown(
            """
            **제작자**: 김찬영  
            **Mail**: chykim1@gmail.com  
            **Ver**: 1.0  
            **Latest update**: 2026-02-20
            """
        )
            
    api_key = get_api_key()

    st.divider()
    
    # 1. Date & Load Stations
    c1, c2 = st.columns([1, 2])
    with c1:
        target_date = st.date_input("기준 날짜 (관측소 목록 조회용)", datetime.now())
        target_tm = target_date.strftime("%Y%m%d") + "0900" 
    
    with st.spinner("관측소 목록 불러오는 중..."):
        df_stations = load_station_list(target_tm, api_key)
    
    if df_stations.empty:
        st.error("관측소 목록을 불러올 수 없습니다. API Key를 확인해주세요.")
        return

    # 2. Region Filter
    st.subheader("지역 선택")
    all_regions = sorted(df_stations['REGION'].unique().astype(str))
    region_options = ['전체 (모든 지역)'] + all_regions
    
    if 'region_sel' not in st.session_state:
        st.session_state['region_sel'] = []
        
    selected_regions_raw = st.multiselect(
        "지역", 
        region_options, 
        key='region_sel',
        on_change=on_region_change,
        label_visibility="collapsed"
    )
    
    if '전체 (모든 지역)' in selected_regions_raw:
        selected_regions = all_regions
    else:
        selected_regions = selected_regions_raw
    
    filtered_stations = df_stations[df_stations['REGION'].isin(selected_regions)]
    filtered_stations = filtered_stations.sort_values('STN_NAME')
    
    st.divider()

    # 3. Station Selection
    st.subheader("관측소 선택")
    station_options = {f"{row['STN_NAME']} ({row['STN_ID']}) - {row['REGION']}": row['STN_ID'] 
                       for idx, row in filtered_stations.iterrows()}
    
    station_options_display = ['전체 (모든 관측소)'] + list(station_options.keys())
    
    # Reset station_sel if region changes and old values become invalid
    valid_station_options = set(station_options_display)
    if 'station_sel' in st.session_state:
        # Keep only valid ones
        st.session_state['station_sel'] = [x for x in st.session_state['station_sel'] if x in valid_station_options]
    else:
        st.session_state['station_sel'] = []
    
    selected_labels = st.multiselect(
        "관측소", 
        options=station_options_display,
        key='station_sel',
        on_change=on_station_change,
        label_visibility="collapsed"
    )
    
    if '전체 (모든 관측소)' in selected_labels:
        selected_ids = list(station_options.values())
        st.success(f"{len(filtered_stations)}개의 관측소가 모두 선택되었습니다.")
    else:
        selected_ids = [station_options[l] for l in selected_labels if l != '전체 (모든 관측소)']

    st.divider()

    # 4. Period Selection (Year & Month)
    current_year = datetime.now().year
    current_month = datetime.now().month

    st.subheader("기간 설정 (월단위)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        start_year = st.number_input("시작 연도", min_value=2010, max_value=current_year, value=2015)
    with c2:
        start_month = st.number_input("시작 월", min_value=1, max_value=12, value=1)
    with c3:
        end_year = st.number_input("종료 연도", min_value=2010, max_value=current_year, value=current_year)
    with c4:
        end_month = st.number_input("종료 월", min_value=1, max_value=12, value=current_month)

    # Start Analysis
    if st.button("분석 시작", type="primary", use_container_width=True):
        if not selected_ids:
            st.warning("최소 한 개 이상의 관측소를 선택해주세요.")
            return
            
        start_val = start_year * 12 + start_month
        end_val = end_year * 12 + end_month
        if start_val > end_val:
            st.warning("종료일이 시작일보다 빠를 수 없습니다.")
            return

        # Fetch Initial Data
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        st.session_state['raw_monthly_df'] = None
        
        try:
            raw_df = fetch_date_range(start_val, end_val, selected_ids, api_key, progress_bar, status_text)
                
            if not raw_df.empty:
                st.session_state['raw_monthly_df'] = raw_df
                
                # Context info
                st.session_state['context_start_val'] = start_val
                st.session_state['context_end_val'] = end_val
                st.session_state['fetched_start_val'] = start_val
                st.session_state['fetched_end_val'] = end_val
                st.session_state['context_station_count'] = len(selected_ids)
                st.session_state['context_selected_ids'] = selected_ids
                
                # Dictionary to map STN_ID to Korean Name using current filtered_stations
                stn_name_map = dict(zip(filtered_stations['STN_ID'].astype(str), filtered_stations['STN_NAME']))
                st.session_state['stn_name_map'] = stn_name_map
                
                go_to_result()
                st.rerun()
            else:
                st.error("해당 기간/관측소에 대한 데이터가 없습니다.")
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}") 

# --- Aggregation Logic ---
def aggregate_data(raw_df, mode, stn_map):
    # Determine grouping column based on toggle
    group_col = 'year' if mode == 'yearly' else 'month'
    
    # Base grouping: always by Station and the Temporal column
    grouped = raw_df.groupby(['stn_id', group_col])
    
    # Define aggregation operations
    agg_funcs = {}
    
    # Means
    for col in ['avgtamax', 'avgtamin', 'taavg', 'avghm', 'ws', 'avgcatot', 'daydur']:
        if col in raw_df.columns:
            agg_funcs[col] = 'mean'
            
    # Max
    for col in ['tamax', 'ws_max', 'max_rn_day']:
        if col in raw_df.columns:
            agg_funcs[col] = 'max'
            
    # Min
    for col in ['tamin']:
        if col in raw_df.columns:
            agg_funcs[col] = 'min'
            
    # Sum
    for col in ['sumssday', 'rn']:
        if col in raw_df.columns:
            agg_funcs[col] = 'sum'
            
    # Rainfall specific logic
    if 'rn_day' in raw_df.columns:
        if mode == 'yearly':
            # Sum of months within the year
            agg_funcs['rn_day'] = 'sum'
        else:
            # Average of the same month across multiple years
            agg_funcs['rn_day'] = 'mean'
            
    # Perform aggregation
    agg_df = grouped.agg(agg_funcs).reset_index()
    
    # Re-attach station names since groupby drops non-aggregated strings
    agg_df['stn_ko'] = agg_df['stn_id'].map(stn_map)
    
    # Round float columns for display
    float_cols = agg_df.select_dtypes(include=['float64']).columns
    agg_df[float_cols] = agg_df[float_cols].round(1)
    
    return agg_df

# --- UI: Result Screen ---
def render_result_screen():
    st.title("📊 분석 결과")
    api_key = get_api_key()
    
    # Sidebar: Dynamic Configuration
    with st.sidebar:
        st.header("⚙️ 분석 설정")
        
        st.info(f"**관측소**: {st.session_state.get('context_station_count', 0)}개 선택됨")
        
        st.subheader("기간 변경")
        
        # Current Context Periods
        cur_start_val = st.session_state.get('context_start_val')
        cur_end_val = st.session_state.get('context_end_val')
        
        cur_sy = (cur_start_val - 1) // 12
        cur_sm = (cur_start_val - 1) % 12 + 1
        cur_ey = (cur_end_val - 1) // 12
        cur_em = (cur_end_val - 1) % 12 + 1
        
        c1, c2 = st.columns(2)
        with c1:
            new_sy = st.number_input("시작 년", min_value=2010, value=cur_sy)
            new_ey = st.number_input("종료 년", min_value=2010, value=cur_ey)
        with c2:
            new_sm = st.number_input("월 ", min_value=1, max_value=12, value=cur_sm, key='sm_new')
            new_em = st.number_input("월", min_value=1, max_value=12, value=cur_em, key='em_new')
            
        new_start_val = new_sy * 12 + new_sm
        new_end_val = new_ey * 12 + new_em
        
        if st.button("기간 적용", use_container_width=True):
            if new_start_val > new_end_val:
                st.error("종료일이 시작일보다 빠릅니다.")
            else:
                fetched_start = st.session_state['fetched_start_val']
                fetched_end = st.session_state['fetched_end_val']
                selected_ids = st.session_state['context_selected_ids']
                
                st_placeholder = st.empty()
                prog_placeholder = st.empty()
                
                # Fetch leading delta if expands to the past
                if new_start_val < fetched_start:
                    head_df = fetch_date_range(new_start_val, fetched_start - 1, selected_ids, api_key, prog_placeholder, st_placeholder)
                    if not head_df.empty:
                        st.session_state['raw_monthly_df'] = pd.concat([head_df, st.session_state['raw_monthly_df']], ignore_index=True)
                    st.session_state['fetched_start_val'] = new_start_val
                    
                # Fetch trailing delta if expands to the future
                if new_end_val > fetched_end:
                    tail_df = fetch_date_range(fetched_end + 1, new_end_val, selected_ids, api_key, prog_placeholder, st_placeholder)
                    if not tail_df.empty:
                        st.session_state['raw_monthly_df'] = pd.concat([st.session_state['raw_monthly_df'], tail_df], ignore_index=True)
                    st.session_state['fetched_end_val'] = new_end_val
                
                # Clean up UI texts
                st_placeholder.empty()
                prog_placeholder.empty()

                # Update context
                st.session_state['context_start_val'] = new_start_val
                st.session_state['context_end_val'] = new_end_val
                st.rerun()

        st.divider()
        
        st.subheader("결과 보기 방식")
        view_mode_raw = st.radio(
            "통합 방식 선택",
            options=["연별 통계", "월별 통계"],
            help="연도별 흐름을 볼지, 전체 기간 동안의 각 월별 평균/합계를 볼지 선택합니다.",
            label_visibility='collapsed'
        )
        view_mode = 'yearly' if '연별' in view_mode_raw else 'monthly'
        
        st.divider()
        if st.button("← 첫 화면으로 돌아가기", type="secondary", use_container_width=True):
            go_to_selection()
            st.rerun()
            
        # Add Footer Info
        st.sidebar.markdown('---')
        st.sidebar.markdown(
            """
            **제작자**: 김찬영  
            **Mail**: chykim1@gmail.com  
            **Ver**: 1.0  
            **Latest update**: 2026-02-20
            """
        )

    raw_df_full = st.session_state.get('raw_monthly_df')
    
    if raw_df_full is None or raw_df_full.empty:
        st.error("데이터가 없습니다. 처음부터 다시 시도해주세요.")
        return

    # Filter raw_df to current requested period (handles shrinking without refetching)
    disp_start = st.session_state['context_start_val']
    disp_end = st.session_state['context_end_val']
    raw_df = raw_df_full[(raw_df_full['time_val'] >= disp_start) & (raw_df_full['time_val'] <= disp_end)]
    
    if raw_df.empty:
        st.warning("선택하신 기간 내에 데이터가 존재하지 않습니다.")
        return

    # Process Aggregation
    stn_map = st.session_state.get('stn_name_map', {})
    master_df = aggregate_data(raw_df, view_mode, stn_map)

    # Column Selection
    grouping_col = 'year' if view_mode == 'yearly' else 'month'
    
    # Filter available API columns in the aggregated DF
    available_api_cols = [c for c in master_df.columns if c in VAR_MAPPING and c not in ['stn_id', 'stn_ko', 'year', 'month']]
    
    def format_func(col):
        return VAR_MAPPING.get(col, col)
        
    # User Requested Default Columns
    user_defaults = ['taavg', 'avgtamax', 'avgtamin', 'avghm', 'ws', 'rn_day']
    # Ensure they exist in data
    defaults = [c for c in user_defaults if c in available_api_cols]
    
    st.subheader("데이터 항목 설정")
    
    st.markdown("**표시할 기상 항목 추가/ 제거**")
    base_options = available_api_cols
    selected_api_cols = st.multiselect("항목 선택", options=base_options, default=defaults, format_func=format_func, label_visibility="collapsed")

    if not selected_api_cols:
        st.warning("항목을 하나 이상 선택해주세요.")
        return

    # Final layout: Time Column, ... Selected Cols (Removed 'stn_ko')
    final_selected_cols = [grouping_col] + selected_api_cols
    rename_dict = {c: VAR_MAPPING.get(c, c) for c in final_selected_cols}
    
    # Excel Generation (Top)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        unique_stns_export = master_df['stn_id'].unique()
        for stn_id in unique_stns_export:
            stn_sub_df = master_df[master_df['stn_id'] == stn_id].copy()
            
            if grouping_col in stn_sub_df.columns:
                stn_sub_df.sort_values(grouping_col, inplace=True)
            
            # Ensure we only pick cols that exist in df
            cols_to_use = [x for x in final_selected_cols if x in stn_sub_df.columns]
            sheet_df = stn_sub_df[cols_to_use].rename(columns=rename_dict)
            
            stn_name = stn_sub_df.iloc[0]['stn_ko'] if 'stn_ko' in stn_sub_df.columns else str(stn_id)
            safe_sheet_name = "".join([c for c in stn_name if c.isalnum() or c in (' ', '_', '-')])[:30]
            sheet_df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            
    st.download_button(
        label="💾 엑셀 다운로드",
        data=buffer.getvalue(),
        file_name=f"weather_summary_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True
    )
    
    # Per-Channel Table Display & Dynamic Charts
    unique_stns = master_df['stn_id'].unique()
    
    st.divider()
    
    for stn_id in unique_stns:
        stn_df = master_df[master_df['stn_id'] == stn_id].copy()
        stn_name = stn_df.iloc[0]['stn_ko'] if 'stn_ko' in stn_df.columns else stn_id
        
        st.subheader(f"📍 {stn_name} ({stn_id})")
        
        if grouping_col in stn_df.columns:
            stn_df.sort_values(grouping_col, inplace=True)
            
        cols_to_use = [x for x in final_selected_cols if x in stn_df.columns]
        display_df = stn_df[cols_to_use].rename(columns=rename_dict)
        st.dataframe(display_df, use_container_width=True)
        
        # Draw Dynamic Chart based on selected columns
        if len(selected_api_cols) > 0:
            # Independent Chart Control
            selected_chart_cols = st.multiselect(
                "📈 그래프 표시 항목", 
                options=selected_api_cols, 
                default=selected_api_cols, 
                format_func=format_func, 
                key=f"chart_vars_{stn_id}",
                help="위쪽 데이터 표(Table)와 별개로 그래프에 그릴 항목만 선택할 수 있습니다."
            )
            
            if len(selected_chart_cols) > 0:
                # Dynamic Chart Styling Block
                chart_config = {}
                with st.expander("⚙️ 그래프 설정", expanded=False):
                    st.markdown("**전역 레이아웃 설정**")
                    lc1, lc2, lc3, lc4 = st.columns(4)
                    with lc1:
                        global_x_title = st.text_input("X축 제목", value='월' if view_mode == 'monthly' else '연도', key=f"x_title_{stn_id}")
                    with lc2:
                        global_y_title = st.text_input("Y축 제목", value='값', key=f"y_title_{stn_id}")
                    with lc3:
                        global_font_size = int(st.number_input("전체 텍스트 크기", min_value=8, max_value=40, value=14, step=1, key=f"fsize_{stn_id}"))
                    with lc4:
                        global_font_color = st.color_picker("전체 텍스트 색상", value="#000000", key=f"fcolor_{stn_id}")
                    
                    show_legend = st.checkbox("범례 표시", value=True, key=f"legend_{stn_id}")
                    
                    st.divider()

                    st.markdown("**개별 항목 스타일 설정**")
                    for idx, col in enumerate(selected_chart_cols):
                        label = VAR_MAPPING.get(col, col)
                        title_clean = label.replace(' ', '')
                        
                        # Determine defaults based on rules
                        if '평균기온' in title_clean and '최고' not in title_clean and '최저' not in title_clean:
                            def_type = '선 그래프 (Line)'
                            def_color = '#000000'
                        elif '최고' in title_clean or '최대' in title_clean:
                            def_type = '막대 그래프 (Bar)'
                            def_color = '#6cb659'
                        elif '최저' in title_clean or '최소' in title_clean:
                            def_type = '막대 그래프 (Bar)'
                            def_color = '#c94c4c'
                        elif '강수량' in title_clean:
                            def_type = '막대 그래프 (Bar)'
                            def_color = '#4682B4'
                        else:
                            def_type = '선 그래프 (Line)'
                            def_color = '#888888'

                        st.markdown(f"**{label}**")
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            ctype = st.selectbox("종류", ['선 그래프 (Line)', '막대 그래프 (Bar)'], index=0 if def_type.startswith('선') else 1, key=f"type_{stn_id}_{idx}")
                        with c2:
                            ccolor = st.color_picker("색상", value=def_color, key=f"color_{stn_id}_{idx}")
                        with c3:
                            cwidth = st.number_input("선 두께", min_value=1, max_value=10, value=2, disabled=not ctype.startswith('선'), key=f"width_{stn_id}_{idx}")
                        with c4:
                            msize = st.number_input("점 크기", min_value=0, max_value=20, value=8, disabled=not ctype.startswith('선'), key=f"msize_{stn_id}_{idx}")
                            
                        chart_config[col] = {
                            'type': 'line' if ctype.startswith('선') else 'bar',
                            'color': ccolor,
                            'width': cwidth,
                            'size': msize
                        }

                fig = go.Figure()
                x_vals = display_df[VAR_MAPPING.get(grouping_col)]
                
                for col in selected_chart_cols:
                    if col not in stn_df.columns:
                        continue
                    label = VAR_MAPPING.get(col, col)
                    y_vals = display_df[label]
                    cfg = chart_config.get(col)
                    
                    if cfg['type'] == 'line':
                        fig.add_trace(go.Scatter(
                            x=x_vals, y=y_vals, mode='lines+markers',
                            name=label, line=dict(color=cfg['color'], width=cfg['width']),
                            marker=dict(color=cfg['color'], size=cfg['size'], symbol='circle')
                        ))
                    else:
                        fig.add_trace(go.Bar(
                            x=x_vals, y=y_vals, name=label, marker_color=cfg['color'],
                            marker_line_color='black', marker_line_width=1
                        ))
                
                fig.update_layout(
                    title=f"{stn_name} 기상 지표 변화",
                    xaxis_title=global_x_title,
                    yaxis_title=global_y_title,
                    barmode='group',
                    plot_bgcolor='white',
                    font=dict(
                        family="Arial, sans-serif",
                        size=global_font_size,
                        color=global_font_color
                    ),
                    showlegend=show_legend,
                    hovermode="x unified",
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                # Add grid lines
                fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
                
                # For monthly mode, force x-axis labels to 1월, 2월 etc if values are 1..12
                if view_mode == 'monthly':
                    fig.update_xaxes(
                        tickmode='array',
                        tickvals=list(range(1, 13)),
                        ticktext=[f"{m}월" for m in range(1, 13)]
                    )
                else:
                     fig.update_xaxes(
                        tickmode='array',
                        tickvals=x_vals,
                        dtick=1
                    )
    
                st.plotly_chart(fig, use_container_width=True, theme=None)
            else:
                st.info("그래프를 그리기 위해 하나 이상의 항목을 선택해 주세요.")

# --- Main Routing ---
if st.session_state['page'] == 'selection':
    render_selection_screen()
elif st.session_state['page'] == 'result':
    render_result_screen()
