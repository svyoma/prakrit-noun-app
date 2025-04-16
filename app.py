from flask import Flask, request, render_template_string, send_file
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DEFAULT_JSON = os.path.join(UPLOAD_FOLDER, "candragomin_grammar.json")

HTML_TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Candragomin Grammar Sutra Viewer</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: auto; padding: 20px; }
    input[type=text], input[type=file] { padding: 5px; width: 300px; margin-bottom: 10px; }
    input[type=submit] { padding: 6px 12px; }
    li { margin-bottom: 15px; }
    .sutra { font-weight: bold; color: #2a4d69; }
    .commentary { margin-left: 10px; color: #555; }
    form { margin-bottom: 20px; }
  </style>
</head>
<body>
<h2>📜 Candragomin Grammar Sutra Viewer</h2>
<form method=post enctype=multipart/form-data>
  <label>Upload JSON file: </label>
  <input type=file name=file>
  <input type=submit value=Upload>
</form>

{% if data %}
  <form method=get>
    🔍 Search keyword: <input type=text name=query value="{{ request.args.get('query', '') }}">
    🔠 Starts with: <input type=text name=starts value="{{ request.args.get('starts', '') }}">
    <input type=submit value=Apply>
  </form>

  <h3>🧾 Parsed Sutras ({{ data|length }} results):</h3>
  <ul>
  {% for item in data %}
    <li><span class="sutra">{{ item.sutra }}</span><br><span class="commentary">{{ item.commentary }}</span></li>
  {% endfor %}
  </ul>

  <form method="post" action="/download">
    <input type="hidden" name="query" value="{{ request.args.get('query', '') }}">
    <input type="hidden" name="starts" value="{{ request.args.get('starts', '') }}">
    <input type="submit" value="⬇️ Download Filtered JSON">
  </form>
{% endif %}
</body>
</html>
'''

data_store = []

# Load default JSON at startup if available
if os.path.exists(DEFAULT_JSON):
    with open(DEFAULT_JSON, 'r', encoding='utf-8') as f:
        data_store = json.load(f)

@app.route('/', methods=['GET', 'POST'])
def upload():
    global data_store
    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        with open(path, 'r', encoding='utf-8') as f:
            data_store = json.load(f)

    query = request.args.get('query', '').strip()
    starts = request.args.get('starts', '').strip()

    filtered = data_store
    if query:
        filtered = [d for d in filtered if query in d.get("sutra", '') or query in d.get("commentary", '')]
    if starts:
        filtered = [d for d in filtered if d.get("sutra", '').startswith(starts)]

    return render_template_string(HTML_TEMPLATE, data=filtered)

@app.route('/download', methods=['POST'])
def download_filtered():
    query = request.form.get('query', '').strip()
    starts = request.form.get('starts', '').strip()

    filtered = data_store
    if query:
        filtered = [d for d in filtered if query in d.get("sutra", '') or query in d.get("commentary", '')]
    if starts:
        filtered = [d for d in filtered if d.get("sutra", '').startswith(starts)]

    output_path = os.path.join(UPLOAD_FOLDER, "filtered_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    return send_file(output_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=False)