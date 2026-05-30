import os
import re
import urllib.request
from html.parser import HTMLParser
from engine.common import CACHE_DIR

# --- HTML Table Parser ---
class RowspanParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.grid = {}
        self.current_row_index = 0
        self.current_col_index = 0
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_cell_text = ""
        self.current_cell_attrs = {}

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.in_table = True
            self.grid = {}
            self.current_row_index = 0
        elif tag == "tr" and self.in_table:
            self.in_row = True
            self.current_col_index = 0
        elif tag in ("td", "th") and self.in_row:
            self.in_cell = True
            self.current_cell_text = ""
            self.current_cell_attrs = dict(attrs)

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell_text += data

    def handle_endtag(self, tag):
        if tag == "table" and self.in_table:
            self.in_table = False
            max_row = max(r for r, c in self.grid.keys()) if self.grid else -1
            max_col = max(c for r, c in self.grid.keys()) if self.grid else -1
            table_list = []
            for r in range(max_row + 1):
                row_list = []
                for c in range(max_col + 1):
                    row_list.append(self.grid.get((r, c), ""))
                table_list.append(row_list)
            self.tables.append(table_list)
        elif tag == "tr" and self.in_row:
            self.in_row = False
            self.current_row_index += 1
        elif tag in ("td", "th") and self.in_cell:
            self.in_cell = False
            rowspan = int(self.current_cell_attrs.get("rowspan", 1))
            colspan = int(self.current_cell_attrs.get("colspan", 1))
            text = self.current_cell_text.strip()
            
            # Find the next free column in the current row
            while (self.current_row_index, self.current_col_index) in self.grid:
                self.current_col_index += 1
                
            # Fill the grid for the rowspan/colspan range
            for r in range(self.current_row_index, self.current_row_index + rowspan):
                for c in range(self.current_col_index, self.current_col_index + colspan):
                    self.grid[(r, c)] = text
            self.current_col_index += colspan

def parse_html_tables(html_content):
    parser = RowspanParser()
    parser.feed(html_content)
    return parser.tables

# --- Helper Functions ---
def clean_value(val):
    val = val.strip().replace("&#8211;", "-").replace("&ndash;", "-").replace("—", "-").replace("–", "-")
    val = re.sub(r'\s+', ' ', val)
    return val

def parse_int(val):
    val = clean_value(val)
    if not val or val in ("-", "–", "—", "??", "???"):
        return 0
    try:
        return int(val)
    except ValueError:
        m = re.search(r'[-+]?\d+', val)
        if m:
            return int(m.group(0))
        return 0

def fetch_page(name, url):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{name}.html")
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()
    
    print(f"Fetching {url}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            content = response.read().decode("utf-8")
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(content)
        return content
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        raise e
