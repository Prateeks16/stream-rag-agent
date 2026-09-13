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
const eventList = document.querySelector('#event-list');

const demoEvents = [
  { topic: 'financial_transactions', id: 'TX-1048', text: 'EUR 1,240.00 / transfer / ACC-0833', detail: 'Supplier transfer' },
  { topic: 'financial_transactions', id: 'TX-1051', text: 'USD 86.40 / purchase / ACC-0418', detail: 'Restaurant bill' },
  { topic: 'financial_transactions', id: 'TX-1054', text: 'EUR 52.00 / refund / ACC-0833', detail: 'Subscription refund' },
  { topic: 'financial_transactions', id: 'TX-1057', text: 'GBP 430.00 / withdrawal / ACC-0192', detail: 'ATM withdrawal' },
  { topic: 'financial_transactions', id: 'TX-1061', text: 'USD 2,800.00 / deposit / ACC-0704', detail: 'Salary deposit' },
  { topic: 'sensor_data', id: 'SEN-204', text: 'M-204 / 78.4 C / 6.8 bar', detail: 'WARN / 4.2 mm/s vibration' },
  { topic: 'sensor_data', id: 'SEN-201', text: 'M-201 / 46.2 C / 4.1 bar', detail: 'NORMAL / 1.1 mm/s vibration' },
  { topic: 'sensor_data', id: 'SEN-207', text: 'M-207 / 51.8 C / 5.4 bar', detail: 'NORMAL / 1.7 mm/s vibration' },
];

eventList.innerHTML = demoEvents.map((event) => `<button class="event-row" type="button" data-query="${event.id}"><span class="event-topic">${event.topic}</span><strong>${event.id}</strong><span>${event.text}</span><em>${event.detail}</em></button>`).join('');
eventList.querySelectorAll('.event-row').forEach((row) => row.addEventListener('click', () => {
  promptInput.value = `What do you know about ${row.dataset.query}?`;
  promptInput.focus();
}));

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
  const matchingEvents = demoEvents.filter((event) => question.includes(event.id.toLowerCase()) || question.includes(event.topic.replace('_', ' ')) || question.includes(event.topic));
  if (matchingEvents.length === 1) {
    const event = matchingEvents[0];
    return `${event.id} is in the ${event.topic} stream: ${event.text}. Details: ${event.detail}.`;
  }
  if (question.includes('sensor') || question.includes('temperature') || question.includes('pressure') || question.includes('machine') || question.includes('vibration')) {
    const sensors = demoEvents.filter((event) => event.topic === 'sensor_data');
    return `I found ${sensors.length} sensor events. ${sensors.map((event) => `${event.id} (${event.text}; ${event.detail})`).join('; ')}.`;
  }
  let transactions = demoEvents.filter((event) => event.topic === 'financial_transactions');
  const currency = ['eur', 'usd', 'gbp'].find((value) => question.includes(value));
  const account = demoEvents.map((event) => event.text.match(/ACC-\d+/)?.[0]).find((value) => value && question.includes(value.toLowerCase()));
  if (currency) transactions = transactions.filter((event) => event.text.toLowerCase().startsWith(currency));
  if (account) transactions = transactions.filter((event) => event.text.includes(account));
  if (question.includes('transaction') || question.includes('payment') || question.includes('refund') || question.includes('account') || currency || account) {
    if (!transactions.length) return 'No matching financial transaction was found in the demo stream. Try EUR, USD, GBP, ACC-0833, or TX-1048.';
    return `I found ${transactions.length} matching transaction${transactions.length === 1 ? '' : 's'}: ${transactions.map((event) => `${event.id} (${event.text}; ${event.detail})`).join('; ')}.`;
  }
  return 'The demo stream has 5 financial transactions and 3 sensor events. Ask about EUR, ACC-0833, TX-1048, M-204, temperature, or vibration.';
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