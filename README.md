# 📊 WhatsApp Chat Analyzer

Transform your raw WhatsApp**.txt**exports into a beautiful, interactive, local web dashboard. This tool allows you to deeply analyze your conversations, texting habits, and group dynamics entirely offline, ensuring your private data never leaves your machine.

## ✨ Features

This project is split into two main components: a powerful text parser and an interactive Gradio web dashboard.

### The Dashboard Visualizations

- **Timeline Graph**: See the entire lifecycle of your chat with a daily message volume bar chart.

- **Activity Heatmaps**: Discover exactly when your chat is most active with a Time of Day vs. Day of Week heatmap, plus a total hourly breakdown.

- **Top Words & Emojis**: Horizontal bar charts displaying the most frequently used words and emojis, scaling dynamically based on your settings.

- **Chat Explorer**: A searchable, tabular view of your actual chat history.

### Deep Filtering & Customization

- **Participant Filtering**: Isolate the data to analyze the habits of one specific person or view the group as a whole.

- **Advanced Search Matching**: Filter the entire dashboard by a specific word or emoji using "Contains", "Exact Word" or "Exact Message" matching.

- **Smart Date Range**: Interactive calendar widgets to restrict analysis to specific months or years.

- **Custom Stop Words**: A built-in text box to dynamically filter out local slang or irrelevant filler words (e.g., "haha", "ok", "yeah") from your top word charts.

- **Appearance Settings**: Manually adjust chart height and font size to prevent overlapping text and optimize the view for your specific screen.

## Installation

It is highly recommended to run this project inside a Python Virtual Environment to prevent conflicts with your system packages (especially on Linux/Raspberry Pi).

**1. Clone the repository and navigate into the directory**: 

```bash
git clone https://www.google.com/search?q=https://github.com/YOUR_USERNAME/WhatsApp-Chat-Analysis.git
cd WhatsApp-Chat-Analysis
```

**2. Create and activate a virtual environment**: 

For Linux / macOS / Raspberry Pi:

```bash
python3 -m venv venv
source venv/bin/activate
```

For Windows:

```
python -m venv venv
venv\Scripts\activate
```

**3. Install the required dependencies**: 

```bash
pip install pandas gradio plotly emoji
```


## 🛠️ How to Use

### Step 1: Export your WhatsApp Chat

1. Open WhatsApp on your phone.
2. Open the individual or group chat you want to analyze.
3. Tap the three dots (Menu) >**More**>**Export chat**.
4. Choose **Without media** (this tool currently analyzes text data).
5. Transfer the **.txt** file to your computer and place it in this project folder.

### Step 2: Parse the Data

Run the parsing script to convert the raw text into a clean CSV file. The script will automatically prompt you to rename participants (useful for converting raw phone numbers into readable names).

```bash
python parse_chat.py your_chat_export.txt
```

This will generate a clean`parsed_your_chat_export.csv` file in the same directory.

### Step 3: Launch the Dashboard

Start the interactive web dashboard by running:

```bash
python dashboard.py
```

-  The terminal will provide a local URL (e.g., `http://127.0.0.1:7860` or `http://localhost:7860`).
-  Open this URL in your web browser.
-  Drag and drop your newly created **parsed_chat.csv** into the upload box and start exploring!

## Issues

- Support for Emojis