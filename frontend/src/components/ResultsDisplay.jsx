import React from "react";
import { getReportDownloadUrl } from "../api/api";

function ScoreBadge({ score }) {
  const level = score >= 75 ? "high" : score >= 40 ? "medium" : "low";
  return <span className={`badge badge--${level}`}>{score.toFixed(1)}%</span>;
}

export default function ResultsDisplay({ result }) {
  if (!result) return null;

  const {
    overall_similarity,
    content_similarity,
    document_a_name,
    document_b_name,
    similar_sections,
    page_wise_stats,
    content_similar_sections = [],
    total_pages_a,
    total_pages_b,
    report_download_url,
  } = result;
  const similarity = Number(overall_similarity) || 0;
  const contentSimilarity = Number(content_similarity) || 0;
  const matchedSections = similar_sections.length;
  const averagePageScore = page_wise_stats.length
    ? page_wise_stats.reduce((total, page) => total + Number(page.similarity_score || 0), 0) / page_wise_stats.length
    : 0;
  const scoreColor = similarity >= 75 ? "var(--teal)" : similarity >= 40 ? "var(--coral)" : "var(--gold)";

  return (
    <div className="results">
      <div className="results__heading">
        <div>
          <span className="step-label">02 / Analysis complete</span>
          <h2>Similarity report</h2>
        </div>
        <span className="report-status"><span /> Ready to review</span>
      </div>
      <div className="results__summary">
        <div className="overall-score">
          <div className="score-ring" style={{ "--score": `${similarity * 3.6}deg`, "--score-color": scoreColor }}><div>
            <div className="overall-score__value">{similarity.toFixed(1)}%</div>
            <div className="overall-score__label">Text overlap</div>
          </div></div>
        </div>
        <div className="results__meta">
          <div className="document-meta"><span className="doc-index">A</span><p><strong>{document_a_name}</strong><span>{total_pages_a} pages analyzed</span></p></div>
          <div className="document-meta"><span className="doc-index doc-index--alt">B</span><p><strong>{document_b_name}</strong><span>{total_pages_b} pages analyzed</span></p></div>
        </div>
        <a
          className="btn btn--secondary"
          href={getReportDownloadUrl(report_download_url)}
          target="_blank"
          rel="noreferrer"
        >
          <span aria-hidden="true">↓</span> Download report
        </a>
      </div>

      <div className="result-metrics result-metrics--four">
        <div className="metric-card"><span className="metric-icon metric-icon--mint">↗</span><div><strong>{matchedSections}</strong><span>Matching sections</span></div></div>
        <div className="metric-card"><span className="metric-icon metric-icon--coral">◎</span><div><strong>{averagePageScore.toFixed(1)}%</strong><span>Average page score</span></div></div>
        <div className="metric-card"><span className="metric-icon metric-icon--ink">▤</span><div><strong>{total_pages_a + total_pages_b}</strong><span>Total pages scanned</span></div></div>
        <div className="metric-card"><span className="metric-icon metric-icon--semantic">≈</span><div><strong>{contentSimilarity.toFixed(1)}%</strong><span>Semantic content</span></div></div>
      </div>

      <section className="results__section">
        <div className="section-title"><div><span className="section-kicker">Content matches</span><h3>Similar sections</h3></div><span className="count-pill">{similar_sections.length} found</span></div>
        {similar_sections.length === 0 ? (
          <p className="muted">No closely matching sections were found.</p>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Doc A Page</th>
                  <th>Doc B Page</th>
                  <th>Doc A Excerpt</th>
                  <th>Doc B Excerpt</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {similar_sections.map((s, i) => (
                  <tr key={i}>
                    <td>{s.doc_a_page}</td>
                    <td>{s.doc_b_page}</td>
                    <td className="excerpt">{s.doc_a_excerpt}</td>
                    <td className="excerpt">{s.doc_b_excerpt}</td>
                    <td>
                      <ScoreBadge score={s.similarity_score} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="results__section">
        <div className="section-title"><div><span className="section-kicker">Meaning-based matches</span><h3>Semantic content matches</h3></div><span className="count-pill">{content_similar_sections.length} found</span></div>
        <p className="semantic-note">This score compares meaning, so paraphrased passages may match. It is a similarity signal, not a plagiarism verdict.</p>
        {content_similar_sections.length === 0 ? (
          <p className="muted">No pages crossed the semantic match threshold.</p>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead><tr><th>Doc A Page</th><th>Doc B Page</th><th>Doc A Content</th><th>Doc B Content</th><th>Meaning Score</th></tr></thead>
              <tbody>{content_similar_sections.map((section, index) => (
                <tr key={`${section.doc_a_page}-${section.doc_b_page}-${index}`}>
                  <td>{section.doc_a_page}</td><td>{section.doc_b_page}</td>
                  <td className="excerpt">{section.doc_a_excerpt}</td><td className="excerpt">{section.doc_b_excerpt}</td>
                  <td><ScoreBadge score={section.similarity_score} /></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </section>

      <section className="results__section page-signal">
        <div className="section-title"><div><span className="section-kicker">Similarity signal</span><h3>Page-by-page pattern</h3></div><span className="signal-legend"><i /> Low <i /> High</span></div>
        <div className="signal-grid">
          {page_wise_stats.map((page, index) => {
            const pageScore = Number(page.similarity_score || 0);
            return <div className="signal-column" key={`${page.page_number}-${index}`} title={`Page ${page.page_number}: ${pageScore.toFixed(1)}%`}><div className="signal-bar"><span style={{ height: `${Math.max(pageScore, 5)}%` }} /></div><small>{page.page_number}</small></div>;
          })}
        </div>
      </section>

      <section className="results__section">
        <div className="section-title"><div><span className="section-kicker">Document coverage</span><h3>Page-wise statistics</h3></div></div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Page (Doc A)</th>
                <th>Matched Page (Doc B)</th>
                <th>Similarity Score</th>
              </tr>
            </thead>
            <tbody>
              {page_wise_stats.map((p, i) => (
                <tr key={i}>
                  <td>{p.page_number}</td>
                  <td>{p.matched_page_in_other_doc ?? "—"}</td>
                  <td>
                    <ScoreBadge score={p.similarity_score} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
