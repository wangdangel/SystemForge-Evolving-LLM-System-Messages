from flask import Flask, render_template, request, jsonify
import yaml
import requests
import json

# Load configuration
def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()
trainee_conf = config["trainee"]

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', system_message=trainee_conf['system_message'])

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    messages = data.get('messages')
    # call trainee endpoint
    try:
        resp = requests.post(f"{trainee_conf['url']}/api/chat", json={"model":trainee_conf['model'], "messages":messages}, timeout=30)
        resp.raise_for_status()
        text = resp.text
        try:
            data_json = resp.json()
            content = data_json.get('message', {}).get('content', '').strip()
        except ValueError:
            # aggregate all JSON lines from NDJSON
            chunks = []
            for line in text.splitlines():
                if not line.strip():
                    continue
                try:
                    part = json.loads(line)
                except ValueError:
                    continue
                if isinstance(part.get('message'), dict):
                    c = part['message'].get('content', '')
                elif isinstance(part.get('choices'), list):
                    delta = part['choices'][0].get('delta', {})
                    c = delta.get('content', '')
                else:
                    c = ''
                if c:
                    chunks.append(c)
            content = ''.join(chunks).strip()
    except Exception as e:
        content = f"[Error] {e}"
    return jsonify({'reply': content})

if __name__ == '__main__':
    port = config.get('server', {}).get('port', 5000)
    app.run(port=port, debug=True)
