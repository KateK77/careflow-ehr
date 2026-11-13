function readList(key) {
  try {
    const values = JSON.parse(localStorage.getItem(key) || "[]");
    return Array.isArray(values) ? values : [];
  } catch {
    return [];
  }
}
function saveList(key, values, status) {
  try {
    localStorage.setItem(key, JSON.stringify(values));
    return true;
  } catch {
    status.textContent = "Browser storage is unavailable.";
    return false;
  }
}
const visitForm = document.querySelector("#visit");
const messageForm = document.querySelector("#message");
const visitStatus = document.querySelector("#visit-status");
const messageStatus = document.querySelector("#message-status");
const slots = document.querySelector("#slot");
const message = document.querySelector("#body");
const visitsKey = "medical-prototypes:visits";
const messagesKey = "medical-prototypes:messages";

function renderVisits() {
  const visits = readList(visitsKey);
  const list = document.querySelector("#visits");
  list.replaceChildren();
  for (const slot of visits) {
    const item = document.createElement("li");
    item.textContent = slot + " ";
    const cancel = document.createElement("button");
    cancel.className = "secondary";
    cancel.textContent = "Cancel";
    cancel.setAttribute("aria-label", "Cancel " + slot);
    cancel.onclick = () => {
      if (saveList(visitsKey, readList(visitsKey).filter(value => value !== slot), visitStatus)) {
        renderVisits();
        visitStatus.textContent = "Demo visit canceled.";
      }
    };
    item.append(cancel);
    list.append(item);
  }
  for (const option of slots.options) option.disabled = visits.includes(option.value);
}
function renderMessages() {
  const list = document.querySelector("#messages");
  list.replaceChildren(...readList(messagesKey).map(value => {
    const item = document.createElement("li");
    item.textContent = value;
    return item;
  }));
}
visitForm.onsubmit = event => {
  event.preventDefault();
  const visits = readList(visitsKey);
  if (!slots.value || visits.includes(slots.value)) return;
  if (saveList(visitsKey, [...visits, slots.value], visitStatus)) {
    visitForm.reset();
    renderVisits();
    visitStatus.textContent = "Demo visit booked.";
  }
};
messageForm.onsubmit = event => {
  event.preventDefault();
  const value = message.value.trim();
  if (!value) {
    messageStatus.textContent = "Enter a message first.";
    return;
  }
  if (saveList(messagesKey, [value, ...readList(messagesKey)], messageStatus)) {
    messageForm.reset();
    renderMessages();
    messageStatus.textContent = "Demo message saved in this browser.";
  }
};
renderVisits();
renderMessages();

function bindDemoAction(buttonId, statusId, key, confirmation) {
  const button = document.querySelector(buttonId);
  const status = document.querySelector(statusId);
  function render() {
    button.disabled = readList(key).length > 0;
    if (button.disabled) status.textContent = confirmation;
  }
  button.onclick = () => {
    if (saveList(key, [true], status)) render();
  };
  render();
}
bindDemoAction("#refill", "#refill-status", "medical-prototypes:refill", "Demo refill request recorded.");
bindDemoAction("#pay", "#payment-status", "medical-prototypes:payment", "Simulated payment recorded. No money was transferred.");
