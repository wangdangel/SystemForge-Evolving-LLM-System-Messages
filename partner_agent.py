import sys
import yaml
import requests

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)


def ollama_chat(url, model, system_message, dialog):
    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    # treat all dialog entries as user messages
    for msg in dialog:
        messages.append({"role": "user", "content": msg})
    payload = {"model": model, "messages": messages, "stream": False}
    try:
        resp = requests.post(f"{url}/api/chat", json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "").strip()
    except Exception as e:
        print(f"[PartnerError] {e}", file=sys.stderr)
        return "[PartnerError]"


def main():
    config = load_config()
    url = config["partner"]["url"]
    model = config["partner"]["model"]
    sys_msg = config["partner"]["system_message"]
    dialog = []  # list of (role_label, message)
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        # parse prefix
        if ":" in line:
            role_label, msg_text = line.split(":", 1)
            role_label = role_label.strip().lower()
            msg_text = msg_text.strip()
        else:
            role_label = 'trainee'
            msg_text = line
        dialog.append((role_label, msg_text))
        # build messages payload including system each time
        messages = [{"role": "system", "content": sys_msg}]
        for rl, txt in dialog:
            role = "assistant" if rl != 'trainee' else "user"
            messages.append({"role": role, "content": txt})
        # call the model
        payload = {"model": model, "messages": messages, "stream": False}
        try:
            resp = requests.post(f"{url}/api/chat", json=payload, timeout=10)
            resp.raise_for_status()
            resp_text = resp.json().get("message", {}).get("content", "").strip()
        except Exception as e:
            resp_text = f"[Error] {e}"
        # append partner reply and print
        dialog.append(('partner', resp_text))
        print(resp_text, flush=True)


if __name__ == "__main__":
    main()
