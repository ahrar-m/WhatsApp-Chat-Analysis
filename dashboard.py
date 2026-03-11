import gradio as gr
import pandas as pd
import plotly.express as px
from collections import Counter
import emoji
import re
import os
import zipfile

# ==========================================
# DEFAULT CONFIGURATIONS (EDIT THESE)
# ==========================================
CFG_START_HOUR = "12 PM"
CFG_TOP_N = 20
CFG_SHOW_COUNTS = True
CFG_FONT_SIZE = 12
CFG_CHART_HEIGHT = 500
CFG_RESOLUTION_MULTIPLIER = 1.0 # Increase for higher quality image downloads

# Base chronological list of hours
BASE_HOURS = ['12 AM', '1 AM', '2 AM', '3 AM', '4 AM', '5 AM', '6 AM', '7 AM', '8 AM', '9 AM', '10 AM', '11 AM', '12 PM', '1 PM', '2 PM', '3 PM', '4 PM', '5 PM', '6 PM', '7 PM', '8 PM', '9 PM', '10 PM', '11 PM']

# ==========================================
# PHASE 1: DATA PARSING & EXTRACTION
# ==========================================

def parse_chat_lines(lines):
    """Core regex parser that converts raw text lines into a Pandas DataFrame."""
    pattern = r'^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}\s?(?:[aApP][mM])?)\s-\s(.*?):\s(.*)$'
    parsed_data = [] 
    
    date, time, sender, message = None, None, None, ""
    
    for line in lines:
        match = re.match(pattern, line)
        if match:
            if sender:
                parsed_data.append([date, time, sender, message.strip()])
            date, time, sender, message_text = match.groups()
            message = message_text + " "
        else:
            if sender:
                message += line.strip() + " "
            
    if sender:
        parsed_data.append([date, time, sender, message.strip()])
        
    df = pd.DataFrame(parsed_data, columns=['Date', 'Time', 'Sender', 'Message'])
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], dayfirst=True, format='mixed', errors='coerce')
    
    return df

def load_chat_data(file_path):
    """Smart loader that handles .zip, .txt, or pre-parsed .csv files dynamically."""
    if not file_path:
        return pd.DataFrame()
        
    # If the user uploads a ZIP, extract and parse it in memory
    if file_path.endswith('.zip'):
        try:
            with zipfile.ZipFile(file_path, 'r') as z:
                txt_files = [f for f in z.namelist() if f.endswith('.txt')]
                if not txt_files:
                    return pd.DataFrame()
                
                with z.open(txt_files[0]) as f:
                    # Decode binary data to utf-8 strings
                    lines = [line.decode('utf-8') for line in f.readlines()]
                    return parse_chat_lines(lines)
        except Exception:
            return pd.DataFrame()
            
    # If the user uploads a raw .txt file directly
    elif file_path.endswith('.txt'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return parse_chat_lines(f.readlines())
        except Exception:
            return pd.DataFrame()
            
    # If the user uploads a previously generated .csv
    elif file_path.endswith('.csv'):
        try:
            return pd.read_csv(file_path)
        except Exception:
            return pd.DataFrame()
            
    return pd.DataFrame()

# ==========================================
# PHASE 2: DATA ANALYSIS FUNCTIONS
# ==========================================

def get_shifted_hours(start_hour):
    idx = BASE_HOURS.index(start_hour)
    return BASE_HOURS[idx:] + BASE_HOURS[:idx]

def get_file_path(file_obj):
    if not file_obj: return None
    return file_obj.name if hasattr(file_obj, 'name') else file_obj

def handle_file_upload(file_input):
    """Triggered instantly when a file is uploaded to populate the UI dropdowns."""
    path = get_file_path(file_input)
    if not path:
        return gr.update(choices=["All Participants"], value="All Participants"), None, None
    
    df = load_chat_data(path)
    if df.empty:
        return gr.update(choices=["All Participants"], value="All Participants"), None, None
        
    df['Datetime'] = pd.to_datetime(df['Datetime'], errors='coerce')
    users = ["All Participants"] + sorted(df['Sender'].dropna().unique().tolist())
    return gr.update(choices=users, value="All Participants"), df['Datetime'].min(), df['Datetime'].max()

def analyze_chat(file_input, search_query, match_type, selected_user, start_hour, top_n, show_counts, start_date, end_date, custom_stop_words, font_size, chart_height, res_scale):
    """Main analysis engine triggered by the 'Generate Analytics' button."""
    path = get_file_path(file_input)
    if not path:
        return pd.DataFrame(), None, None, None, None, None
    
    df = load_chat_data(path)
    if df.empty:
         return pd.DataFrame(["Error: Could not parse file."]), None, None, None, None, None
         
    df['Datetime'] = pd.to_datetime(df['Datetime'], errors='coerce')
    df = df.dropna(subset=['Message']) 
    
    if start_date:
        try: df = df[df['Datetime'] >= pd.to_datetime(start_date).tz_localize(None)]
        except Exception: pass
    if end_date:
        try: df = df[df['Datetime'] <= pd.to_datetime(end_date).tz_localize(None) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)]
        except Exception: pass

    if selected_user != "All Participants":
        df = df[df['Sender'] == selected_user]
        
    if search_query:
        if match_type == "Exact Word":
            pattern = rf'(?<!\w){re.escape(search_query)}(?!\w)'
            df = df[df['Message'].astype(str).str.contains(pattern, case=False, na=False, regex=True)]
        elif match_type == "Exact Message":
            df = df[df['Message'].astype(str).str.lower().str.strip() == search_query.lower().strip()]
        else:
            df = df[df['Message'].astype(str).str.contains(search_query, case=False, na=False)]
        
    if df.empty:
        return pd.DataFrame(["No messages found matching these filters."]), None, None, None, None, None

    chat_explore = df[['Date', 'Time', 'Sender', 'Message']].tail(500)
    
    df['Hour_Num'] = df['Datetime'].dt.hour
    df['Hour Label'] = df['Hour_Num'].apply(lambda x: BASE_HOURS[int(x)] if pd.notnull(x) else None)
    df['Day'] = df['Datetime'].dt.day_name()
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    shifted_hours = get_shifted_hours(start_hour)

    scaled_height = int(chart_height * res_scale)
    scaled_font = int(font_size * res_scale)

    common_layout = dict(
        font_size=scaled_font, 
        font_family="Arial, 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', sans-serif", 
        height=scaled_height, 
        autosize=True, 
        margin=dict(l=20, r=20, t=50, b=20)
    )

    timeline_data = df.groupby(df['Datetime'].dt.date).size().reset_index(name='Total Messages')
    timeline_data.rename(columns={'Datetime': 'Date'}, inplace=True) 
    fig_timeline = px.bar(timeline_data, x='Date', y='Total Messages', title=f"Daily Message Timeline ({selected_user})", color='Total Messages', color_continuous_scale="Viridis", text='Total Messages' if show_counts else None)
    if show_counts: fig_timeline.update_traces(textposition='outside')
    fig_timeline.update_layout(**common_layout)
        
    hourly_sum_data = df.groupby('Hour Label').size().reset_index(name='Total Messages')
    fig_hourly_sum = px.bar(hourly_sum_data, x='Hour Label', y='Total Messages', title=f"Total Messages per Hour ({selected_user})", category_orders={'Hour Label': shifted_hours}, color='Total Messages', color_continuous_scale="Blues", text='Total Messages' if show_counts else None)
    if show_counts: fig_hourly_sum.update_traces(textposition='outside')
    fig_hourly_sum.update_layout(**common_layout)
    
    heatmap_data = df.groupby(['Day', 'Hour Label']).size().reset_index(name='Count')
    fig_heatmap = px.density_heatmap(heatmap_data, x='Hour Label', y='Day', z='Count', category_orders={'Day': days_order, 'Hour Label': shifted_hours}, title=f"Message Activity Heatmap ({selected_user})", color_continuous_scale="Blues", labels={'Hour Label': 'Time of Day', 'Day': 'Day of Week', 'Count': 'Messages'}, text_auto=show_counts)
    fig_heatmap.update_layout(**common_layout)
    
    all_text = " ".join(df['Message'].astype(str).tolist()).lower()
    words = re.findall(r'\b\w+\b', all_text)
    stop_words = {'the', 'and', 'i', 'to', 'a', 'of', 'in', 'it', 'is', 'that', 'you', 'for', 'on', 'this', 'was', 'my', 'are', 'we', 'have', 'omitted', 'media', 'your', 'with', 'but', 'not', 'can', 'be', 'as', 'do'}
    if custom_stop_words:
        user_stops = {w.strip().lower() for w in custom_stop_words.split(',') if w.strip()}
        stop_words.update(user_stops)
        
    filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
    word_counts = pd.DataFrame(Counter(filtered_words).most_common(top_n), columns=['Word', 'Count']).sort_values(by='Count', ascending=True)
    fig_words = px.bar(word_counts, x='Count', y='Word', orientation='h', title=f"Top {top_n} Words ({selected_user})", color='Count', color_continuous_scale="Viridis", text='Count' if show_counts else None)
    if show_counts: fig_words.update_traces(textposition='outside')
    
    dynamic_height = max(scaled_height, top_n * (scaled_font * 1.5))
    fig_words.update_layout(font_size=scaled_font, font_family=common_layout["font_family"], height=dynamic_height, autosize=True, margin=dict(l=20, r=20, t=50, b=20))
    
    emojis_found = [char for char in all_text if char in emoji.EMOJI_DATA]
    emoji_counts = pd.DataFrame(Counter(emojis_found).most_common(top_n), columns=['Emoji', 'Count']).sort_values(by='Count', ascending=True)
    fig_emojis = px.bar(emoji_counts, x='Count', y='Emoji', orientation='h', title=f"Top {top_n} Emojis ({selected_user})", color='Count', color_continuous_scale="Plasma", text='Count' if show_counts else None)
    if show_counts: fig_emojis.update_traces(textposition='outside')
    fig_emojis.update_layout(font_size=scaled_font, font_family=common_layout["font_family"], height=dynamic_height, autosize=True, margin=dict(l=20, r=20, t=50, b=20))

    return chat_explore, fig_timeline, fig_hourly_sum, fig_heatmap, fig_words, fig_emojis

# ==========================================
# PHASE 3: GRADIO UI LAYOUT
# ==========================================
if __name__ == "__main__":
    
    with gr.Blocks() as app:
        gr.Markdown("# 📊 WhatsApp Chat Analyzer")
        
        with gr.Row():
            # UPDATED: File input now explicitly asks for .zip (or .txt/.csv)
            file_input = gr.File(label="1. Upload WhatsApp Export (.zip, .txt, or .csv)", file_types=[".zip", ".txt", ".csv"], scale=2)
            user_dropdown = gr.Dropdown(label="2. Filter by Participant", choices=["All Participants"], value="All Participants", interactive=True, scale=2)
            
            with gr.Column(scale=2):
                search_input = gr.Textbox(label="3. Filter by Word/Emoji", placeholder="e.g., 'lunch' or '😂'...", lines=1)
                match_type_input = gr.Radio(label="Match Behavior", choices=["Contains", "Exact Word", "Exact Message"], value="Contains")
            
        with gr.Row():
            start_date_input = gr.DateTime(label="Start Date", include_time=False, interactive=True, type="datetime")
            end_date_input = gr.DateTime(label="End Date", include_time=False, interactive=True, type="datetime")
            start_hour_input = gr.Dropdown(label="Day Starts At", choices=BASE_HOURS, value=CFG_START_HOUR, interactive=True)
            
        with gr.Row():
            custom_stop_words_input = gr.Textbox(label="Custom Stop Words", placeholder="e.g., haha, yeah, ok, lol", lines=1, scale=3)
            top_n_input = gr.Slider(label="Top Words/Emojis", minimum=5, maximum=100, step=5, value=CFG_TOP_N, interactive=True, scale=2)
            show_counts_input = gr.Checkbox(label="Show Counts", value=CFG_SHOW_COUNTS, interactive=True, scale=1)
            
        with gr.Accordion("🎨 Appearance Settings", open=False):
            with gr.Row():
                font_size_input = gr.Slider(label="Font Size", minimum=8, maximum=32, step=1, value=CFG_FONT_SIZE, interactive=True)
                chart_height_input = gr.Slider(label="Base Chart Height (px)", minimum=300, maximum=1000, step=50, value=CFG_CHART_HEIGHT, interactive=True)
                resolution_input = gr.Slider(label="Export Resolution Multiplier", minimum=1.0, maximum=4.0, step=0.5, value=CFG_RESOLUTION_MULTIPLIER, interactive=True)
            
        with gr.Row():
            analyze_btn = gr.Button("Generate Analytics", variant="primary")
                
        with gr.Tabs():
            with gr.TabItem("Timeline"):
                timeline_output = gr.Plot()
            with gr.TabItem("Activity Timing"):
                hourly_sum_output = gr.Plot()
                heatmap_output = gr.Plot()
            with gr.TabItem("Top Words & Emojis"):
                words_output = gr.Plot()
                emojis_output = gr.Plot()
            with gr.TabItem("Explore Chat"):
                chat_df_output = gr.Dataframe(wrap=True)

        file_input.change(fn=handle_file_upload, inputs=[file_input], outputs=[user_dropdown, start_date_input, end_date_input])
        
        analyze_btn.click(
            fn=analyze_chat,
            inputs=[file_input, search_input, match_type_input, user_dropdown, start_hour_input, top_n_input, show_counts_input, start_date_input, end_date_input, custom_stop_words_input, font_size_input, chart_height_input, resolution_input],
            outputs=[chat_df_output, timeline_output, hourly_sum_output, heatmap_output, words_output, emojis_output]
        )

    print("\n🌐 Starting Web Server...")
    app.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft())