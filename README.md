<!-- PROJECT LOGO & BADGES -->
<p align="center">
  <img src="https://img.shields.io/badge/SystemForge-Evolving%20LLM%20System%20Messages-blueviolet?style=for-the-badge" alt="SystemForge LLM System Messages"/>
  <img src="https://img.shields.io/badge/Python-3.8%2B-informational?style=for-the-badge&logo=python" alt="Python 3.8+"/>
  <br>
  <img src="https://img.shields.io/badge/Flask-Web%20UI-green?style=for-the-badge&logo=flask" alt="Flask Web UI"/>
  <br><br>
  <img src="https://raw.githubusercontent.com/edent/SuperTinyIcons/master/images/svg/robot.svg" alt="AI Logo" width="80"/>
  <h1 align="center">SystemForge: Evolving LLM System Messages</h1>
  <p align="center"><b>Train, optimize, and evaluate conversational AI agents with reinforcement learning and web-based chat.</b></p>
  <p align="center">
    <a href="https://www.buymeacoffee.com/ambientflare" target="_blank">
      <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=☕&slug=ambientflare&button_colour=FFDD00&font_colour=000000&font_family=Arial&outline_colour=000000&coffee_colour=ffffff" alt="Buy Me A Coffee" style="height: 40px !important;width: 170px !important;" >
    </a>
  </p>
</p>

---

## ✨ Features
- **Web Chat Interface**: Interact with a chatbot through a modern Flask UI.
- **Agent-vs-Agent Evaluation**: Run automated, head-to-head agent conversations for robust testing.
- **Evolutionary RL Loop**: Optimize system messages using evolutionary strategies and custom scoring.
- **Configurable Agents**: Easily swap models, system messages, and starter conversations via `config.yaml`.
- **Custom Scoring**: Define success with flexible, editable rules in `scoring_rules.json`.
- **Logging & Lineage**: Visualize model evolution and keep detailed logs of every run.

---

## 🗂️ Project Structure
- `app.py` — Flask web server for chat interface
- `bridge.py` — Orchestrates agent-vs-agent conversations
- `partner_agent.py` — Partner agent logic
- `trainee_agent.py` — Trainee agent logic
- `train_rl.py` — RL for system message mutation and scoring
- `test_mutation.py` — Test system message mutation logic
- `config.yaml` — Main configuration (models, system messages, files)
- `scoring_rules.json` — Scoring rules for RL
- `texts/` — Conversation starter files
- `templates/` — HTML templates for web UI
- `static/` — Static files (if any)
- `logs/` — Logs, lineage, and evaluation artifacts

---

## 🚦 Step-by-Step: From Download to RL-Optimized System Messages

Follow these steps to go from your first download to running a reinforcement learning optimization and chatting with your improved system message!

### 1. 📥 Download & Install

1. **Clone or download the repository.**
2. **Create a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt):**
     ```cmd
     python -m venv venv
     .\venv\Scripts\activate.bat
     ```
   - **Linux/macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
3. **Install dependencies:**
   - **All platforms:**
     ```bash
     pip install -r requirements.txt
     # or if using python3 only:
     python3 -m pip install -r requirements.txt
     ```

### 2. ⚙️ Configure Your Agents

- Open `config.yaml` and set the following:
  - **`trainee` and `partner` URLs:** Point to your local or remote LLM API (e.g., Ollama).
  - **Models:** Choose which LLMs to use for each agent.
  - **System messages:** Customize the behavior/personality of each agent.
  - **Conversation starter files:** Add or edit files in `texts/` for realistic dialog openers.

### 3. 🧪 Run Your First System Message Optimization

1. **Start the system message optimization:**
   ```bash
   python train_rl.py
   ```
2. The script will simulate agent-vs-agent conversations, mutate the trainee's system message, and score responses using your rules in `scoring_rules.json`.
3. At the end, the script will print:
   - The **final winning system message** for your trainee agent.
   - Example:
     ```
     === FINAL WINNING SYSTEM MESSAGE ===
     Copy the following and paste it into your config.yaml under trainee.system_message:
     <your optimized system message here>
     ==============================
     ```

### 4. ✍️ Copy the Optimized System Message

- Open `config.yaml`.
- Replace the `trainee.system_message` value with the optimized system message from the RL output.
- Save the file.

### 5. 💬 Test Your Improved Agent in the Web UI

1. **Start the web server:**
   ```bash
   python app.py
   ```
2. Open [http://localhost:5000](http://localhost:5000) in your browser.
3. Chat with your trainee agent and experience the improved responses!

### 6. 🎯 Fine-Tune Your Scoring Rules (Make It Yours!)

To get the best results for your use case, you can fine-tune how the RL system scores conversations:

1. **Open `scoring_rules.json` in your favorite text editor.**

2. **Understand the structure:**
   - There are sections for things like length, repetition, conversational markers, questions, on-topic overlap, originality, typos, hedging, back-channeling, and more.
   - Each section has parameters for rewards and penalties (e.g., `min_words`, `too_short_penalty`, `contraction_reward`).

3. **Adjust the values:**
   - Want longer answers? Increase `min_words` or the reward for length.
   - Want more questions? Increase the reward for `question`.
   - Want more conversational style? Boost `conversational_markers` or `hedging` rewards.
   - Want less copying? Increase `originality` penalties.

4. **Example tweak:**
   ```json
   "length": {
     "min_words": 12,
     "too_short_penalty": -3,
     "too_long_penalty": -2
   },
   "question": {
     "reward": 2
   },
   "conversational_markers": {
     "contractions": ["I'm", "you're", "we're"],
     "contraction_reward": 2
   }
   ```

5. **Save the file and re-run system message optimization:**
   ```bash
   python train_rl.py
   ```
   - The new winner will reflect your updated scoring preferences!

6. **Iterate:**
   - Keep adjusting and re-running until the agent's output matches your ideal style, length, and tone.

**Tip:** You can always add new scoring criteria or remove ones you don't care about. The system message optimization will adapt to whatever you define!

---

## 🚀 Getting Started

1. **Create a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt):**
     ```cmd
     python -m venv venv
     .\venv\Scripts\activate.bat
     ```
   - **Linux/macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
2. **Activate the virtual environment:**
   - **All platforms:**
     ```bash
     # Activate the virtual environment
     # (Windows PowerShell)
     .\venv\Scripts\Activate.ps1
     # (Windows Command Prompt)
     .\venv\Scripts\activate.bat
     # (Linux/macOS)
     source venv/bin/activate
     ```
3. **Install dependencies:**
   - **All platforms:**
     ```bash
     pip install -r requirements.txt
     # or if using python3 only:
     python3 -m pip install -r requirements.txt
     ```

---

## 💬 Using the Lab

### Web Chat
1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Open [http://localhost:5000](http://localhost:5000) in your browser to use the chat interface.

### Agent-vs-Agent & RL
- **Simulate conversation:**
  ```bash
  python bridge.py
  ```
- **Reinforcement Learning (system message optimization):**
  ```bash
  python train_rl.py
  ```
- **Test system message mutation:**
  ```bash
  python test_mutation.py
  ```

---

## ⚙️ Configuration
- **`config.yaml`**: Set agent models, system messages, conversation files, and server port.
- **`scoring_rules.json`**: Customize scoring for RL system message optimization.
- **Conversation starters**: Add/edit files in `texts/`.

---

## 📦 Requirements
- Python 3.8+
- Flask
- PyYAML
- requests

Install all dependencies with `pip install -r requirements.txt`.

---

## 📝 Notes
- The agents expect a local or remote LLM API compatible with the `/api/chat` endpoint (e.g., Ollama, OpenAI-compatible server).
- RL loop logs and artifacts are saved in `logs/`.
- System messages are optimized for safety and tone; edit `config.yaml` to experiment.
- For advanced usage, modify `train_rl.py` and scoring rules.

---

## ☕ Support
If you find this project useful, please consider supporting development:

<p align="left">
  <a href="https://www.buymeacoffee.com/ambientflare" target="_blank">
    <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=☕&slug=ambientflare&button_colour=FFDD00&font_colour=000000&font_family=Arial&outline_colour=000000&coffee_colour=ffffff" alt="Buy Me A Coffee" style="height: 40px !important;width: 170px !important;" >
  </a>
</p>

---

## 📄 License
MIT
