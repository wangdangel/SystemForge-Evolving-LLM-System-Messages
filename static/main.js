document.addEventListener('DOMContentLoaded', () => {
  const systemData = document.getElementById('system-data');
  const systemMessage = JSON.parse(systemData.textContent);
  const chatContainer = document.getElementById('chat-container');
  const input = document.getElementById('message-input');
  const sendBtn = document.getElementById('send-btn');
  let dialog = [];

  function appendMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', role === 'user' ? 'user' : 'assistant');
    const bubble = document.createElement('div');
    bubble.classList.add('bubble');
    bubble.innerText = text;
    msgDiv.appendChild(bubble);
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  sendBtn.addEventListener('click', () => {
    const text = input.value.trim();
    if (!text) return;
    appendMessage('user', text);
    dialog.push({ role: 'user', content: text });
    input.value = '';
    fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: [{ role: 'system', content: systemMessage }, ...dialog] })
    })
      .then(res => res.json())
      .then(data => {
        const reply = data.reply;
        appendMessage('assistant', reply);
        dialog.push({ role: 'assistant', content: reply });
      })
      .catch(err => {
        appendMessage('assistant', '[Error] ' + err);
      });
  });

  input.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendBtn.click();
  });
});
