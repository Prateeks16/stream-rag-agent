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
const demoMode = document.querySelector('#demo-mode');

apiInput.value = localStorage.getItem('strag-api-url') || apiInput.value;
apiInput.addEventListener('change', () => localStorage.setItem('strag-api-url', apiInput.value.replace(/\/$/, '')));

function setStatus(online, demo = false) {
  statusChip.classList.toggle('online', online);
  statusText.textContent = demo ? 'Demo data' : online ? 'Agent online' : 'Offline';
  navStatus.textContent = demo ? 'Demo mode' : online ? 'Agent online' : 'Agent unavailable';
}

async function checkHealth() {
  if (demoMode.checked) { setStatus(true, true); return; }
  try {
    const response = await fetch(`${apiInput.value.replace(/\/$/, '')}/health`, { signal: AbortSignal.timeout(4000) });
    setStatus(response.ok);
  } catch { setStatus(false); }
}

function getDemoAnswer(prompt) {
  const question = prompt.toLowerCase();
  if (question.includes('sensor') || question.includes('temperature') || question.includes('pressure') || question.includes('machine')) {
    return 'I found 3 recent sensor windows. Machine M-204 is the only one worth watching: temperature reached 78.4 C, pressure was 6.8 bar, and vibration measured 4.2 mm/s at 14:32 UTC. Its status is WARN. Machines M-201 and M-207 remained within their normal ranges.';
  }
  if (question.includes('account') || question.includes('transaction') || question.includes('eur') || question.includes('refund') || question.includes('payment')) {
    return 'Yes. The demo stream contains 3 financial transactions: TX-1048 for EUR 1,240.00 on account ACC-0833, TX-1051 for USD 86.40 on ACC-0418, and a EUR 52.00 refund on ACC-0833. The largest EUR transaction is TX-1048, a supplier transfer.';
  }
  return 'The demo index contains financial_transactions and sensor_data windows. Try asking about EUR transactions, account ACC-0833, machine temperature, pressure, or sensor warnings.';
}

demoMode.addEventListener('change', checkHealth);

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const prompt = promptInput.value.trim();
  const baseUrl = apiInput.value.trim().replace(/\/$/, '');
  error.textContent = '';
  if (!prompt || (!baseUrl && !demoMode.checked)) { error.textContent = 'Enter a question and an agent endpoint.'; return; }
  button.disabled = true;
  placeholder.style.display = 'none'; content.style.display = 'none'; loading.style.display = 'block';
  try {
    let responseText;
    if (demoMode.checked) {
      await new Promise((resolve) => setTimeout(resolve, 650));
      responseText = getDemoAnswer(prompt);
    } else {
      const response = await fetch(`${baseUrl}/query`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt }) });
      const data = await response.json();
      if (!response.ok || data.error) throw new Error(data.error || 'The agent could not answer this query.');
      responseText = data.answer;
    }
    answer.textContent = responseText;
    answerTime.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    loading.style.display = 'none'; content.style.display = 'block'; setStatus(true, demoMode.checked);
  } catch (queryError) {
    loading.style.display = 'none'; placeholder.style.display = 'block'; error.textContent = queryError.message || 'Unable to reach the agent.'; setStatus(false);
  } finally { button.disabled = false; }
});

checkHealth();