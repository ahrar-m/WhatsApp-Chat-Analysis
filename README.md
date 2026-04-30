# WhatsApp Chat Analyzer

A local, private web application to analyze WhatsApp chat exports. All processing is done entirely in your browser; your chat data never leaves your computer.

## Features

- **Private & Local Analysis**: No server-side processing. Your chat files remain on your device.
- **Interactive Dashboard**:
    - **Message Volume Over Time**: View trends with interactive tooltips showing exact message counts.
    - **Participant Activity**: Compare message volume per user.
    - **Hourly & Weekly Activity**: Understand when users are most active during the day and week.
    - **Activity Heatmap**: A comprehensive grid showing message intensity by hour and day.
- **N-grams Analysis**: Identify common phrases with user-driven skipping functionality.
- **Filtering**:
    - **Participant Filter**: Use checkboxes to include or exclude specific participants from the analysis.
    - **Time Range**: Set start and end dates with an aesthetic date-picker interface.

## How to use

1.  Open `Whatsapp Chat Anlayzer.html` in your web browser.
2.  Drop your WhatsApp export (a `.zip` or `.txt` file) into the designated area.
3.  The application will automatically parse the file and generate interactive charts and tables.
4.  Use the filter section at the top of the dashboard to customize the views.
5.  Click "Analyze New Chat" to reset and start over with a new file.

## Technical Details

- **Frameworks/Libraries**:
    - [Tailwind CSS](https://tailwindcss.com/) for styling.
    - [Chart.js](https://www.chartjs.org/) for data visualization.
    - [Moment.js](https://momentjs.com/) for date parsing and formatting.
    - [JSZip](https://stuk.github.io/jszip/) for handling ZIP files locally.
- **Browser Compatibility**: The tool utilizes modern browser APIs and should run in all recent versions of major web browsers.
