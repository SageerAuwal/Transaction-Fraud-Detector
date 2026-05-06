import os
import urllib.request
import re

FRONTEND_DIR = "frontend"
FONTS_DIR = os.path.join(FRONTEND_DIR, "fonts")
os.makedirs(FONTS_DIR, exist_ok=True)

# 1. Download Chart.js
print("Downloading Chart.js...")
chart_url = "https://cdn.jsdelivr.net/npm/chart.js"
chart_path = os.path.join(FRONTEND_DIR, "chart.js")
req = urllib.request.Request(chart_url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response, open(chart_path, 'wb') as out_file:
    out_file.write(response.read())
print("Chart.js saved.")

# 2. Download Google Fonts CSS
print("Downloading Inter font CSS...")
font_url = "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap"
# Need modern user agent to get woff2
req = urllib.request.Request(font_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'})
with urllib.request.urlopen(req) as response:
    css_content = response.read().decode('utf-8')

# Find all woff2 URLs
urls = re.findall(r'url\((https://fonts\.gstatic\.com/[^\)]+)\)', css_content)
for i, url in enumerate(urls):
    filename = f"inter_{i}.woff2"
    filepath = os.path.join(FONTS_DIR, filename)
    print(f"Downloading {filename}...")
    req_font = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req_font) as font_response, open(filepath, 'wb') as font_file:
        font_file.write(font_response.read())
    # Replace in CSS
    css_content = css_content.replace(url, f"fonts/{filename}")

# Save the updated CSS
css_path = os.path.join(FRONTEND_DIR, "fonts.css")
with open(css_path, 'w', encoding='utf-8') as f:
    f.write(css_content)
print("Fonts CSS saved.")
