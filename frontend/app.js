const promptInput = document.querySelector('#prompt');
const apiInput = document.querySelector('#api-url');
const form = document.querySelector('#query-form');
const button = form.querySelector('button');
const error = document.querySelector('#form-error');
const placeholder = document.querySelector('#answer-placeholder');
const loading = document.querySelector('#answer-loading');
const content = document.querySelector('#answer-content');
const answer = document.querySelector('#answer-text');
const answerTime = document.querySelector('#answer-time');
const statusChip = document.querySelector('#status-chip');
const statusText = document.querySelector('#status-text');
const navStatus = document.querySelector('#nav-status');

apiInput.value = localStorage.getItem('strag-api-url') || apiInput.value;
apiInput.addEventListener('change', () => localStorage.setItem('strag-api-url', apiInput.value.replace(/\/$/, '')));

function setStatus(online) {
  statusChip.classList.toggle('online', online);
  statusText.textContent = online ? 'Agent online' : 'Offline';
  navStatus.textContent = online ? 'Agent online' : 'Agent unavailable';
}

async function checkHealth() {
  try {
    const response = await fetch(`${apiInput.value.replace(/\/$/, '')}/health`, { signal: AbortSignal.timeout(4000) });
    setStatus(response.ok);
  } catch { setStatus(false); }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const prompt = promptInput.value.trim();
  const baseUrl = apiInput.value.trim().replace(/\/$/, '');
  error.textContent = '';
  if (!prompt || !baseUrl) { error.textContent = 'Enter a question and an agent endpoint.'; return; }
  button.disabled = true;
  placeholder.style.display = 'none'; content.style.display = 'none'; loading.style.display = 'block';
  try {
    const response = await fetch(`${baseUrl}/query`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt }) });
    const data = await response.json();
    if (!response.ok || data.error) throw new Error(data.error || 'The agent could not answer this query.');
    answer.textContent = data.answer;
    answerTime.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    loading.style.display = 'none'; content.style.display = 'block'; setStatus(true);
  } catch (queryError) {
    loading.style.display = 'none'; placeholder.style.display = 'block'; error.textContent = queryError.message || 'Unable to reach the agent.'; setStatus(false);
  } finally { button.disabled = false; }
});

checkHealth();