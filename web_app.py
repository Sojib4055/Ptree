from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from engine import analyze
from response.formatter import format

app = FastAPI()

INDEX_HTML = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Semantic Parser Studio</title>
    <style>
      :root {
        --ink: #12263a;
        --ink-soft: #3c5468;
        --accent: #f2b04f;
        --accent-2: #e36d5b;
        --panel: rgba(255, 255, 255, 0.86);
        --stroke: rgba(18, 38, 58, 0.12);
        --shadow: 0 22px 60px rgba(18, 38, 58, 0.18);
        --font-display: \"Bodoni MT\", \"Didot\", \"Garamond\", serif;
        --font-body: \"Gill Sans\", \"Trebuchet MS\", \"Optima\", sans-serif;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        font-family: var(--font-body);
        color: var(--ink);
        background: radial-gradient(circle at 15% 10%, #fbe9c6, transparent 45%),
          radial-gradient(circle at 85% 20%, #cbe9ff, transparent 40%),
          linear-gradient(145deg, #f6f4ef 0%, #e9f4fb 60%, #f8efe5 100%);
      }

      body::before,
      body::after {
        content: "";
        position: fixed;
        width: 240px;
        height: 240px;
        border-radius: 999px;
        filter: blur(2px);
        opacity: 0.25;
        z-index: 0;
      }

      body::before {
        background: #f4a259;
        top: -60px;
        right: -40px;
      }

      body::after {
        background: #7cc6fe;
        bottom: -80px;
        left: -60px;
      }

      main {
        position: relative;
        z-index: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 48px 20px 64px;
        gap: 28px;
      }

      header {
        text-align: center;
        animation: fadeIn 600ms ease;
      }

      h1 {
        font-family: var(--font-display);
        font-size: clamp(2.4rem, 5vw, 3.8rem);
        letter-spacing: 0.02em;
        margin: 0 0 8px;
      }

      p {
        margin: 0;
        color: var(--ink-soft);
        font-size: 1.05rem;
      }

      .card {
        width: min(900px, 100%);
        background: var(--panel);
        border: 1px solid var(--stroke);
        border-radius: 24px;
        padding: 28px;
        box-shadow: var(--shadow);
        animation: floatIn 680ms ease;
      }

      .prompt {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }

      input[type=\"text\"] {
        flex: 1 1 320px;
        padding: 14px 16px;
        border-radius: 16px;
        border: 1px solid rgba(18, 38, 58, 0.2);
        font-size: 1rem;
        font-family: var(--font-body);
        background: #ffffff;
        outline: none;
        transition: border 160ms ease, box-shadow 160ms ease;
      }

      input[type=\"text\"]:focus {
        border-color: var(--accent-2);
        box-shadow: 0 0 0 3px rgba(227, 109, 91, 0.2);
      }

      button {
        flex: 0 0 auto;
        padding: 14px 22px;
        border-radius: 999px;
        border: none;
        font-size: 1rem;
        font-family: var(--font-body);
        font-weight: 600;
        color: #1b140c;
        background: linear-gradient(120deg, var(--accent), var(--accent-2));
        cursor: pointer;
        box-shadow: 0 10px 18px rgba(227, 109, 91, 0.25);
        transition: transform 160ms ease, box-shadow 160ms ease;
      }

      button:hover {
        transform: translateY(-1px);
        box-shadow: 0 14px 20px rgba(227, 109, 91, 0.3);
      }

      .result {
        margin-top: 20px;
        padding: 18px;
        border-radius: 16px;
        background: rgba(18, 38, 58, 0.06);
        min-height: 64px;
        font-size: 1.02rem;
        color: var(--ink);
        animation: fadeIn 500ms ease;
      }

      .result.loading {
        color: var(--ink-soft);
      }

      .result.error {
        color: #9b2c2c;
      }

      .result h3 {
        margin: 0 0 12px;
        font-size: 1rem;
        color: var(--ink-soft);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }

      .table-wrap {
        margin-top: 12px;
        border-radius: 14px;
        overflow: auto;
        max-height: 320px;
        border: 1px solid rgba(18, 38, 58, 0.12);
        background: #ffffff;
      }

      table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
      }

      th,
      td {
        padding: 10px 12px;
        text-align: left;
        border-bottom: 1px solid rgba(18, 38, 58, 0.08);
      }

      th {
        position: sticky;
        top: 0;
        background: #f7f3ec;
        font-weight: 600;
        color: var(--ink);
      }

      tr:nth-child(even) td {
        background: rgba(18, 38, 58, 0.03);
      }

      .hint {
        margin-top: 14px;
        font-size: 0.95rem;
        color: var(--ink-soft);
      }

      .chip {
        display: inline-block;
        margin-top: 10px;
        padding: 6px 12px;
        border-radius: 999px;
        border: 1px dashed rgba(18, 38, 58, 0.25);
        font-size: 0.85rem;
        color: var(--ink);
        background: rgba(255, 255, 255, 0.6);
      }

      @media (max-width: 720px) {
        .card {
          padding: 22px;
        }

        button {
          width: 100%;
        }
      }

      @keyframes floatIn {
        from {
          opacity: 0;
          transform: translateY(16px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @keyframes fadeIn {
        from {
          opacity: 0;
        }
        to {
          opacity: 1;
        }
      }
    </style>
  </head>
  <body>
    <main>
      <header>
        <h1>Semantic Parser Studio</h1>
        <p>Ask a question about sales data and see the answer instantly.</p>
      </header>

      <section class=\"card\">
        <form id=\"question-form\" class=\"prompt\">
          <input id=\"question-input\" type=\"text\" placeholder=\"Show revenue in 2024\" autocomplete=\"off\" />
          <button type=\"submit\">Parse and Answer</button>
        </form>
        <div class=\"hint\">Parse trees are printed to the terminal where FastAPI is running.</div>
        <div class=\"chip\">Try: list sales orders in 2023</div>
        <div id=\"result\" class=\"result\"></div>
      </section>
    </main>

    <script>
      const form = document.getElementById("question-form");
      const input = document.getElementById("question-input");
      const result = document.getElementById("result");

      const buildTable = (rows) => {
        if (!rows.length) {
          return "";
        }
        const columns = Object.keys(rows[0]);
        const header = columns.map((col) => `<th>${col}</th>`).join("");
        const body = rows
          .map(
            (row) =>
              `<tr>${columns
                .map((col) => `<td>${row[col] ?? ""}</td>`)
                .join("")}</tr>`
          )
          .join("");
        return `
          <div class=\"table-wrap\">
            <table>
              <thead><tr>${header}</tr></thead>
              <tbody>${body}</tbody>
            </table>
          </div>
        `;
      };

      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const question = input.value.trim();
        result.classList.remove("error");

        if (!question) {
          result.textContent = "Type a question first.";
          result.classList.add("error");
          return;
        }

        result.textContent = "Thinking...";
        result.classList.add("loading");

        try {
          const response = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question })
          });

          const payload = await response.json();

          if (!response.ok) {
            throw new Error(payload.answer || "Request failed.");
          }

          const rows = Array.isArray(payload.rows) ? payload.rows : [];
          const tableMarkup = rows.length ? buildTable(rows) : "";

          result.innerHTML = `
            <h3>Answer</h3>
            <div>${payload.answer}</div>
            ${tableMarkup}
          `;
        } catch (error) {
          result.textContent = error.message;
          result.classList.add("error");
        } finally {
          result.classList.remove("loading");
        }
      });
    </script>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML


@app.post("/ask")
async def ask_question(request: Request):
    payload = await request.json()
    question = (payload.get("question") or "").strip()
    if not question:
        return JSONResponse({"answer": "Please enter a question."}, status_code=400)

    analysis = analyze(question, show_tree=True)
    answer = format(analysis["metric"], analysis["result"], analysis["filters"])
    rows = analysis["result"] if analysis["intent"] == "LIST" else None
    return {"answer": answer, "rows": rows}
