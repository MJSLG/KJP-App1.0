import streamlit as st
import pandas as pd
import tempfile
import os
from datetime import datetime
import math
import base64
from io import BytesIO

def check_expiry():
    """Check if the app has expired"""
    expiry_date = datetime(2025, 12, 10)
    current_date = datetime.now()
    
    if current_date > expiry_date:
        st.error("🚫 This application has expired as of December 10th, 2025.")
        st.error("📞 Pls contact App Developer")
        st.stop()

class KamalBerijuApp:
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        if 'kamal_data' not in st.session_state:
            st.session_state.kamal_data = []
        if 'kamal_editing_index' not in st.session_state:
            st.session_state.kamal_editing_index = None
    
    def parse_extent(self, extent_text, field_name=""):
        try:
            if not extent_text or extent_text in ["A-G-A", "", "0"]:
                return 0.0
            
            parts = extent_text.split('-')
            if len(parts) == 1:
                acres = float(parts[0].strip()) if parts[0].strip() else 0.0
                return acres * 40
            elif len(parts) == 2:
                acres = float(parts[0].strip()) if parts[0].strip() else 0.0
                gunta = float(parts[1].strip()) if parts[1].strip() else 0.0
                if gunta >= 40:
                    raise ValueError(f"{field_name} gunta must be less than 40.")
                return acres * 40 + gunta
            elif len(parts) == 3:
                acres = float(parts[0].strip()) if parts[0].strip() else 0.0
                gunta = float(parts[1].strip()) if parts[1].strip() else 0.0
                aana = float(parts[2].strip()) if parts[2].strip() else 0.0
                if gunta >= 40:
                    raise ValueError(f"{field_name} gunta must be less than 40.")
                if aana >= 16:
                    raise ValueError(f"{field_name} aana must be less than 16.")
                return acres * 40 + gunta + aana / 16.0
            else:
                raise ValueError(f"Invalid extent format for {field_name}. Use format like '12-15' or '12-15-13'.")
        except ValueError as e:
            if str(e).startswith(field_name):
                raise
            raise ValueError(f"Invalid input for {field_name} extent.")
    
    def parse_assessment(self, assessment_text):
        try:
            assessment = 0 if assessment_text in ["", "0"] else float(assessment_text.strip())
            if assessment < 0:
                raise ValueError("Assessment cannot be negative.")
            return assessment
        except ValueError:
            raise ValueError("Invalid assessment input.")
    
    def format_extent(self, gunta_float):
        if gunta_float <= 0:
            return "0-0-0"
        acres = int(gunta_float // 40)
        gunta_rem = gunta_float % 40
        gunta = int(gunta_rem)
        aana_rem = (gunta_rem - gunta) * 16
        aana = int(round(aana_rem))
        
        if aana >= 16:
            gunta += 1
            aana = 0
            if gunta >= 40:
                acres += 1
                gunta = 0
        
        return f"{acres}-{gunta}-{aana}"
    
    def get_extent_float(self, extent_str):
        if not extent_str or extent_str in ["0-0", "0-0-0", "", "-"]:
            return 0.0
        parts = extent_str.split("-")
        acres = float(parts[0].strip() or 0)
        gunta = float(parts[1].strip() or 0) if len(parts) > 1 else 0
        aana = float(parts[2].strip() or 0) if len(parts) > 2 else 0
        return acres * 40 + gunta + aana / 16
    
    def get_kjp_location_data(self):
        """Get location data from KJP app session state"""
        if 'kjp_location_data' in st.session_state:
            return st.session_state.kjp_location_data
        return {
            'district': '', 'taluka': '', 'hobli': '', 
            'village': '', 'kjp_share': ''
        }
    
    def generate_print_html(self):
        location_data = self.get_kjp_location_data()
        
        # Prepare table data
        table_rows = ""
        for record in st.session_state.kamal_data:
            if record.get("type") == "separator":
                table_rows += '<tr class="separator-row"><td colspan="10"></td></tr>'
            elif record.get("type") == "total":
                table_rows += '<tr class="total-row">'
                table_rows += f'<td>{record.get("AsIs_LandType", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_TotalExtent", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Kharab", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Cultivable", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Assessment", "")}</td>'
                table_rows += f'<td>{record.get("Amended_TotalExtent", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Kharab", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Cultivable", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Assessment", "")}</td>'
                table_rows += f'<td>{record.get("Remark", "")}</td>'
                table_rows += '</tr>'
            else:
                table_rows += '<tr class="data-row">'
                table_rows += f'<td>{record.get("AsIs_LandType", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_TotalExtent", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Kharab", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Cultivable", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Assessment", "")}</td>'
                table_rows += f'<td>{record.get("Amended_TotalExtent", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Kharab", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Cultivable", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Assessment", "")}</td>'
                table_rows += f'<td>{record.get("Remark", "")}</td>'
                table_rows += '</tr>'
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="kn">
        <head>
            <meta charset="UTF-8">
            <title>ಕಮಾಲ ಬೇರಿಜು - Print</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; text-align: center; background: #fff; }}
                .header {{ font-size: 20px; font-weight: bold; margin-bottom: 10px; color: #333; }}
                .location-info {{ display: flex; justify-content: space-between; margin: 15px 0; font-size: 13px; color: #555; background: #f0f0f0; padding: 8px; border-radius: 4px; }}
                .location-info div {{ margin: 0 8px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                th, td {{ border: 1px solid #999; padding: 6px; text-align: center; }}
                th.section-header {{ background-color: #d0d0d0; font-size: 12px; font-weight: bold; }}
                th.column-header {{ background-color: #e0e0e0; font-weight: bold; font-size: 13px; }}
                .data-row:nth-child(even) {{ background-color: #f5f5f5; }}
                .data-row:nth-child(odd) {{ background-color: #ffffff; }}
                .total-row {{ background-color: #e0e0e0; font-weight: bold; }}
                .separator-row td {{ border: none; height: 8px; background-color: #d3d3d3; }}
                .signature-row {{ display: flex; justify-content: space-between; gap: 20px; margin: 20px auto 10px; width: 95%; flex-wrap: nowrap; }}
                .signature-row p {{ margin: 0; font-size: 14px; border-top: 1px solid #000; padding-top: 10px; width: 180px; text-align: center; }}
                @media print {{
                    body {{ margin: 10px; }}
                    table {{ page-break-inside: auto; }}
                    tr {{ page-break-inside: avoid; page-break-after: auto; }}
                    thead {{ display: table-header-group; }}
                    @page {{
                        size: A4 landscape;
                        margin: 10mm;
                    }}
                }}
                .print-controls {{ margin: 15px 0; text-align: center; }}
                .print-btn, .close-btn {{ 
                    padding: 8px 16px; margin: 0 10px; font-size: 14px; cursor: pointer; 
                    border: none; border-radius: 4px; color: white; 
                }}
                .print-btn {{ background-color: #4CAF50; }}
                .close-btn {{ background-color: #f44336; }}
            </style>
        </head>
        <body>
            <div class="print-controls">
                <button class="print-btn" onclick="window.print()">Print</button>
                <button class="close-btn" onclick="window.close()">Close</button>
            </div>
            <div class="header">ಕರ್ನಾಟಕ ಸರ್ಕಾರ</div>
            <div class="header">ಕಮಾಲ ಬೇರಿಜು</div>
            
            <div class="location-info">
                <div>ಗ್ರಾಮ: {location_data['village']}</div>
                <div>ಹೋಬಳಿ: {location_data['hobli']}</div>
                <div>ತಾಲೂಕು: {location_data['taluka']}</div>
                <div>ಜಿಲ್ಲೆ: {location_data['district']}</div>
                <div>ಕ.ಜ.ಪ ಶೇ.ನಂ.: {location_data['kjp_share']}</div>
            </div>
            
            <table>
                <thead>
                    <tr class="section-header">
                        <th colspan="5">ಈಗಿನ ಪ್ರಕಾರ</th>
                        <th colspan="5">ದುರಸ್ತಿ ಪ್ರಕಾರ</th>
                    </tr>
                    <tr class="column-header">
                        <th>ಜಮೀನ ತರಹೆ</th>
                        <th>ಒಟ್ಟು ಕ್ಷೇತ್ರ</th>
                        <th>ಖರಾಬ</th>
                        <th>ಸಾಗು ಕ್ಷೇತ್ರ</th>
                        <th>ಆಕಾರ (₹)</th>
                        <th>ಒಟ್ಟು</th>
                        <th>ಖರಾಬ</th>
                        <th>ಸಾಗು ಕ್ಷೇತ್ರ</th>
                        <th>ಆಕಾರ (₹)</th>
                        <th>ಷರಾ</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            
            <div class="signature-row">
                <p>ದುರಸ್ತಿ ಭೂಮಾಪಕರ ಸಹಿ</p>
                <p>ತಪಾಸಕರ ಸಹಿ</p>
                <p>ಭೂ.ದಾ.ಸ.ನಿ {location_data['taluka']} ಸಹಿ</p>
                <p>ಭೂ.ದಾ.ಉ.ನಿ {location_data['district']} ಸಹಿ</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def render(self):
        # Check expiry before rendering anything
        check_expiry()
        
        # Stylish modern heading with smaller font
        st.markdown(
            """
            <div style='
                text-align: center; 
                margin-top: 0; 
                padding-top: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            '>
                <h1 style='
                    color: white; 
                    font-size: 24px; 
                    font-weight: 700;
                    margin: 0;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                    font-family: "Arial", sans-serif;
                '>M. J. Sikandar's KJP App</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Location inputs like original app - in main content area
        st.subheader("Location Information")
        loc_col1, loc_col2, loc_col3, loc_col4, loc_col5 = st.columns(5)
        
        with loc_col1:
            district = st.text_input("ಜಿಲ್ಲೆ", placeholder="Enter District", 
                                   value=st.session_state.kjp_location_data['district'],
                                   key="kamal_district")
            st.session_state.kjp_location_data['district'] = district
        
        with loc_col2:
            taluka = st.text_input("ತಾಲೂಕು", placeholder="Enter Taluka",
                                 value=st.session_state.kjp_location_data['taluka'],
                                 key="kamal_taluka")
            st.session_state.kjp_location_data['taluka'] = taluka
        
        with loc_col3:
            hobli = st.text_input("ಹೋಬಳಿ", placeholder="Enter Hobli",
                                value=st.session_state.kjp_location_data['hobli'],
                                key="kamal_hobli")
            st.session_state.kjp_location_data['hobli'] = hobli
        
        with loc_col4:
            village = st.text_input("ಗ್ರಾಮ", placeholder="Enter Village",
                                  value=st.session_state.kjp_location_data['village'],
                                  key="kamal_village")
            st.session_state.kjp_location_data['village'] = village
        
        with loc_col5:
            kjp_share = st.text_input("ಕ.ಜ.ಪ ಶೇ.ನಂ.", placeholder="Enter KJP Share",
                                    value=st.session_state.kjp_location_data['kjp_share'],
                                    key="kamal_kjp_share")
            st.session_state.kjp_location_data['kjp_share'] = kjp_share
        
        # Input form - Matching original layout
        st.subheader("Enter Record Details")
        
        # First row of inputs
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("**ಜಮೀನ ತರಹೆ**")
            land_type = st.selectbox("ಜಮೀನ ತರಹೆ", ["ಖುಷ್ಕಿ", "ತರಿ", "ಬಾಗಾಯತ"], label_visibility="collapsed", key="land_type")
        
        with col2:
            st.markdown("**ಒಟ್ಟು ಕ್ಷೇತ್ರ**")
            total_extent = st.text_input("ಒಟ್ಟು ಕ್ಷೇತ್ರ", placeholder="A-G-A", label_visibility="collapsed", key="total_extent")
        
        with col3:
            st.markdown("**ಖರಾಬ**")
            kharab_extent = st.text_input("ಖರಾಬ", placeholder="A-G-A", label_visibility="collapsed", key="kharab_extent")
        
        with col4:
            st.markdown("**ಆಕಾರ**")
            assessment = st.text_input("ಆಕಾರ", placeholder="Enter Assessment", label_visibility="collapsed", key="assessment")
        
        # Second row of inputs
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            st.markdown("**ಕಜಪ ಕ್ಷೇತ್ರ**")
            kjp_extent = st.text_input("ಕಜಪ ಕ್ಷೇತ್ರ", placeholder="A-G-A", label_visibility="collapsed", key="kjp_extent")
        
        with col6:
            st.markdown("**ಆಕಾರ**")
            kjp_assessment = st.text_input("ಆಕಾರ", placeholder="Enter Assessment", label_visibility="collapsed", key="kjp_assessment")
        
        with col7:
            st.markdown("**ಜಮೀನ ತರಹೆ**")
            kjp_land_type = st.selectbox("ಜಮೀನ ತರಹೆ", ["ಖುಷ್ಕಿ", "ತರಿ", "ಬಾಗಾಯತ"], label_visibility="collapsed", key="kjp_land_type")
        
        with col8:
            st.markdown("&nbsp;")
            # Empty space since Add button is moved to buttons row
        
        # Action buttons - Add button in buttons row like KJP app
        st.markdown("---")
        col9, col10, col11, col12, col13 = st.columns(5)
        
        with col9:
            add_clicked = st.button("Add", use_container_width=True, key="add_btn")
        
        with col10:
            edit_clicked = st.button("Edit", use_container_width=True, key="edit_btn")
        
        with col11:
            delete_clicked = st.button("Delete", use_container_width=True, key="delete_btn")
        
        with col12:
            total_clicked = st.button("Total", use_container_width=True, key="total_btn")
        
        with col13:
            print_clicked = st.button("Print", use_container_width=True, key="print_btn")
        
        # Handle Add button
        if add_clicked:
            try:
                total_extent_val = self.parse_extent(total_extent, "Total Extent")
                kharab_extent_val = self.parse_extent(kharab_extent, "Kharab")
                assessment_val = self.parse_assessment(assessment)
                kjp_extent_val = self.parse_extent(kjp_extent, "KJP Extent")
                kjp_assessment_val = self.parse_assessment(kjp_assessment)
                
                if not land_type:
                    st.error("Land type is mandatory.")
                    return
                
                if kharab_extent_val > total_extent_val:
                    st.error("Kharab extent cannot exceed total extent.")
                    return
                
                if kjp_extent_val > 0 and not kjp_land_type:
                    st.error("KJP land type is mandatory when KJP extent is provided.")
                    return
                
                cultivable_extent = total_extent_val - kharab_extent_val
                amended_total_extent = total_extent_val
                amended_kharab_extent = kharab_extent_val
                amended_cultivable_extent = cultivable_extent
                amended_assessment = assessment_val
                remark = "-"

                if kjp_extent_val > 0:
                    if land_type == kjp_land_type:
                        amended_kharab_extent = kharab_extent_val + kjp_extent_val
                        amended_cultivable_extent = total_extent_val - amended_kharab_extent
                        amended_assessment = assessment_val - kjp_assessment_val
                        remark = self.format_extent(kjp_extent_val)
                    else:
                        remark = "-"
                
                record = {
                    "AsIs_LandType": land_type,
                    "AsIs_TotalExtent": self.format_extent(total_extent_val),
                    "AsIs_Kharab": self.format_extent(kharab_extent_val),
                    "AsIs_Cultivable": self.format_extent(cultivable_extent),
                    "AsIs_Assessment": f"{assessment_val:.2f}" if assessment_val > 0 else "",
                    "Amended_TotalExtent": self.format_extent(amended_total_extent),
                    "Amended_Kharab": self.format_extent(amended_kharab_extent),
                    "Amended_Cultivable": self.format_extent(amended_cultivable_extent),
                    "Amended_Assessment": f"{amended_assessment:.2f}" if amended_assessment != 0 else "",
                    "Remark": remark,
                    "type": "data"
                }
                
                st.session_state.kamal_data.append(record)
                st.success("Record added successfully!")
                st.rerun()
                
            except ValueError as e:
                st.error(str(e))
        
        # Handle other buttons
        if edit_clicked:
            self.edit_record()
        
        if delete_clicked:
            self.delete_record()
        
        if total_clicked:
            self.update_totals()
        
        if print_clicked:
            self.print_data()
        
        # Display data table
        st.markdown("---")
        if st.session_state.kamal_data:
            # Prepare display data
            display_data = []
            for record in st.session_state.kamal_data:
                if record.get("type") in ["data", "total"]:
                    display_record = {
                        "ಜಮೀನ ತರಹೆ": record["AsIs_LandType"],
                        "ಒಟ್ಟು ಕ್ಷೇತ್ರ": record["AsIs_TotalExtent"],
                        "ಖರಾಬ": record["AsIs_Kharab"],
                        "ಸಾಗು ಕ್ಷೇತ್ರ": record["AsIs_Cultivable"],
                        "ಆಕಾರ (₹)": record["AsIs_Assessment"],
                        "ದುರಸ್ತಿ_ಒಟ್ಟು": record["Amended_TotalExtent"],
                        "ದುರಸ್ತಿ_ಖರಾಬ": record["Amended_Kharab"],
                        "ದುರಸ್ತಿ_ಸಾಗು": record["Amended_Cultivable"],
                        "ದುರಸ್ತಿ_ಆಕಾರ": record["Amended_Assessment"],
                        "ಷರಾ": record["Remark"]
                    }
                    display_data.append(display_record)
            
            if display_data:
                df = pd.DataFrame(display_data)
                st.dataframe(df, use_container_width=True)
        else:
            st.info("No records added yet.")
    
    def edit_record(self):
        if not st.session_state.kamal_data:
            st.warning("No records to edit.")
            return
        
        # Filter only data records (not separators or totals)
        data_records = [i for i, record in enumerate(st.session_state.kamal_data) if record.get("type") == "data"]
        
        if not data_records:
            st.warning("No data records to edit.")
            return
        
        selected_index = st.selectbox("Select record to edit:", data_records, format_func=lambda x: f"Record {x+1}")
        
        if st.button("Load for Editing", key="load_edit"):
            st.session_state.kamal_editing_index = selected_index
            self.show_edit_form()
    
    def show_edit_form(self):
        if st.session_state.kamal_editing_index is None:
            return
        
        record = st.session_state.kamal_data[st.session_state.kamal_editing_index]
        
        st.subheader("Edit Record")
        
        with st.form("edit_kamal_form"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                land_type = st.selectbox("ಜಮೀನ ತರಹೆ", ["ಖುಷ್ಕಿ", "ತರಿ", "ಬಾಗಾಯತ"], 
                                       index=["ಖುಷ್ಕಿ", "ತರಿ", "ಬಾಗಾಯತ"].index(record["AsIs_LandType"]),
                                       key="edit_land_type")
                total_extent = st.text_input("ಒಟ್ಟು ಕ್ಷೇತ್ರ", value=record["AsIs_TotalExtent"], key="edit_total_extent")
            
            with col2:
                kharab_extent = st.text_input("ಖರಾಬ", value=record["AsIs_Kharab"], key="edit_kharab_extent")
                assessment = st.text_input("ಆಕಾರ", value=record["AsIs_Assessment"], key="edit_assessment")
            
            with col3:
                # Extract KJP extent from remark
                kjp_extent = "0-0-0" if record["Remark"] == "-" else record["Remark"]
                kjp_extent_input = st.text_input("ಕಜಪ ಕ್ಷೇತ್ರ", value=kjp_extent, key="edit_kjp_extent")
                
                # Calculate KJP assessment
                as_is_assessment = float(record["AsIs_Assessment"] or 0)
                amended_assessment = float(record["Amended_Assessment"] or 0)
                kjp_assessment_val = as_is_assessment - amended_assessment
                kjp_assessment = st.text_input("ಆಕಾರ", value=f"{kjp_assessment_val:.2f}", key="edit_kjp_assessment")
            
            with col4:
                kjp_land_type = st.selectbox("ಜಮೀನ ತರಹೆ", ["ಖುಷ್ಕಿ", "ತರಿ", "ಬಾಗಾಯತ"], 
                                           key="edit_kjp_land_type_select")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                save_clicked = st.form_submit_button("Save", use_container_width=True)
            
            with col_cancel:
                cancel_clicked = st.form_submit_button("Cancel", use_container_width=True)
            
            if save_clicked:
                try:
                    total_extent_val = self.parse_extent(total_extent, "Total Extent")
                    kharab_extent_val = self.parse_extent(kharab_extent, "Kharab")
                    assessment_val = self.parse_assessment(assessment)
                    kjp_extent_val = self.parse_extent(kjp_extent_input, "KJP Extent")
                    kjp_assessment_val = self.parse_assessment(kjp_assessment)
                    
                    if not land_type:
                        st.error("Land type is mandatory.")
                        return
                    
                    if kharab_extent_val > total_extent_val:
                        st.error("Kharab extent cannot exceed total extent.")
                        return
                    
                    if kjp_extent_val > 0 and not kjp_land_type:
                        st.error("KJP land type is mandatory when KJP extent is provided.")
                        return
                    
                    cultivable_extent = total_extent_val - kharab_extent_val
                    amended_total_extent = total_extent_val
                    amended_kharab_extent = kharab_extent_val
                    amended_cultivable_extent = cultivable_extent
                    amended_assessment = assessment_val
                    remark = "-"
                    
                    if kjp_extent_val > 0:
                        if land_type == kjp_land_type:
                            amended_kharab_extent = kharab_extent_val + kjp_extent_val
                            amended_cultivable_extent = total_extent_val - amended_kharab_extent
                            amended_assessment = assessment_val - kjp_assessment_val
                            remark = self.format_extent(kjp_extent_val)
                        else:
                            remark = "-"
                    
                    updated_record = {
                        "AsIs_LandType": land_type,
                        "AsIs_TotalExtent": self.format_extent(total_extent_val),
                        "AsIs_Kharab": self.format_extent(kharab_extent_val),
                        "AsIs_Cultivable": self.format_extent(cultivable_extent),
                        "AsIs_Assessment": f"{assessment_val:.2f}" if assessment_val > 0 else "",
                        "Amended_TotalExtent": self.format_extent(amended_total_extent),
                        "Amended_Kharab": self.format_extent(amended_kharab_extent),
                        "Amended_Cultivable": self.format_extent(amended_cultivable_extent),
                        "Amended_Assessment": f"{amended_assessment:.2f}" if amended_assessment != 0 else "",
                        "Remark": remark,
                        "type": "data"
                    }
                    
                    st.session_state.kamal_data[st.session_state.kamal_editing_index] = updated_record
                    st.session_state.kamal_editing_index = None
                    st.success("Record updated successfully!")
                    st.rerun()
                    
                except ValueError as e:
                    st.error(str(e))
            
            if cancel_clicked:
                st.session_state.kamal_editing_index = None
                st.rerun()
    
    def delete_record(self):
        if not st.session_state.kamal_data:
            st.warning("No records to delete.")
            return
        
        # Filter only data records (not separators or totals)
        data_records = [i for i, record in enumerate(st.session_state.kamal_data) if record.get("type") == "data"]
        
        if not data_records:
            st.warning("No data records to delete.")
            return
        
        selected_index = st.selectbox("Select record to delete:", data_records, format_func=lambda x: f"Record {x+1}", key="delete_select")
        
        if st.button("Delete Selected Record", key="confirm_delete"):
            # Adjust index since we're showing only data records
            actual_index = data_records[selected_index]
            deleted_record = st.session_state.kamal_data.pop(actual_index)
            st.success("Record deleted successfully!")
            st.rerun()
    
    def update_totals(self):
        if not st.session_state.kamal_data:
            st.warning("No records to calculate totals.")
            return
        
        # Remove existing totals and separators
        st.session_state.kamal_data = [record for record in st.session_state.kamal_data if record.get("type") not in ["separator", "total"]]
        
        # Add separator
        separator_record = {f"AsIs_{col}": "-" for col in ["LandType", "TotalExtent", "Kharab", "Cultivable", "Assessment"]}
        separator_record.update({f"Amended_{col}": "-" for col in ["TotalExtent", "Kharab", "Cultivable", "Assessment"]})
        separator_record["Remark"] = "-"
        separator_record["type"] = "separator"
        st.session_state.kamal_data.append(separator_record)
        
        # Calculate totals
        total_columns = {
            "AsIs_TotalExtent": 0,
            "AsIs_Kharab": 0,
            "AsIs_Cultivable": 0,
            "AsIs_Assessment": 0,
            "Amended_TotalExtent": 0,
            "Amended_Kharab": 0,
            "Amended_Cultivable": 0,
            "Amended_Assessment": 0
        }
        
        data_records = [record for record in st.session_state.kamal_data if record.get("type") == "data"]
        
        for record in data_records:
            for col in total_columns:
                if col in ["AsIs_TotalExtent", "AsIs_Kharab", "AsIs_Cultivable", "Amended_TotalExtent", "Amended_Kharab", "Amended_Cultivable"]:
                    if record[col] and record[col] != "0-0-0":
                        total_columns[col] += self.get_extent_float(record[col])
                else:
                    if record[col]:
                        total_columns[col] += float(record[col])
        
        # Add total row
        total_record = {
            "AsIs_LandType": "Total",
            "AsIs_TotalExtent": self.format_extent(total_columns["AsIs_TotalExtent"]) if total_columns["AsIs_TotalExtent"] > 0 else "0-0-0",
            "AsIs_Kharab": self.format_extent(total_columns["AsIs_Kharab"]) if total_columns["AsIs_Kharab"] > 0 else "0-0-0",
            "AsIs_Cultivable": self.format_extent(total_columns["AsIs_Cultivable"]) if total_columns["AsIs_Cultivable"] > 0 else "0-0-0",
            "AsIs_Assessment": f"{total_columns['AsIs_Assessment']:.2f}" if total_columns['AsIs_Assessment'] > 0 else "",
            "Amended_TotalExtent": self.format_extent(total_columns["Amended_TotalExtent"]) if total_columns["Amended_TotalExtent"] > 0 else "0-0-0",
            "Amended_Kharab": self.format_extent(total_columns["Amended_Kharab"]) if total_columns["Amended_Kharab"] > 0 else "0-0-0",
            "Amended_Cultivable": self.format_extent(total_columns["Amended_Cultivable"]) if total_columns["Amended_Cultivable"] > 0 else "0-0-0",
            "Amended_Assessment": f"{total_columns['Amended_Assessment']:.2f}" if total_columns['Amended_Assessment'] > 0 else "",
            "Remark": "-",
            "type": "total"
        }
        
        st.session_state.kamal_data.append(total_record)
        st.success("Totals updated successfully!")
        st.rerun()
    
    def print_data(self):
        if not st.session_state.kamal_data:
            st.warning("No data available to print.")
            return
        
        location_data = self.get_kjp_location_data()
        if not all([location_data['village'], location_data['taluka'], location_data['district'], location_data['kjp_share']]):
            st.warning("Please enter location details before printing.")
            return
        
        html_content = self.generate_print_html()
        
        # Improved JS: Open popup, load content, no auto-print
        js = f"""
        <script>
            function openPreview() {{
                var htmlContent = `{html_content}`;
                var previewWindow = window.open('', '_blank', 'width=1000,height=600,resizable=yes,scrollbars=yes');
                if (previewWindow) {{
                    previewWindow.document.write(htmlContent);
                    previewWindow.document.close();
                    previewWindow.focus();  // Bring to front
                }} else {{
                    alert('Popup blocked! Please allow popups for this site.');
                }}
            }}
            openPreview();
        </script>
        """
        st.components.v1.html(js, height=0)
        st.success("Print preview opened in a popup window!")


class KJPLandSurveyApp:
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        if 'kjp_data' not in st.session_state:
            st.session_state.kjp_data = []
        if 'kjp_editing_index' not in st.session_state:
            st.session_state.kjp_editing_index = None
        if 'ex_kjp_mode' not in st.session_state:
            st.session_state.ex_kjp_mode = False
        if 'kjp_location_data' not in st.session_state:
            st.session_state.kjp_location_data = {
                'district': '', 'taluka': '', 'hobli': '', 
                'village': '', 'kjp_share': ''
            }
        if 'current_survey_no' not in st.session_state:
            st.session_state.current_survey_no = ""
        if 'current_hissa_no' not in st.session_state:
            st.session_state.current_hissa_no = 1
    
    def parse_extent(self, extent_text, field_name=""):
        try:
            if not extent_text or extent_text in ["A-G-A", "", "0"]:
                return 0.0
            
            parts = extent_text.split('-')
            if len(parts) == 1:
                acres = float(parts[0].strip()) if parts[0].strip() else 0.0
                return acres * 40
            elif len(parts) == 2:
                acres = float(parts[0].strip()) if parts[0].strip() else 0.0
                gunta = float(parts[1].strip()) if parts[1].strip() else 0.0
                if gunta >= 40:
                    raise ValueError(f"{field_name} gunta must be less than 40.")
                return acres * 40 + gunta
            elif len(parts) == 3:
                acres = float(parts[0].strip()) if parts[0].strip() else 0.0
                gunta = float(parts[1].strip()) if parts[1].strip() else 0.0
                aana = float(parts[2].strip()) if parts[2].strip() else 0.0
                if gunta >= 40:
                    raise ValueError(f"{field_name} gunta must be less than 40.")
                if aana >= 16:
                    raise ValueError(f"{field_name} aana must be less than 16.")
                return acres * 40 + gunta + aana / 16.0
            else:
                raise ValueError(f"Invalid extent format for {field_name}. Use format like '12-15' or '12-15-13'.")
        except ValueError as e:
            if str(e).startswith(field_name):
                raise
            raise ValueError(f"Invalid input for {field_name} extent.")
    
    def parse_rate(self, rate_text):
        try:
            rate = 0 if rate_text in ["", "0"] else float(rate_text.strip())
            if rate < 0:
                raise ValueError("Rate cannot be negative.")
            return rate
        except ValueError:
            raise ValueError("Invalid rate input.")
    
    def format_extent(self, gunta_float):
        if gunta_float <= 0:
            return "0-0-0"
        acres = int(gunta_float // 40)
        gunta_rem = gunta_float % 40
        gunta = int(gunta_rem)
        aana_rem = (gunta_rem - gunta) * 16
        aana = int(round(aana_rem))
        
        if aana >= 16:
            gunta += 1
            aana = 0
            if gunta >= 40:
                acres += 1
                gunta = 0
        
        return f"{acres}-{gunta}-{aana}"
    
    def get_extent_float(self, extent_str):
        if not extent_str or extent_str in ["0-0", "0-0-0", "", "-"]:
            return 0.0
        parts = extent_str.split("-")
        acres = float(parts[0].strip() or 0)
        gunta = float(parts[1].strip() or 0) if len(parts) > 1 else 0
        aana = float(parts[2].strip() or 0) if len(parts) > 2 else 0
        return acres * 40 + gunta + aana / 16
    
    def generate_print_html(self):
        location_data = st.session_state.kjp_location_data
        
        # Prepare table data
        table_rows = ""
        for record in st.session_state.kjp_data:
            if record.get("type") == "separator":
                table_rows += '<tr class="separator-row"><td colspan="12"></td></tr>'
            elif record.get("type") == "total":
                table_rows += '<tr class="total-row">'
                table_rows += f'<td>{record.get("AsIs_SurveyHissa", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_TotalExtent", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Kharab", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Cultivable", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Rate", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Assessment", "")}</td>'
                table_rows += f'<td>{record.get("Amended_SurveyHissa", "")}</td>'
                table_rows += f'<td>{record.get("Amended_TotalExtent", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Kharab", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Cultivable", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Rate", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Assessment", "")}</td>'
                table_rows += '</tr>'
            elif record.get("type") == "kjp_row":
                # KJP Row (B row) with merged cells
                table_rows += '<tr class="kjp-row">'
                table_rows += f'<td></td>'  # AsIs_SurveyHissa
                table_rows += f'<td></td>'  # AsIs_TotalExtent
                table_rows += f'<td></td>'  # AsIs_Kharab
                table_rows += f'<td></td>'  # AsIs_Cultivable
                table_rows += f'<td></td>'  # AsIs_Rate
                table_rows += f'<td></td>'  # AsIs_Assessment
                table_rows += f'<td>{record.get("Amended_SurveyHissa", "")}</td>'
                table_rows += f'<td>{record.get("Amended_TotalExtent", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Kharab", "")}</td>'
                table_rows += f'<td colspan="3">ಬಿನ್ ಶೇತ್ಕಿ ಕಡೆಗೆ ಹೋಗಿದೆ</td>'
                table_rows += '</tr>'
            elif record.get("type") == "ex_kjp":
                # Ex KJP row with merged cells
                table_rows += '<tr class="kjp-row">'
                table_rows += f'<td>{record.get("AsIs_SurveyHissa", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_TotalExtent", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Kharab", "")}</td>'
                table_rows += f'<td colspan="3"></td>'
                table_rows += f'<td>{record.get("Amended_SurveyHissa", "")}</td>'
                table_rows += f'<td>{record.get("Amended_TotalExtent", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Kharab", "")}</td>'
                table_rows += f'<td colspan="3">{record.get("Amended_Cultivable", "")}</td>'
                table_rows += '</tr>'
            else:
                # Normal data row
                table_rows += '<tr class="data-row">'
                table_rows += f'<td>{record.get("AsIs_SurveyHissa", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_TotalExtent", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Kharab", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Cultivable", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Rate", "")}</td>'
                table_rows += f'<td>{record.get("AsIs_Assessment", "")}</td>'
                table_rows += f'<td>{record.get("Amended_SurveyHissa", "")}</td>'
                table_rows += f'<td>{record.get("Amended_TotalExtent", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Kharab", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Cultivable", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Rate", "")}</td>'
                table_rows += f'<td>{record.get("Amended_Assessment", "")}</td>'
                table_rows += '</tr>'
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="kn">
        <head>
            <meta charset="UTF-8">
            <title>ಕಜಪ ಪತ್ರಿಕೆ - Print</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; text-align: center; background: #fff; }}
                .header {{ font-size: 20px; font-weight: bold; margin-bottom: 10px; color: #333; }}
                .location-info {{ display: flex; justify-content: space-between; margin: 15px 0; font-size: 13px; color: #555; background: #f0f0f0; padding: 8px; border-radius: 4px; }}
                .location-info div {{ margin: 0 8px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
                th, td {{ border: 1px solid #999; padding: 6px; text-align: center; }}
                th.section-header {{ background-color: #d0d0d0; font-size: 12px; font-weight: bold; }}
                th.column-header {{ background-color: #e0e0e0; font-weight: bold; font-size: 13px; }}
                .data-row:nth-child(even) {{ background-color: #f5f5f5; }}
                .data-row:nth-child(odd) {{ background-color: #ffffff; }}
                .total-row {{ background-color: #e0e0e0; font-weight: bold; }}
                .kjp-row {{ background-color: #FFE0B2; font-weight: bold; }}
                .separator-row td {{ border: none; height: 8px; background-color: #d3d3d3; }}
                .signature-row {{ display: flex; justify-content: space-between; gap: 20px; margin: 20px auto 10px; width: 95%; flex-wrap: nowrap; }}
                .signature-row p {{ margin: 0; font-size: 14px; border-top: 1px solid #000; padding-top: 10px; width: 180px; text-align: center; }}
                @media print {{
                    body {{ margin: 10px; }}
                    table {{ page-break-inside: auto; }}
                    tr {{ page-break-inside: avoid; page-break-after: auto; }}
                    thead {{ display: table-header-group; }}
                    @page {{
                        size: A4 landscape;
                        margin: 10mm;
                    }}
                }}
                .print-controls {{ margin: 15px 0; text-align: center; }}
                .print-btn, .close-btn {{ 
                    padding: 8px 16px; margin: 0 10px; font-size: 14px; cursor: pointer; 
                    border: none; border-radius: 4px; color: white; 
                }}
                .print-btn {{ background-color: #4CAF50; }}
                .close-btn {{ background-color: #f44336; }}
            </style>
        </head>
        <body>
            <div class="print-controls">
                <button class="print-btn" onclick="window.print()">Print</button>
                <button class="close-btn" onclick="window.close()">Close</button>
            </div>
            <div class="header">ಕರ್ನಾಟಕ ಸರ್ಕಾರ</div>
            <div class="header">ಕಜಪ ಪತ್ರಿಕೆ</div>
            
            <div class="location-info">
                <div>ಗ್ರಾಮ: {location_data['village']}</div>
                <div>ಹೋಬಳಿ: {location_data['hobli']}</div>
                <div>ತಾಲೂಕು: {location_data['taluka']}</div>
                <div>ಜಿಲ್ಲೆ: {location_data['district']}</div>
                <div>ಕ.ಜ.ಪ ಶೇ.ನಂ.: {location_data['kjp_share']}</div>
            </div>
            
            <table>
                <thead>
                    <tr class="section-header">
                        <th colspan="6">ಈಗಿನ ಪ್ರಕಾರ</th>
                        <th colspan="6">ದುರಸ್ತಿ ಪ್ರಕಾರ</th>
                    </tr>
                    <tr class="column-header">
                        <th>ಸ.ನಂ/ಹಿ.ನಂ.</th>
                        <th>ಒಟ್ಟು ಕ್ಷೇತ್ರ</th>
                        <th>ಖರಾಬ</th>
                        <th>ಸಾಗು ಕ್ಷೇತ್ರ</th>
                        <th>ದರ</th>
                        <th>ಆಕಾರ (₹)</th>
                        <th>ಸ.ನಂ/ಹಿ.ನಂ.</th>
                        <th>ಒಟ್ಟು ಕ್ಷೇತ್ರ</th>
                        <th>ಖರಾಬ</th>
                        <th>ಸಾಗು ಕ್ಷೇತ್ರ</th>
                        <th>ದರ</th>
                        <th>ಆಕಾರ (₹)</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
            
            <div class="signature-row">
                <p>ದುರಸ್ತಿ ಭೂಮಾಪಕರ ಸಹಿ</p>
                <p>ತಪಾಸಕರ ಸಹಿ</p>
                <p>ಭೂ.ದಾ.ಸ.ನಿ {location_data['taluka']} ಸಹಿ</p>
                <p>ಭೂ.ದಾ.ಉ.ನಿ {location_data['district']} ಸಹಿ</p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def render(self):
        # Check expiry before rendering anything
        check_expiry()
        
        # Stylish modern heading with smaller font
        st.markdown(
            """
            <div style='
                text-align: center; 
                margin-top: 0; 
                padding-top: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            '>
                <h1 style='
                    color: white; 
                    font-size: 24px; 
                    font-weight: 700;
                    margin: 0;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                    font-family: "Arial", sans-serif;
                '>M. J. Sikandar's KJP App</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Location inputs like original app - in main content area
        st.subheader("Location Information")
        loc_col1, loc_col2, loc_col3, loc_col4, loc_col5 = st.columns(5)
        
        with loc_col1:
            district = st.text_input("ಜಿಲ್ಲೆ", placeholder="Enter District", 
                                   value=st.session_state.kjp_location_data['district'],
                                   key="kjp_district")
            st.session_state.kjp_location_data['district'] = district
        
        with loc_col2:
            taluka = st.text_input("ತಾಲೂಕು", placeholder="Enter Taluka",
                                 value=st.session_state.kjp_location_data['taluka'],
                                 key="kjp_taluka")
            st.session_state.kjp_location_data['taluka'] = taluka
        
        with loc_col3:
            hobli = st.text_input("ಹೋಬಳಿ", placeholder="Enter Hobli",
                                value=st.session_state.kjp_location_data['hobli'],
                                key="kjp_hobli")
            st.session_state.kjp_location_data['hobli'] = hobli
        
        with loc_col4:
            village = st.text_input("ಗ್ರಾಮ", placeholder="Enter Village",
                                  value=st.session_state.kjp_location_data['village'],
                                  key="kjp_village")
            st.session_state.kjp_location_data['village'] = village
        
        with loc_col5:
            kjp_share = st.text_input("ಕ.ಜ.ಪ ಶೇ.ನಂ.", placeholder="Enter KJP Share",
                                    value=st.session_state.kjp_location_data['kjp_share'],
                                    key="kjp_kjp_share")
            st.session_state.kjp_location_data['kjp_share'] = kjp_share
        
        # Ex KJP mode toggle
        st.subheader("Record Details")
        col_ex1, col_ex2 = st.columns([1, 4])
        with col_ex1:
            ex_kjp_mode = st.checkbox("Ex KJP", value=st.session_state.ex_kjp_mode)
            st.session_state.ex_kjp_mode = ex_kjp_mode
        
        with col_ex2:
            if ex_kjp_mode:
                ex_kjp_input = st.text_input("Ex KJP Input", placeholder="Enter Ex KJP details")
        
        # Input form with survey number handling
        if not ex_kjp_mode:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown("**ಸ.ನಂ/ಹಿ.ನಂ.**")
                survey_input = st.text_input("ಸ.ನಂ/ಹಿ.ನಂ.", placeholder="Enter Survey No", label_visibility="collapsed", 
                                           key="survey_input")
                
                # Auto-generate survey/hissa number with auto-increment
                if survey_input and "/" not in survey_input:
                    # New survey number entered
                    st.session_state.current_survey_no = survey_input
                    st.session_state.current_hissa_no = 1
                    survey_hissa = f"{survey_input}/1"
                elif st.session_state.current_survey_no:
                    # Auto-increment hissa number for each new record
                    if st.session_state.kjp_data:
                        # Find the highest hissa number for current survey
                        data_records = [r for r in st.session_state.kjp_data if r.get("type") == "data"]
                        if data_records:
                            last_record = data_records[-1]
                            if last_record.get("AsIs_SurveyHissa", "").startswith(st.session_state.current_survey_no):
                                try:
                                    last_hissa = int(last_record.get("AsIs_SurveyHissa", "").split("/")[-1])
                                    st.session_state.current_hissa_no = last_hissa + 1
                                except:
                                    st.session_state.current_hissa_no += 1
                            else:
                                st.session_state.current_hissa_no += 1
                        else:
                            st.session_state.current_hissa_no += 1
                    else:
                        st.session_state.current_hissa_no += 1
                    
                    survey_hissa = f"{st.session_state.current_survey_no}/{st.session_state.current_hissa_no}"
                else:
                    survey_hissa = survey_input
                
                if survey_input:
                    st.info(f"Current: {survey_hissa}")
                
            with col2:
                st.markdown("**ಒಟ್ಟು ಕ್ಷೇತ್ರ**")
                total_extent = st.text_input("ಒಟ್ಟು ಕ್ಷೇತ್ರ", placeholder="A-G-A", label_visibility="collapsed", key="total_extent")
            
            with col3:
                st.markdown("**ಖರಾಬ**")
                kharab_extent = st.text_input("ಖರಾಬ", placeholder="A-G-A", label_visibility="collapsed", key="kharab_extent")
            
            with col4:
                st.markdown("**ದರ**")
                rate = st.text_input("ದರ", placeholder="Enter Rate", label_visibility="collapsed", key="rate")
            
            with col5:
                st.markdown("**ಕಜಪ ಕ್ಷೇತ್ರ**")
                kjp_extent = st.text_input("ಕಜಪ ಕ್ಷೇತ್ರ", placeholder="A-G-A", label_visibility="collapsed", key="kjp_extent")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("**ಸ.ನಂ/ಹಿ.ನಂ.**")
                survey_hissa = st.text_input("ಸ.ನಂ/ಹಿ.ನಂ.", placeholder="Enter Survey/Hissa", label_visibility="collapsed", key="ex_survey")
            with col2:
                st.markdown("**ಕಜಪ ಕ್ಷೇತ್ರ**")
                kjp_extent = st.text_input("ಕಜಪ ಕ್ಷೇತ್ರ", placeholder="A-G-A", label_visibility="collapsed", key="ex_kjp_extent")
        
        # Action buttons
        st.markdown("---")
        col_btn1, col_btn2, col_btn3, col_btn4, col_btn5 = st.columns(5)
        
        with col_btn1:
            add_clicked = st.button("Add", use_container_width=True)
        
        with col_btn2:
            edit_clicked = st.button("Edit", use_container_width=True)
        
        with col_btn3:
            delete_clicked = st.button("Delete", use_container_width=True)
        
        with col_btn4:
            total_clicked = st.button("Total", use_container_width=True)
        
        with col_btn5:
            print_clicked = st.button("Print", use_container_width=True)
        
        # Handle Add button
        if add_clicked:
            try:
                # Check if location data is available
                location_data = st.session_state.kjp_location_data
                if not all([location_data['village'], location_data['hobli'], location_data['taluka'], location_data['district']]):
                    st.error("Please enter location details before adding records.")
                elif not survey_hissa:
                    st.error("Survey/Hissa number is required.")
                else:
                    if ex_kjp_mode:
                        if not ex_kjp_input:
                            st.error("Ex KJP input is required in Ex KJP mode.")
                        else:
                            kjp_extent_val = self.parse_extent(kjp_extent, "KJP Extent")
                            
                            record = {
                                "AsIs_SurveyHissa": survey_hissa,
                                "AsIs_TotalExtent": self.format_extent(kjp_extent_val),
                                "AsIs_Kharab": self.format_extent(kjp_extent_val),
                                "AsIs_Cultivable": "",
                                "AsIs_Rate": "",
                                "AsIs_Assessment": "",
                                "Amended_SurveyHissa": survey_hissa,
                                "Amended_TotalExtent": self.format_extent(kjp_extent_val),
                                "Amended_Kharab": self.format_extent(kjp_extent_val),
                                "Amended_Cultivable": ex_kjp_input,
                                "Amended_Rate": "",
                                "Amended_Assessment": "",
                                "type": "ex_kjp"
                            }
                            
                            st.session_state.kjp_data.append(record)
                            st.success("Ex KJP record added successfully!")
                            st.rerun()
                    else:
                        total_extent_val = self.parse_extent(total_extent, "Total Extent")
                        kharab_extent_val = self.parse_extent(kharab_extent, "Kharab")
                        rate_val = self.parse_rate(rate)
                        kjp_extent_val = self.parse_extent(kjp_extent, "KJP Extent")
                        
                        cultivable_extent = total_extent_val - kharab_extent_val
                        if cultivable_extent < 0:
                            raise ValueError("Cultivable area cannot be negative.")
                        
                        # A row calculations
                        a_row_amended_total_extent = total_extent_val - kjp_extent_val
                        a_row_amended_kharab_extent = kharab_extent_val
                        a_row_amended_cultivable_extent = a_row_amended_total_extent - a_row_amended_kharab_extent
                        
                        cultivable_acres = cultivable_extent / 40
                        assessment = rate_val * cultivable_acres
                        a_row_amended_cultivable_acres = a_row_amended_cultivable_extent / 40
                        a_row_amended_assessment = rate_val * a_row_amended_cultivable_acres
                        
                        # For amended survey/hissa, add * if KJP extent exists
                        amended_survey_hissa = survey_hissa + "*" if kjp_extent_val > 0 else survey_hissa
                        
                        # A row (main record)
                        a_row_record = {
                            "AsIs_SurveyHissa": survey_hissa,
                            "AsIs_TotalExtent": self.format_extent(total_extent_val),
                            "AsIs_Kharab": self.format_extent(kharab_extent_val),
                            "AsIs_Cultivable": self.format_extent(cultivable_extent),
                            "AsIs_Rate": f"{rate_val:.2f}" if rate_val > 0 else "",
                            "AsIs_Assessment": f"{assessment:.2f}" if assessment > 0 else "",
                            "Amended_SurveyHissa": amended_survey_hissa,
                            "Amended_TotalExtent": self.format_extent(a_row_amended_total_extent),
                            "Amended_Kharab": self.format_extent(a_row_amended_kharab_extent),
                            "Amended_Cultivable": self.format_extent(a_row_amended_cultivable_extent),
                            "Amended_Rate": f"{rate_val:.2f}" if rate_val > 0 else "",
                            "Amended_Assessment": f"{a_row_amended_assessment:.2f}" if a_row_amended_assessment > 0 else "",
                            "type": "data"
                        }
                        
                        st.session_state.kjp_data.append(a_row_record)
                        
                        # Add KJP row (B row) if KJP extent exists and is less than total extent
                        if kjp_extent_val > 0 and kjp_extent_val < total_extent_val:
                            b_row_record = {
                                "AsIs_SurveyHissa": "",
                                "AsIs_TotalExtent": "",
                                "AsIs_Kharab": "",
                                "AsIs_Cultivable": "",
                                "AsIs_Rate": "",
                                "AsIs_Assessment": "",
                                "Amended_SurveyHissa": amended_survey_hissa,
                                "Amended_TotalExtent": self.format_extent(kjp_extent_val),
                                "Amended_Kharab": self.format_extent(kjp_extent_val),
                                "Amended_Cultivable": "ಬಿನ್ ಶೇತ್ಕಿ ಕಡೆಗೆ ಹೋಗಿದೆ",
                                "Amended_Rate": "",
                                "Amended_Assessment": "",
                                "type": "kjp_row"
                            }
                            st.session_state.kjp_data.append(b_row_record)
                        
                        # Auto-increment hissa number for next record
                        if st.session_state.current_survey_no:
                            st.session_state.current_hissa_no += 1
                        
                        st.success("Record added successfully!")
                        st.rerun()
                        
            except ValueError as e:
                st.error(f"Invalid input: {str(e)}")
        
        # Handle other buttons
        if edit_clicked:
            self.edit_record()
        
        if delete_clicked:
            self.delete_record()
        
        if total_clicked:
            self.update_totals()
        
        if print_clicked:
            self.print_data()
        
        # Display data table - Show all record types including Ex KJP
        st.markdown("---")
        if st.session_state.kjp_data:
            # Prepare display data - Include all record types
            display_data = []
            for record in st.session_state.kjp_data:
                if record.get("type") in ["data", "total", "ex_kjp", "kjp_row"]:
                    if record.get("type") == "ex_kjp":
                        # Special display for Ex KJP records
                        display_record = {
                            "ಸ.ನಂ/ಹಿ.ನಂ.": record["AsIs_SurveyHissa"],
                            "ಒಟ್ಟು ಕ್ಷೇತ್ರ": record["AsIs_TotalExtent"],
                            "ಖರಾಬ": record["AsIs_Kharab"],
                            "ಸಾಗು ಕ್ಷೇತ್ರ": "EX KJP",
                            "ದರ": "EX KJP", 
                            "ಆಕಾರ (₹)": "EX KJP",
                            "ದುರಸ್ತಿ_ಸ.ನಂ": record["Amended_SurveyHissa"],
                            "ದುರಸ್ತಿ_ಒಟ್ಟು": record["Amended_TotalExtent"],
                            "ದುರಸ್ತಿ_ಖರಾಬ": record["Amended_Kharab"],
                            "ದುರಸ್ತಿ_ಸಾಗು": record["Amended_Cultivable"],
                            "ದುರಸ್ತಿ_ದರ": "EX KJP",
                            "ದುರಸ್ತಿ_ಆಕಾರ": "EX KJP"
                        }
                    elif record.get("type") == "kjp_row":
                        # Special display for KJP rows
                        display_record = {
                            "ಸ.ನಂ/ಹಿ.ನಂ.": "",
                            "ಒಟ್ಟು ಕ್ಷೇತ್ರ": "",
                            "ಖರಾಬ": "",
                            "ಸಾಗು ಕ್ಷೇತ್ರ": "",
                            "ದರ": "",
                            "ಆಕಾರ (₹)": "",
                            "ದುರಸ್ತಿ_ಸ.ನಂ": record["Amended_SurveyHissa"],
                            "ದುರಸ್ತಿ_ಒಟ್ಟು": record["Amended_TotalExtent"],
                            "ದುರಸ್ತಿ_ಖರಾಬ": record["Amended_Kharab"],
                            "ದುರಸ್ತಿ_ಸಾಗು": "ಬಿನ್ ಶೇತ್ಕಿ ಕಡೆಗೆ ಹೋಗಿದೆ",
                            "ದುರಸ್ತಿ_ದರ": "",
                            "ದುರಸ್ತಿ_ಆಕಾರ": ""
                        }
                    else:
                        # Normal data and total rows
                        display_record = {
                            "ಸ.ನಂ/ಹಿ.ನಂ.": record["AsIs_SurveyHissa"],
                            "ಒಟ್ಟು ಕ್ಷೇತ್ರ": record["AsIs_TotalExtent"],
                            "ಖರಾಬ": record["AsIs_Kharab"],
                            "ಸಾಗು ಕ್ಷೇತ್ರ": record["AsIs_Cultivable"],
                            "ದರ": record["AsIs_Rate"],
                            "ಆಕಾರ (₹)": record["AsIs_Assessment"],
                            "ದುರಸ್ತಿ_ಸ.ನಂ": record["Amended_SurveyHissa"],
                            "ದುರಸ್ತಿ_ಒಟ್ಟು": record["Amended_TotalExtent"],
                            "ದುರಸ್ತಿ_ಖರಾಬ": record["Amended_Kharab"],
                            "ದುರಸ್ತಿ_ಸಾಗು": record["Amended_Cultivable"],
                            "ದುರಸ್ತಿ_ದರ": record["Amended_Rate"],
                            "ದುರಸ್ತಿ_ಆಕಾರ": record["Amended_Assessment"]
                        }
                    display_data.append(display_record)
            
            if display_data:
                df = pd.DataFrame(display_data)
                st.dataframe(df, use_container_width=True)
        else:
            st.info("No records added yet.")
    
    def edit_record(self):
        st.info("Edit functionality would be implemented here")
        # Similar to KamalBerijuApp edit functionality
    
    def delete_record(self):
        st.info("Delete functionality would be implemented here")
        # Similar to KamalBerijuApp delete functionality
    
    def update_totals(self):
        if not st.session_state.kjp_data:
            st.warning("No records to calculate totals.")
            return
        
        # Remove existing totals and separators
        st.session_state.kjp_data = [record for record in st.session_state.kjp_data if record.get("type") not in ["separator", "total"]]
        
        # Add separator
        separator_record = {f"AsIs_{col}": "-" for col in ["SurveyHissa", "TotalExtent", "Kharab", "Cultivable", "Rate", "Assessment"]}
        separator_record.update({f"Amended_{col}": "-" for col in ["SurveyHissa", "TotalExtent", "Kharab", "Cultivable", "Rate", "Assessment"]})
        separator_record["type"] = "separator"
        st.session_state.kjp_data.append(separator_record)
        
        # Calculate totals (only from data records, not KJP rows or Ex KJP)
        total_columns = {
            "AsIs_TotalExtent": 0,
            "AsIs_Kharab": 0,
            "AsIs_Cultivable": 0,
            "AsIs_Assessment": 0,
            "Amended_TotalExtent": 0,
            "Amended_Kharab": 0,
            "Amended_Cultivable": 0,
            "Amended_Assessment": 0
        }
        
        data_records = [record for record in st.session_state.kjp_data if record.get("type") == "data"]
        
        for record in data_records:
            for col in total_columns:
                if col in ["AsIs_TotalExtent", "AsIs_Kharab", "AsIs_Cultivable", "Amended_TotalExtent", "Amended_Kharab", "Amended_Cultivable"]:
                    if record[col] and record[col] != "0-0-0":
                        total_columns[col] += self.get_extent_float(record[col])
                else:
                    if record[col]:
                        total_columns[col] += float(record[col])
        
        # Add total row
        total_record = {
            "AsIs_SurveyHissa": "Total",
            "AsIs_TotalExtent": self.format_extent(total_columns["AsIs_TotalExtent"]) if total_columns["AsIs_TotalExtent"] > 0 else "0-0-0",
            "AsIs_Kharab": self.format_extent(total_columns["AsIs_Kharab"]) if total_columns["AsIs_Kharab"] > 0 else "0-0-0",
            "AsIs_Cultivable": self.format_extent(total_columns["AsIs_Cultivable"]) if total_columns["AsIs_Cultivable"] > 0 else "0-0-0",
            "AsIs_Rate": "-",
            "AsIs_Assessment": f"{total_columns['AsIs_Assessment']:.2f}" if total_columns['AsIs_Assessment'] > 0 else "",
            "Amended_SurveyHissa": "-",
            "Amended_TotalExtent": self.format_extent(total_columns["Amended_TotalExtent"]) if total_columns["Amended_TotalExtent"] > 0 else "0-0-0",
            "Amended_Kharab": self.format_extent(total_columns["Amended_Kharab"]) if total_columns["Amended_Kharab"] > 0 else "0-0-0",
            "Amended_Cultivable": self.format_extent(total_columns["Amended_Cultivable"]) if total_columns["Amended_Cultivable"] > 0 else "0-0-0",
            "Amended_Rate": "-",
            "Amended_Assessment": f"{total_columns['Amended_Assessment']:.2f}" if total_columns['Amended_Assessment'] > 0 else "",
            "type": "total"
        }
        
        st.session_state.kjp_data.append(total_record)
        st.success("Totals updated successfully!")
        st.rerun()
    
    def print_data(self):
        if not st.session_state.kjp_data:
            st.warning("No data available to print.")
            return
        
        # Check location data
        location_data = st.session_state.kjp_location_data
        if not all([location_data['village'], location_data['hobli'], location_data['taluka'], location_data['district']]):
            st.warning("Please enter location details before printing.")
            return
        
        html_content = self.generate_print_html()
        
        # Improved JS: Open popup, load content, no auto-print
        js = f"""
        <script>
            function openPreview() {{
                var htmlContent = `{html_content}`;
                var previewWindow = window.open('', '_blank', 'width=1000,height=600,resizable=yes,scrollbars=yes');
                if (previewWindow) {{
                    previewWindow.document.write(htmlContent);
                    previewWindow.document.close();
                    previewWindow.focus();  // Bring to front
                }} else {{
                    alert('Popup blocked! Please allow popups for this site.');
                }}
            }}
            openPreview();
        </script>
        """
        st.components.v1.html(js, height=0)
        st.success("Print preview opened in a popup window!")


def main():
    # Check if app has expired before rendering anything
    check_expiry()
    
    st.set_page_config(
        page_title="M. J. Sikandar's KJP App",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state for location data
    if 'kjp_location_data' not in st.session_state:
        st.session_state.kjp_location_data = {
            'district': '', 'taluka': '', 'hobli': '', 
            'village': '', 'kjp_share': ''
        }
    
    st.sidebar.title("KJP Applications")
    app_choice = st.sidebar.radio(
        "Select Application:",
        ["ಕ.ಜ.ಪ ಪತ್ರಿಕೆ", "ಕಮಾಲ ಬೇರಿಜು"]
    )
    
    if app_choice == "ಕ.ಜ.ಪ ಪತ್ರಿಕೆ":
        kjp_app = KJPLandSurveyApp()
        kjp_app.render()
    else:
        kamal_app = KamalBerijuApp()
        kamal_app.render()

if __name__ == "__main__":
    main()