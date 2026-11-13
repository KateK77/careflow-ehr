const form = document.querySelector("#ask");
const question = document.querySelector("#question");
const answer = document.querySelector("#answer");
document.querySelectorAll("[data-topic]").forEach(button => button.addEventListener("click", () => {
  question.value = button.dataset.topic;
  form.requestSubmit();
}));
form.addEventListener("submit", event => {
  event.preventDefault();
  const input = question.value.trim().toLowerCase();
  if (!input) {
    answer.textContent = "Enter a research question first.";
    return;
  }
  const topics = [/\b(dapa[ -]ckd|dapagliflozin)\b/, /\b(sprint|blood[ -]pressure)\b/, /\bsemaglutide\b/, /\b(semaglutide|obesity)\b/];
  const matches = papers.filter((paper, index) => topics[index].test(input));
  const content = matches.length ? matches.map(paper => `<article class="card"><h3>${paper.title}</h3><p>${paper.summary}</p><a href="${articleUrl(paper.id)}">PubMed · ${paper.id}</a></article>`).join("") : "<p class='card'>No topic matched in the sample library. Try one of the example questions.</p>";
  rememberQuestion(question.value.trim());
  answer.innerHTML = "<h2>Evidence from the sample library</h2>" + content;
});

const historyKey = "medical-prototypes:evidence-history";
const historyList = document.querySelector("#history");
let questions = [];
try {
  const stored = JSON.parse(localStorage.getItem(historyKey) || "[]");
  if (Array.isArray(stored)) questions = stored.filter(value => typeof value === "string");
} catch {}
function renderHistory() {
  historyList.replaceChildren();
  for (const previous of questions) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.className = "secondary";
    button.textContent = previous;
    button.onclick = () => {
      question.value = previous;
      form.requestSubmit();
    };
    item.append(button);
    historyList.append(item);
  }
}
function rememberQuestion(value) {
  questions = [value, ...questions.filter(previous => previous !== value)].slice(0, 8);
  try { localStorage.setItem(historyKey, JSON.stringify(questions)); } catch {}
  renderHistory();
}
document.querySelector("#clear").onclick = () => {
  questions = [];
  try { localStorage.removeItem(historyKey); } catch {}
  renderHistory();
};
renderHistory();
