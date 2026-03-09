import gradio as gr
import pandas as pd
import plotly.express as px
from collections import Counter
import emoji
import re

# Base chronological list of hours
BASE_HOURS = [
    '12 AM', '1 AM', '2 AM', '3 AM', '4 AM', '5 AM', '6 AM', '7 AM', '8 AM', '9 AM', '10 AM', '11 AM',
    '12 PM', '1 PM', '2 PM', '3 PM', '4 PM', '5 PM', '6 PM', '7 PM', '8 PM', '9 PM', '10 PM', '11 PM'
]

def get_shifted_hours(start_hour):
    """Shifts the 24-hour list to begin at the user's chosen start time."""
    idx = BASE_HOURS.index(start_hour)
    return BASE_HOURS[idx:] + BASE_HOURS[:idx]

def handle_file_upload(file_path):
    """Reads the CSV upon upload to populate participants and chat date range."""
    if not file_path:
        return gr.update(choices=["All Participants"], value="All Participants"), None, None
    try:
        df = pd.read_csv(file_path.name)
        df['Datetime'] = pd.to_datetime(df['Datetime'], errors='coerce')
        
        users = ["All Participants"] + sorted(df['Sender'].dropna().unique().tolist())
        min_date = df['Datetime'].min()
        max_date = df['Datetime'].max()
        
        return gr.update(choices=users, value="All Participants"), min_date, max_date
    except Exception:
        return gr.update(choices=["All Participants"], value="All Participants"), None, None

def analyze_chat(file_path, search_query, match_type, selected_user, start_hour, top_n, show_counts, start_date, end_date, custom_stop_words, font_size, chart_height):
    """Main analysis engine to filter data and generate all Plotly figures."""
    if not file_path:
        return pd.DataFrame(), None, None, None, None, None
    
    # Load data
    df = pd.read_csv(file_path.name)
    df['Datetime'] = pd.to_datetime(df['Datetime'], errors='coerce')
    df = df.dropna(subset=['Message']) 
    
    # --- Apply Date Range ---
    if start_date:
        try: 
            start_dt = pd.to_datetime(start_date).tz_localize(None)
            df = df[df['Datetime'] >= start_dt]
        except Exception: pass
            
    if end_date:
        try: 
            end_dt = pd.to_datetime(end_date).tz_localize(None) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            df = df[df['Datetime'] <= end_dt]
        except Exception: pass

    # --- Apply Global Filters ---
    if selected_user != "All Participants":
        df = df[df['Sender'] == selected_user]
        
    # NEW: Match Type Logic
    if search_query:
        if match_type == "Exact Word":
            # (?<!\w) and (?!\w) ensure the search term isn't surrounded by other letters/numbers.
            # This works much better than \b when dealing with emojis and punctuation.
            pattern = rf'(?<!\w){re.escape(search_query)}(?!\w)'
            df = df[df['Message'].astype(str).str.contains(pattern, case=False, na=False, regex=True)]
        elif match_type == "Exact Message":
            # Strips accidental spaces and checks if the entire message is exactly the query
            df = df[df['Message'].astype(str).str.lower().str.strip() == search_query.lower().strip()]
        else:
            # Standard "Contains" match
            df = df[df['Message'].astype(str).str.contains(search_query, case=False, na=False)]
        
    if df.empty:
        return pd.DataFrame(["No messages found matching these filters."]), None, None, None, None, None

    # Limit explore view to prevent browser lag
    chat_explore = df[['Date', 'Time', 'Sender', 'Message']].tail(500)
    
    # Time logic
    df['Hour_Num'] = df['Datetime'].dt.hour
    df['Hour Label'] = df['Hour_Num'].apply(lambda x: BASE_HOURS[int(x)] if pd.notnull(x) else None)
    df['Day'] = df['Datetime'].dt.day_name()
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    shifted_hours = get_shifted_hours(start_hour)

    # --- Explicit Global Layout ---
    common_layout = dict(
        font_size=font_size,
        font_family="Arial, 'Segoe UI Emoji', 'Apple Color Emoji', 'Noto Color Emoji', sans-serif",
        height=chart_height,
        autosize=True,
        margin=dict(l=20, r=20, t=50, b=20)
    )

    # --- 1. Timeline Bar Graph ---
    timeline_data = df.groupby(df['Datetime'].dt.date).size().reset_index(name='Total Messages')
    timeline_data.rename(columns={'Datetime': 'Date'}, inplace=True) 
    
    fig_timeline = px.bar(
        timeline_data, x='Date', y='Total Messages', title=f"Daily Message Timeline ({selected_user})",
        color='Total Messages', color_continuous_scale="Viridis", text='Total Messages' if show_counts else None
    )
    if show_counts: fig_timeline.update_traces(textposition='outside')
    fig_timeline.update_layout(**common_layout)
        
    # --- 2. Hourly Sum Bar Chart ---
    hourly_sum_data = df.groupby('Hour Label').size().reset_index(name='Total Messages')
    fig_hourly_sum = px.bar(
        hourly_sum_data, x='Hour Label', y='Total Messages', title=f"Total Messages per Hour ({selected_user})",
        category_orders={'Hour Label': shifted_hours}, color='Total Messages', color_continuous_scale="Blues", text='Total Messages' if show_counts else None
    )
    if show_counts: fig_hourly_sum.update_traces(textposition='outside')
    fig_hourly_sum.update_layout(**common_layout)
    
    # --- 3. Time Activity Heatmap ---
    heatmap_data = df.groupby(['Day', 'Hour Label']).size().reset_index(name='Count')
    fig_heatmap = px.density_heatmap(
        heatmap_data, x='Hour Label', y='Day', z='Count',
        category_orders={'Day': days_order, 'Hour Label': shifted_hours},
        title=f"Message Activity Heatmap ({selected_user})", color_continuous_scale="Blues",
        labels={'Hour Label': 'Time of Day', 'Day': 'Day of Week', 'Count': 'Messages'}, text_auto=show_counts 
    )
    fig_heatmap.update_layout(**common_layout)
    
    # --- Words & Emojis Setup ---
    all_text = " ".join(df['Message'].astype(str).tolist()).lower()
    
    # --- 4. Word Counts with Custom Stop Words ---
    words = re.findall(r'\b\w+\b', all_text)
    
    # Base stop words
    stop_words = {'the', 'and', 'i', 'to', 'a', 'of', 'in', 'it', 'is', 'that', 'you', 'for', 'on', 'this', 'was', 'my', 'are', 'we', 'have', 'omitted', 'media', 'your', 'with', 'but', 'not', 'can', 'be', 'as', 'do'}
    
    if custom_stop_words:
        user_stops = {w.strip().lower() for w in custom_stop_words.split(',') if w.strip()}
        stop_words.update(user_stops)
        
    filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
    
    word_counts = pd.DataFrame(Counter(filtered_words).most_common(top_n), columns=['Word', 'Count']).sort_values(by='Count', ascending=True)
    fig_words = px.bar(
        word_counts, x='Count', y='Word', orientation='h', 
        title=f"Top {top_n} Words ({selected_user})", color='Count', color_continuous_scale="Viridis", text='Count' if show_counts else None
    )
    if show_counts: fig_words.update_traces(textposition='outside')
    dynamic_height = max(chart_height, top_n * (font_size * 1.5))
    fig_words.update_layout(font_size=font_size, font_family=common_layout["font_family"], height=dynamic_height, autosize=True, margin=dict(l=20, r=20, t=50, b=20))
    
    # --- 5. Emoji Counts ---
    emojis_found = [char for char in all_text if char in emoji.EMOJI_DATA]
    emoji_counts = pd.DataFrame(Counter(emojis_found).most_common(top_n), columns=['Emoji', 'Count']).sort_values(by='Count', ascending=True)

    fig_emojis = px.bar(
        emoji_counts, x='Count', y='Emoji', orientation='h', 
        title=f"Top {top_n} Emojis ({selected_user})", color='Count', color_continuous_scale="Plasma", text='Count' if show_counts else None
    )
    if show_counts: fig_emojis.update_traces(textposition='outside')
    fig_emojis.update_layout(font_size=font_size, font_family=common_layout["font_family"], height=dynamic_height, autosize=True, margin=dict(l=20, r=20, t=50, b=20))

    return chat_explore, fig_timeline, fig_hourly_sum, fig_heatmap, fig_words, fig_emojis

# ==========================================
# GRADIO UI LAYOUT
# ==========================================
with gr.Blocks() as app:
    gr.Markdown("# 📊 WhatsApp Chat Analyzer")
    gr.Markdown("Upload your `parsed_chat.csv` file below to explore your data.")
    
    # Row 1: Primary File and Global Filters
    with gr.Row():
        file_input = gr.File(label="1. Upload parsed CSV file", file_types=[".csv"], scale=2)
        user_dropdown = gr.Dropdown(label="2. Filter by Participant", choices=["All Participants"], value="All Participants", interactive=True, scale=2)
        
        # Wrapped the search inputs in a column so they stack neatly together
        with gr.Column(scale=2):
            search_input = gr.Textbox(label="3. Filter by Word/Emoji", placeholder="e.g., 'lunch' or '😂'...", lines=1)
            match_type_input = gr.Radio(label="Match Behavior", choices=["Contains", "Exact Word", "Exact Message"], value="Contains")
        
    # Row 2: Date & Time Settings
    with gr.Row():
        start_date_input = gr.DateTime(label="Start Date", include_time=False, interactive=True, type="datetime")
        end_date_input = gr.DateTime(label="End Date", include_time=False, interactive=True, type="datetime")
        start_hour_input = gr.Dropdown(label="Day Starts At", choices=BASE_HOURS, value="12 PM", interactive=True)
        
    # Row 3: Chart Customizations
    with gr.Row():
        custom_stop_words_input = gr.Textbox(label="Custom Stop Words (comma-separated)", placeholder="e.g., haha, yeah, ok, lol", lines=1, scale=3)
        top_n_input = gr.Slider(label="Top Words/Emojis", minimum=5, maximum=100, step=5, value=25, interactive=True, scale=2)
        show_counts_input = gr.Checkbox(label="Show Counts", value=True, interactive=True, scale=1)
        
    with gr.Accordion("🎨 Appearance Settings", open=False):
        with gr.Row():
            font_size_input = gr.Slider(label="Font Size", minimum=8, maximum=32, step=1, value=12, interactive=True)
            chart_height_input = gr.Slider(label="Base Chart Height (px)", minimum=300, maximum=1000, step=50, value=500, interactive=True)
        
    with gr.Row():
        analyze_btn = gr.Button("Generate Analytics", variant="primary")
            
    with gr.Tabs():
        with gr.TabItem("Timeline"):
            timeline_output = gr.Plot(label="Daily Messages Over Time")
            
        with gr.TabItem("Activity Timing"):
            hourly_sum_output = gr.Plot(label="Total Messages by Hour")
            heatmap_output = gr.Plot(label="Time of Day vs. Day of Week")
            
        with gr.TabItem("Top Words & Emojis"):
            with gr.Row():
                words_output = gr.Plot()
                emojis_output = gr.Plot()
                
        with gr.TabItem("Explore Chat"):
            chat_df_output = gr.Dataframe(label="Chat History (Showing last 500 matching messages)", wrap=True)

    file_input.change(
        fn=handle_file_upload,
        inputs=[file_input],
        outputs=[user_dropdown, start_date_input, end_date_input]
    )

    # Make sure all inputs are passed to the analyze_chat function in the correct order
    analyze_btn.click(
        fn=analyze_chat,
        inputs=[
            file_input, search_input, match_type_input, user_dropdown, start_hour_input, 
            top_n_input, show_counts_input, start_date_input, end_date_input,
            custom_stop_words_input, font_size_input, chart_height_input
        ],
        outputs=[chat_df_output, timeline_output, hourly_sum_output, heatmap_output, words_output, emojis_output]
    )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft())
