/**
 * LAQEditor - Interactive editor for validating and editing extracted LAQ data
 */

import { useState } from 'react'
import { HiPlus, HiTrash, HiSave, HiX } from 'react-icons/hi'
import './LAQEditor.css'

function LAQEditor({ initialData, availableAnnexures, onConfirm, onCancel }) {
  const [laqData, setLaqData] = useState(initialData)

  // Update metadata field
  const updateMetadata = (field, value) => {
    setLaqData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  // Update Q&A pair
  const updateQAPair = (index, field, value) => {
    setLaqData(prev => ({
      ...prev,
      qa_pairs: prev.qa_pairs.map((qa, i) => 
        i === index ? { ...qa, [field]: value } : qa
      )
    }))
  }

  // Add attachment to Q&A pair
  const addAttachment = (qaIndex, annexure) => {
    setLaqData(prev => ({
      ...prev,
      qa_pairs: prev.qa_pairs.map((qa, i) => {
        if (i === qaIndex) {
          const attachments = qa.attachments || []
          if (!attachments.includes(annexure)) {
            return { ...qa, attachments: [...attachments, annexure] }
          }
        }
        return qa
      })
    }))
  }

  // Remove attachment from Q&A pair
  const removeAttachment = (qaIndex, annexure) => {
    setLaqData(prev => ({
      ...prev,
      qa_pairs: prev.qa_pairs.map((qa, i) => {
        if (i === qaIndex) {
          return {
            ...qa,
            attachments: (qa.attachments || []).filter(a => a !== annexure)
          }
        }
        return qa
      })
    }))
  }

  // Delete Q&A pair
  const deleteQAPair = (index) => {
    if (laqData.qa_pairs.length <= 1) {
      alert('Cannot delete the last Q&A pair. At least one is required.')
      return
    }
    
    if (window.confirm('Are you sure you want to delete this Q&A pair?')) {
      setLaqData(prev => ({
        ...prev,
        qa_pairs: prev.qa_pairs.filter((_, i) => i !== index)
      }))
    }
  }

  // Add new Q&A pair
  const addQAPair = () => {
    setLaqData(prev => ({
      ...prev,
      qa_pairs: [
        ...prev.qa_pairs,
        {
          question: '',
          answer: '',
          attachments: []
        }
      ]
    }))
  }

  // Validate and submit
  const handleConfirm = () => {
    // Validate required fields
    if (!laqData.laq_number?.trim()) {
      alert('LAQ Number is required')
      return
    }

    if (!laqData.minister?.trim()) {
      alert('Minister name is required')
      return
    }

    if (!laqData.date?.trim()) {
      alert('Date is required')
      return
    }

    // Validate Q&A pairs
    for (let i = 0; i < laqData.qa_pairs.length; i++) {
      const qa = laqData.qa_pairs[i]
      if (!qa.question?.trim()) {
        alert(`Question ${i + 1} cannot be empty`)
        return
      }
    }

    onConfirm(laqData)
  }

  return (
    <div className="laq-editor">
      <div className="editor-header">
        <h2>Validate & Edit LAQ Data</h2>
        <p className="editor-subtitle">Review and modify the extracted data before storing to database</p>
      </div>

      {/* Metadata Section */}
      <div className="editor-section">
        <h3 className="section-title">Document Metadata</h3>
        <div className="metadata-grid">
          <div className="form-group">
            <label>Title</label>
            <input
              type="text"
              value={laqData.pdf_title || ''}
              onChange={(e) => updateMetadata('pdf_title', e.target.value)}
              placeholder="Enter document title"
            />
          </div>

          <div className="form-group">
            <label>LAQ Number *</label>
            <input
              type="text"
              value={laqData.laq_number || ''}
              onChange={(e) => updateMetadata('laq_number', e.target.value)}
              placeholder="e.g., 123"
              required
            />
          </div>

          <div className="form-group">
            <label>LAQ Type</label>
            <input
              type="text"
              value={laqData.laq_type || ''}
              onChange={(e) => updateMetadata('laq_type', e.target.value)}
              placeholder="e.g., Starred, Unstarred"
            />
          </div>

          <div className="form-group">
            <label>Minister *</label>
            <input
              type="text"
              value={laqData.minister || ''}
              onChange={(e) => updateMetadata('minister', e.target.value)}
              placeholder="Enter minister name"
              required
            />
          </div>

          <div className="form-group">
            <label>MLA Name</label>
            <input
              type="text"
              value={laqData.mla_name || ''}
              onChange={(e) => updateMetadata('mla_name', e.target.value)}
              placeholder="Enter MLA name"
            />
          </div>

          <div className="form-group">
            <label>Date *</label>
            <input
              type="text"
              value={laqData.date || ''}
              onChange={(e) => updateMetadata('date', e.target.value)}
              placeholder="e.g., 2024-01-15"
              required
            />
          </div>
        </div>
      </div>

      {/* Q&A Pairs Section */}
      <div className="editor-section">
        <div className="section-header-with-action">
          <h3 className="section-title">Q&A Pairs ({laqData.qa_pairs.length})</h3>
          <button className="btn-add-qa" onClick={addQAPair}>
            <HiPlus /> Add Q&A Pair
          </button>
        </div>

        {laqData.qa_pairs.map((qa, index) => (
          <div key={index} className="qa-editor-card">
            <div className="qa-header">
              <h4>Q&A Pair {index + 1}</h4>
              <button
                className="btn-delete-qa"
                onClick={() => deleteQAPair(index)}
                title="Delete this Q&A pair"
              >
                <HiTrash />
              </button>
            </div>

            <div className="form-group">
              <label>Question *</label>
              <textarea
                value={qa.question || ''}
                onChange={(e) => updateQAPair(index, 'question', e.target.value)}
                placeholder="Enter the question"
                rows="3"
                required
              />
            </div>

            <div className="form-group">
              <label>Answer</label>
              <textarea
                value={qa.answer || ''}
                onChange={(e) => updateQAPair(index, 'answer', e.target.value)}
                placeholder="Enter the answer"
                rows="5"
              />
            </div>

            {/* Attachments */}
            <div className="form-group">
              <label>Attachments</label>
              <div className="attachments-section">
                {qa.attachments && qa.attachments.length > 0 && (
                  <div className="current-attachments">
                    {qa.attachments.map((att, attIndex) => (
                      <div key={attIndex} className="attachment-tag">
                        <span>{att}</span>
                        <button
                          className="remove-attachment"
                          onClick={() => removeAttachment(index, att)}
                          title="Remove attachment"
                        >
                          <HiX />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {availableAnnexures.length > 0 && (
                  <div className="add-attachment">
                    <select
                      onChange={(e) => {
                        if (e.target.value) {
                          addAttachment(index, e.target.value)
                          e.target.value = ''
                        }
                      }}
                      className="attachment-select"
                    >
                      <option value="">+ Add attachment from uploaded files</option>
                      {availableAnnexures
                        .filter(ann => !(qa.attachments || []).includes(ann))
                        .map((ann, annIdx) => (
                          <option key={annIdx} value={ann}>{ann}</option>
                        ))}
                    </select>
                  </div>
                )}

                {availableAnnexures.length === 0 && (
                  <p className="no-annexures">No annexure files uploaded</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="editor-actions">
        <button className="btn-cancel" onClick={onCancel}>
          <HiX /> Cancel
        </button>
        <button className="btn-confirm" onClick={handleConfirm}>
          <HiSave /> Confirm & Store to Database
        </button>
      </div>
    </div>
  )
}

export default LAQEditor
