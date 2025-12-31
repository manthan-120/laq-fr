import { useState, useEffect } from 'react';
import './Validation.css';

const Validation = () => {
  const [validationSummary, setValidationSummary] = useState(null);
  const [usageStats, setUsageStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');

  useEffect(() => {
    loadValidationData();
  }, []);

  const loadValidationData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load validation summary
      const summaryResponse = await fetch('http://localhost:8000/api/validation/all');
      if (!summaryResponse.ok) {
        throw new Error('Failed to load validation summary');
      }
      const summaryData = await summaryResponse.json();
      setValidationSummary(summaryData);

      // Load usage statistics
      const statsResponse = await fetch('http://localhost:8000/api/validation/stats');
      if (!statsResponse.ok) {
        throw new Error('Failed to load usage statistics');
      }
      const statsData = await statsResponse.json();
      setUsageStats(statsData);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    return status === 'valid' ? 'status-valid' : 'status-invalid';
  };

  const getStatusIcon = (status) => {
    return status === 'valid' ? '✓' : '⚠';
  };

  if (loading) {
    return (
      <div className="validation-page">
        <div className="loading">Loading validation data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="validation-page">
        <div className="error">Error: {error}</div>
        <button onClick={loadValidationData} className="retry-btn">Retry</button>
      </div>
    );
  }

  return (
    <div className="validation-page">
      <div className="validation-header">
        <h1>Annexure Validation</h1>
        <p>Verify that LAQ references to annexures are properly matched</p>
        <button onClick={loadValidationData} className="refresh-btn">🔄 Refresh</button>
      </div>

      <div className="validation-tabs">
        <button
          className={activeTab === 'summary' ? 'tab-active' : ''}
          onClick={() => setActiveTab('summary')}
        >
          Summary
        </button>
        <button
          className={activeTab === 'details' ? 'tab-active' : ''}
          onClick={() => setActiveTab('details')}
        >
          Details
        </button>
        <button
          className={activeTab === 'stats' ? 'tab-active' : ''}
          onClick={() => setActiveTab('stats')}
        >
          Statistics
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'summary' && validationSummary && (
          <div className="summary-tab">
            <div className="summary-stats">
              <div className="stat-card">
                <h3>Total LAQs Validated</h3>
                <div className="stat-number">{validationSummary.total_laqs_validated}</div>
              </div>
              <div className="stat-card">
                <h3>Valid LAQs</h3>
                <div className="stat-number valid">{validationSummary.summary.valid_laqs}</div>
              </div>
              <div className="stat-card">
                <h3>Invalid LAQs</h3>
                <div className="stat-number invalid">{validationSummary.summary.invalid_laqs}</div>
              </div>
              <div className="stat-card">
                <h3>Overall Status</h3>
                <div className={`stat-status ${getStatusColor(validationSummary.summary.overall_status)}`}>
                  {getStatusIcon(validationSummary.summary.overall_status)} {validationSummary.summary.overall_status}
                </div>
              </div>
            </div>

            {validationSummary.validation_reports.length > 0 && (
              <div className="issues-section">
                <h3>LAQs with Issues</h3>
                <div className="issues-list">
                  {validationSummary.validation_reports
                    .filter(report => report.validation_status === 'invalid')
                    .map((report, index) => (
                      <div key={index} className="issue-item">
                        <div className="issue-header">
                          <span className="laq-number">LAQ {report.laq_number}</span>
                          <span className="pdf-name">{report.pdf_name}</span>
                          <span className={`status ${getStatusColor(report.validation_status)}`}>
                            {getStatusIcon(report.validation_status)}
                          </span>
                        </div>
                        <div className="issue-details">
                          {report.issues.map((issue, i) => (
                            <div key={i} className="issue-text">{issue}</div>
                          ))}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'details' && validationSummary && (
          <div className="details-tab">
            <h3>Detailed Validation Reports</h3>
            <div className="reports-list">
              {validationSummary.validation_reports.map((report, index) => (
                <div key={index} className="report-card">
                  <div className="report-header">
                    <h4>LAQ {report.laq_number} - {report.pdf_name}</h4>
                    <span className={`status ${getStatusColor(report.validation_status)}`}>
                      {getStatusIcon(report.validation_status)} {report.validation_status}
                    </span>
                  </div>

                  <div className="report-stats">
                    <div className="stat">LAQ Documents: {report.total_laq_documents}</div>
                    <div className="stat">Annexures: {report.total_annexures}</div>
                    <div className="stat">Uploaded Annexures: <span className="uploaded-count">{report.total_uploaded_annexures}</span></div>
                  </div>

                  <div className="annexure-info">
                    <p className="info-text">✓ Uploaded annexures are stored and searchable. They may show as "not mentioned" if the LAQ answer doesn't explicitly reference them.</p>
                  </div>

                  {report.referenced_annexures.length > 0 && (
                    <div className="annexure-list">
                      <strong>Mentioned in answer:</strong> {report.referenced_annexures.join(', ')}
                    </div>
                  )}

                  {report.available_annexures.length > 0 && (
                    <div className="annexure-list">
                      <strong>Available (Uploaded):</strong> {report.available_annexures.join(', ')}
                    </div>
                  )}

                  {report.issues.length > 0 && (
                    <div className="issues">
                      <strong>Issues:</strong>
                      <ul>
                        {report.issues.map((issue, i) => (
                          <li key={i}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'stats' && usageStats && (
          <div className="stats-tab">
            <div className="stats-grid">
              <div className="stat-card">
                <h3>Total Annexure Documents</h3>
                <div className="stat-number">{usageStats.total_annexure_documents}</div>
              </div>
              <div className="stat-card">
                <h3>Unique Annexure Labels</h3>
                <div className="stat-number">{usageStats.unique_annexure_labels}</div>
              </div>
              <div className="stat-card">
                <h3>Total References in LAQs</h3>
                <div className="stat-number">{usageStats.total_references_in_laqs}</div>
              </div>
              <div className="stat-card">
                <h3>Unique Referenced Annexures</h3>
                <div className="stat-number">{usageStats.unique_referenced_annexures}</div>
              </div>
            </div>

            <div className="usage-breakdown">
              <h3>Annexure Usage Breakdown</h3>
              <div className="usage-list">
                {Object.entries(usageStats.annexure_usage_breakdown).map(([annexure, count]) => (
                  <div key={annexure} className="usage-item">
                    <span className="annexure-label">{annexure}</span>
                    <span className="usage-count">{count} reference{count !== 1 ? 's' : ''}</span>
                  </div>
                ))}
              </div>
            </div>

            {(usageStats.unreferenced_annexures.length > 0 || usageStats.referenced_but_missing.length > 0) && (
              <div className="anomalies">
                <h3>Anomalies</h3>

                {usageStats.unreferenced_annexures.length > 0 && (
                  <div className="anomaly-section">
                    <h4>⚠ Unreferenced Annexures</h4>
                    <p>These annexures exist but are not referenced in any LAQ:</p>
                    <div className="anomaly-list">
                      {usageStats.unreferenced_annexures.map(annexure => (
                        <span key={annexure} className="anomaly-item">{annexure}</span>
                      ))}
                    </div>
                  </div>
                )}

                {usageStats.referenced_but_missing.length > 0 && (
                  <div className="anomaly-section">
                    <h4>❌ Missing Annexures</h4>
                    <p>These annexures are referenced in LAQs but don&#39;t exist:</p>
                    <div className="anomaly-list">
                      {usageStats.referenced_but_missing.map(annexure => (
                        <span key={annexure} className="anomaly-item">{annexure}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Validation;
