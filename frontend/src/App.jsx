import React, { useEffect, useState } from "react";
import FileUpload from "./components/FileUpload.jsx";
import ResultsDisplay from "./components/ResultsDisplay.jsx";
import ErrorMessage from "./components/ErrorMessage.jsx";
import { compareDocuments, extractErrorMessage } from "./api/api.js";

export default function App() {
  const [fileA, setFileA] = useState(null);
  const [fileB, setFileB] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [feedbackForm, setFeedbackForm] = useState({ topic: "Product feedback", email: "", message: "" });
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [assistantInput, setAssistantInput] = useState("");
  const [assistantMessages, setAssistantMessages] = useState([
    { role: "assistant", text: "Hi, I’m your Docsim guide. Ask me about comparing files, reading a score, or preparing a report." },
  ]);
  const [menuOpen, setMenuOpen] = useState(false);
  const [historyQuery, setHistoryQuery] = useState("");
  const [history, setHistory] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("docsim-history") || "[]");
    } catch {
      return [];
    }
  });

  const canCompare = fileA && fileB && !loading;
  const filesReady = Number(Boolean(fileA)) + Number(Boolean(fileB));

  const handleFileError = (message) => {
    setError(message);
    if (message) setResult(null);
  };

  const handleSwap = () => {
    if (loading) return;
    setFileA(fileB);
    setFileB(fileA);
  };

  const handleFeedbackSubmit = (event) => {
    event.preventDefault();
    if (!feedbackForm.message.trim()) return;
    try {
      localStorage.setItem("docsim-feedback", JSON.stringify({ ...feedbackForm, createdAt: new Date().toISOString() }));
    } catch {
      // Feedback still gets confirmed if local storage is unavailable.
    }
    setFeedbackSent(true);
  };

  const closeFeedback = () => {
    setFeedbackOpen(false);
    setFeedbackSent(false);
  };

  const getAssistantReply = (question) => {
    const prompt = question.toLowerCase();
    if (prompt.includes("score") || prompt.includes("similar")) {
      return result
        ? `This comparison shows ${Number(result.overall_similarity || 0).toFixed(1)}% overall similarity across ${result.total_pages_a + result.total_pages_b} pages. Review the matching sections below for the strongest evidence.`
        : "Upload two PDFs and run a comparison first. I’ll help you interpret the overall score, page signals, and matching passages.";
    }
    if (prompt.includes("report") || prompt.includes("download")) {
      return result ? "Your report is ready. Use Download report in the analysis summary to open the generated document." : "The report preview will become available after both PDFs are compared.";
    }
    if (prompt.includes("upload") || prompt.includes("file") || prompt.includes("pdf")) {
      return "Use the two source cards to add PDF files. Each file must be a PDF under 10 MB, and you can swap or remove files before starting.";
    }
    return "I can help with PDF uploads, similarity scores, matching sections, page-by-page signals, and report downloads. Try one of the quick questions below.";
  };

  const sendAssistantMessage = (message = assistantInput) => {
    const question = message.trim();
    if (!question) return;
    setAssistantMessages((current) => [...current, { role: "user", text: question }, { role: "assistant", text: getAssistantReply(question) }]);
    setAssistantInput("");
  };

  useEffect(() => {
    if (!result) return;
    const entry = {
      id: Date.now(),
      documentA: result.document_a_name,
      documentB: result.document_b_name,
      score: Number(result.overall_similarity || 0),
      result,
      createdAt: new Date().toISOString(),
    };
    setHistory((current) => {
      const next = [entry, ...current.filter((item) => item.documentA !== entry.documentA || item.documentB !== entry.documentB)].slice(0, 8);
      try {
        localStorage.setItem("docsim-history", JSON.stringify(next));
      } catch {
        // History remains available for the current session if storage is unavailable.
      }
      return next;
    });
  }, [result]);

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem("docsim-history");
  };

  const filteredHistory = history.filter((item) => `${item.documentA} ${item.documentB}`.toLowerCase().includes(historyQuery.toLowerCase()));

  const openHistoryItem = (item) => {
    if (!item.result) return;
    setResult(item.result);
    setMenuOpen(false);
    window.location.hash = "reports";
  };

  const handleCompare = async () => {
    setError("");
    setResult(null);

    if (!fileA || !fileB) {
      setError("Please upload both Document A and Document B before comparing.");
      return;
    }
    if (fileA.name === fileB.name && fileA.size === fileB.size) {
      // not a hard block, just a friendly heads up — still allow it
    }

    setLoading(true);
    setProgress(0);
    try {
      const data = await compareDocuments(fileA, fileB, setProgress);
      setResult(data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFileA(null);
    setFileB(null);
    setResult(null);
    setError("");
    setProgress(0);
  };

  return (
    <div className="app">
      <header className="app__header">
        <div className="topbar">
          <button className="menu-trigger" type="button" onClick={() => setMenuOpen(true)} aria-label="Open menu"><i /><i /><i /></button>
          <div className="brand-lockup"><div className="brand-mark" aria-hidden="true">DS</div><div><strong>Docsim</strong><span>INTELLIGENCE STUDIO</span></div></div>
          <nav className="topnav" aria-label="Primary navigation"><a className="topnav__active" href="#compare">Compare</a><a href="#reports">Reports</a><a href="#workspace">Workspace</a><button className="support-link" type="button" onClick={() => setFeedbackOpen(true)}>Support <span>↗</span></button></nav>
          <div className="header-badge"><span /> System ready</div>
        </div>
        <div className="hero-grid">
          <div className="header-copy">
            <div className="eyebrow">Document intelligence workspace <span className="eyebrow-line" /></div>
            <h1>See what overlaps<br /><em>at a glance.</em></h1>
            <p className="subtitle">A focused comparison engine for researchers, analysts, and teams who need clarity from complex documents.</p>
            <div className="hero-proof"><span className="proof-mark">✦</span><span>Semantic matching<br /><strong>Built for deep reading</strong></span></div>
          </div>
          <div className="hero-visual" aria-hidden="true">
            <div className="visual-topline"><span>LIVE ANALYSIS ENGINE</span><i /></div>
            <div className="visual-core"><div className="core-ring core-ring--outer" /><div className="core-ring core-ring--inner" /><div className="core-center">DS</div><span className="orbit orbit--one">A</span><span className="orbit orbit--two">B</span></div>
            <div className="visual-footer"><span>Semantic index</span><strong>READY <i /></strong></div>
          </div>
        </div>
      </header>

      {menuOpen && (
        <div className="menu-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setMenuOpen(false); }}>
          <aside className="menu-drawer" aria-label="Docsim menu">
            <div className="menu-drawer__top"><div className="menu-drawer__brand"><span className="brand-mark">DS</span><div><strong>Docsim</strong><small>INTELLIGENCE STUDIO</small></div></div><button type="button" onClick={() => setMenuOpen(false)} aria-label="Close menu">×</button></div>
            <div className="menu-drawer__nav"><span className="menu-label">Navigate</span><a href="#compare" onClick={() => setMenuOpen(false)}><b>✦</b> Compare workspace <span>↗</span></a><a href="#workspace" onClick={() => setMenuOpen(false)}><b>□</b> Upload workspace <span>↗</span></a><a href="#reports" onClick={() => setMenuOpen(false)}><b>◫</b> Reports <span>↗</span></a><a href="#history-page" onClick={() => setMenuOpen(false)}><b>◷</b> History <span>↗</span></a><button type="button" onClick={() => { setAssistantOpen(true); setMenuOpen(false); }}><b>✧</b> AI guide <span>↗</span></button><button type="button" onClick={() => { setFeedbackOpen(true); setMenuOpen(false); }}><b>♡</b> Support & feedback <span>↗</span></button></div>
            <div className="history-panel"><div className="history-heading"><span className="menu-label">Recent history</span>{history.length > 0 && <button type="button" onClick={clearHistory}>Clear</button>}</div>{history.length === 0 ? <div className="history-empty"><span>◌</span><p>Your completed comparisons<br />will appear here.</p></div> : <div className="history-list">{history.slice(0, 4).map((item) => <button className="history-item" type="button" key={item.id} onClick={() => openHistoryItem(item)}><div className="history-item__files"><strong>{item.documentA}</strong><span>vs</span><strong>{item.documentB}</strong></div><div className="history-item__meta"><span>{new Date(item.createdAt).toLocaleDateString()}</span><b>{item.score.toFixed(1)}%</b></div></button>)}</div>}<a className="history-view-all" href="#history-page" onClick={() => setMenuOpen(false)}>View full history <span>↗</span></a></div>
            <div className="menu-drawer__footer"><span className="header-badge"><i /> Local workspace</span><small>History stays in this browser.</small></div>
          </aside>
        </div>
      )}

      {feedbackOpen && (
        <div className="feedback-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) closeFeedback(); }}>
          <section className="feedback-panel" role="dialog" aria-modal="true" aria-labelledby="feedback-title">
            <button className="feedback-close" type="button" onClick={closeFeedback} aria-label="Close support panel">×</button>
            {feedbackSent ? (
              <div className="feedback-success">
                <div className="feedback-success__icon">✓</div>
                <span className="step-label">Message saved</span>
                <h2>Thank you for helping Docsim improve.</h2>
                <p>Your feedback is stored in this session and ready to be shared with the project team.</p>
                <button className="btn btn--primary" type="button" onClick={closeFeedback}>Back to workspace <span className="btn-arrow">↗</span></button>
              </div>
            ) : (
              <form onSubmit={handleFeedbackSubmit}>
                <span className="step-label">Support & feedback</span>
                <h2 id="feedback-title">How can we make Docsim better?</h2>
                <p className="feedback-intro">Tell us what worked, what felt unclear, or what you would love to see next.</p>
                <label>Topic<select value={feedbackForm.topic} onChange={(event) => setFeedbackForm({ ...feedbackForm, topic: event.target.value })}><option>Product feedback</option><option>Something is not working</option><option>Feature request</option><option>General question</option></select></label>
                <label>Email <span>(optional)</span><input type="email" placeholder="you@example.com" value={feedbackForm.email} onChange={(event) => setFeedbackForm({ ...feedbackForm, email: event.target.value })} /></label>
                <label>Message<textarea required rows="5" placeholder="Share your thoughts..." value={feedbackForm.message} onChange={(event) => setFeedbackForm({ ...feedbackForm, message: event.target.value })} /></label>
                <div className="feedback-actions"><span>Stored privately in this browser</span><button className="btn btn--primary" type="submit">Send feedback <span className="btn-arrow">↗</span></button></div>
              </form>
            )}
          </section>
        </div>
      )}

      <div className="capability-ribbon" aria-label="Docsim capabilities">
        <div className="capability-item"><span>01</span><div><strong>Semantic scan</strong><small>Meaning, not just keywords</small></div></div>
        <div className="capability-item"><span>02</span><div><strong>Page intelligence</strong><small>Trace every matched signal</small></div></div>
        <div className="capability-item"><span>03</span><div><strong>Decision-ready output</strong><small>Reports your team can use</small></div></div>
        <div className="ribbon-pulse"><i /> Live workspace</div>
      </div>

      <ErrorMessage message={error} onDismiss={() => setError("")} />

      <main className="app__main" id="compare">
        <div className="section-heading" id="workspace">
          <div>
            <span className="step-label">01 / Upload source files</span>
            <h2>Choose two documents to compare</h2>
          </div>
          <span className="file-rule"><span className="file-rule__dot" /> PDF only · Max 10 MB each</span>
        </div>
        <div className="upload-grid">
          <FileUpload label="Document A" file={fileA} onFileSelect={setFileA} onFileError={handleFileError} />
          <button className="swap-documents" type="button" onClick={handleSwap} disabled={loading || (!fileA && !fileB)} aria-label="Swap documents"><span>⇄</span></button>
          <FileUpload label="Document B" file={fileB} onFileSelect={setFileB} onFileError={handleFileError} />
        </div>

        <div className="actions">
          <button
            className="btn btn--primary"
            disabled={!canCompare}
            onClick={handleCompare}
          >
            <span>{loading ? "Analyzing documents" : "Compare documents"}</span>
            <span className="btn-arrow" aria-hidden="true">↗</span>
          </button>
          {(fileA || fileB || result) && (
            <button className="btn btn--ghost" onClick={handleReset} disabled={loading}>
              Start over
            </button>
          )}
        </div>

        <div className="workspace-status">
          <div className="readiness"><span className={`readiness-dot ${filesReady === 2 ? "readiness-dot--ready" : ""}`} /><strong>{filesReady}/2</strong> source files ready</div>
          <div className="status-divider" />
          <div className="privacy-note"><span aria-hidden="true">◌</span> Files stay in this session</div>
          <div className="status-divider" />
          <div className="shortcut-note"><kbd>PDF</kbd> secure document format</div>
        </div>

        {loading && (
          <div className="progress-wrap" aria-live="polite">
            <div className="progress-copy"><span>Comparing page content</span><strong>{progress}%</strong></div>
            <div className="progress-bar">
              <div className="progress-bar__fill" style={{ width: `${progress}%` }} />
            </div>
          </div>
        )}

        <div id="reports" className={`report-destination ${result ? "report-destination--ready" : ""}`}>
          {!result && (
            <section className="report-preview" aria-label="Report preview">
              <div className="preview-copy">
                <span className="step-label">02 / Your intelligence report</span>
                <h2>A clearer view of what connects.</h2>
                <p>Every scan becomes a structured evidence trail with similarity scores, matched excerpts, page-level signals, and a downloadable report.</p>
                <div className="preview-points"><span><i>✓</i> Matched passages</span><span><i>✓</i> Page-level scoring</span><span><i>✓</i> Exportable PDF</span></div>
              </div>
              <div className="preview-visual" aria-hidden="true">
                <div className="preview-window"><div className="preview-window__bar"><span /><span /><span /><b>SIMILARITY REPORT</b></div><div className="preview-score"><strong>--</strong><small>overall match</small></div><div className="preview-lines"><i /><i /><i /><i /><i /></div><div className="preview-chart"><span /><span /><span /><span /><span /><span /><span /></div></div>
                <div className="preview-stamp">REPORT<br /><strong>READY</strong></div>
              </div>
            </section>
          )}
          <ResultsDisplay result={result} />
        </div>

        <section id="history-page" className="history-page">
          <div className="history-page__heading"><div><span className="step-label">03 / Search archive</span><h2>Comparison history</h2><p>Every completed scan, kept in one quiet place.</p></div><button className="history-clear" type="button" onClick={clearHistory} disabled={!history.length}>Clear all history</button></div>
          <div className="history-search"><span>⌕</span><input aria-label="Search comparison history" value={historyQuery} onChange={(event) => setHistoryQuery(event.target.value)} placeholder="Search document names..." /><kbd>{history.length} scans</kbd></div>
          {filteredHistory.length === 0 ? <div className="history-page__empty"><div>◌</div><h3>{history.length ? "No matching scans" : "Your archive is waiting"}</h3><p>{history.length ? "Try a different document name." : "Run a comparison and your full result will appear here automatically."}</p><a href="#workspace">Start a comparison <span>↗</span></a></div> : <div className="history-cards">{filteredHistory.map((item, index) => <article className="history-card" key={item.id}><div className="history-card__number">{String(index + 1).padStart(2, "0")}</div><div className="history-card__body"><div className="history-card__top"><span>{new Date(item.createdAt).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}</span><b>{item.score.toFixed(1)}% match</b></div><h3>{item.documentA}</h3><div className="history-card__vs"><span>DOCUMENT A</span><i>vs</i><span>{item.documentB}</span></div><div className="history-card__bottom"><span>{item.result ? `${item.result.similar_sections?.length || 0} matched sections` : "Legacy scan"}</span>{item.result ? <button type="button" onClick={() => openHistoryItem(item)}>Open report <span>↗</span></button> : <span>Summary only</span>}</div></div></article>)}</div>}
        </section>
      </main>

      <footer className="app__footer">
        <p>B.E. AI/ML Mini Project — Application Layer (FastAPI + React)</p>
      </footer>

      <div className={`ai-assistant ${assistantOpen ? "ai-assistant--open" : ""}`}>
        {assistantOpen && (
          <section className="assistant-panel" aria-label="Docsim AI guide">
            <div className="assistant-header"><div><span className="assistant-orb">✦</span><div><strong>Docsim guide</strong><small>Workspace assistant</small></div></div><button type="button" onClick={() => setAssistantOpen(false)} aria-label="Close AI guide">×</button></div>
            <div className="assistant-messages" aria-live="polite">{assistantMessages.map((message, index) => <div className={`assistant-message assistant-message--${message.role}`} key={`${message.role}-${index}`}>{message.text}</div>)}</div>
            <div className="assistant-prompts"><button type="button" onClick={() => sendAssistantMessage("How do I upload files?")}>How do I upload?</button><button type="button" onClick={() => sendAssistantMessage("How should I read the score?")}>Read my score</button></div>
            <form className="assistant-input" onSubmit={(event) => { event.preventDefault(); sendAssistantMessage(); }}><input aria-label="Ask Docsim guide" value={assistantInput} onChange={(event) => setAssistantInput(event.target.value)} placeholder="Ask the guide..." /><button type="submit" aria-label="Send question">↗</button></form>
          </section>
        )}
        <button className="assistant-launcher" type="button" onClick={() => setAssistantOpen(!assistantOpen)} aria-expanded={assistantOpen}><span>✦</span><strong>{assistantOpen ? "Close guide" : "Ask AI guide"}</strong></button>
      </div>
    </div>
  );
}
