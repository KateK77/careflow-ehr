# Medical Software Prototype Experiment

Open [index.html](index.html) to launch the three browser prototypes. No dependencies are required. To keep appointments, messages, and saved papers available after refreshing, run `python -m http.server 8080 --bind 127.0.0.1` from this directory and visit `http://127.0.0.1:8080/`.

- [OpenEvidence prototype](openevidence.html) matches questions against a fixed set of studies and shows prepared summaries, PubMed citations, and question history. Try DAPA-CKD, SPRINT, semaglutide, and a topic outside the sample library.
- [MyChart prototype](mychart.html) uses a fictional patient record. Review test results and the health summary, book or cancel a demo visit, save a demo message, request a mock refill, or simulate a payment.
- [PubMed prototype](pubmed.html) searches four sample articles. Filter by year, publication type, title, or journal. Sort results, save papers, export PMIDs, or open the corresponding search on PubMed.

[Round 1 notes](rounds/01.md)

Each app may be developed and reviewed in its own Codex chat. Keep the source code, generation prompt, version, and feedback for each round in the shared CareFlow EHR repository. Use the user's feedback to start the next round for that app. Each app can run for up to five rounds and may finish early.

After an app's final version is frozen, have AI write and run easy, medium, and hard tests. Include single-step workflows, combined operations and persistence, and invalid inputs or repeated actions. Report passes, tests executed, pass rate, and failures for each app and difficulty level.
