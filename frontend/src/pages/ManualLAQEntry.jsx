import React, { useState } from 'react'
import './ManualLAQEntry.css'

const createReply = () => ({ id: Date.now() + Math.random(), text: '', files: [] })
const createNode = () => ({ id: Date.now() + Math.random(), question: '', reply: createReply(), followUps: [] })
// follow-up nodes are simple and must not contain further followUps
const createFollowUp = () => ({ id: Date.now() + Math.random(), question: '', reply: createReply() })

function QuestionNode({ node, onChange, onRemove, level = 0 }) {
  const update = (changes) => onChange({ ...node, ...changes })

  const setQuestion = (q) => update({ question: q })

  const setReplyText = (text) => update({ reply: { ...node.reply, text } })

  const setReplyFiles = (files) => update({ reply: { ...node.reply, files: Array.from(files || []) } })

  // only root nodes should be able to add follow-ups; follow-ups created this way have no nested followUps
  const addFollowUp = () => update({ followUps: [...(node.followUps || []), createFollowUp()] })

  const updateFollowUp = (idx, updatedChild) => {
    const copy = (node.followUps || []).map((c) => ({ ...c }))
    copy[idx] = updatedChild
    update({ followUps: copy })
  }

  const removeFollowUp = (idx) => {
    const copy = [...(node.followUps || [])]
    copy.splice(idx, 1)
    update({ followUps: copy })
  }

  return (
    <div className="qa-node" style={{ marginLeft: level * 18 }}>
      <div className="qa-header">
        <div className="qa-index">{/* index display handled by parent */}</div>
        <div className="qa-actions">
          {level === 0 && (
            <button type="button" onClick={addFollowUp} className="small">Add Sub-question</button>
          )}
          {onRemove && <button type="button" onClick={onRemove} className="danger small">Remove</button>}
        </div>
      </div>

      <div className="qa-row">
        <div className="qa-col qa-col-question">
          <label>Question</label>
          <textarea value={node.question} onChange={(e) => setQuestion(e.target.value)} placeholder="Enter question text" />
        </div>

        <div className="qa-col qa-col-replies">
          <label>Reply</label>
          <div className="reply-item">
            <div className="form-row">
              <textarea value={node.reply.text} onChange={(e) => setReplyText(e.target.value)} placeholder="Enter reply text" />
            </div>

            <div className="form-row">
              <input
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.xls,.xlsx,.csv"
                onChange={(e) => setReplyFiles(e.target.files)}
              />
              {node.reply.files && node.reply.files.length > 0 && (
                <div className="attachments-list">
                  {node.reply.files.map((f, i) => (
                    <div key={i} className="attachment-item">{f.name} ({Math.round(f.size / 1024)} KB)</div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {(node.followUps || []).length > 0 && (
        <div className="followups">
          {(node.followUps || []).map((child, ci) => (
            <QuestionNode
              key={child.id}
              node={child}
              onChange={(n) => updateFollowUp(ci, n)}
              onRemove={() => removeFollowUp(ci)}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function ManualLAQEntry() {
  const [title, setTitle] = useState('')
  const [laqType, setLaqType] = useState('starred')
  const [laqNumber, setLaqNumber] = useState('')
  const [mlaName, setMlaName] = useState('')
  const [date, setDate] = useState('')
  const [qaPairs, setQaPairs] = useState([createNode()])

  const addQAPair = () => setQaPairs([...qaPairs, createNode()])

  const updateQAPair = (idx, updated) => {
    const copy = qaPairs.map((q) => ({ ...q }))
    copy[idx] = updated
    setQaPairs(copy)
  }

  const removeQAPair = (idx) => {
    const copy = [...qaPairs]
    copy.splice(idx, 1)
    setQaPairs(copy)
  }

  const validateAll = () => {
    if (!title.trim()) return 'Title is required'
    // ensure each question and every reply exists; follow-ups must NOT have further follow-ups
    const validateRootNode = (n) => {
      if (!n.question || !n.question.trim()) return 'Every question must have text'
      const r = n.reply || { text: '', files: [] }
      const hasText = r.text && r.text.trim()
      const hasFiles = r.files && r.files.length > 0
      if (!hasText && !hasFiles) return 'Each reply must contain text or at least one file'

      // validate follow-ups (they must be simple and cannot have further follow-ups)
      const followUps = n.followUps || []
      for (const child of followUps) {
        if (!child.question || !child.question.trim()) return 'Every follow-up question must have text'
        const cr = child.reply || { text: '', files: [] }
        const chHasText = cr.text && cr.text.trim()
        const chHasFiles = cr.files && cr.files.length > 0
        if (!chHasText && !chHasFiles) return 'Each reply must contain text or at least one file'
        if (child.followUps && child.followUps.length > 0) return 'Follow-up questions cannot have further follow-ups'
      }

      return null
    }

    for (const n of qaPairs) {
      const err = validateRootNode(n)
      if (err) return err
    }
    return null
  }

  // Assemble only two levels: root nodes and their follow-ups (follow-ups have no nested follow-ups)
  const assemble = (nodes) => nodes.map((n) => ({
    question: n.question,
    reply: (n.reply && { text: n.reply.text || null, files: n.reply.files ? n.reply.files.map((f) => ({ name: f.name, size: f.size, type: f.type })) : [] }) || { text: null, files: [] },
    followUps: (n.followUps || []).map((f) => ({
      question: f.question,
      reply: (f.reply && { text: f.reply.text || null, files: f.reply.files ? f.reply.files.map((ff) => ({ name: ff.name, size: ff.size, type: ff.type })) : [] }) || { text: null, files: [] }
    }))
  }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    const err = validateAll()
    if (err) return alert(err)

    const payload = {
      title,
      laq_type: laqType,
      laq_number: laqNumber, // alphanumeric allowed
      mla_name: mlaName,
      date,
      qa_pairs: assemble(qaPairs)
    }

    try {
      // Collect all files into a map by filename to send to backend (include follow-up replies)
      const filesMap = {}
      qaPairs.forEach((q) => {
        const r = q.reply
        if (r && r.files && r.files.length) {
          r.files.forEach((f) => {
            if (f instanceof File) filesMap[f.name] = f
          })
        }
        ;(q.followUps || []).forEach((child) => {
          const cr = child.reply
          if (cr && cr.files && cr.files.length) {
            cr.files.forEach((f) => {
              if (f instanceof File) filesMap[f.name] = f
            })
          }
        })
      })

      // Debug: ensure we have real File objects and inspect payload
      console.debug('Manual LAQ payload', payload)
      console.debug('Submitting manual LAQ; filesMap keys:', Object.keys(filesMap))

      // Lazy-import API helper to avoid circular issues
      const { submitManualLAQ } = await import('../services/api')
      const res = await submitManualLAQ(payload, filesMap)
      alert(`Manual LAQ submitted. Stored documents: ${res.stored_documents}`)
    } catch (e) {
      console.error(e)
      alert('Failed to submit manual LAQ: ' + (e.response?.data?.detail || e.message))
    }
  }

  return (
    <div className="manual-page">
      <div className="manual-container">
        {/* <h2>Manual LAQ Entry</h2> */}

        <form onSubmit={handleSubmit} className="manual-form">
          <div className="form-row">
            <label>LAQ Title / Subject</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Enter LAQ title or subject" />
          </div>

          <div className="form-row small-grid">
            <div>
              <label>LAQ Type</label>
              <select value={laqType} onChange={(e) => setLaqType(e.target.value)}>
                <option value="starred">Starred</option>
                <option value="unstarred">Unstarred</option>
              </select>
            </div>

            <div>
              <label>LAQ Number</label>
              <input value={laqNumber} onChange={(e) => setLaqNumber(e.target.value)} placeholder="e.g. LAQ-123A" />
            </div>

            <div>
              <label>MLA Name</label>
              <input value={mlaName} onChange={(e) => setMlaName(e.target.value)} placeholder="Person who tabled the LAQ" />
            </div>

            <div>
              <label>Date (to be answered on)</label>
              <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
            </div>
          </div>

          <div className="qa-section">
            <h3>Question & Answer Pairs</h3>

            {qaPairs.map((qa, idx) => (
              <div key={qa.id} className="qa-item">
                <div className="qa-meta">
                  <div className="qa-index">Q{idx + 1}</div>
                  <div className="qa-actions">
                    <button type="button" onClick={() => removeQAPair(idx)} className="danger small">Remove Question</button>
                  </div>
                </div>

                <QuestionNode
                  node={qa}
                  onChange={(n) => updateQAPair(idx, n)}
                  onRemove={null}
                  level={0}
                />
              </div>
            ))}

            <div className="qa-controls">
              <button type="button" onClick={addQAPair}>Add Question</button>
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="primary">Save Manual LAQ</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ManualLAQEntry
