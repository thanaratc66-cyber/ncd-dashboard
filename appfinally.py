import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.colors as mcolors
import base64
import os
from streamlit_pdf_viewer import pdf_viewer
import joblib
import time

# คอลัมน์เชิงปริมาณสำหรับนำไปวิเคราะห์
numerical_features_A = [
    'Age', 'BMI', 'SBP', 'DBP', 'ผลการตรวจน้ำตาลในเลือด FBS',
    'ผลการตรวจระดับไขมันในเลือด (Cholesterol)', 'ALT (SGPT)',
    'Protein in urine_Score', 'Glucose in urine_Score', 'eGFR'
]

numerical_features_B = [
    'Age', 'BMI', 'SBP', 'DBP',
    'ผลการตรวจน้ำตาลในเลือด FBS',
    'ไขมันเลว LDL-C',
    'ไขมัน Triglyceride', 'ไขมันดี HDL-C', 'ALT (SGPT)',
    'Protein in urine_Score', 'Glucose in urine_Score', 'eGFR'
]

# โหลดข้อมูลหลัก (ใช้ cache เพื่อความเร็ว)
@st.cache_data
def load_data():
    # เปลี่ยนชื่อไฟล์ให้ตรงกับของคุณ
    df = pd.read_csv("master_health_data_finally.csv")
    return df

df_master = load_data()

available_years = ["ทั้งหมด"] + sorted([int(y) for y in df_master['Year'].dropna().unique()])
st.set_page_config(layout="wide", page_title="NCDs Dashboard")

# 2. INITIALIZE SESSION STATE (ต้องอยู่บนสุด ก่อนการใช้งาน)
if 'current_page' not in st.session_state: 
    st.session_state.current_page = "🏠 หน้าแรก"
if 'menu_open' not in st.session_state: 
    st.session_state.menu_open = False
if 'video_clicked' not in st.session_state:
    st.session_state.video_clicked = False

# --- ประกาศตัวแปร Global ไว้ด้านบนสุดของไฟล์ ---

# 1. รายชื่อตัวแปร
variables_package_A = ["BMI", "SBP", "DBP","ผลการตรวจน้ำตาลในเลือด FBS", "ผลการตรวจระดับไขมันในเลือด (Cholesterol)", "ALT (SGPT)"]
variables_package_B = ["BMI", "SBP", "DBP","ผลการตรวจน้ำตาลในเลือด FBS", "ผลการตรวจระดับไขมันในเลือด (Cholesterol)", "ไขมันเลว LDL-C", "ไขมัน Triglyceride", "ไขมันดี HDL-C", "ALT (SGPT)"]

# 2. ตัวแปรกลุ่มความเสี่ยง (นี่คือจุดที่ Error)
package_clusters = {
    'A': {
        0: "กลุ่มเสี่ยงโรคอ้วน + ไขมันในเลือดสูง + ความดันโลหิตสูง",
        1: "กลุ่มสุขภาพปกติ (ภาวะไขมันในเลือดเกินเกณฑ์เล็กน้อย)",
        2: "กลุ่มสุขภาพดี (ภาวะไขมันในเลือดสูงผิดปกติ)",
    },
    'B': {
        0: "กลุ่มโรคอ้วน + โรคความดันโลหิตสูง + ภาวะไขมันในเลือดผิดปกติ",
        1: "กลุ่มเฝ้าระวังไขมันในเลือด + เสี่ยงโรคความดันโลหิตสูง + ไตเสื่อมระยะ2",
        2: "กลุ่มสุขภาพดี (เฝ้าระวังไขมันในเลือด)",
        3: "กลุ่มโรคเบาหวานและโรคอ้วนระยะเริ่มต้น (เสี่ยงโรคความดันโลหิตสูง + ไขมันไตรกลีเซอไรด์สูง และไตเสื่อมระยะ2)",
        4: "กลุ่มโรคเบาหวานและโรคอ้วนรุนแรง (เสี่ยงโรคความดันโลหิตสูง + ไขมันไตรกลีเซอไรด์สูง และไตเสื่อมระยะ2)",
    }
}
package_vars = {
    'A': ["BMI", "SBP", "DBP", "ผลการตรวจน้ำตาลในเลือด FBS","ผลการตรวจระดับไขมันในเลือด (Cholesterol)", "ALT (SGPT)"],
    'B': ["Weight", "BMI", "SBP", "DBP","ผลการตรวจน้ำตาลในเลือด FBS",  "ผลการตรวจระดับไขมันในเลือด (Cholesterol)", "ไขมันเลว LDL-C", "ไขมัน Triglyceride", "ไขมันดี HDL-C", "ALT (SGPT)"]
}
# 3. ตัวแปรสี (Color Map)
# แพ็คเกจ A
color_map_A = {
    "กลุ่มเสี่ยงโรคอ้วน + ไขมันในเลือดสูง + ความดันโลหิตสูง": "#ff9b54", # สีส้มเหลือง
    "กลุ่มสุขภาพปกติ (ภาวะไขมันในเลือดเกินเกณฑ์เล็กน้อย)": "#50c878",   # สีฟ้า
    "กลุ่มสุขภาพดี (ภาวะไขมันในเลือดสูงผิดปกติ)": "#69a2f2"           # สีเขียวอ่อน
}


# แพ็คเกจ B
color_map_B = {
    "กลุ่มโรคอ้วน + โรคความดันโลหิตสูง + ภาวะไขมันในเลือดผิดปกติ": "#F9BCDD",
    "กลุ่มเฝ้าระวังไขมันในเลือด + เสี่ยงโรคความดันโลหิตสูง + ไตเสื่อมระยะ2": "#97C5D8",
    "กลุ่มสุขภาพดี (เฝ้าระวังไขมันในเลือด)": "#BBE0C7",
    "กลุ่มโรคเบาหวานและโรคอ้วนระยะเริ่มต้น (เสี่ยงโรคความดันโลหิตสูง + ไขมันไตรกลีเซอไรด์สูง และไตเสื่อมระยะ2)": "#FAC357",
    "กลุ่มโรคเบาหวานและโรคอ้วนรุนแรง (เสี่ยงโรคความดันโลหิตสูง + ไขมันไตรกลีเซอไรด์สูง และไตเสื่อมระยะ2)": "#E67E22"
}

all_colors_map = {
    "รวมทั้งหมด": "#79099c",
    "กลุ่มเสี่ยงโรคอ้วน + ไขมันในเลือดสูง + ความดันโลหิตสูง": "#ff9b54",
    "กลุ่มสุขภาพปกติ (ภาวะไขมันในเลือดเกินเกณฑ์เล็กน้อย)": "#50c878",
    "กลุ่มสุขภาพดี (ภาวะไขมันในเลือดสูงผิดปกติ)": "#69a2f2",
    "กลุ่มโรคอ้วน + โรคความดันโลหิตสูง + ภาวะไขมันในเลือดผิดปกติ": "#FF82A9",
    "กลุ่มสุขภาพดี (เฝ้าระวังไขมันในเลือด)": "#BBDED6",
    "กลุ่มเฝ้าระวังไขมันในเลือด + เสี่ยงโรคความดันโลหิตสูง + ไตเสื่อมระยะ2": "#FCAD84",
    "กลุ่มโรคเบาหวานและโรคอ้วนรุนแรง (เสี่ยงโรคความดันโลหิตสูง + ไขมันไตรกลีเซอไรด์สูง และไตเสื่อมระยะ2)": "#eb6e44",
    "กลุ่มโรคเบาหวานและโรคอ้วนระยะเริ่มต้น (เสี่ยงโรคความดันโลหิตสูง + ไขมันไตรกลีเซอไรด์สูง และไตเสื่อมระยะ2)": "#EDE9AC"
    
}

all_colors_map = {
        "รวมทั้งหมด": "#79099c",
    "กลุ่มเสี่ยงโรคอ้วน + ไขมันในเลือดสูง + ความดันโลหิตสูง": "#ff9b54",
    "กลุ่มสุขภาพปกติ (ภาวะไขมันในเลือดเกินเกณฑ์เล็กน้อย)": "#50c878",
    "กลุ่มสุขภาพดี (ภาวะไขมันในเลือดสูงผิดปกติ)": "#69a2f2",
    "กลุ่มโรคอ้วน + โรคความดันโลหิตสูง + ภาวะไขมันในเลือดผิดปกติ": "#FF82A9",
    "กลุ่มสุขภาพดี (เฝ้าระวังไขมันในเลือด)": "#BBDED6",
    "กลุ่มเฝ้าระวังไขมันในเลือด + เสี่ยงโรคความดันโลหิตสูง + ไตเสื่อมระยะ2": "#FCAD84",
    "กลุ่มโรคเบาหวานและโรคอ้วนรุนแรง (เสี่ยงโรคความดันโลหิตสูง + ไขมันไตรกลีเซอไรด์สูง และไตเสื่อมระยะ2)": "#eb6e44",
    "กลุ่มโรคเบาหวานและโรคอ้วนระยะเริ่มต้น (เสี่ยงโรคความดันโลหิตสูง + ไขมันไตรกลีเซอไรด์สูง และไตเสื่อมระยะ2)": "#EDE9AC"
}
risk_levels = {
    'A': {0: "กลุ่มเสี่ยงโรคอ้วน + ไขมันในเลือดสูง + ความดันโลหิตสูง"},
    'B': {1: "กลุ่มโรคเบาหวานและโรคอ้วนรุนแรง (เสี่ยงโรคความดันโลหิตสูง + ไขมันไตรกลีเซอไรด์สูง และไตเสื่อมระยะ2)"}
}

# ==========================================
# 📦 รวมฟังก์ชันหลักทั้งหมด (วางไว้ด้านบนสุดของไฟล์)
# ==========================================

def get_image_as_base64(file_path):
    try:
        if not os.path.exists(file_path): return ""
        with open(file_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{data}"
    except: return ""

def render_header(text):
    st.markdown(f'''
        <div class="card-header-custom">
            <h4 style="margin:0; font-size: 0.9rem; color: #333;">{text}</h4>
        </div>
    ''', unsafe_allow_html=True)

def render_kpi_card_custom(title, value, gradient, tooltip_text=""):
    return f'''
    <div title="{tooltip_text}" class="kpi-box-custom" style="background: {gradient}; cursor: help; padding: 20px; border-radius: 15px; color: white; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
        <div style="font-size: 0.7rem; font-weight: bold; text-transform: uppercase; margin-bottom: 5px;">{title}</div>
        <div style="font-size: 1.5rem; font-weight: 800;">{value:,}</div>
        <div style="font-size: 0.6rem; margin-top: 5px; opacity: 0.7;"></div>
    </div>
    '''

def calculate_variable_trends(df_pkg, package_code, current_selected_year, variables_list):
    stats_data = []
    all_years = sorted(df_pkg['Year'].dropna().unique().astype(int).tolist())
    if not all_years: 
        return pd.DataFrame()
    
    first_year = all_years[0]
    last_year = all_years[-1]
    numeric_vars = [v for v in variables_list if v in df_pkg.columns and pd.api.types.is_numeric_dtype(df_pkg[v])]

    for var in numeric_vars:
        means = df_pkg.groupby('Year')[var].mean(numeric_only=True).to_dict()
        min_val = df_pkg[var].min()
        max_val = df_pkg[var].max()
        
        base = means.get(first_year, 0)
        curr = means.get(last_year, 0)
        diff_pct = ((curr - base) / base * 100) if base != 0 else 0

        row = {"ตัวแปร": var}
        for y in all_years:
            row[str(y)] = round(means.get(y, 0), 2)
        
        row.update({
            "Min": round(min_val, 2), 
            "Max": round(max_val, 2), 
            "เปลี่ยน (%)": round(diff_pct, 1)
        })
        stats_data.append(row)
    
    return pd.DataFrame(stats_data)

def predict_health_clusters(df):
    df['Package_Type'] = df['Age'].apply(lambda x: 'A' if x < 35 else 'B')
    df['Predicted_Cluster'] = None
    
    for pkg in ['A', 'B']:
        subset = df[df['Package_Type'] == pkg].copy()
        if subset.empty: continue
        
        features = numerical_features_A if pkg == 'A' else numerical_features_B
        subset[features] = subset[features].fillna(subset[features].mean())
        
        scaler = joblib.load(f'scaler_{pkg}.pkl')
        model = joblib.load(f'clustering_model_{pkg}.pkl')
        
        scaled_data = scaler.transform(subset[features])
        df.loc[df['Package_Type'] == pkg, 'Predicted_Cluster'] = model.predict(scaled_data)
    return df

def render_package_dashboard(df_source, package_code, variables_list, cluster_names, current_color_map, selected_year, dept_name):
    for col in variables_list:
        if col in df_source.columns:
            df_source[col] = pd.to_numeric(df_source[col], errors='coerce')
            
    df_pkg = df_source[df_source['Package'] == package_code].copy()
    df_pkg['Cluster'] = df_pkg['Cluster'].astype(str).str.strip()
    
    if 'Gender' in df_pkg.columns:
        df_pkg['Gender'] = df_pkg['Gender'].astype(str).str.strip().str.capitalize()
    
    title = f"PACKAGE {package_code}"
    if df_pkg.empty: 
        st.info(f"ไม่มีข้อมูลสำหรับ {title} ในเงื่อนไขที่คุณเลือก")
        return

    counts = df_pkg['Cluster'].value_counts()
    total_screened = len(df_pkg)
    
    color_map_custom = {
        'รวมทั้งหมด': '#79099c',
        "กลุ่มเสี่ยงโรคอ้วน + ไขมันในเลือดสูง + ความดันโลหิตสูง": "#F59E0B",
        "กลุ่มสุขภาพปกติ (ภาวะไขมันในเลือดเกินเกณฑ์เล็กน้อย)": "#10B981",
        "กลุ่มสุขภาพดี (ภาวะไขมันในเลือดสูงผิดปกติ)": "#3B82F6",
        "กลุ่มโรคอ้วน + โรคความดันโลหิตสูง + ภาวะไขมันในเลือดผิดปกติ": "#EC4899",
        "กลุ่มสุขภาพดี (เฝ้าระวังไขมันในเลือด)": "#14B8A6",
        "กลุ่มเฝ้าระวังไขมันในเลือด + เสี่ยงโรคความดันโลหิตสูง + ไตเสื่อมระยะ2": "#D97706",
        "กลุ่มโรคเบาหวานและโรคอ้วนรุนแรง (เสี่ยงโรคความดันโลหิตสูง + ไขมันไตรกลีเซอไรด์สูง และไตเสื่อมระยะ2)": "#C2410C",
        "กลุ่มโรคเบาหวานและโรคอ้วนระยะเริ่มต้น (เสี่ยงโรคความดันโลหิตสูง + ไขมันไตรกลีเซอไรด์สูง และไตเสื่อมระยะ2)": "#EAB308"
    }

    df_pkg['Cluster'] = df_pkg['Cluster'].fillna("ไม่ระบุ")
    df_pkg['Gender'] = df_pkg['Gender'].fillna("ไม่ระบุ")
    
    # ฟังก์ชันช่วยสร้างหัวข้อหลักแบบพรีเมียม (ชิดซ้าย เว้นระยะห่าง และสดใส)
    def render_section_title(title_text, subtitle_text):
        st.markdown(f"""
            <div style="margin-top: 40px; margin-bottom: 18px; border-left: 5px solid #2563EB; padding-left: 14px;">
                <h3 style="color: #111827; font-size: 1.25rem; font-weight: 800; margin: 0 0 4px 0; letter-spacing: -0.01em;">{title_text}</h3>
                <p style="color: #6B7280; font-size: 0.85rem; font-weight: 400; margin: 0;">{subtitle_text}</p>
            </div>
        """, unsafe_allow_html=True)

    # ==========================================
    # 1. Executive Summary (การ์ดสรุปประเด็นสำคัญสำหรับผู้บริหาร)
    # ==========================================
    if not counts.empty:
        top_cluster_name = counts.idxmax()
        top_cluster_count = counts.max()
        top_cluster_pct = (top_cluster_count / total_screened * 100) if total_screened > 0 else 0
        
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%); border: 1px solid #BFDBFE; border-left: 6px solid #1D4ED8; border-radius: 16px; padding: 20px 24px; margin-bottom: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.02);">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 1.5rem;">📌</span>
                    <div>
                        <h4 style="margin: 0 0 4px 0; color: #1E3A8A; font-size: 0.95rem; font-weight: 700;">Executive Summary & Key Takeaways</h4>
                        <p style="margin: 0; color: #374151; font-size: 0.88rem; line-height: 1.5;">
                            ภาพรวมรอบข้อมูลปี <b>{selected_year}</b> ของ <b>{title}</b> พบว่าบุคลากรส่วนใหญ่มีความหนาแน่นสูงสุดใน <b>{top_cluster_name}</b> จำนวน <b>{top_cluster_count:,} คน</b> คิดเป็น <b>{top_cluster_pct:.1f}%</b> ของผู้ตรวจทั้งหมด ซึ่งผู้บริหารควรใช้เป็นข้อมูลเร่งรัดมาตรการควบคุมและให้คำแนะนำเชิงป้องกัน
                        </p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ==========================================
    # 2. Macro KPI Metrics (สถิติภาพรวมตัวชี้วัดด่วน)
    # ==========================================
    render_section_title("สถิติประชากรภาพรวมองค์กรจำแนกตามกลุ่มเสี่ยง", "Top-Level KPI Metrics & Population Overview")
    
    total_val = len(df_pkg)

    if package_code == 'A':
        cols = st.columns(4)
        with cols[0]: 
            total_bg = color_map_custom.get('รวมทั้งหมด', '#79099c')
            st.markdown(f'''
                <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-left: 5px solid {total_bg}; border-radius: 14px; padding: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.02); min-height: 220px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="font-size: 0.78rem; font-weight: 700; color: #374151; line-height: 1.3; min-height: 40px;">รวมประชากรตรวจทั้งหมด</div>
                        <div style="font-size: 1.6rem; font-weight: 800; color: #111827; margin-top: 6px;">{total_val:,} <span style="font-size: 0.85rem; font-weight: normal; color: #6B7280;">คน</span></div>
                        <div style="font-size: 0.8rem; font-weight: 700; color: {total_bg}; margin-top: 2px;">อัตราส่วนรวม 100.0%</div>
                    </div>
            ''', unsafe_allow_html=True)
            
            fig_total = go.Figure(go.Indicator(
                mode = "gauge+number", value = 100, domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {'axis': {'range': [0, 100], 'visible': False}, 'bar': {'color': total_bg}, 'bgcolor': "#F3F4F6"}
            ))
            fig_total.update_layout(height=55, margin=dict(l=5, r=5, t=5, b=5))
            st.plotly_chart(fig_total, use_container_width=True, key=f"macro_kpi_total_{package_code}", config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
        
        for i in range(3): 
            label = cluster_names.get(i)
            if label:
                df_cluster_filtered = df_pkg[df_pkg['Cluster'] == label]
                group_cnt = int(counts.get(label, 0))
                pct = (group_cnt / total_screened * 100) if total_screened > 0 else 0
                bg_col = color_map_custom.get(label, '#3B82F6')
                
                numeric_cols = df_cluster_filtered[variables_list].select_dtypes(include=[np.number]).columns
                avg_vals = df_cluster_filtered[numeric_cols].mean().round(2)
                tooltip_text = f"ค่าเฉลี่ยกลุ่ม {label} ({group_cnt} คน):\n" + "\n".join([f"{var}: {avg_vals.get(var, 0)}" for var in numeric_cols])
                
                with cols[i+1]:
                    st.markdown(f'''
                        <div title="{tooltip_text}" style="background: #FFFFFF; border: 1px solid #E5E7EB; border-left: 5px solid {bg_col}; border-radius: 14px; padding: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.02); min-height: 220px; display: flex; flex-direction: column; justify-content: space-between; cursor: help;">
                            <div>
                                <div style="font-size: 0.78rem; font-weight: 700; color: #374151; line-height: 1.3; min-height: 40px;">{label}</div>
                                <div style="font-size: 1.6rem; font-weight: 800; color: #111827; margin-top: 6px;">{group_cnt:,} <span style="font-size: 0.85rem; font-weight: normal; color: #6B7280;">คน</span></div>
                                <div style="font-size: 0.8rem; font-weight: 700; color: {bg_col}; margin-top: 2px;">คิดเป็น {pct:.1f}% ของผู้ตรวจ</div>
                            </div>
                    ''', unsafe_allow_html=True)
                    
                    fig_mini = go.Figure(go.Indicator(
                        mode = "gauge+number", value = pct, domain = {'x': [0, 1], 'y': [0, 1]},
                        gauge = {'axis': {'range': [0, 100], 'visible': False}, 'bar': {'color': bg_col}, 'bgcolor': "#F3F4F6"}
                    ))
                    fig_mini.update_layout(height=55, margin=dict(l=5, r=5, t=5, b=5))
                    st.plotly_chart(fig_mini, use_container_width=True, key=f"macro_kpi_gauge_{package_code}_{i}", config={'displayModeBar': False})
                    st.markdown('</div>', unsafe_allow_html=True)

    elif package_code == 'B':
        def get_tooltip(label, sub_df, vars_list):
            numeric_cols = sub_df[vars_list].select_dtypes(include=[np.number]).columns
            avg_vals = sub_df[numeric_cols].mean().round(2)
            return f"ค่าเฉลี่ยกลุ่ม {label} ({len(sub_df)} คน):\n" + "\n".join([f"{v}: {avg_vals.get(v, 0)}" for v in numeric_cols])

        cols1 = st.columns(3)
        total_bg = color_map_custom.get('รวมทั้งหมด', '#79099c')
        
        with cols1[0]: 
            st.markdown(f'''
                <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-left: 5px solid {total_bg}; border-radius: 14px; padding: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.02); min-height: 220px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="font-size: 0.78rem; font-weight: 700; color: #374151; line-height: 1.3; min-height: 40px;">รวมประชากรตรวจทั้งหมด</div>
                        <div style="font-size: 1.6rem; font-weight: 800; color: #111827; margin-top: 6px;">{total_val:,} <span style="font-size: 0.85rem; font-weight: normal; color: #6B7280;">คน</span></div>
                        <div style="font-size: 0.8rem; font-weight: 700; color: {total_bg}; margin-top: 2px;">อัตราส่วนรวม 100.0%</div>
                    </div>
            ''', unsafe_allow_html=True)
            
            fig_total_b = go.Figure(go.Indicator(
                mode = "gauge+number", value = 100, domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {'axis': {'range': [0, 100], 'visible': False}, 'bar': {'color': total_bg}, 'bgcolor': "#F3F4F6"}
            ))
            fig_total_b.update_layout(height=55, margin=dict(l=5, r=5, t=5, b=5))
            st.plotly_chart(fig_total_b, use_container_width=True, key=f"macro_kpi_total_b", config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)
        
        for i in range(2):
            label = cluster_names.get(i)
            if label:
                df_cluster_filtered = df_pkg[df_pkg['Cluster'] == label]
                group_cnt = int(counts.get(label, 0))
                pct = (group_cnt / total_screened * 100) if total_screened > 0 else 0
                bg_col = color_map_custom.get(label, '#3B82F6')
                tooltip_text = get_tooltip(label, df_cluster_filtered, variables_list)
                
                with cols1[i+1]: 
                    st.markdown(f'''
                        <div title="{tooltip_text}" style="background: #FFFFFF; border: 1px solid #E5E7EB; border-left: 5px solid {bg_col}; border-radius: 14px; padding: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.02); min-height: 220px; display: flex; flex-direction: column; justify-content: space-between; cursor: help;">
                            <div>
                                <div style="font-size: 0.78rem; font-weight: 700; color: #374151; line-height: 1.3; min-height: 40px;">{label}</div>
                                <div style="font-size: 1.6rem; font-weight: 800; color: #111827; margin-top: 6px;">{group_cnt:,} <span style="font-size: 0.85rem; font-weight: normal; color: #6B7280;">คน</span></div>
                                <div style="font-size: 0.8rem; font-weight: 700; color: {bg_col}; margin-top: 2px;">คิดเป็น {pct:.1f}% ของผู้ตรวจ</div>
                            </div>
                    ''', unsafe_allow_html=True)
                    
                    fig_mini = go.Figure(go.Indicator(
                        mode = "gauge+number", value = pct, domain = {'x': [0, 1], 'y': [0, 1]},
                        gauge = {'axis': {'range': [0, 100], 'visible': False}, 'bar': {'color': bg_col}, 'bgcolor': "#F3F4F6"}
                    ))
                    fig_mini.update_layout(height=55, margin=dict(l=5, r=5, t=5, b=5))
                    st.plotly_chart(fig_mini, use_container_width=True, key=f"macro_kpi_b_row1_{i}", config={'displayModeBar': False})
                    st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
        
        cols2 = st.columns(3)
        for i in range(2, 5):
            label = cluster_names.get(i)
            if label:
                df_cluster_filtered = df_pkg[df_pkg['Cluster'] == label]
                group_cnt = int(counts.get(label, 0))
                pct = (group_cnt / total_screened * 100) if total_screened > 0 else 0
                bg_col = color_map_custom.get(label, '#3B82F6')
                tooltip_text = get_tooltip(label, df_cluster_filtered, variables_list)
                
                if i - 2 < len(cols2):
                    with cols2[i-2]: 
                        st.markdown(f'''
                            <div title="{tooltip_text}" style="background: #FFFFFF; border: 1px solid #E5E7EB; border-left: 5px solid {bg_col}; border-radius: 14px; padding: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.02); min-height: 220px; display: flex; flex-direction: column; justify-content: space-between; cursor: help;">
                                <div>
                                    <div style="font-size: 0.78rem; font-weight: 700; color: #374151; line-height: 1.3; min-height: 40px;">{label}</div>
                                    <div style="font-size: 1.6rem; font-weight: 800; color: #111827; margin-top: 6px;">{group_cnt:,} <span style="font-size: 0.85rem; font-weight: normal; color: #6B7280;">คน</span></div>
                                    <div style="font-size: 0.8rem; font-weight: 700; color: {bg_col}; margin-top: 2px;">คิดเป็น {pct:.1f}% ของผู้ตรวจ</div>
                                </div>
                        ''', unsafe_allow_html=True)
                        
                        fig_mini = go.Figure(go.Indicator(
                            mode = "gauge+number", value = pct, domain = {'x': [0, 1], 'y': [0, 1]},
                            gauge = {'axis': {'range': [0, 100], 'visible': False}, 'bar': {'color': bg_col}, 'bgcolor': "#F3F4F6"}
                        ))
                        fig_mini.update_layout(height=55, margin=dict(l=5, r=5, t=5, b=5))
                        st.plotly_chart(fig_mini, use_container_width=True, key=f"macro_kpi_b_row2_{i}", config={'displayModeBar': False})
                        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ==========================================
    # 3. Key Health Metrics vs Thresholds Cards
    # ==========================================
    render_section_title("ค่าเฉลี่ยตัวชี้วัดสุขภาพภาพรวมองค์กรเทียบกับเกณฑ์มาตรฐาน", "Key Health Metrics vs Ministry Thresholds")
    
    m_bmi = df_pkg['BMI'].mean() if 'BMI' in df_pkg.columns else 0
    m_sbp = df_pkg['SBP'].mean() if 'SBP' in df_pkg.columns else 0
    m_fbs = df_pkg['ผลการตรวจน้ำตาลในเลือด FBS'].mean() if 'ผลการตรวจน้ำตาลในเลือด FBS' in df_pkg.columns else 0
    m_chol = df_pkg['ผลการตรวจระดับไขมันในเลือด (Cholesterol)'].mean() if 'ผลการตรวจระดับไขมันในเลือด (Cholesterol)' in df_pkg.columns else 0

    metric_cols = st.columns(4)
    with metric_cols[0]:
        status_bmi = "⚠️ เกินเกณฑ์" if m_bmi > 23.0 else "🟢 ปกติ/สมส่วน"
        st.markdown(f'''
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="font-size: 0.75rem; color: #6B7280; font-weight: 600;">ค่า BMI เฉลี่ยองค์กร</div>
                <div style="font-size: 1.4rem; font-weight: 800; color: #111827; margin-top: 4px;">{m_bmi:.1f}</div>
                <div style="font-size: 0.75rem; color: {'#EF4444' if '⚠️' in status_bmi else '#10B981'}; font-weight: 700; margin-top: 4px;">{status_bmi} (เกณฑ์ &le; 23)</div>
            </div>
        ''', unsafe_allow_html=True)
        
    with metric_cols[1]:
        status_sbp = "⚠️ สูงกว่าปกติ" if m_sbp >= 130 else "🟢 ปกติ/เหมาะสม"
        st.markdown(f'''
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="font-size: 0.75rem; color: #6B7280; font-weight: 600;">ความดัน SBP เฉลี่ยองค์กร</div>
                <div style="font-size: 1.4rem; font-weight: 800; color: #111827; margin-top: 4px;">{m_sbp:.1f} mmHg</div>
                <div style="font-size: 0.75rem; color: {'#EF4444' if '⚠️' in status_sbp else '#10B981'}; font-weight: 700; margin-top: 4px;">{status_sbp} (เกณฑ์ < 130)</div>
            </div>
        ''', unsafe_allow_html=True)

    with metric_cols[2]:
        status_fbs = "⚠️ เสี่ยงเบาหวาน" if m_fbs >= 100 else "🟢 ปกติ"
        st.markdown(f'''
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="font-size: 0.75rem; color: #6B7280; font-weight: 600;">น้ำตาล FBS เฉลี่ยองค์กร</div>
                <div style="font-size: 1.4rem; font-weight: 800; color: #111827; margin-top: 4px;">{m_fbs:.1f} mg/dL</div>
                <div style="font-size: 0.75rem; color: {'#EF4444' if '⚠️' in status_fbs else '#10B981'}; font-weight: 700; margin-top: 4px;">{status_fbs} (เกณฑ์ < 100)</div>
            </div>
        ''', unsafe_allow_html=True)

    with metric_cols[3]:
        status_chol = "⚠️ เกณฑ์สูง" if m_chol >= 200 else "🟢 เหมาะสม"
        st.markdown(f'''
            <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                <div style="font-size: 0.75rem; color: #6B7280; font-weight: 600;">ไขมันรวม Chol เฉลี่ยองค์กร</div>
                <div style="font-size: 1.4rem; font-weight: 800; color: #111827; margin-top: 4px;">{m_chol:.1f} mg/dL</div>
                <div style="font-size: 0.75rem; color: {'#EF4444' if '⚠️' in status_chol else '#10B981'}; font-weight: 700; margin-top: 4px;">{status_chol} (เกณฑ์ < 200)</div>
            </div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 4. บรรทัดที่ 1: วงกลมสัดส่วนความเสี่ยง (Pie Chart) คู่กับ กราฟเส้นแนวโน้มระยะยาว (สัดส่วน 1:1 และหัวข้ออยู่ด้านบน)
    # ==========================================
    render_section_title("สัดส่วนความเสี่ยงและแนวโน้มระยะยาว", "Macro Analytics & Long-Term Trends")
    
    # เปลี่ยนสัดส่วนเป็น [1, 1] เพื่อให้แบ่งคนละครึ่งเท่ากันพอดี
    row1_left, row1_right = st.columns([1, 1], gap="medium")
    
    with row1_left:
        # ชื่อหัวข้อกราฟวงกลมมาอยู่ด้านบนสุด
        st.markdown("""
            <div style="text-align: left; margin-bottom: 8px;">
                <h4 style="margin:0; font-size: 0.95rem; color: #1F2937; font-weight: 700;">สัดส่วนความเสี่ยงสุขภาพภาพรวม</h4>
                <p style="font-size: 0.78rem; color: #4B5563; margin-top: 2px;">สัดส่วนบุคลากรทั้งองค์กรจำแนกตามกลุ่มเสี่ยง</p>
            </div>
        """, unsafe_allow_html=True)
        
        fig_pie = px.pie(df_pkg, names='Cluster', color='Cluster', color_discrete_map=all_colors_map, hole=0.45)
        # ปรับตำแหน่ง legend ให้มาอยู่ด้านล่าง เพื่อไม่ให้บีบตัวกราฟจนหาย และกำหนดความสูงให้พอดี
        fig_pie.update_layout(
            margin=dict(t=10, b=10, l=10, r=10), 
            height=320, 
            showlegend=True, 
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, font=dict(size=8))
        )
        st.plotly_chart(fig_pie, use_container_width=True, key=f"macro_pie_{package_code}")
        
        
    with row1_right:
        # ชื่อหัวข้อกราฟเส้นมาอยู่ด้านบนสุดเช่นกัน
        st.markdown("""
            <div style="text-align: left; margin-bottom: 8px;">
                <h4 style="margin:0; font-size: 0.95rem; color: #1F2937; font-weight: 700;">แนวโน้มสัดส่วนกลุ่มเสี่ยงรายปี</h4>
                <p style="font-size: 0.78rem; color: #4B5563; margin-top: 2px;">ติดตามการเปลี่ยนแปลงจำนวนบุคลากรในแต่ละกลุ่มสุขภาพย้อนหลัง</p>
            </div>
        """, unsafe_allow_html=True)
        
        df_trend = df_pkg.groupby(['Year', 'Cluster']).size().reset_index(name='count')
        fig_trend = px.line(df_trend, x='Year', y='count', color='Cluster', color_discrete_map=all_colors_map, markers=True)
        fig_trend.update_traces(mode='lines+markers', fill='tozeroy', fillcolor='rgba(99, 102, 241, 0.05)')
        fig_trend.update_layout(
            height=320, 
            margin=dict(t=10, b=10, l=10, r=10), 
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5, font=dict(size=8)),
            xaxis=dict(tickmode='linear')
        )
        st.plotly_chart(fig_trend, use_container_width=True, key=f"macro_line_{package_code}_{selected_year}_{dept_name}")

    # ==========================================
    # 5. บรรทัดที่ 2: แผนภาพการกระจายตัว (Scatter Plot) เต็มบรรทัด
    # ==========================================
    render_section_title("การวิเคราะห์ความสัมพันธ์ตัวแปรสุขภาพ", "Health Variables Correlation & Thresholds")
    
    st.markdown("""
        <div style="text-align: left; margin-bottom: 10px;">
            <h4 style="margin:0; font-size: 0.95rem; color: #1F2937; font-weight: 700;">แผนภาพการกระจายตัวเปรียบเทียบตัวแปรสุขภาพ (องค์กร)</h4>
            <p style="font-size: 0.78rem; color: #4B5563; margin-top: 2px;">ตรวจสอบความสัมพันธ์ตัวแปรสุขภาพเทียบกับเกณฑ์มาตรฐานกรมควบคุมโรค</p>
        </div>
    """, unsafe_allow_html=True)
    
    sc_x_col, sc_y_col = st.columns(2)
    with sc_x_col:
        x_p = st.selectbox("เลือกตัวแปรแกน X:", variables_list, key=f"macro_x_{package_code}")
    with sc_y_col:
        y_p = st.selectbox("เลือกตัวแปรแกน Y:", variables_list, key=f"macro_y_{package_code}")
    
    fig_s = px.scatter(df_pkg, x=x_p, y=y_p, color='Cluster', color_discrete_map=all_colors_map, opacity=0.8)
    
    thresholds = {
        'BMI': {'line': 23.0, 'name': 'เกณฑ์เริ่มน้ำหนักเกิน (23)'},
        'SBP': {'line': 140.0, 'name': 'เกณฑ์ความดันสูงระดับ 1 (140)'},
        'DBP': {'line': 90.0, 'name': 'เกณฑ์ความดันสูงระดับ 1 (90)'},
        'ผลการตรวจน้ำตาลในเลือด FBS': {'line': 100.0, 'name': 'เกณฑ์เสี่ยงเบาหวาน (100)'},
        'ผลการตรวจระดับไขมันในเลือด (Cholesterol)': {'line': 200.0, 'name': 'เกณฑ์ไขมันเหมาะสม (<200)'},
        'ALT (SGPT)': {'line': 40.0, 'name': 'เกณฑ์ตับอักเสบ (>40)'},
        'eGFR': {'line': 90.0, 'name': 'เกณฑ์การทำงานของไต (<90 ผิดปกติ)'},
        'ไขมันเลว LDL-C': {'line': 130.0, 'name': 'เกณฑ์ LDL เหมาะสม (<130)'},
        'ไขมัน Triglyceride': {'line': 150.0, 'name': 'เกณฑ์ Triglyceride เหมาะสม (<150)'},
        'ไขมันดี HDL-C': {'line': 40.0, 'name': 'เกณฑ์ HDL เหมาะสม (>40)'}
    }
    
    if y_p in thresholds:
        t_info = thresholds[y_p]
        fig_s.add_hline(y=t_info['line'], line_dash="dash", line_color="#EF4444", annotation_text=t_info['name'], annotation_position="top right")
    if x_p in thresholds:
        t_info = thresholds[x_p]
        fig_s.add_vline(x=t_info['line'], line_dash="dash", line_color="#EF4444", annotation_text=t_info['name'], annotation_position="top left")

    fig_s.update_layout(height=320, margin=dict(t=15, b=0, l=0, r=0), showlegend=False, xaxis_title=x_p, yaxis_title=y_p)
    st.plotly_chart(fig_s, use_container_width=True, key=f"macro_scatter_{package_code}")

    st.markdown(f"""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px 16px; border-radius: 12px; margin-top: 12px; text-align: left;">
            <p style="margin: 0 0 6px 0; font-size: 0.8rem; color: #1E3A8A; font-weight: 700;">
                วิธีการอ่านและตีความแผนภาพการกระจายตัว:
            </p>
            <ul style="margin: 0; padding-left: 18px; font-size: 0.76rem; color: #334151; line-height: 1.5;">
                <li><b>จุดแต่ละจุด (Data Points):</b> แทนบุคลากรแต่ละคนในองค์กร โดยจำแนกสีตามกลุ่มความเสี่ยงสุขภาพ</li>
                <li><b>เส้นประสีแดง (Thresholds):</b> เส้นตัดขวางหรือเส้นตั้งฉากแสดงค่าเกณฑ์มาตรฐานของกระทรวงสาธารณสุข/กรมควบคุมโรค</li>
                <li><b>โซนความเสี่ยงสูง (High-Risk Quadrants):</b> บุคลากรที่จุดพล็อตอยู่เหนือเส้นประ (สำหรับแกน Y) หรืออยู่ทางขวาของเส้นประ (สำหรับแกน X) เป็นกลุ่มที่ค่าตรวจเกินเกณฑ์มาตรฐาน ซึ่งต้องเฝ้าระวังเป็นพิเศษ</li>
                <li><b>การดูความสัมพันธ์:</b> หากจุดพล็อตเกาะกลุ่มกันพุ่งขึ้นทางขวา แสดงว่าตัวแปรทั้งสองมีความสัมพันธ์ในทิศทางเดียวกัน (เช่น BMI เพิ่มขึ้น ความดัน SBP มีแนวโน้มสูงขึ้นตาม)</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 6. บรรทัดที่ 3: การวิเคราะห์มิติเชิงลึก เพศ (Gender vs Risk) และ ช่วงอายุ (Age Group vs Risk)
    # ==========================================
    render_section_title("การวิเคราะห์มิติเชิงลึกระดับองค์กร", "Advanced Risk Breakdown by Demographics")

    adv_c1, adv_c2 = st.columns(2, gap="medium")

    with adv_c1:
        st.markdown("""
            <div style="text-align: left; margin-bottom: 10px;">
                <h4 style="margin:0; font-size: 0.95rem; color: #1F2937; font-weight: 700;">สัดส่วนกลุ่มเสี่ยงแยกตามเพศ (Gender vs Risk)</h4>
                <p style="font-size: 0.78rem; color: #4B5563; margin-top: 2px;">เปรียบเทียบแนวโน้มการป่วยในแต่ละกลุ่มความเสี่ยงระหว่างเพศชายและหญิง</p>
            </div>
        """, unsafe_allow_html=True)
        
        df_gender_risk = df_pkg.groupby(['Gender', 'Cluster']).size().reset_index(name='count')
        fig_gender_risk = px.bar(df_gender_risk, x='Cluster', y='count', color='Gender', barmode='group', color_discrete_map={"Male": "#60A5FA", "Female": "#F472B6"})
        fig_gender_risk.update_layout(height=280, margin=dict(l=20, r=10, t=10, b=40), xaxis=dict(title="", tickangle=-15, tickfont=dict(size=9)), yaxis=dict(title="จำนวน (คน)"), legend=dict(title="เพศ"))
        st.plotly_chart(fig_gender_risk, use_container_width=True, key=f"macro_gender_risk_{package_code}_{selected_year}_{dept_name}")

    with adv_c2:
        st.markdown("""
            <div style="text-align: left; margin-bottom: 10px;">
                <h4 style="margin:0; font-size: 0.95rem; color: #1F2937; font-weight: 700;">การกระจายตัวช่วงอายุตามกลุ่มเสี่ยง (Age Group vs Risk)</h4>
                <p style="font-size: 0.78rem; color: #4B5563; margin-top: 2px;">วิเคราะห์ช่วงอายุใดของบุคลากรที่มีความเสี่ยงในแต่ละกลุ่มหนาแน่นที่สุด</p>
            </div>
        """, unsafe_allow_html=True)
        
        if 'Age' in df_pkg.columns:
            df_pkg['Age_Group'] = pd.cut(df_pkg['Age'], bins=[0, 30, 40, 50, 60, 100], labels=['<30 ปี', '31-40 ปี', '41-50 ปี', '51-60 ปี', '>60 ปี'])
            df_age_risk = df_pkg.groupby(['Age_Group', 'Cluster'], observed=False).size().reset_index(name='count')
            
            fig_age_risk = px.bar(df_age_risk, x='Age_Group', y='count', color='Cluster', barmode='stack', color_discrete_map=all_colors_map)
            fig_age_risk.update_layout(height=280, margin=dict(l=20, r=10, t=10, b=40), xaxis=dict(title="", tickfont=dict(size=10)), yaxis=dict(title="จำนวน (คน)"), legend=dict(title="", orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5, font=dict(size=8)))
            st.plotly_chart(fig_age_risk, use_container_width=True, key=f"macro_age_risk_{package_code}_{selected_year}_{dept_name}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 7. บรรทัดที่ 4: พฤติกรรมเสี่ยง (Behavioral Risk Breakdown) แยกแท่งชัดเจน
    # ==========================================
    c_smoke = next((c for c in df_pkg.columns if any(k in str(c) for k in ['บุหรี่', 'Smoking', 'smoke'])), None)
    c_alcohol = next((c for c in df_pkg.columns if any(k in str(c) for k in ['แอลกอฮอล์', 'สุรา', 'Alcohol', 'alcohol'])), None)
    c_exercise = next((c for c in df_pkg.columns if any(k in str(c) for k in ['ออกกำลังกาย', 'Exercise', 'exercise'])), None)

    if c_smoke:
        df_pkg['Smoking_Mapped'] = df_pkg[c_smoke].astype(str).str.strip()
        smoke_mapping = {
            "ไม่สูบบุหรี่": "ไม่สูบบุหรี่ / ไม่เคยสูบ",
            "ไม่เคยสูบบุหรี่": "ไม่สูบบุหรี่ / ไม่เคยสูบ",
            "สูบบุหรี่": "สูบบุหรี่",
            "เคยสูบบุหรี่": "เคยสูบบุหรี่"
        }
        df_pkg['Smoking_Mapped'] = df_pkg['Smoking_Mapped'].map(smoke_mapping).fillna(df_pkg['Smoking_Mapped'])
    else:
        df_pkg['Smoking_Mapped'] = "ไม่มีข้อมูล"

    if c_alcohol:
        df_pkg['Alcohol_Mapped'] = df_pkg[c_alcohol].astype(str).str.strip()
        alcohol_mapping = {
            "ไม่ดื่มแอลกอฮอล์": "ไม่ดื่มแอลกอฮอล์",
            "ดื่มแอลกอฮอล์": "ดื่มแอลกอฮอล์",
            "เคยดื่มแอลกอฮอล์": "เคยดื่มแอลกอฮอล์"
        }
        df_pkg['Alcohol_Mapped'] = df_pkg['Alcohol_Mapped'].map(alcohol_mapping).fillna(df_pkg['Alcohol_Mapped'])
    else:
        df_pkg['Alcohol_Mapped'] = "ไม่มีข้อมูล"

    if c_exercise:
        df_pkg['Exercise_Mapped'] = df_pkg[c_exercise].astype(str).str.strip()
    else:
        df_pkg['Exercise_Mapped'] = "ไม่มีข้อมูล"

    render_section_title("การวิเคราะห์พฤติกรรมเสี่ยงและสุขภาพ", "Behavioral Risk Factors Breakdown")
    st.markdown("<p style='font-size: 0.8rem; color: #4B5563; margin-top: -10px; margin-bottom: 20px; text-align: left;'>สัดส่วนพฤติกรรมการสูบบุหรี่ การดื่มแอลกอฮอล์ และการออกกำลังกาย จำแนกตามกลุ่มเสี่ยง</p>", unsafe_allow_html=True)
    
    beh_c1, beh_c2, beh_c3 = st.columns(3, gap="medium")
    
    with beh_c1:
        st.markdown("<p style='font-size: 0.85rem; font-weight: bold; color: #374151; text-align: center; margin-bottom: 5px;'>พฤติกรรมการสูบบุหรี่</p>", unsafe_allow_html=True)
        fig_sm = px.histogram(
            df_pkg, x="Smoking_Mapped", color="Cluster", color_discrete_map=all_colors_map, barmode="stack",
            category_orders={"Smoking_Mapped": ["ไม่สูบบุหรี่ / ไม่เคยสูบ", "เคยสูบบุหรี่", "สูบบุหรี่"]}
        )
        fig_sm.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, xaxis_title="", yaxis_title="จำนวน (คน)")
        st.plotly_chart(fig_sm, use_container_width=True, key=f"macro_smoking_{package_code}_{selected_year}_{dept_name}")
        
    with beh_c2:
        st.markdown("<p style='font-size: 0.85rem; font-weight: bold; color: #374151; text-align: center; margin-bottom: 5px;'>พฤติกรรมการดื่มแอลกอฮอล์</p>", unsafe_allow_html=True)
        fig_al = px.histogram(
            df_pkg, x="Alcohol_Mapped", color="Cluster", color_discrete_map=all_colors_map, barmode="stack",
            category_orders={"Alcohol_Mapped": ["ไม่ดื่มแอลกอฮอล์", "เคยดื่มแอลกอฮอล์", "ดื่มแอลกอฮอล์"]}
        )
        fig_al.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, xaxis_title="", yaxis_title="จำนวน (คน)")
        st.plotly_chart(fig_al, use_container_width=True, key=f"macro_alcohol_{package_code}_{selected_year}_{dept_name}")

    with beh_c3:
        st.markdown("<p style='font-size: 0.85rem; font-weight: bold; color: #374151; text-align: center; margin-bottom: 5px;'>พฤติกรรมการออกกำลังกาย</p>", unsafe_allow_html=True)
        fig_ex = px.histogram(
            df_pkg, x="Exercise_Mapped", color="Cluster", color_discrete_map=all_colors_map, barmode="stack"
        )
        fig_ex.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, xaxis_title="", yaxis_title="จำนวน (คน)")
        st.plotly_chart(fig_ex, use_container_width=True, key=f"macro_exercise_{package_code}_{selected_year}_{dept_name}")


    # ==========================================
    # 8. บรรทัดที่ 5: การกระจายตัวระดับหน่วยงาน (Top 5 คณะกลุ่มเสี่ยงสูงสุด)
    # ==========================================
    render_section_title("การกระจายตัวระดับหน่วยงาน", "Department Insights & Critical Risks")
    
    if package_code == 'A':
        target_risk_group = "กลุ่มเสี่ยงโรคอ้วน + ไขมันในเลือดสูง + ความดันโลหิตสูง"
        section_title = f"Top 5 คณะที่มีบุคลากรกลุ่มเสี่ยงสูงสุด: {target_risk_group}"
        badge_color = "#F59E0B"
    else:
        target_risk_group = "กลุ่มโรคเบาหวานและโรคอ้วนรุนแรง (เสี่ยงโรคความดันโลหิตสูง + ไขมันไตรกลีเซอไรด์สูง และไตเสื่อมระยะ2)"
        section_title = f"Top 5 คณะที่มีบุคลากรกลุ่มเสี่ยงสูงสุด: {target_risk_group}"
        badge_color = "#C2410C"

    st.markdown(f"<p style='font-size: 0.95rem; font-weight: 700; color: #1F2937; margin-bottom: 2px;'>{section_title}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 0.78rem; color: #6B7280; margin-top: 0; margin-bottom: 15px;'>วิเคราะห์ความหนาแน่นรายหน่วยงานเฉพาะกลุ่มวิกฤตของ {title}</p>", unsafe_allow_html=True)
    
    df_risk = df_pkg[df_pkg['Cluster'] == target_risk_group]
    top5 = df_risk['คณะ'].value_counts().head(5).reset_index()
    top5.columns = ['คณะ', 'count']
    
    if not top5.empty:
        fig_bar = px.bar(top5, x='count', y='คณะ', orientation='h', color_discrete_sequence=[badge_color])
        fig_bar.update_layout(height=220, margin=dict(l=110, r=10, t=10, b=10), yaxis=dict(tickfont=dict(size=10), autorange="reversed"))
        st.plotly_chart(fig_bar, use_container_width=True, key=f"bar_top5_{package_code}")
        
        top_dept = top5.iloc[0]['คณะ']
        top_count = top5.iloc[0]['count']
        st.markdown(f"""
        <div style="background-color: #FEF3C7; padding: 12px 16px; border-radius: 12px; border: 1px solid #FCD34D; text-align: center; margin-top: 15px; max-width: 750px; margin-left: auto; margin-right: auto;">
            <p style="margin: 0; font-size: 0.78rem; color: #92400E; font-weight: 600;">⚠️ คณะ/หน่วยงานที่มีความหนาแน่นสูงสุดในกลุ่มนี้คือ</p>
            <p style="margin: 3px 0 0 0; font-size: 0.95rem; font-weight: 800; color: #92400E;">{top_dept} (จำนวน {top_count:,} คน)</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info(f"ไม่พบข้อมูลบุคลากรในกลุ่มเสี่ยงดังกล่าวสำหรับ {title}")
    
    

# สิ้นสุดหน้าที่ 1 -------------------------------------------------------------   

# ฟังก์ชันแปลงรูป
def get_image_as_base64(file_path):
    try:
        if not os.path.exists(file_path): return ""
        with open(file_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{data}"
    except: return ""

# โหลดรูป
img1 = get_image_as_base64("logorsu.png")
img2 = get_image_as_base64("logobme.png")

def menu_card_minimal(img_filename, btn_label, page_key, btn_key):
        img_b64 = get_image_as_base64(img_filename) # ตรวจสอบว่าเรียกใช้ฟังก์ชัน get_image_as_base64 ได้
        st.markdown(f"""
            <div style="background-color: white; padding: 30px; border-radius: 20px; 
                        box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: center;
                        width: 200px; margin-bottom: 0px;">
                <img src="{img_b64}" style="width: 70%; border-radius: 80px;">
            </div>
        """, unsafe_allow_html=True)
        st.markdown("""
                <style>
                div.stButton > button {
                    height: 10px !important;    /* ปรับความสูงปุ่มให้เล็กลง */
                    padding-top: 1px !important;
                    padding-bottom: 0px !important;
                    width: 200px;
                    font-size: 14px !important; /* ปรับขนาดตัวอักษร */
                }
                </style>
            """, unsafe_allow_html=True)
        is_active = (getattr(st.session_state, 'pkg_choice', 'Package A') == btn_label)
        
        if st.button(f"{btn_label}", key=btn_key, use_container_width=True, type="primary" if is_active else "secondary"):
            if "Package" in btn_label:
                st.session_state.pkg_choice = btn_label
            else:
                st.session_state.current_page = page_key
            st.rerun()

# 2. CSS ปรับแต่งทั้งหมด
st.markdown("""
    <style>
        /* นำเข้าฟอนต์ Roboto จาก Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap');

    /* เปลี่ยนฟอนต์หลักของหน้าแอป */
    html, body, [class*="st-"] {
        font-family: 'Roboto', sans-serif !important;
    }

    /* กรณีต้องการให้ส่วนหัวข้อหนาเป็นพิเศษ (900) */
    .main-title, h1, h2, h3 {
        font-family: 'Roboto', sans-serif !important;
        font-weight: 1000 !important; 
    }
          
        
        header[data-testid="stHeader"] { display: none !important; }
        .stApp { padding-top: 100px; background: linear-gradient(90deg, #89CFEF 10%, #C1E1C1 50%, #FDDF8E 100%); }
        /* Navbar มนมากๆ (border-radius: 50px) */
        .navbar {
            position: fixed; top: 10px; left: 10px; right: 10px;
            height: 200px;
            background-color: #FFFFFF; 
            z-index: 9999;
            display: flex; align-items: center; padding: 0 40px;
            border-radius: 50px; 
            border: 1px solid #ddd;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }

        .custom-title { color: #2c3e50; font-size: 50px; font-weight: bold; }
        .custom-subtitle { color: #34495e; font-size: 20px; }
        .logo-1 { width: 50px; height: auto; margin-right: 15px; }
        .logo-2 { width: 60px; height: auto; }    
        
        /* กล่องเมนูแบบลอย */
        .menu-container {
            position: fixed; top: 160px; right: 20px; width: 250px;
            background-color: white; padding: 15px;
            border: 2px solid #D9534F; border-radius: 25px; /* ปรับความมนที่นี่ */
            z-index: 9999; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        /* ปุ่มเมนูแบบสี่เหลี่ยมมน */
        .menu-box-button button {
            background-color: #ffffff !important;
            border: 1px solid #ddd !important;
            border-radius: 15px !important; /* ปุ่มมน */
            height: 50px !important; width: 100% !important;
            margin-bottom: 5px !important;
        }
        .nav-text {
            font-size: 15px;      /* ปรับขนาดตัวอักษรให้พอดีสองบรรทัด */
            font-weight: bold;
            color: #FFFFFS;
            margin-left: 50px;    /* เพิ่มระยะห่างจากรูปภาพ */
            line-height: 1.1;     /* ระยะห่างระหว่างบรรทัด */
            text-align: left;
        }
        /* เพิ่ม margin ให้โลโก้เพื่อผลักกันออก */
        .logo-2 {
            width: 60px;
            height: auto;
            margin-right: 7px;   /* เพิ่มระยะห่างระหว่างโลโก้กับข้อความ */
        }
        /* จัดการสไตล์ปุ่มสีเหลือง */
        div.stButton > button[key="final_open_btn"] {
            background: linear-gradient(to bottom, #FFF9C4, #FBC02D) !important; /* ไล่เฉดสีเหลือง */
            color: #333 !important; /* สีตัวอักษร */
            font-weight: bold !important;
            border: 1px solid #FBC02D !important;
            border-radius: 20px !important; /* ปรับมุมให้มน */
            padding: 10px 30px !important;
            font-size: 16px !important;
        }
        /* เอฟเฟกต์ตอนเอาเมาส์ไปชี้ */
        div.stButton > button[key="final_open_btn"]:hover {
            background: #F9A825 !important;
            color: white !important;
        }
        /* ปรับวิดีโอให้ขอบมน */
    video {
        border-radius: 40px !important;
        overflow: hidden !important;
        box-shadow: 0 7px 15px rgba(0,0,0,0.2);
    }
    .navbar { position: fixed; top: 10px; left: 10px; right: 10px; height: 120px; background-color: #FFFFFF; z-index: 9999; display: flex; align-items: center; padding: 0 40px; border-radius: 10px; border: 1px solid #ddd; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        
        div[data-testid="stVideo"] video { border-radius: 30px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }
        .t
    /* สร้าง Class พิเศษสำหรับปุ่มเมนู */
    .custom-menu-button button {
        width: 250px !important;
        height: 60px !important;
        border-radius: 30px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        background-color: white !important;
        border: 2px solid #ddd !important;
        transition: 0.3s !important;
    }
    .custom-menu-button button:hover {
        background-color: #f0f0f0 !important;
        border-color: #FBC02D !important;
        transform: scale(1.05) !important;
    }
            
    /* จัดการให้ Sidebar เป็นสีขาวและมน */
        [data-testid="stSidebar"] {
            background-color: white !important;
            border-top-left-radius: 30px;
            border-bottom-left-radius: 30px;
            box-shadow: -5px 0 15px rgba(0,0,0,0.1);
        }
        /* ปรับปุ่มให้มนและใหญ่ */
        [data-testid="stSidebar"] button {
            width: 100% !important;
            height: 60px !important;
            border-radius: 20px !important;
            font-size: 18px !important;
            font-weight: bold !important;
            margin-bottom: 10px !important;
        
        .drawer-menu {
    position: fixed;
    top: 0;
    right: 0;
    width: 300px;
    height: 100%;
    background-color: white;
    box-shadow: -5px 0 15px rgba(0,0,0,0.2);
    z-index: 10000;
    padding: 100px 20px 20px 20px;
    border-top-left-radius: 30px;
    border-bottom-left-radius: 30px;
}
[data-testid="stSidebar"] { display: block !important; }

    /* 2. เมนูแบบแผ่นลอย (Floating Menu) */
    .floating-menu {
        position: fixed; 
        top: 150px; /* ปรับให้พอดีกับ Navbar */
        right: 20px; 
        width: 250px;
        background: white; 
        padding: 20px; 
        border-radius: 25px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2); 
        z-index: 99999;
    }
    .floating-menu {
    /* ... ค่าเดิม ... */
    height: auto; /* ให้สูงตามเนื้อหาที่เพิ่มเข้าไป */
    max-height: 80vh; /* จำกัดความสูงไม่ให้ล้นจอ */
    overflow-y: auto; /* เพิ่ม Scroll bar ถ้าลิงก์เยอะเกิน */
}

    .db-square-box:hover { transform: scale(1.05); }
    .db-square-box img { width: 80px; height: 80px; margin-bottom: 10px; }
    .link-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        flex-wrap: wrap;
        margin-top: 30px;
    }
    .db-card {
        background: white;
        width: 250px;
        height: 200px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: 0.3s;
        padding: 20px;
    }
    .db-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }
    .db-card img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }
    /* ปรับขอบมนให้รูปภาพและวิดีโอ */
        .rounded-media {
            border-radius: 70px !important;
            overflow: hidden !important;
            width: 100%;
        }

        /* จัดให้เมนูในคอลัมน์ขวาชิดขวา */
    [data-testid="column"] {
        display: flex;
        justify-content: flex-end; /* จัดปุ่มให้ชิดขวา */
    }
    
    /* ปรับขนาดปุ่มเมนูให้เล็กลงและดูเป็นระเบียบ */
    div.stButton > button[key^="nav_"] {
        padding: 5px 10px !important;
        font-size: 14px !important;
        width: auto !important; /* ไม่ให้ปุ่มยืดเต็มจอ */
        border-radius: 15px !important;
        background-color: #f8f9fa !important;
        border: 1px solid #ddd !important;
    }
    /* บังคับให้ div ที่ห่อหุ้มปุ่มของ Streamlit เรียงตัวแบบ flex และชิดขวา */
        div[data-testid="column"] > div > div > div.menu-container-right {
            display: flex !important;
            flex-direction: row !important;
            justify-content: flex-end !important;
            width: 100% !important;
        }

        /* หรือวิธีที่ง่ายที่สุด: ใช้ container ของ Streamlit จัดการแทน */
        .menu-container-right {
            display: flex !important;
            justify-content: flex-end !important;
            width: 100% !important;
        }
        
        /* ปรับให้ปุ่มแต่ละปุ่มไม่ถูกบังคับให้เต็มความกว้าง */
        .menu-container-right div.stButton > button {
            width: auto !important;
            margin-left: 5px !important;
        }
            
        /* จัดการ Container หลักของแต่ละการ์ด */
    div.stColumns > div[data-testid="column"] {
        display: flex;
        flex-direction: column;
        justify-content: center; /* จัดให้เนื้อหาอยู่ตรงกลางในแนวตั้ง */
    }

    /* ปรับแต่ง Container ของรูปภาพ (ฝั่งซ้ายเดิม) */
    .img-card {
        background-color: #f8f9fa !important;
        border-radius: 25px !important;
        padding: 20px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        height: 350px !important; /* กำหนดความสูงให้คงที่ */
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 20px !important;
    }
    
    .img-card img {
        max-height: 90% !important;
        object-fit: contain;
    }

    /* ปรับแต่ง Container ของปุ่ม (ฝั่งขวาเดิม) ให้มีขนาดเท่ารูป */
    .btn-card {
        background-color: #d9534f !important; /* สีแดงเข้มตามรูป */
        border-radius: 25px !important;
        padding: 30px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        height: 350px !important; /* กำหนดความสูงให้เท่ากับการ์ดรูป */
        display: flex;
        flex-direction: column;
        justify-content: space-between; /* กระจายปุ่มให้เต็มความสูง */
        margin-bottom: 20px !important;
    }

    /* ปรับแต่งสไตล์ปุ่มให้เป็นปุ่มกดขนาดใหญ่และกว้างสูงเท่ากัน */
    div.stButton > button.big-btn {
        background-color: rgba(255, 255, 255, 0.15) !important; /* พื้นหลังปุ่มโปร่งใส */
        color: white !important;
        border: none !important;
        border-radius: 20px !important;
        padding: 20px !important;
        font-size: 24px !important;
        font-weight: bold !important;
        width: 100% !important;
        height: 140px !important; /* กำหนดความสูงปุ่มให้เท่ากัน */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        transition: 0.3s !important;
        box-shadow: none !important;
    }
/* 1. กล่องสีขาวหลัก */
    .white-box {
        background-color: white !important;
        border-radius: 30px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
        padding: 20px !important;
        margin: 20px auto !important;
        display: flex !important;
        align-items: center !important;
        gap: 20px !important;
        width: 80% !important;
    }

    /* 2. กรอบรูปภาพที่จำกัดขนาดไว้ */
    .image-frame {
        width: 150px !important;
        height: 150px !important;
        flex-shrink: 0;        /* ห้ามยืดหรือหด */
        overflow: hidden;      /* ตัดส่วนที่เกิน */
        border-radius: 20px;   /* มุมมน */
    }

    /* 3. รูปภาพภายในกรอบ */
    .bounded-image {
        width: 100% !important;
        height: 100% !important;
        object-fit: cover;     /* บังคับให้พอดีกรอบและไม่เบี้ยว */
    }
    div.stButton > button {
    background: linear-gradient(135deg, #FFF9C4 0%, #FBC02D 100%) !important;
    border-radius: 30px !important; /* ปรับความมนของปุ่ม */
    padding: 20px 40px !important;  /* ปรับขนาดปุ่ม (ความกว้าง/สูง) */
    font-size: 20px !important;     /* ปรับขนาดตัวอักษร */
}
 /* ปรับ Sidebar ให้เป็นกรอบสีขาวแยกออกมา */
[data-testid="stSidebar"] {
    background-color: #ffffff !important;
    border-radius: 25px !important;
    margin: 20px 20px 20px 0px !important; /* เว้นขอบให้ดูเป็นกรอบ */
    padding: 20px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
    width: 250px !important; /* ความกว้างไม่กว้างเกินไป */
} 

/* สไตล์ปุ่มปกติ */
div.stButton > button {
    border-radius: 15px !important;
}

/* สไตล์ปุ่มที่ถูกเลือก (สีเขียว) */
div.stButton > button.active-btn {
    background-color: #27ae60 !important;
    color: white !important;
    border: 2px solid #2ecc71 !important;
}

    .filter-box {
        background-color: white !important;
        padding: 20px !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05) !important;
        margin-bottom: 20px !important;
    }
    .filter-box {
        /* เปลี่ยนสีพื้นหลังตรงนี้ (ใช้สีอ่อนๆ เพื่อให้อ่านง่าย) */
        background-color: #E8F4F8 !important; 
        
        /* ใส่เส้นขอบสีฟ้าเข้มขึ้นเล็กน้อยเพื่อให้ดูเป็นระเบียบ */
        border: 1px solid #BDE0E8 !important;
        
        padding: 20px !important;
        border-radius: 20px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05) !important;
        margin-bottom: 20px !important;
    }

    /* ปรับให้ Label ของ Selectbox มีสีที่ชัดขึ้น */
    div[data-testid="stSelectbox"] label {
        color: #1b305b !important;
        font-weight: bold !important;
    }
div[data-testid="stSelectbox"] > div > div {
    background-color: #FFFFFF !important; /* ให้ตัวช่องกรอกเป็นสีขาวโดดออกมาจากกล่องฟิลเตอร์ */
    border-radius: 10px !important;
}
 /* สไตล์กล่อง KPI แบบในรูป */
[data-testid="stMetric"] {
    background-color: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    text-align: center;
}

            /* สไตล์กล่อง KPI แบบ Dashboard สวยงาม */
.kpi-container {
    display: flex;
    gap: 15px;
    margin-bottom: 20px;
}
.kpi-box {
    flex: 1;
    padding: 20px;
    border-radius: 20px;
    color: white;
    text-align: center;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.kpi-label { font-size: 0.85rem; font-weight: 600; opacity: 0.9; }
.kpi-number { font-size: 1.8rem; font-weight: 800; margin-top: 5px; }  

/* 1. เปลี่ยนสีพื้นหลังของกล่อง Selectbox ให้เป็นสีขาว */
div[data-testid="stSelectbox"] div[data-baseweb="select"] {
    background-color: #FFFFFF !important;
    border-radius: 10px !important;
    border: 1px solid #D1D5DB !important;
}

/* 2. เปลี่ยนสีตัวอักษรในกล่อง */
div[data-testid="stSelectbox"] div[data-baseweb="select"] span {
    color: #1b305b !important;
    font-weight: 600 !important;
}

/* 3. ปรับพื้นหลังของกล่อง Filter-box */
.filter-box {
    background-color: #F8F9FA !important; /* เปลี่ยนรหัสสีนี้เป็นสีที่คุณต้องการ */
    padding: 20px !important;
    border-radius: 20px !important;
    border: 1px solid #E5E7EB !important;
    margin-bottom: 20px !important;
}                    
    </style>
""", unsafe_allow_html=True)
# --- วางโค้ด Navbar ไว้ที่นี่ (หน้าไหนก็เห็นเหมือนกันหมด) ---
st.markdown(f'''
    <div class="navbar">
        <img src="{img1}" style="width:50px; margin-right:15px;">
        <img src="{img2}" style="width:60px; margin-right:7px;">
        <div style="font-size:15px; font-weight:bold;">คณะวิศวกรรมชีวการแพทย์<br>มหาวิทยาลัยรังสิต</div>
    </div>
''', unsafe_allow_html=True)

# รายชื่อหน้าที่เรา "ไม่อยาก" ให้โชว์เมนู
pages_without_menu = ["OverviewPage", "DeptPage"]

# ตรวจสอบว่าหน้าปัจจุบันอยู่ในรายการที่ต้องซ่อนหรือไม่
if st.session_state.current_page not in pages_without_menu:

    st.markdown('<div class="menu-container-right">', unsafe_allow_html=True)
    st.markdown("")
    st.markdown("")
    st.markdown("")
    st.markdown("")
    col_spacer, col_menu1, col_menu2, col_menu3, col_menu4 = st.columns([0.5, 0.3, 0.1, 0.1, 0.1])

    menu_items = [
        ("หน้าแรก", "🏠 หน้าแรก"), 
        ("Dashboard", "Dashboard"), 
        ("คลังความรู้", "คลังความรู้"), 
        ("คู่มือใช้งาน", "คู่มือ")
    ]

    for i, (label, page) in enumerate(menu_items):
        with locals()[f"col_menu{i+1}"]:
            if st.button(label, key=f"nav_main_{page}"):
                st.session_state.current_page = page
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    # --- จบโค้ด Navbar ---

if st.session_state.current_page == "🏠 หน้าแรก":
    
    # --- CSS สำหรับตกแต่งหน้าแรก รวมถึงปุ่มเมนูด้านบนให้เป็นกรอบขาวมน ---
    st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
        }
        
        .hero-title-box {
            margin-bottom: 20px;
        }
        .hero-main-title {
            background: linear-gradient(135deg, #1A365D 0%, #2B6CB0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 52px;
            font-weight: 1000;
            letter-spacing: -1px;
            line-height: 1.15;
            margin-bottom: 12px;
        }
        .hero-desc-badge {
            background: linear-gradient(135deg, rgba(43, 108, 176, 0.05) 0%, rgba(43, 108, 176, 0.1) 100%);
            border-left: 5px solid #2B6CB0;
            padding: 14px 18px;
            border-radius: 0 14px 14px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.03);
            margin-bottom: 20px;
        }
        .hero-desc-text {
            color: #2D3748;
            font-size: 15px;
            font-weight: 500;
            line-height: 1.6;
            margin: 0;
        }

        /* 🌟 1. ปุ่มเมนูด้านบน (หน้าแรก, Dashboard, คลังความรู้, คู่มือใช้งาน) ให้เป็นกรอบขาวทรงมน */
        div[data-testid="stHorizontalBlock"] > div div.stButton > button {
            background: #ffffff !important;
            color: #1A365D !important;
            border-radius: 50px !important;
            font-weight: 700 !important;
            border: 1px solid rgba(226, 232, 240, 0.9) !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stHorizontalBlock"] > div div.stButton > button:hover {
            background: #f7fafc !important;
            border-color: #2B6CB0 !important;
            box-shadow: 0 6px 20px rgba(43, 108, 176, 0.15) !important;
            transform: translateY(-2px);
        }

        /* 2. ปุ่มหลักเปิด NCD Dashboard (โทนสีส้มทองพรีเมียม) */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #F6AD55 0%, #ED8936 50%, #DD6B20 100%) !important;
            color: #ffffff !important;
            border-radius: 16px !important;
            font-weight: 800 !important;
            font-size: 17px !important;
            border: none !important;
            padding: 14px 28px !important;
            box-shadow: 0 10px 25px rgba(237, 137, 54, 0.45) !important;
            transition: all 0.3s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #ED8936 0%, #DD6B20 100%) !important;
            box-shadow: 0 15px 30px rgba(221, 107, 32, 0.6) !important;
            transform: translateY(-3px) scale(1.02) !important;
        }

        /* 3. ปุ่มเฉพาะสำหรับวิดีโอ (ทรงแคปซูลสีฟ้า) */
        div[data-testid="stButton"] button[key="btn_video_action"],
        div[data-testid="stButton"] button[key="btn_video_close"] {
            background: linear-gradient(135deg, #2B6CB0 0%, #1A365D 100%) !important;
            color: #ffffff !important;
            border-radius: 50px !important;
            font-weight: 700 !important;
            font-size: 14.5px !important;
            border: none !important;
            padding: 10px 20px !important;
            box-shadow: 0 6px 20px rgba(43, 108, 176, 0.3) !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stButton"] button[key="btn_video_action"]:hover,
        div[data-testid="stButton"] button[key="btn_video_close"]:hover {
            background: linear-gradient(135deg, #3182CE 0%, #2B6CB0 100%) !important;
            box-shadow: 0 8px 25px rgba(49, 130, 206, 0.45) !important;
            transform: translateY(-2px) scale(1.02) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # ใช้สัดส่วน 1:1 พร้อม gap="large"
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        # --- หัวข้อหลัก: NCD Dashboard ---
        st.markdown("""
        <div class="hero-title-box">
            <h1 class="hero-main-title">NCD Dashboard</h1>
            <div class="hero-desc-badge">
                <p class="hero-desc-text">
                    <b>NCD Dashboard:</b> <br>
                    <b style="color: #1A365D;">มุ่งเน้น:</b> โรคเบาหวาน, ความดันโลหิตสูง และภาวะไขมันในเลือดสูง เพื่อการดูแลเชิงป้องกันที่มีประสิทธิภาพ
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 🎯 จัดรูปภาพให้อยู่ตรงกลาง และกำหนดขนาดให้พอดี (เช่น width=380 หรือ 400)
        if os.path.exists("b25.png"): 
            img_l, img_c, img_r = st.columns([0.5, 4, 0.5])
            with img_c:
                st.image("b25.png", width=550)
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            
        # 🎯 จัดปุ่มให้แคบลงและอยู่กึ่งกลาง (ไม่ให้กว้างเต็มหน้าจอ)
        b_left, b_mid, b_right = st.columns([1, 2.5, 1])
        with b_mid:
            if st.button("เปิดใช้งาน NCD Dashboard", key="btn_dash_home", type="primary", use_container_width=True):
                st.session_state.current_page = "Dashboard"
                st.rerun()

    with col2:
        st.markdown("")
        st.markdown("")
        
        # ปรับระยะห่างด้านบนให้สมดุลกับฝั่งซ้ายพอดี (ลดจำนวน st.markdown ที่ไม่จำเป็นออก)
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        
        if not st.session_state.video_clicked:
            if os.path.exists("s1.png"):
                st.image("s1.png", use_container_width=True)
                
            # เพิ่มหัวข้อข้อความประกอบการใช้งานให้อยู่เหนือปุ่มอย่างสวยงาม
            st.markdown("""
                <div style='text-align: center; margin: 14px 0 10px 0;'>
                    <span style='color: #1A365D; font-size: 15px; font-weight: 700; letter-spacing: 0.3px;'>
                        รับชมวิดีโอสาธิตการใช้งานระบบ
                    </span>
                    <div style='color: #718096; font-size: 13px; font-weight: 400; margin-top: 2px;'>
                        เรียนรู้ขั้นตอนการวิเคราะห์ข้อมูลและฟีเจอร์ต่างๆ อย่างละเอียด
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # ปุ่มเปิดดูวิดีโอ (จัดกึ่งกลางและปรับสัดส่วนความกว้างให้สวยงามพอดี ไม่ยาวจนเกินไป)
            b_left, b_mid, b_right = st.columns([0.8, 2.5, 0.8])
            with b_mid:
                if st.button("▶  คลิกเพื่อรับชมวิดีโอ", key="btn_video_action", use_container_width=True):
                    st.session_state.video_clicked = True
                    st.rerun()
        else:
            
            
            # 🌟 แสดงผลวิดีโอจากลิงก์ Google Drive ของคุณ (แปลงเป็น /preview แล้ว)
            drive_video_url = "https://drive.google.com/file/d/1rHEsZIQu7u-SD0wgHoB4j-Hm5Vecwomu/view?usp=sharing&t=28.02"
            st.components.v1.iframe(drive_video_url, width=None, height=350, scrolling=False)
            
            # 🌟 ลิงก์สำหรับกดเปิดดูวิดีโอเต็มจอใน Google Drive แยกต่างหาก
            st.markdown("""
                <div style='text-align: center; margin: 10px 0 15px 0;'>
                    <a href="https://drive.google.com/file/d/1rHEsZIQu7u-SD0wgHoB4j-Hm5Vecwomu/view?usp=sharing&t=28.02" target="_blank" style='color: #2B6CB0; font-size: 14px; font-weight: 700; text-decoration: none;'>
                        🔗 คลิกที่นี่เพื่อเปิดดูวิดีโอเต็มจอใน Google Drive
                    </a>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            
            b_left, b_mid, b_right = st.columns([1, 2, 1])
            with b_mid:
                if st.button("✕  ปิดวิดีโอ", key="btn_video_close", use_container_width=True):
                    st.session_state.video_clicked = False
                    st.rerun()

    if st.session_state.menu_open:
        st.markdown('<div class="floating-menu">', unsafe_allow_html=True)
        st.subheader("เมนูหลัก")
        menu_items = [("🏠 หน้าแรก", "🏠 หน้าแรก"), ("📊 Dashboard", "Dashboard"), ("📚 คลังความรู้", "คลังความรู้"), ("📖 คู่มือการใช้งาน", "คู่มือ")]
        for label, page in menu_items:
            if st.button(label, key=f"btn_m_{page}"):
                st.session_state.current_page = page
                st.session_state.menu_open = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <style>
        .link-container { 
            display: flex; 
            justify-content: space-between; 
            gap: 3px; 
            flex-wrap: wrap; 
            padding: 0 20px;            
            margin-top: 30px; 
        }
        .db-card {
            background: white; 
            width: 350px;               
            height: 200px;              
            border-radius: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.06); 
            display: flex;
            align-items: center; 
            justify-content: center; 
            transition: all 0.3s ease; 
            padding: 15px;
        }
        .db-card:hover { transform: translateY(-5px); box-shadow: 0 10px 25px rgba(43, 108, 176, 0.15); }
        .db-card img { 
            max-width: 90%; 
            max-height: 90%; 
            object-fit: contain; 
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.divider() 
    
    # --- ฐานข้อมูลที่เกี่ยวข้อง ---
    st.markdown("<h2 style='text-align: center; color: #1b305b; font-size: 36px; font-weight: 900; margin-top: 30px;'>ฐานข้อมูลที่เกี่ยวข้อง</h2>", unsafe_allow_html=True)
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    data = [
        ("https://www.moph.go.th/", "c1.jpg"),
        ("https://ddc.moph.go.th/index.php", "c2.jpg"),
        ("https://itepincd.ddc.moph.go.th/", "c3.jpg"),
        ("https://www.dmthai.org/new/", "c5.jpg")
    ]

    html_links = '<div class="link-container">'
    for url, img_file in data:
        img_b64 = get_image_as_base64(img_file)
        if img_b64:
            html_links += f'<a href="{url}" target="_blank"><div class="db-card"><img src="{img_b64}"></div></a>'
    html_links += '</div>'
    st.markdown(html_links, unsafe_allow_html=True)
    
    # --- Footer ส่วนท้าย ---
    st.markdown("""
        <style>
            .footer-container {
                background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
                color: #ddd;
                padding: 40px;
                margin-top: 50px;
                border-radius: 24px;
                display: flex;
                justify-content: space-between;
                align-items: flex-end;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }
            .footer-left { flex: 2; }
            .footer-right { flex: 1; text-align: right; font-size: 0.9em; color: #a0aec0; }
            .footer-title { color: white; font-size: 20px; font-weight: bold; margin-bottom: 10px; }
            .footer-link { color: #63b3ed; text-decoration: none; }
            .footer-link:hover { text-decoration: underline; }
        </style>
        
        <div class="footer-container">
            <div class="footer-left">
                <div class="footer-title">มหาวิทยาลัยรังสิต Rangsit University</div>
                <div style="font-size: 13.5px; line-height: 1.7; color: #cbd5e1; margin-bottom: 5px;">ตึก 1 อาคารอาทิตย์อุไรรัตน์ ชั้น 10 มหาวิทยาลัยรังสิต 52/347 หมู่บ้านเมืองเอก ถนนพหลโยธิน ต.หลักหก อ.เมือง ปทุมธานี 12000</div>
                <div style="font-size: 13.5px; line-height: 1.7; color: #cbd5e1; margin-bottom: 5px;">โทรศัพท์ : 02-791-5926 ถึง 02-791-5929 | โทรสาร : 0-2791-5926</div>
                <div style="font-size: 13.5px; line-height: 1.7; color: #cbd5e1;">เว็บไซต์: <a href="https://otp.rsu.ac.th" class="footer-link">https://otp.rsu.ac.th</a></div>
            </div>
            <div class="footer-right">
                <div>© 2026 สำนักงานอธิการบดี มหาวิทยาลัยรังสิต · All Rights Reserved.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)



# ---------------------------------------------------------------------------------------------

elif st.session_state.current_page == "Dashboard":
    
    # --- CSS สำหรับปรับแต่งสีปุ่มเมนูบน, ปุ่ม Card น้ำเงิน, และปุ่มบันทึก/ยกเลิก (เขียว/แดง) ---
    st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
        }

        .top-text {
            text-align: center;
            font-size: 15px;
            color: #4A5568;
            margin-bottom: 5px;
            font-weight: 500;
        }
        .main-title {
            text-align: center;
            font-size: 36px;
            font-weight: 1000;
            color: #1A365D;
            margin-bottom: 15px;
            letter-spacing: -1px;
        }
        .custom-button {
            display: block;
            margin: 0 auto;
            background: linear-gradient(135deg, #2B6CB0 0%, #1A365D 100%);
            color: white;
            padding: 10px 24px;
            border-radius: 50px;
            text-align: center;
            width: fit-content;
            font-weight: 700;
            font-size: 14px;
            box-shadow: 0 4px 15px rgba(43, 108, 176, 0.25);
        }

        /* 1. ปุ่มเมนูด้านบน (หน้าแรก, Dashboard, คลังความรู้, คู่มือใช้งาน) ให้เป็นสีขาว */
        div[data-testid="stHorizontalBlock"] > div div.stButton > button {
            background: #ffffff !important;
            color: #1A365D !important;
            border-radius: 50px !important;
            font-weight: 700 !important;
            border: 1px solid #cbd5e0 !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stHorizontalBlock"] > div div.stButton > button:hover {
            background: #f7fafc !important;
            border-color: #2B6CB0 !important;
            transform: translateY(-2px);
        }

        /* 2. ปุ่มกดไปหน้าภาพรวมและรายหน่วยงาน (ให้เป็นสีน้ำเงินสีเดิม) */
        div[data-testid="stColumn"] div.stButton > button[key="btn_overview"],
        div[data-testid="stColumn"] div.stButton > button[key="btn_dept"] {
            background: linear-gradient(135deg, #2B6CB0 0%, #1A365D 100%) !important;
            color: #ffffff !important;
            border-radius: 50px !important;
            font-weight: 700 !important;
            border: none !important;
            box-shadow: 0 6px 20px rgba(43, 108, 176, 0.3) !important;
        }
        div[data-testid="stColumn"] div.stButton > button[key="btn_overview"]:hover,
        div[data-testid="stColumn"] div.stButton > button[key="btn_dept"]:hover {
            background: linear-gradient(135deg, #3182CE 0%, #2B6CB0 100%) !important;
            transform: translateY(-2px) scale(1.02) !important;
        }

        /* 3. ปุ่มบันทึกข้อมูล (สีเขียว) */
        div.stButton > button[key="btn_save_data"] {
            background: linear-gradient(135deg, #48BB78 0%, #38A169 100%) !important;
            color: #ffffff !important;
            border-radius: 50px !important;
            font-weight: 700 !important;
            border: none !important;
            box-shadow: 0 6px 20px rgba(56, 161, 105, 0.35) !important;
            transition: all 0.3s ease !important;
        }
        div.stButton > button[key="btn_save_data"]:hover {
            background: linear-gradient(135deg, #38A169 0%, #2F855A 100%) !important;
            transform: translateY(-2px) scale(1.01) !important;
        }

        /* 4. ปุ่มยกเลิก (สีแดง) */
        div.stButton > button[key="btn_cancel_data"] {
            background: linear-gradient(135deg, #F56565 0%, #E53E3E 100%) !important;
            color: #ffffff !important;
            border-radius: 50px !important;
            font-weight: 700 !important;
            border: none !important;
            box-shadow: 0 6px 20px rgba(229, 62, 62, 0.35) !important;
            transition: all 0.3s ease !important;
        }
        div.stButton > button[key="btn_cancel_data"]:hover {
            background: linear-gradient(135deg, #E53E3E 0%, #C53030 100%) !important;
            transform: translateY(-2px) scale(1.01) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 1. ส่วนหัวข้อ (Dashboard Header)
    with st.container():
        st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <p style='color: #4A5568; font-size: 15px; font-weight: 500; margin-bottom: 5px; letter-spacing: 0.5px;'>
                    โรคเบาหวาน  |  โรคความดันโลหิตสูง  |  ภาวะไขมันในเลือดสูง
                </p>
                <h1 style='color: #1A365D; font-weight: 1000; font-size: 42px; margin-top: 0; letter-spacing: -1px;'>
                    แดชบอร์ดโรคไม่ติดต่อเรื้อรัง
                </h1>
                <div style="display: inline-block; background: linear-gradient(135deg, rgba(43, 108, 176, 0.08) 0%, rgba(43, 108, 176, 0.15) 100%); color: #1A365D; padding: 8px 20px; border-radius: 50px; font-weight: 700; font-size: 13.5px; margin-top: 8px; border: 1px solid rgba(43, 108, 176, 0.1);">
                    แดชบอร์ดโรคไม่ติดต่อเรื้อรังของบุคลากรมหาวิทยาลัยรังสิต
                </div>
            </div>
        """, unsafe_allow_html=True)

    # 2. ฟังก์ชันสร้าง Card ดีไซน์แนวนอน
    def create_horizontal_card(title_text, description_text, image_path, target_page, btn_key):
        img_b64 = f"data:image/png;base64,{base64.b64encode(open(image_path, 'rb').read()).decode()}" if os.path.exists(image_path) else ''
        
        st.markdown(f'''
            <div style="
                background: #ffffff; 
                border-radius: 20px; 
                padding: 25px; 
                box-shadow: 0 8px 25px rgba(0,0,0,0.05); 
                border: 1px solid rgba(226, 232, 240, 0.8);
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 20px;
            ">
                <div style="flex-shrink: 0; background: #f7fafc; padding: 12px; border-radius: 16px; border: 1px solid #edf2f7;">
                    <img src="{img_b64}" style="width: 110px; height: 90px; object-fit: contain; border-radius: 10px;">
                </div>
                <div style="flex-grow: 1; text-align: left;">
                    <span style="background-color: #2b6cb0; color: white; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;">ACTIVE WORKSPACE</span>
                    <h2 style="color: #1A365D; font-size: 20px; font-weight: 800; margin: 6px 0 6px 0;">{title_text}</h2>
                    <p style="margin: 0 0 15px 0; color: #4a5568; font-size: 13.5px; line-height: 1.5;">{description_text}</p>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        b_l, b_c, b_r = st.columns([1, 3, 1])
        with b_c:
            if st.button(f"ไปที่หน้า {title_text}", key=btn_key, use_container_width=True):
                st.session_state.current_page = target_page
                st.rerun()

    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        create_horizontal_card(
            "ภาพรวม", 
            "ชุดตรวจสุขภาพเชิงลึกสำหรับบุคลากร<br>รายละเอียดข้อมูลภาพรวมที่คุณต้องการแสดงผลเชิงวิเคราะห์", 
            "overview.png", 
            "OverviewPage", 
            "btn_overview"
        )
        
    with col2:
        create_horizontal_card(
            "รายหน่วยงาน", 
            "ชุดตรวจสุขภาพเชิงลึกสำหรับบุคลากร<br>รายละเอียดข้อมูลแยกตามรายหน่วยงานเพื่อการบริหารจัดการ", 
            "dept.png", 
            "DeptPage", 
            "btn_dept"
        )

    # 3. ส่วนจัดการและอัปโหลดไฟล์
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div class="top-text">อัปโหลดไฟล์ | จัดการข้อมูล | ตรวจสอบความถูกต้อง</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-title">ระบบจัดการไฟล์ผลตรวจสุขภาพ</div>', unsafe_allow_html=True)
    st.markdown('<div class="custom-button">อัปโหลดไฟล์ผลตรวจสุขภาพประจำปีของบุคลากร</div>', unsafe_allow_html=True)
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("""
            <div style="background-color: #f8f9fa; padding: 25px; border-radius: 20px; border: 2px dashed #cbd5e0; text-align: center;">
                <p style="font-size: 45px; margin-bottom: 10px;">📄</p>
                <p style="font-weight: 700; color: #2D3748; margin-bottom: 5px;">คลิกหรือลากไฟล์ผลตรวจสุขภาพมาวางที่นี่</p>
                <p style="font-size: 13px; color: #718096;">รองรับไฟล์ CSV, PDF, JPG, PNG</p>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("", type=["csv", "pdf", "jpg", "png"], label_visibility="collapsed")

    c1, c2, c3 = st.columns([3, 2, 3])
    with c2:
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        st.markdown("""
            <p style='text-align: center; 
                    background: linear-gradient(135deg, #2B6CB0 0%, #1A365D 100%); 
                    color: #FFFFFF; 
                    padding: 8px 20px; 
                    border-radius: 20px; 
                    font-size: 16px;
                    font-weight: 700;
                    box-shadow: 0 4px 12px rgba(43, 108, 176, 0.2);
                    '>
                ระบุปีของข้อมูล
            </p>
        """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([3, 2, 3])
    with c2:
        target_year = st.number_input("", min_value=2500, max_value=3000, value=2569, step=1)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    b1, b2 = st.columns(2)
    with b1:
        save_btn = st.button("บันทึกข้อมูล", use_container_width=True, key="btn_save_data")
    with b2:
        cancel_btn = st.button("ยกเลิก", use_container_width=True, key="btn_cancel_data")

    if save_btn:
        if uploaded_file:
            with st.spinner("กำลังวิเคราะห์ข้อมูล..."):
                try:
                    new_data = pd.read_csv(uploaded_file)
                    new_data['Year'] = target_year
                    result_df = predict_health_clusters(new_data)
                    st.success("ประมวลผลสำเร็จ!")
                    st.dataframe(result_df.head())
                    result_df.to_csv("master_health_data.csv", index=False)
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการประมวลผลไฟล์ CSV: {e}")
        else:
            st.error("กรุณาอัปโหลดไฟล์ก่อนครับ!")

    if cancel_btn:
        st.info("ยกเลิกการดำเนินการแล้ว")


# ---------------------------------------------------------------------------------------------
elif st.session_state.current_page == "OverviewPage":
    
    # 🌟 คำสั่ง JavaScript เลื่อนหน้าจอขึ้นไปด้านบนสุดทันทีเมื่อเปลี่ยนหน้า
    st.components.v1.html("<script>window.parent.scrollTo({top: 0, behavior: 'instant'});</script>", height=0)
    st.markdown("""<style>.stApp { background: #F8F9FA !important; }</style>""", unsafe_allow_html=True)
    
    col_menu, col_content = st.columns([1, 4])
    st.markdown("""
    <style>
        /* บังคับให้คอลัมน์เมนูด้านซ้าย (คอลัมน์แรก) ลอยติดหน้าจอเวลาเลื่อนลง */
        div[data-testid="column"]:nth-of-type(1) {
            position: sticky;
            top: 20px;
            z-index: 999;
            height: fit-content;
        }
    </style>
""", unsafe_allow_html=True)
    with col_menu:
        st.markdown("<br><br>", unsafe_allow_html=True)
        menu_card_minimal("A1.png", "Package A", "DeptPage", "btn_pkg_a")
        menu_card_minimal("A2.png", "Package B", "DeptPage", "btn_pkg_b")
        menu_card_minimal("A3.png", "กลับหน้าหลัก", "Dashboard", "btn_home")

    with col_content:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 🌟 ตรวจสอบสเตท Package ปัจจุบัน
        current_pkg_code = 'A' if st.session_state.get('pkg_choice', 'Package A') == 'Package A' else 'B'
        
        banner_img = "b24.png" if current_pkg_code == 'A' else "bb24.png"
        img_b64 = get_image_as_base64(banner_img)
        
        if current_pkg_code == 'A':
            pkg_title = "Dashboard Overview - Package A"
            pkg_desc = "ชุดตรวจสุขภาพเชิงลึกสำหรับบุคลากร<br><b>กลุ่มอายุไม่เกิน 34 ปี</b> (วัยเริ่มต้นทำงาน)"
            accent_color = "#1E429F"
        else:
            pkg_title = "Dashboard Overview - Package B"
            pkg_desc = "ชุดตรวจสุขภาพเชิงลึกสำหรับบุคลากร<br><b>กลุ่มอายุ 35 ปีขึ้นไป</b> (วัยทำงานและผู้บริหาร)"
            accent_color = "#9D174D"

        current_date_str = time.strftime("%d %b %Y", time.gmtime())

        # 1. หัวข้อด้านบนสุด (Dashboard + วันที่)
        st.markdown(f'''
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 15px;">
                <div>
                    <h1 style="color: #111827; font-weight: 800; font-size: 1rem; margin: 0; font-family: -apple-system, BlinkMacSystemFont;">Dashboard Overview</h1>
                    <span style="color: #6B7280; font-size: 0.85rem; font-weight: 500;">{current_date_str}</span>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E5E7EB; padding: 6px 14px; border-radius: 12px; font-size: 0.82rem; font-weight: 600; color: #374151; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                    📅 Active Period: {current_date_str}
                </div>
            </div>
        ''', unsafe_allow_html=True)

        # 2. การ์ดแบนเนอร์หลัก (เอาบล็อกสถานะออกแล้ว จัดรูปและข้อความเต็มตาสวยงาม)
        
        
        sub_c1, sub_c2 = st.columns([1, 4])
        with sub_c1:
            if img_b64:
                st.markdown(f'''
                    <div style="width: 130px; height: 85px; background: #F8F9FA; border-radius: 12px; padding: 4px; display: flex; align-items: center; justify-content: center; border: 1px solid #E5E7EB;">
                        <img src="{img_b64}" style="max-width: 100%; max-height: 100%; object-fit: contain; border-radius: 8px;">
                    </div>
                ''', unsafe_allow_html=True)
        with sub_c2:
            st.markdown(f'''
                <div>
                    <span style="background-color: {accent_color}; color: #FFFFFF; padding: 2px 10px; border-radius: 20px; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Active Workspace</span>
                    <h2 style="color: #111827; font-weight: 800; font-size: 1.35rem; margin: 5px 0 3px 0;">{pkg_title}</h2>
                    <p style="color: #4B5563; font-size: 0.85rem; margin: 0; line-height: 1.4;">{pkg_desc}</p>
                </div>
            ''', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

        # 3. แผงตัวกรอง (Filter Box)
        st.markdown('<div class="filter-box">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        year = c1.selectbox("Academic Year", available_years, key='f_year')
        age = c2.selectbox("Age Range", ["ทั้งหมด", "น้อยกว่า 30", "31-40", "41-50", "51-60", "60 ขึ้นไป"], key='f_age')
        gender = c3.selectbox("Gender", ["ทั้งหมด", "Female", "Male"], key='f_gender')
        st.markdown('</div>', unsafe_allow_html=True)

        # 4. กระบวนการกรองข้อมูล
        df_home = df_master.copy()
        if year != "ทั้งหมด": df_home = df_home[df_home['Year'] == int(year)]
        if gender != "ทั้งหมด": df_home = df_home[df_home['Gender'] == gender]
        
        if age != "ทั้งหมด":
            df_home['Age'] = pd.to_numeric(df_home['Age'], errors='coerce')
            if age == "น้อยกว่า 30": df_home = df_home[df_home['Age'] < 30]
            elif age == "31-40": df_home = df_home[(df_home['Age'] >= 31) & (df_home['Age'] <= 40)]
            elif age == "41-50": df_home = df_home[(df_home['Age'] >= 41) & (df_home['Age'] <= 50)]
            elif age == "51-60": df_home = df_home[(df_home['Age'] >= 51) & (df_home['Age'] <= 60)]
            elif age == "60 ขึ้นไป": df_home = df_home[df_home['Age'] >= 60]

        # 5. แสดงผลแดชบอร์ดภาพรวม
        if not df_home.empty:
    
            render_package_dashboard(
                df_home, 
                current_pkg_code, 
                package_vars[current_pkg_code],
                package_clusters[current_pkg_code],
                color_map_A if current_pkg_code == 'A' else color_map_B,
                year,
                "ภาพรวม"
            )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("⚠️ ไม่พบข้อมูลตามเงื่อนไขตัวกรองที่คุณเลือก")
  
# -----------------------------------------------------------------------
elif st.session_state.current_page == "DeptPage":
    # 🌟 คำสั่ง JavaScript เลื่อนหน้าจอขึ้นไปด้านบนสุดทันทีเมื่อเปลี่ยนหน้า
    st.components.v1.html("<script>window.parent.scrollTo({top: 0, behavior: 'instant'});</script>", height=0)
    st.markdown("""<style>.stApp { background: #FFFFFF !important; }</style>""", unsafe_allow_html=True)
  
    st.markdown("""
        <style>
        .stApp { background-color: #F8F9FA !important; }
        
        .filter-card-minimal {
            background-color: #FFFFFF !important;
            padding: 15px 25px !important;
            border-radius: 16px !important;
            border: 1px solid #E5E7EB !important;
            margin-bottom: 25px !important;
        }
        
        .reference-card {
            background-color: #FFFFFF !important;
            border: 1px solid #E5E7EB !important;
            border-radius: 16px !important;
            padding: 20px !important;
            margin-bottom: 20px !important;
            min-height: 280px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 4px 20px rgba(0,0,0,0.02);
            transition: all 0.3s ease;
        }
        .reference-card:hover {
            box-shadow: 0 8px 30px rgba(0,0,0,0.05);
            transform: translateY(-2px);
        }
        
        .card-title-sub {
            font-size: 0.85rem !important;
            font-weight: 700 !important;
            color: #374151 !important;
            margin-bottom: 6px !important;
            text-transform: uppercase;
            line-height: 1.3;
            letter-spacing: 0.5px;
        }
        
        .card-value-big {
            font-size: 1.35rem !important;
            font-weight: 700 !important;
            color: #111827 !important;
            margin-bottom: 8px !important;
            line-height: 1.3;
        }
        
        .card-desc-bottom {
            font-size: 0.75rem !important;
            color: #4B5563 !important;
            margin-top: 8px !important;
            line-height: 1.3;
        }

        /* 🌟 สไตล์หัวข้อหลักและหัวข้อประเภทย่อยให้โดดเด่นสะดุดตา */
        .section-header-box {
            background: linear-gradient(135deg, #1E429F 0%, #1A365D 100%);
            color: white;
            padding: 14px 22px;
            border-radius: 14px;
            margin-top: 25px;
            margin-bottom: 15px;
            box-shadow: 0 4px 15px rgba(30, 66, 159, 0.2);
        }
        </style>
    """, unsafe_allow_html=True)
    
    col_menu, col_content = st.columns([1, 4])

    with col_menu:
        st.markdown("")
        st.markdown("")
        menu_card_minimal("A1.png", "Package A", "DeptPage", "btn_pkg_a")
        menu_card_minimal("A2.png", "Package B", "DeptPage", "btn_pkg_b")
        menu_card_minimal("A3.png", "กลับหน้าหลัก", "Dashboard", "btn_home")

    with col_content:
        current_choice = st.session_state.get('pkg_choice', 'Package A')
        package_code = 'A' if current_choice == 'Package A' else 'B'
        package_label = "Package A (อายุไม่เกิน 34 ปี)" if package_code == 'A' else "Package B (อายุ 35 ปีขึ้นไป)"
        
        st.markdown(f"<h2 style='color: #111827; font-weight: 700; margin-bottom: 2px;'>Welcome back, User</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #6B7280; font-size: 0.9rem; margin-bottom: 20px;'>กำลังตรวจสอบแดชบอร์ดรายหน่วยงานเชิงลึกในกลุ่มประชากร {package_label}</p>", unsafe_allow_html=True)
        
        # 🌟 ปรับดีไซน์ส่วนหัวให้มีรูปภาพประกอบด้านซ้ายและข้อความด้านขวา (ดีไซน์คล้ายหน้าภาพรวมแต่ใช้รูปต่างกัน)
        if package_code == 'A':
            package_header_html = f'''
                <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 16px; padding: 20px 24px; margin-bottom: 25px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);">
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px;">
                        <div style="display: flex; align-items: center; gap: 20px;">
                            <div style="background: #F0F6FF; border: 1px solid #BFDBFE; border-radius: 12px; padding: 10px; display: flex; align-items: center; justify-content: center; min-width: 90px; height: 75px;">
                                <span style="font-size: 32px;">📰</span>
                            </div>
                            <div>
                                <span style="background-color: #EFF6FF; color: #1E429F; padding: 3px 12px; border-radius: 30px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">ACTIVE WORKSPACE</span>
                                <h1 style="color: #1E429F; font-weight: 850; margin: 4px 0 2px 0; font-size: 1.8rem; font-family:-apple-system,BlinkMacSystemFont; line-height: 1.2;">Department Analysis - Package A</h1>
                                <p style="color: #4B5563; font-size: 0.85rem; margin: 0; font-weight: 500;">
                                    เจาะลึกข้อมูลสุขภาพรายหน่วยงานสำหรับบุคลากร<br>
                                    <span style="color: #6B7280; font-size: 0.8rem;">กลุ่มอายุไม่เกิน 34 ปี (โรคอ้วน + ไขมันในเลือด + ความดันโลหิต)</span>
                                </p>
                            </div>
                        </div>
                        <div style="background: #F8FAFC; padding: 10px 16px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: right;">
                            <span style="color: #6B7280; font-size: 0.72rem; font-weight: 600; display: block;">📅 Active Period</span>
                            <span style="color: #1E429F; font-weight: 700; font-size: 0.85rem;">21 Jul 2026</span>
                        </div>
                    </div>
                </div>
            '''
        else:
            package_header_html = f'''
                <div style="background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 16px; padding: 20px 24px; margin-bottom: 25px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);">
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 20px;">
                        <div style="display: flex; align-items: center; gap: 20px;">
                            <div style="background: #FFF5F5; border: 1px solid #FECDD3; border-radius: 12px; padding: 10px; display: flex; align-items: center; justify-content: center; min-width: 90px; height: 75px;">
                                <span style="font-size: 32px;">📑</span>
                            </div>
                            <div>
                                <span style="background-color: #FFF1F2; color: #9D174D; padding: 3px 12px; border-radius: 30px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;">ACTIVE WORKSPACE</span>
                                <h1 style="color: #9D174D; font-weight: 850; margin: 4px 0 2px 0; font-size: 1.8rem; font-family:-apple-system,BlinkMacSystemFont; line-height: 1.2;">Department Analysis - Package B</h1>
                                <p style="color: #4B5563; font-size: 0.85rem; margin: 0; font-weight: 500;">
                                    เจาะลึกข้อมูลสุขภาพรายหน่วยงานสำหรับบุคลากร<br>
                                    <span style="color: #6B7280; font-size: 0.8rem;">กลุ่มอายุ 35 ปีขึ้นไป (โรคเบาหวาน + อ้วน + ความดัน + ไขมัน)</span>
                                </p>
                            </div>
                        </div>
                        <div style="background: #F8FAFC; padding: 10px 16px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: right;">
                            <span style="color: #6B7280; font-size: 0.72rem; font-weight: 600; display: block;">📅 Active Period</span>
                            <span style="color: #9D174D; font-weight: 700; font-size: 0.85rem;">21 Jul 2026</span>
                        </div>
                    </div>
                </div>
            '''

        st.markdown(package_header_html, unsafe_allow_html=True)
        
        # ฟิลเตอร์หลัก
        available_depts = ["ทั้งหมด"] + sorted(list(df_master['คณะ'].dropna().unique()))
        available_years = ["ทั้งหมด"] + sorted(df_master['Year'].dropna().unique().astype(int).tolist())
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: active_dept = st.selectbox("Department Focus", available_depts, key="dept_deep_filter")
        with c2: selected_year_d = st.selectbox("Academic Year", available_years, key="year_deep_filter")
        with c3: age_filter = st.selectbox("Age Range", ["ทั้งหมด", "น้อยกว่า 30", "31-40", "41-50", "51-60", "60 ขึ้นไป"], key="age_deep_filter")
        with c4: gender_filter = st.selectbox("Gender", ["ทั้งหมด", "Female", "Male"], key="gender_deep_filter")
        st.markdown('</div>', unsafe_allow_html=True)
        
        df_base = df_master.copy()
        
        if 'Cluster' in df_base.columns:
            df_base['Cluster'] = df_base['Cluster'].astype(str).str.strip()

        if package_code == 'A':
            df_pkg_d = df_base[df_base['Package'] == 'A'].copy()
            color_map = color_map_A.copy()
            cluster_list = list(package_clusters['A'].values())
        else:
            df_pkg_d = df_base[df_base['Package'] == 'B'].copy()
            color_map = color_map_B.copy()
            cluster_list = list(package_clusters['B'].values())

        if active_dept != "ทั้งหมด":
            df_pkg_d = df_pkg_d[df_pkg_d['คณะ'] == active_dept].copy()
        if selected_year_d != "ทั้งหมด": 
            df_pkg_d = df_pkg_d[df_pkg_d['Year'] == int(selected_year_d)].copy()
        if gender_filter != "ทั้งหมด": 
            df_pkg_d = df_pkg_d[df_pkg_d['Gender'] == gender_filter].copy()
        if age_filter != "ทั้งหมด":
            df_pkg_d['Age'] = pd.to_numeric(df_pkg_d['Age'], errors='coerce')
            if age_filter == "น้อยกว่า 30": df_pkg_d = df_pkg_d[df_pkg_d['Age'] < 30].copy()
            elif age_filter == "31-40": df_pkg_d = df_pkg_d[(df_pkg_d['Age'] >= 31) & (df_pkg_d['Age'] <= 40)].copy()
            elif age_filter == "41-50": df_pkg_d = df_pkg_d[(df_pkg_d['Age'] >= 41) & (df_pkg_d['Age'] <= 50)].copy()
            elif age_filter == "51-60": df_pkg_d = df_pkg_d[(df_pkg_d['Age'] >= 51) & (df_pkg_d['Age'] <= 60)].copy()
            elif age_filter == "60 ขึ้นไป": df_pkg_d = df_pkg_d[df_pkg_d['Age'] >= 60].copy()

        color_map["ไม่ระบุกลุ่ม"] = "#E5E7EB"

        if not df_pkg_d.empty:
            total_screened = len(df_pkg_d)
            counts_series = df_pkg_d['Cluster'].value_counts()

            # 🌟 หัวข้อส่วนที่ 1
            st.markdown(f'''
                <div class="section-header-box">
                    <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">ตัวชี้วัดและสัดส่วนประชากรประจำหน่วยงาน: <span style="color: #93C5FD;">{active_dept}</span></h3>
                </div>
            ''', unsafe_allow_html=True)
            
            # 🔳 แถวที่ 1: การ์ดภาพรวมสถิติตัวชี้วัดเฉลี่ยหลัก
            cols_row1 = st.columns(4)
            
            with cols_row1[0]:
                st.markdown(f'''
                    <div class="reference-card" style="min-height: 175px !important; padding: 18px !important;">
                        <div>
                            <div class="card-title-sub" style="border-left: 4px solid #79099c; padding-left: 8px;">Total Screened</div>
                            <div class="card-value-big" style="font-size: 1.8rem !important; margin-top: 10px;">{total_screened:,} <span style="font-size:1rem; color:#6B7280; font-weight:normal;">คน</span></div>
                        </div>
                        <div class="card-desc-bottom" style="margin-top: 5px;">จำนวนบุคลากรในคณะที่เข้ารับการตรวจสุขภาพประจำปีตามตัวกรองย่อย</div>
                    </div>
                ''', unsafe_allow_html=True)
                
            with cols_row1[1]:
                mean_bmi = df_pkg_d['BMI'].mean() if 'BMI' in df_pkg_d.columns else 0
                mean_sbp = df_pkg_d['SBP'].mean() if 'SBP' in df_pkg_d.columns else 0
                mean_dbp = df_pkg_d['DBP'].mean() if 'DBP' in df_pkg_d.columns else 0
                
                bmi_lbl = "สมส่วน" if mean_bmi <= 22.9 else ("น้ำหนักเกิน" if mean_bmi <= 24.9 else "โรคอ้วน")
                bp_lbl = "ปกติ/เหมาะสม" if mean_sbp < 130 and mean_dbp < 85 else "เสี่ยง/สูง"
                c_bmi = "#10B981" if "สมส่วน" in bmi_lbl else "#EF4444"
                c_bp = "#10B981" if "ปกติ" in bp_lbl else "#EF4444"

                st.markdown(f'''
                    <div class="reference-card" style="min-height: 175px !important; padding: 18px !important;">
                        <div>
                            <div class="card-title-sub" style="border-left: 4px solid #10B981; padding-left: 8px;">BMI & Blood Pressure</div>
                            <div class="card-value-big" style="font-size: 1.05rem !important; margin-top: 8px; font-weight: 500; line-height: 1.5;">
                                <div>BMI: <b>{mean_bmi:.1f}</b> <span style="color:{c_bmi}; font-size:0.75rem; font-weight:600;">({bmi_lbl})</span></div>
                                <div style="margin-top:2px;">BP: <b>{int(mean_sbp)}/{int(mean_dbp)}</b> <span style="color:{c_bp}; font-size:0.75rem; font-weight:600;">({bp_lbl})</span></div>
                            </div>
                        </div>
                        <div class="card-desc-bottom" style="margin-top: 5px; font-size: 0.7rem;">ดัชนีมวลกายเฉลี่ย และระดับความดันโลหิตเฉลี่ย ประจำหน่วยงาน</div>
                    </div>
                ''', unsafe_allow_html=True)

            with cols_row1[2]:
                mean_fbs = df_pkg_d['ผลการตรวจน้ำตาลในเลือด FBS'].mean() if 'ผลการตรวจน้ำตาลในเลือด FBS' in df_pkg_d.columns else 0
                mean_chol = df_pkg_d['ผลการตรวจระดับไขมันในเลือด (Cholesterol)'].mean() if 'ผลการตรวจระดับไขมันในเลือด (Cholesterol)' in df_pkg_d.columns else 0
                
                fbs_lbl = "ปกติ" if mean_fbs < 100 else ("เสี่ยงเบาหวาน" if mean_fbs <= 125 else "เบาหวาน")
                chol_lbl = "เหมาะสม" if mean_chol < 200 else "สูงเกินเกณฑ์"
                c_fbs = "#10B981" if "ปกติ" in fbs_lbl else "#EF4444"
                c_chol = "#10B981" if "เหมาะสม" in chol_lbl else "#EF4444"

                st.markdown(f'''
                    <div class="reference-card" style="min-height: 175px !important; padding: 18px !important;">
                        <div>
                            <div class="card-title-sub" style="border-left: 4px solid #F59E0B; padding-left: 8px;">Blood Sugar & Cholesterol</div>
                            <div class="card-value-big" style="font-size: 1.05rem !important; margin-top: 8px; font-weight: 500; line-height: 1.5;">
                                <div>FBS: <b>{mean_fbs:.1f}</b> <span style="color:{c_fbs}; font-size:0.75rem; font-weight:600;">({fbs_lbl})</span></div>
                                <div style="margin-top:2px;">Chol: <b>{mean_chol:.1f}</b> <span style="color:{c_chol}; font-size:0.75rem; font-weight:600;">({chol_lbl})</span></div>
                            </div>
                        </div>
                        <div class="card-desc-bottom" style="margin-top: 5px; font-size: 0.7rem;">ค่าน้ำตาลในเลือดเฉลี่ย และระดับไขมันรวมเฉลี่ยประจำหน่วยงาน</div>
                    </div>
                ''', unsafe_allow_html=True)

            with cols_row1[3]:
                mean_egfr = df_pkg_d['eGFR'].mean() if 'eGFR' in df_pkg_d.columns else 0
                mean_alt = df_pkg_d['ALT (SGPT)'].mean() if 'ALT (SGPT)' in df_pkg_d.columns else 0
                
                egfr_lbl = "ปกติ" if mean_egfr >= 90.0 else "ไตเริ่มเสื่อม/ผิดปกติ"
                alt_lbl = "ปกติ" if mean_alt <= 40.0 else "ตับอักเสบ"
                c_egfr = "#10B981" if "ปกติ" in egfr_lbl else "#EF4444"
                c_alt = "#10B981" if "ปกติ" in alt_lbl else "#EF4444"

                st.markdown(f'''
                    <div class="reference-card" style="min-height: 175px !important; padding: 18px !important;">
                        <div>
                            <div class="card-title-sub" style="border-left: 4px solid #EF4444; padding-left: 8px;">Kidney & Liver Functions</div>
                            <div class="card-value-big" style="font-size: 1.05rem !important; margin-top: 8px; font-weight: 500; line-height: 1.5;">
                                <div>eGFR: <b>{mean_egfr:.1f}</b> <span style="color:{c_egfr}; font-size:0.75rem; font-weight:600;">({egfr_lbl})</span></div>
                                <div style="margin-top:2px;">ALT: <b>{mean_alt:.1f}</b> <span style="color:{c_alt}; font-size:0.75rem; font-weight:600;">({alt_lbl})</span></div>
                            </div>
                        </div>
                        <div class="card-desc-bottom" style="margin-top: 5px; font-size: 0.7rem;">อัตราการกรองของไตเฉลี่ย และค่าเอนไซม์ตับอักเสบเฉลี่ย</div>
                    </div>
                ''', unsafe_allow_html=True)

            # 🔳 แถวที่ 2: การ์ดแสดงผลชื่อกลุ่มแต่ละแพ็กเกจ (Cluster Cards)
            st.markdown("<p style='color: #374151; font-size: 0.95rem; font-weight: 700; margin-top: 20px; margin-bottom: 10px;'>สัดส่วนประชากรจำแนกตามกลุ่มความเสี่ยงประจำแพ็กเกจ:</p>", unsafe_allow_html=True)
            
            num_cards = len(cluster_list)
            card_slots = st.columns(3 if num_cards > 3 else num_cards)
            
            for idx, cluster_name in enumerate(cluster_list):
                people_in_group = int(counts_series.get(cluster_name, 0))
                pct_in_group = (people_in_group / total_screened * 100) if total_screened > 0 else 0
                bg_color = color_map.get(cluster_name, "#E5E7EB")
                
                slot_idx = idx % 3 if num_cards > 3 else idx
                with card_slots[slot_idx]:
                    st.markdown(f'''
                        <div class="reference-card">
                            <div>
                                <div class="card-title-sub" style="border-left: 4px solid {bg_color}; padding-left: 8px; min-height:36px;">{cluster_name}</div>
                                <div class="card-value-big" style="margin-top: 10px;">{people_in_group:,} <span style="font-size:0.9rem; color:#6B7280; font-weight:normal;">คน</span></div>
                                <div style="font-size:0.9rem; font-weight:600; color:{bg_color};">คิดเป็น {pct_in_group:.1f}%</div>
                            </div>
                    ''', unsafe_allow_html=True)
                    
                    fig_mini = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = pct_in_group,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        gauge = {'axis': {'range': [0, 100], 'visible': False},
                                 'bar': {'color': bg_color},
                                 'bgcolor': "#F3F4F6"}
                    ))
                    fig_mini.update_layout(height=65, margin=dict(l=10, r=10, t=10, b=10))
                    st.plotly_chart(fig_mini, use_container_width=True, key=f"mini_chart_{package_code}_{idx}", config={'displayModeBar': False})
                    st.markdown('</div>', unsafe_allow_html=True)

            # ==========================================
            # 🌟 แถวที่ 3: ส่วนวิเคราะห์พฤติกรรมสุขภาพ
            # ==========================================
            st.markdown(f'''
                <div class="section-header-box" style="background: linear-gradient(135deg, #0D9488 0%, #0F766E 100%);">
                    <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">พฤติกรรมสุขภาพและความเสี่ยงไลฟ์สไตล์ประจำหน่วยงาน: <span style="color: #99F6E4;">{active_dept}</span></h3>
                </div>
            ''', unsafe_allow_html=True)
            st.markdown("<p style='color: #4B5563; font-size: 0.88rem; margin-bottom: 12px; font-weight: 500;'>สถิติต่างๆ และสัดส่วนพฤติกรรมการสูบบุหรี่ การดื่มแอลกอฮอล์ และการออกกำลังกาย</p>", unsafe_allow_html=True)

            smoke_col = next((c for c in df_pkg_d.columns if 'สูบ' in c or 'Smoke' in c), None)
            alcohol_col = next((c for c in df_pkg_d.columns if 'แอลกอฮอล์' in c or 'Drink' in c or 'Alcohol' in c), None)
            exercise_col = next((c for c in df_pkg_d.columns if 'ออกกำลัง' in c or 'Exercise' in c or 'Activity' in c), None)

            if smoke_col:
                df_pkg_d[smoke_col] = df_pkg_d[smoke_col].fillna("ไม่ระบุ").astype(str).str.strip()
                df_pkg_d[smoke_col] = df_pkg_d[smoke_col].replace({
                    "ไม่เคยสูบบุหรี่": "ไม่สูบบุหรี่",
                    "ไม่เคยสูบ": "ไม่สูบบุหรี่"
                })

            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                smoke_options = ["ทั้งหมด"] + (sorted(df_pkg_d[smoke_col].dropna().unique().tolist()) if smoke_col else [])
                selected_smoke = st.selectbox("กรองตามพฤติกรรมการสูบบุหรี่", smoke_options, key="filter_smoke_sub")
            with f_col2:
                alc_options = ["ทั้งหมด"] + (sorted(df_pkg_d[alcohol_col].dropna().astype(str).unique().tolist()) if alcohol_col else [])
                selected_alc = st.selectbox("กรองตามการดื่มแอลกอฮอล์", alc_options, key="filter_alc_sub")
            with f_col3:
                ex_options = ["ทั้งหมด"] + (sorted(df_pkg_d[exercise_col].dropna().astype(str).unique().tolist()) if exercise_col else [])
                selected_ex = st.selectbox("กรองตามการออกกำลังกาย", ex_options, key="filter_ex_sub")

            df_beh_filtered = df_pkg_d.copy()
            if selected_smoke != "ทั้งหมด" and smoke_col:
                df_beh_filtered = df_beh_filtered[df_beh_filtered[smoke_col] == selected_smoke]
            if selected_alc != "ทั้งหมด" and alcohol_col:
                df_beh_filtered = df_beh_filtered[df_beh_filtered[alcohol_col].astype(str) == selected_alc]
            if selected_ex != "ทั้งหมด" and exercise_col:
                df_beh_filtered = df_beh_filtered[df_beh_filtered[exercise_col].astype(str) == selected_ex]

            st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

            beh_col1, beh_col2, beh_col3 = st.columns(3)

            with beh_col1:
                
                st.markdown('<div class="card-title-sub" style="border-left: 4px solid #3B82F6; padding-left: 8px;">พฤติกรรมการสูบบุหรี่ (SMOKING HABIT)</div>', unsafe_allow_html=True)
                if smoke_col and not df_beh_filtered.empty:
                    smoke_counts = df_beh_filtered[smoke_col].value_counts()
                    fig_smoke = px.pie(values=smoke_counts.values, names=smoke_counts.index, hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_smoke.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), showlegend=True, legend=dict(font=dict(size=10), orientation="h", y=-0.2))
                    st.plotly_chart(fig_smoke, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("ไม่พบข้อมูลตามเงื่อนไขตัวกรอง")
                st.markdown('</div>', unsafe_allow_html=True)

            with beh_col2:
                
                st.markdown('<div class="card-title-sub" style="border-left: 4px solid #8B5CF6; padding-left: 8px;">การดื่มแอลกอฮอล์ (ALCOHOL CONSUMPTION)</div>', unsafe_allow_html=True)
                if alcohol_col and not df_beh_filtered.empty:
                    alc_counts = df_beh_filtered[alcohol_col].fillna("ไม่ระบุ").astype(str).value_counts()
                    fig_alc = px.pie(values=alc_counts.values, names=alc_counts.index, hole=0.5, color_discrete_sequence=px.colors.qualitative.Set2)
                    fig_alc.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), showlegend=True, legend=dict(font=dict(size=10), orientation="h", y=-0.2))
                    st.plotly_chart(fig_alc, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("ไม่พบข้อมูลตามเงื่อนไขตัวกรอง")
                st.markdown('</div>', unsafe_allow_html=True)

            with beh_col3:
                
                st.markdown('<div class="card-title-sub" style="border-left: 4px solid #10B981; padding-left: 8px;">พฤติกรรมการออกกำลังกาย (PHYSICAL ACTIVITY)</div>', unsafe_allow_html=True)
                if exercise_col and not df_beh_filtered.empty:
                    ex_counts = df_beh_filtered[exercise_col].fillna("ไม่ระบุ").astype(str).value_counts()
                    fig_ex = px.pie(values=ex_counts.values, names=ex_counts.index, hole=0.5, color_discrete_sequence=px.colors.qualitative.Safe)
                    fig_ex.update_layout(height=160, margin=dict(l=10, r=10, t=10, b=10), showlegend=True, legend=dict(font=dict(size=10), orientation="h", y=-0.2))
                    st.plotly_chart(fig_ex, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("ไม่พบข้อมูลตามเงื่อนไขตัวกรอง")
                st.markdown('</div>', unsafe_allow_html=True)

            # 🔳 แผนภูมิแท่งเปรียบเทียบสัดส่วนเสี่ยงของแต่ละตึก
            st.markdown(f'''
                <div class="section-header-box" style="background: linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%);">
                    <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">แผนภูมิแท่งจำแนกสัดส่วนประชากรความเสี่ยงรายคณะ (<span style="color: #DDD6FE;">{package_label}</span>)</h3>
                </div>
            ''', unsafe_allow_html=True)
            
            df_fac_filtered = df_pkg_d[df_pkg_d['Cluster'].isin(cluster_list)].copy()
            
            if not df_fac_filtered.empty:
                df_fac_sum = df_fac_filtered.groupby(['คณะ', 'Cluster']).size().reset_index(name='counts')
                df_fac_totals = df_fac_filtered.groupby('คณะ').size().reset_index(name='total')
                df_fac_sum = pd.merge(df_fac_sum, df_fac_totals, on='คณะ').sort_values(by='total', ascending=True)

                num_unique_facs = df_fac_sum['คณะ'].nunique()
                dynamic_height = max(380, num_unique_facs * 25)

                st.markdown('<div style="background-color:#FFFFFF; border:1px solid #E5E7EB; border-radius:16px; padding:20px; margin-bottom:20px; box-shadow: 0 4px 20px rgba(0,0,0,0.02);">', unsafe_allow_html=True)
                fig_main_bar = px.bar(
                    df_fac_sum, x='counts', y='คณะ', color='Cluster', orientation='h',
                    color_discrete_map=color_map
                )
                fig_main_bar.update_layout(
                    height=dynamic_height, margin=dict(l=200, r=10, t=10, b=40),
                    legend=dict(title="", orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
                    xaxis=dict(title="จำนวนคนตรวจ (คน)"), yaxis=dict(title="", tickfont=dict(size=10)),
                    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
                )
                selected_bar_points = st.plotly_chart(fig_main_bar, on_select="rerun", use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("ไม่มีข้อมูลสัดส่วนความเสี่ยงสอดคล้องในเงื่อนไขนี้")

            # 🔳 Executive Action Plan & Medical Insights
            st.markdown(f'''
                <div class="section-header-box" style="background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);">
                    <h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #FFFFFF;">Executive Action Plan & Medical Insights</h3>
                </div>
            ''', unsafe_allow_html=True)
            st.markdown("<p style='color: #4B5563; font-size: 0.88rem; margin-bottom: 20px; font-weight: 500;'>บทสรุปพฤติกรรมสุขภาพทางคลินิกและการประเมินดัชนีกลุ่มเสี่ยงตามเกณฑ์กระทรวงสาธารณสุข</p>", unsafe_allow_html=True)

            if selected_bar_points and "points" in selected_bar_points and len(selected_bar_points["points"]) > 0:
                clicked_fac = selected_bar_points["points"][0].get("y")
                df_insights_target = df_pkg_d[df_pkg_d['คณะ'] == clicked_fac].copy()
                display_dept_name = clicked_fac
                st.info(f"กำลังแสดงผลบทสรุปเฉพาะหน่วยงาน: {clicked_fac}")
            else:
                df_insights_target = df_pkg_d.copy()
                display_dept_name = active_dept

            critical_sbp_count = len(df_insights_target[df_insights_target['SBP'] > 160])
            critical_fbs_count = len(df_insights_target[df_insights_target['ผลการตรวจน้ำตาลในเลือด FBS'] > 126])
            critical_chol_count = len(df_insights_target[df_insights_target['ผลการตรวจระดับไขมันในเลือด (Cholesterol)'] >= 200])
            critical_bmi_count = len(df_insights_target[df_insights_target['BMI'] >= 30])
            critical_alt_count = len(df_insights_target[df_insights_target['ALT (SGPT)'] > 40])

            alert_cols = st.columns(4)
            
            with alert_cols[0]:
                if critical_sbp_count > 0:
                    st.markdown(f'''
                        <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px; padding: 18px 16px; min-height: 105px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <span style="background-color: #FEF2F2; color: #EF4444; font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 20px; text-transform: uppercase;">CRITICAL ALERT</span>
                                <div style="color: #111827; font-weight: 700; font-size: 0.9rem; margin-top: 8px;">ความดันโลหิตสูง</div>
                            </div>
                            <div style="color: #4B5563; font-size: 0.8rem; margin-top: 4px;">พบเคส SBP > 160 ยอดรวม <b style="color:#EF4444; font-size:1.05rem;">{critical_sbp_count}</b> ราย</div>
                        </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown('''
                        <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px; padding: 18px 16px; min-height: 105px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <span style="background-color: #F0FDF4; color: #10B981; font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 20px; text-transform: uppercase;">STABLE</span>
                                <div style="color: #111827; font-weight: 700; font-size: 0.9rem; margin-top: 8px;">ระบบความดันโลหิต</div>
                            </div>
                            <div style="color: #6B7280; font-size: 0.78rem; margin-top: 4px;">🟢 ทุกคนอยู่ในเกณฑ์ปลอดภัย</div>
                        </div>
                    ''', unsafe_allow_html=True)

            with alert_cols[1]:
                if critical_fbs_count > 0:
                    st.markdown(f'''
                        <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px; padding: 18px 16px; min-height: 105px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <span style="background-color: #FEF2F2; color: #EF4444; font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 20px; text-transform: uppercase;">CRITICAL ALERT</span>
                                <div style="color: #111827; font-weight: 700; font-size: 0.9rem; margin-top: 8px;">ภาวะโรคเบาหวาน</div>
                            </div>
                            <div style="color: #4B5563; font-size: 0.8rem; margin-top: 4px;">พบเคส FBS > 126 ยอดรวม <b style="color:#EF4444; font-size:1.05rem;">{critical_fbs_count}</b> ราย</div>
                        </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown('''
                        <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px; padding: 18px 16px; min-height: 105px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <span style="background-color: #F0FDF4; color: #10B981; font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 20px; text-transform: uppercase;">STABLE</span>
                                <div style="color: #111827; font-weight: 700; font-size: 0.9rem; margin-top: 8px;">ระดับน้ำตาลในเลือด</div>
                            </div>
                            <div style="color: #6B7280; font-size: 0.78rem; margin-top: 4px;">🟢 อยู่ในเกณฑ์ควบคุมได้ปกติ</div>
                        </div>
                    ''', unsafe_allow_html=True)

            with alert_cols[2]:
                if critical_chol_count > 0:
                    st.markdown(f'''
                        <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px; padding: 18px 16px; min-height: 105px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <span style="background-color: #FFFBEB; color: #F59E0B; font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 20px; text-transform: uppercase;">ATTENTION</span>
                                <div style="color: #111827; font-weight: 700; font-size: 0.9rem; margin-top: 8px;">ไขมันในเลือดสูง</div>
                            </div>
                            <div style="color: #4B5563; font-size: 0.8rem; margin-top: 4px;">พบ Chol &ge; 200 ยอดรวม <b style="color:#F59E0B; font-size:1.05rem;">{critical_chol_count}</b> ราย</div>
                        </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown('''
                        <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px; padding: 18px 16px; min-height: 105px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <span style="background-color: #F0FDF4; color: #10B981; font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 20px; text-transform: uppercase;">OPTIMAL</span>
                                <div style="color: #111827; font-weight: 700; font-size: 0.9rem; margin-top: 8px;">ระดับไขมันรวม</div>
                            </div>
                            <div style="color: #6B7280; font-size: 0.78rem; margin-top: 4px;">🟢 ดัชนีเหมาะสมตามเกณฑ์</div>
                        </div>
                    ''', unsafe_allow_html=True)

            with alert_cols[3]:
                if critical_bmi_count > 0 or critical_alt_count > 0:
                    st.markdown(f'''
                        <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px; padding: 14px 16px; min-height: 105px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <span style="background-color: #FFFBEB; color: #F59E0B; font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 20px; text-transform: uppercase;">MONITORING</span>
                                <div style="color: #111827; font-weight: 700; font-size: 0.9rem; margin-top: 6px;">ดัชนีโรคอ้วน & ตับ</div>
                            </div>
                            <div style="color: #4B5563; font-size: 0.75rem; line-height: 1.3;">
                                • อ้วนอันตราย: <span style="color:#F59E0B; font-weight:700;">{critical_bmi_count}</span> ราย<br>
                                • ตับอักเสบ: <span style="color:#F59E0B; font-weight:700;">{critical_alt_count}</span> ราย
                            </div>
                        </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown('''
                        <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px; padding: 18px 16px; min-height: 105px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <span style="background-color: #F0FDF4; color: #10B981; font-size: 0.65rem; font-weight: 700; padding: 3px 8px; border-radius: 20px; text-transform: uppercase;">HEALTHY</span>
                                <div style="color: #111827; font-weight: 700; font-size: 0.9rem; margin-top: 8px;">ภาวะอ้วน & ตับอักเสบ</div>
                            </div>
                            <div style="color: #6B7280; font-size: 0.78rem; margin-top: 4px;">🟢 ผลโครงสร้างปกติสอดคล้อง</div>
                        </div>
                    ''', unsafe_allow_html=True)

            st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

            advice_col = 'คำแนะนำ ส่วนของแพทย์หลังได้รับผลแลป' if 'คำแนะนำ ส่วนของแพทย์หลังได้รับผลแลป' in df_insights_target.columns else ('คำแนะนำ ผลการตรวจระดับไขมัน inเลือด' if 'คำแนะนำ ผลการตรวจระดับไขมันในเลือด' in df_insights_target.columns else None)
            
            if advice_col:
                valid_advices = df_insights_target[advice_col].dropna().astype(str).str.strip()
                if not valid_advices.empty:
                    top_advice = valid_advices.mode()[0]
                    st.markdown(f'''
                        <div style="background-color: #FFFFFF; border: 1px solid #E5E7EB; border-left: 5px solid #4F46E5; border-radius: 14px; padding: 20px 24px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); margin-top: 15px;">
                            <h5 style="color: #111827; margin: 0 0 8px 0; font-size: 1rem; font-weight: 700;">Automated Medical Insight</h5>
                            <p style="color: #4B5563; margin: 0; font-size: 0.88rem; line-height: 1.6;">
                                จากการประมวลผลฐานข้อมูลเชิงคุณภาพของหน่วยงาน <span style="color:#4F46E5; font-weight:600;">{display_dept_name}</span> คณะแพทย์ผู้ตรวจสุขภาพส่วนใหญ่มีแนวทางสรุปข้อแนะนำเชิงการดำเนินมาตรการระบุไว้ว่า:<br>
                                <span style="color: #111827; font-weight: 600; font-size: 0.92rem; display: block; margin-top: 6px; padding-left: 12px; border-left: 2px dashed #E5E7EB;">"{top_advice}"</span>
                            </p>
                        </div>
                    ''', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            footer_col1, footer_col2 = st.columns([3, 1])
            with footer_col1:
                st.markdown(f"<p style='color: #6B7280; font-size: 0.82rem; margin-top: 10px; font-weight: 400;'>หากต้องการตรวจสอบโครงสร้างข้อมูลและผลแล็บอย่างละเอียดรายบุคคลของหน่วยงาน {display_dept_name} สามารถคลิกดาวน์โหลดรายงานภายนอกได้ที่ปุ่มทางขวามือ</p>", unsafe_allow_html=True)
            with footer_col2:
                csv_data = df_pkg_d.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Export to CSV Report",
                    data=csv_data,
                    file_name=f"Health_Report_{display_dept_name}_{package_code}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            st.markdown('</div>', unsafe_allow_html=True)
            
        else:
            st.warning(f"⚠️ ไม่พบข้อมูลผู้เข้าตรวจของ {package_label} ตามเงื่อนไขฟิลเตอร์ที่คุณระบุในระบบ")


# ---------------------------------------------------------------------------------------------
elif st.session_state.current_page == "คลังความรู้":
    
    # --- CSS สำหรับปรับแต่งหน้าคลังความรู้ และปุ่มเมนูด้านบนให้เป็นกรอบขาวมน ---
    st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
        }

        /* 🌟 ปรับแต่งปุ่มเมนูด้านบนให้เป็นกรอบสีขาว ทรงมนสวยงาม */
        div[data-testid="stHorizontalBlock"] > div div.stButton > button {
            background: #ffffff !important;
            color: #1A365D !important;
            border-radius: 50px !important; /* ทำเป็นทรงมนแคปซูล */
            font-weight: 700 !important;
            border: 1px solid rgba(226, 232, 240, 0.9) !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stHorizontalBlock"] > div div.stButton > button:hover {
            background: #f7fafc !important;
            border-color: #2B6CB0 !important;
            box-shadow: 0 6px 20px rgba(43, 108, 176, 0.15) !important;
            transform: translateY(-2px);
        }
    </style>
    """, unsafe_allow_html=True)

    # ส่วนหัวข้อหน้าคลังความรู้
    with st.container():
        st.markdown("""
            <div style="text-align: center; margin-bottom: 30px;">
                <p style='color: #4A5568; font-size: 15px; font-weight: 500; margin-bottom: 5px; letter-spacing: 0.5px;'>
                    แหล่งรวบรวมข้อมูลเชิงวิชาการที่น่าเชื่อถือ
                </p>
                <h1 style='color: #1A365D; font-weight: 1000; font-size: 42px; margin-top: 0; letter-spacing: -1px;'>
                    คลังความรู้ เอกสารงานวิชาการ
                </h1>
                <div style="display: inline-block; background: linear-gradient(135deg, #2B6CB0 0%, #1A365D 100%); color: #ffffff; padding: 8px 22px; border-radius: 50px; font-weight: 700; font-size: 13.5px; margin-top: 8px; box-shadow: 0 4px 15px rgba(43, 108, 176, 0.3);">
                    ฐานข้อมูลความรู้ด้านโรคไม่ติดต่อเรื้อรัง (NCDs)
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    articles = [
        ("โรคไม่ติดต่อกับวันสำคัญ", "https://ddc.moph.go.th/dncd/publishinfodetail.php?publish=15238&deptcode=dncd", "วัน.jpg"),
        ("Q & A โรคไม่ติดต่อ", "https://ddc.moph.go.th/dncd/publishinfodetail.php?publish=17967&deptcode=dncd", "คำถาม.jpg"),
        ("โรคเบาหวาน", "https://ddc.moph.go.th/dncd/publishinfodetail.php?publish=15232&deptcode=dncd", "เบา.jpg"),
        ("โรคไต", "https://ddc.moph.go.th/dncd/publishinfodetail.php?publish=15233&deptcode=dncd", "ไต.jpg"),
        ("โรคความดันโลหิตสูง", "https://ddc.moph.go.th/dncd/publishinfodetail.php?publish=15231&deptcode=dncd", "ดัน.jpg"),
        ("ความดันฯ ปรับเปลี่ยนพฤติกรรม", "https://ddc.moph.go.th/dncd/publishinfodetail.php?publish=17598&deptcode=dncd", "ดันป้องกัน.jpg"),
        ("ปัจจัยเสี่ยงความดันโลหิตสูง", "https://ddc.moph.go.th/dncd/publishinfodetail.php?publish=17046&deptcode=dncd", "ปัจจัยดัน.jpg"),
        ("ภาวะก่อนเบาหวาน", "https://ddc.moph.go.th/dncd/publishinfodetail.php?publish=11392&deptcode=dncd", "ก่อนเบา.jpg"),
        ("กินโซเดียมมากไป...", "https://ddc.moph.go.th/dncd/publishinfodetail.php?publish=17753&deptcode=dncd", "โซ.jpg")
    ]

    # จัดการส่วนแสดงผลเป็นชุดละ 3 รายการ
    # ใช้ enumerate เพื่อแบ่งกลุ่มละ 3 รายการ
    for i in range(0, len(articles), 4):
        cols = st.columns(4) # สร้าง 3 คอลัมน์ในทุกๆ รอบของการวนลูป
        
        # ดึงรายการออกมาทีละ 3 ตัว (chunk)
        chunk = articles[i:i+4]
        
        for j, (title, url, img_name) in enumerate(chunk):
            with cols[j]:
                img_b64 = get_image_as_base64(img_name)
                
                # การ์ดแสดงผล
                st.markdown(f"""
                    <div style="background-color: white; border: 1px solid #ddd; border-radius: 40px; 
                                padding: 20px; text-align: center; margin-bottom: 20px; width: 90% ; height: 400px; 
                                box-shadow: 0 4px 6px rgba(0.1,0,0,0.1);">
                        <img src="{img_b64}" style="width: 100%; height: 230px; object-fit: contain; border-radius: 10px;">
                        <h5 style="color: #1b305b; margin: 15px 0;">{title}</h5>
                        <a href="{url}" target="_blank" style="padding: 10px 20px; background-color: #1b305b; color: white; border-radius: 10px; text-decoration: none;">อ่านเพิ่มเติม</a>
                    </div>
                """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------------------------
elif st.session_state.current_page == "คู่มือ":
    
    # --- CSS สำหรับตกแต่งหน้ากระดาษ A4 และสไตล์องค์ประกอบภายใน ---
    st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 3rem !important;
        }

        /* ปุ่มเมนูด้านบนกรอบขาวทรงมน */
        div[data-testid="stHorizontalBlock"] > div div.stButton > button {
            background: #ffffff !important;
            color: #1A365D !important;
            border-radius: 50px !important;
            font-weight: 700 !important;
            border: 1px solid rgba(226, 232, 240, 0.9) !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05) !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stHorizontalBlock"] > div div.stButton > button:hover {
            background: #f7fafc !important;
            border-color: #2B6CB0 !important;
            box-shadow: 0 6px 20px rgba(43, 108, 176, 0.15) !important;
            transform: translateY(-2px);
        }

        /* 📄 สไตล์จำลองหน้ากระดาษ A4 สีขาว */
        .a4-paper-container {
            background: #ffffff;
            width: 100%;
            max-width: 850px;
            margin: 0 auto;
            padding: 50px 60px;
            border-radius: 20px;
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(226, 232, 240, 0.8);
            box-sizing: border-box;
        }

        /* หัวข้อภายในกระดาษ A4 */
        .a4-heading {
            color: #1A365D;
            font-size: 24px;
            font-weight: 800;
            margin-top: 25px;
            margin-bottom: 12px;
            border-bottom: 2px solid #E2E8F0;
            padding-bottom: 8px;
        }

        .a4-subheading {
            color: #2B6CB0;
            font-size: 17px;
            font-weight: 700;
            margin-top: 20px;
            margin-bottom: 8px;
        }

        .a4-text {
            color: #4A5568;
            font-size: 15px;
            line-height: 1.7;
            margin-bottom: 15px;
        }

        .a4-step-box {
            background: #F7FAFC;
            border-left: 4px solid #2B6CB0;
            padding: 14px 18px;
            border-radius: 0 12px 12px 0;
            margin-bottom: 15px;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- ส่วนหัวข้อหลักด้านนอกหน้ากระดาษ ---
    with st.container():
        st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <p style='color: #4A5568; font-size: 15px; font-weight: 500; margin-bottom: 5px;'>
                    เอกสารคำแนะนำและวิธีใช้งานระบบเชิงปฏิบัติการ
                </p>
                <h1 style='color: #1A365D; font-weight: 1000; font-size: 40px; margin-top: 0; letter-spacing: -1px;'>
                    คู่มือการใช้งานระบบ (User Manual)
                </h1>
                <div style="display: inline-block; background: linear-gradient(135deg, #2B6CB0 0%, #1A365D 100%); color: #ffffff; padding: 8px 22px; border-radius: 50px; font-weight: 700; font-size: 13.5px; margin-top: 8px; box-shadow: 0 4px 15px rgba(43, 108, 176, 0.3);">
                    📖 คู่มือการใช้งานระบบแดชบอร์ดโรคไม่ติดต่อเรื้อรัง (NCDs)
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # --- ตรวจสอบไฟล์ 'บทที่ 1.pdf' หากมีจะแสดงผลผ่าน PDF Viewer ถ้าไม่มีจะแสดงเนื้อหาข้อความ HTML ---
    file_path = "คู่มือการใช้งาน.pdf"
    
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            
        st.markdown(f'''
        <div class="a4-paper-container">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #1A365D; font-size: 24px; font-weight: 900; margin: 0;">เอกสาร: คู่มือการใช้งาน</h2>
            </div>
            <embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf">
        </div>
        ''', unsafe_allow_html=True)
        
    else:
        st.markdown("""
        <div class="a4-paper-container">
            <div style="text-align: center; margin-bottom: 30px;">    
                <h2 style="color: #1A365D; font-size: 28px; font-weight: 900; margin: 0;">คู่มือการใช้งานระบบ NCD Dashboard</h2>    
                <p style="color: #718096; font-size: 14px; margin-top: 5px;">มหาวิทยาลัยรังสิต | สำนักงานอธิการบดี</p>
            </div>
            
            <div class="a4-heading">1. บทนำภาพรวมระบบ</div>
            <p class="a4-text">    
                ระบบ <b>NCD Dashboard</b> ถูกพัฒนาขึ้นเพื่อใช้ในการวิเคราะห์ ติดตาม และประเมินความเสี่ยงโรคไม่ติดต่อเรื้อรัง (Non-Communicable Diseases) ได้แก่ โรคเบาหวาน โรคความดันโลหิตสูง และภาวะไขมันในเลือดสูง ของบุคลากรภายในมหาวิทยาลัยรังสิต เพื่อสนับสนุนการดูแลสุขภาพเชิงป้องกันที่มีประสิทธิภาพสูงสุด
            </p>
            
            <div class="a4-heading">2. ขั้นตอนการใช้งานฟังก์ชันหลัก</div>
            
            <div class="a4-subheading">2.1 การเข้าสู่หน้าแรก (Home Page)</div>
            <div class="a4-step-box">    
                <p class="a4-text" style="margin:0;">        
                    • แสดงผลสรุปภาพรวมและวิดีโอสาธิตการใช้งานระบบ<br>        
                    • สามารถกดปุ่ม <b>"เปิดใช้งาน NCD Dashboard"</b> สีส้มทองเพื่อเข้าสู่หน้าแดชบอร์ดหลักทันที    
                </p>
            </div>
            
            <div class="a4-subheading">2.2 การจัดการและอัปโหลดข้อมูลผลตรวจสุขภาพ</div>
            <div class="a4-step-box">    
                <p class="a4-text" style="margin:0;">        
                    1. ไปที่เมนู <b>Dashboard</b><br>        
                    2. เลื่อนลงมาที่ส่วน <i>"ระบบจัดการไฟล์ผลตรวจสุขภาพ"</i><br>        
                    3. อัปโหลดไฟล์ข้อมูล (รองรับไฟล์ CSV, PDF, JPG, PNG)<br>        
                    4. ระบุปีของข้อมูลให้ถูกต้อง จากนั้นกดปุ่ม <b>"บันทึกข้อมูล"</b> เพื่อให้ระบบทำการประมวลผลคลัสเตอร์สุขภาพ    
                </p>
            </div>
            
            <div class="a4-subheading">2.3 การเรียกดูรายงานเชิงวิเคราะห์</div>
            <div class="a4-step-box">    
                <p class="a4-text" style="margin:0;">        
                    • <b>ภาพรวม (Overview):</b> ตรวจสอบสถิติมิติต่างๆ ในภาพรวมของบุคลากร<br>        
                    • <b>รายหน่วยงาน (Department):</b> ค้นหาและดูข้อมูลเจาะลึกแยกตามสังกัดหน่วยงาน    
                </p>
            </div>
            
            <div class="a4-heading">3. การติดต่อและสนับสนุนทางเทคนิค</div>
            <p class="a4-text">    
                หากพบปัญหาในการใช้งานระบบหรือต้องการความช่วยเหลือเพิ่มเติม สามารถติดต่อได้ที่:<br>    
                <b>สถานที่ตั้ง:</b> ตึก 1 อาคารอาทิตย์อุไรรัตน์ ชั้น 10 มหาวิทยาลัยรังสิต<br>    
                <b>โทรศัพท์:</b> 02-791-5926 ถึง 02-791-5929<br>    
                <b>เว็บไซต์:</b> <a href="https://otp.rsu.ac.th" target="_blank" style="color: #2B6CB0; text-decoration: none;">https://otp.rsu.ac.th</a>
            </p>
        </div>
        """, unsafe_allow_html=True)