const form = document.querySelector("#search");
const query = document.querySelector("#query");
const type = document.querySelector("#type");
const year = document.querySelector("#year");
const titleWords = document.querySelector("#title-words");
const journal = document.querySelector("#journal");
const sort = document.querySelector("#sort");
const results = document.querySelector("#results");
const count = document.querySelector("#count");
const savedButton = document.querySelector("#saved");
const savedKey = "medical-prototypes:papers";
let saved = [];
try {
  const stored = JSON.parse(localStorage.getItem(savedKey) || "[]");
  if (Array.isArray(stored)) saved = stored;
} catch {}
let savedOnly = false;

function render() {
  const terms = query.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
  const matches = papers.filter(paper => {
    const searchable = [paper.id, paper.title, paper.keywords, paper.journal].join(" ").toLowerCase();
    return terms.every(term => searchable.includes(term))
      && paper.title.toLowerCase().includes(titleWords.value.trim().toLowerCase())
      && paper.journal.toLowerCase().includes(journal.value.trim().toLowerCase())
      && (!type.value || paper.type === type.value)
      && (!year.value || paper.year >= Number(year.value))
      && (!savedOnly || saved.includes(paper.id));
  });
  if (sort.value === "recent") matches.sort((first, second) => second.year - first.year);
  count.textContent = matches.length + (matches.length === 1 ? " paper" : " papers");
  results.innerHTML = matches.map(paper => `<article class="card"><h3><a href="${articleUrl(paper.id)}">${paper.title}</a></h3><small>${paper.journal} · ${paper.year} · ${paper.type} · PMID ${paper.id}</small><p>${paper.summary}</p><button class="secondary" data-paper="${paper.id}" aria-pressed="${saved.includes(paper.id)}">${saved.includes(paper.id) ? "Remove from saved" : "Save paper"}</button></article>`).join("") || "<p class='card'>No papers match these filters.</p>";
}
form.onsubmit = event => {
  event.preventDefault();
  render();
};
savedButton.onclick = () => {
  savedOnly = !savedOnly;
  savedButton.setAttribute("aria-pressed", String(savedOnly));
  render();
};
results.onclick = event => {
  const button = event.target.closest("[data-paper]");
  if (!button) return;
  const id = button.dataset.paper;
  const updated = saved.includes(id) ? saved.filter(value => value !== id) : [...saved, id];
  try {
    localStorage.setItem(savedKey, JSON.stringify(updated));
  } catch {
    count.textContent = "Browser storage is unavailable.";
    return;
  }
  saved = updated;
  render();
  results.querySelector('[data-paper="' + id + '"]')?.focus();
};
render();

document.querySelector("#advanced").onsubmit = form.onsubmit;
sort.onchange = render;
document.querySelector("#live").onclick = () => {
  if (!form.reportValidity()) return;
  const publicationType = {Trial:"Randomized Controlled Trial[pt]", Review:"Review[pt]"}[type.value];
  const term = [
    query.value.trim(),
    titleWords.value.trim() && titleWords.value.trim() + "[Title]",
    journal.value.trim() && journal.value.trim() + "[Journal]",
    publicationType,
    year.value && year.value + ":3000[dp]"
  ].filter(Boolean).map(part => "(" + part + ")").join(" AND ");
  const url = new URL("https://pubmed.ncbi.nlm.nih.gov/");
  if (term) url.searchParams.set("term", term);
  if (sort.value === "recent") url.searchParams.set("sort", "date");
  window.open(url.href, "_blank", "noopener,noreferrer");
};
document.querySelector("#export").onclick = () => {
  if (!saved.length) {
    count.textContent = "Save at least one paper before exporting.";
    return;
  }
  const url = URL.createObjectURL(new Blob([saved.join("\n") + "\n"], {type:"text/plain"}));
  const link = document.createElement("a");
  link.href = url;
  link.download = "saved-pmids.txt";
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
