/**
 * Upload page component - LAQ validation workflow
 */

import { useState, useRef } from 'react'
import { HiCloudUpload, HiDocument, HiCheckCircle, HiExclamation, HiX, HiPaperClip } from 'react-icons/hi'
import { processLAQForValidation, confirmAndStore } from '../services/api'
import LAQEditor from '../components/LAQEditor'
import './Upload.css'

function Upload() {
  // File states
  const [replyFile, setReplyFile] = useState(null)
  const [annexureFiles, setAnnexureFiles] = useState([])
  
  // Processing states
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState(null)
  
  // Validation states
  const [processingResponse, setProcessingResponse] = useState(null)
  const [showEditor, setShowEditor] = useState(false)
  
  // Success state
  const [storeSuccess, setStoreSuccess] = useState(null)
  
  // Refs
  const replyInputRef = useRef(null)
  const annexureInputRef = useRef(null)
  
  // Drag and drop states
  const [dragActive, setDragActive] = useState(false)

  // Handle drag events for reply document
  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleReplyFile(e.dataTransfer.files[0])
    }
  }

  // Handle reply file selection
  const handleReplyFile = (selectedFile) => {
    const validExtensions = ['.pdf', '.doc', '.docx']
    const fileExtension = selectedFile.name.toLowerCase().slice(selectedFile.name.lastIndexOf('.'))
    
    if (!validExtensions.includes(fileExtension)) {
      setError('Reply document must be PDF or Word file (.pdf, .doc, .docx)')
      return
    }

    const maxSize = 50 * 1024 * 1024 // 50MB
    if (selectedFile.size > maxSize) {
      setError('File size must be less than 50MB')
      return
    }

    setReplyFile(selectedFile)
    setError(null)
  }

  const handleReplyInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleReplyFile(e.target.files[0])
    }
  }

  const removeReplyFile = () => {
    setReplyFile(null)
    if (replyInputRef.current) {
      replyInputRef.current.value = ''
    }
  }

  // Handle annexure files
  const handleAnnexureInput = (e) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files)
      setAnnexureFiles(prev => [...prev, ...newFiles])
    }
  }

  const removeAnnexureFile = (index) => {
    setAnnexureFiles(prev => prev.filter((_, i) => i !== index))
  }

  // Process files and get data for validation
  const handleProcessAndValidate = async () => {
    if (!replyFile) {
      setError('Please select a reply document')
      return
    }

    setProcessing(true)
    setError(null)
    setShowEditor(false)
    setProcessingResponse(null)
    setStoreSuccess(null)

    try {
      const response = await processLAQForValidation(replyFile, annexureFiles)
      setProcessingResponse(response)
      setShowEditor(true)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Processing failed')
    } finally {
      setProcessing(false)
    }
  }

  // Confirm and store to database
  const handleConfirm = async (validatedData) => {
    setProcessing(true)
    setError(null)

    try {
      const response = await confirmAndStore(
        validatedData,
        processingResponse.stored_directory
      )
      
      setStoreSuccess(response)
      setShowEditor(false)
      
      // Reset form
      setReplyFile(null)
      setAnnexureFiles([])
      setProcessingResponse(null)
      if (replyInputRef.current) replyInputRef.current.value = ''
      if (annexureInputRef.current) annexureInputRef.current.value = ''
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to store data')
    } finally {
      setProcessing(false)
    }
  }

  const handleCancelValidation = () => {
    setShowEditor(false)
    setProcessingResponse(null)
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  // Show editor if processing succeeded
  if (showEditor && processingResponse) {
    return (
      <LAQEditor
        initialData={processingResponse.laq_data}
        availableAnnexures={processingResponse.available_annexures}
        onConfirm={handleConfirm}
        onCancel={handleCancelValidation}
      />
    )
  }

  return (
    <div className="upload-page">
      <div className="upload-container">
        <div className="upload-header">
          <h2>Upload LAQ Documents</h2>
          <p>Upload reply document and optional annexure files for processing</p>
        </div>

        {/* Reply Document Section */}
        <div className="section-card">
          <h3 className="section-title-inline">Reply Document *</h3>
          
          <div
            className={`upload-zone ${dragActive ? 'drag-active' : ''} ${replyFile ? 'has-file' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => !replyFile && replyInputRef.current?.click()}
          >
            <input
              ref={replyInputRef}
              type="file"
              accept=".pdf,.doc,.docx"
              onChange={handleReplyInput}
              style={{ display: 'none' }}
            />

            {!replyFile ? (
              <>
                <div className="upload-icon">
                  <HiCloudUpload />
                </div>
                <div className="upload-title">Drop reply document here or click to browse</div>
                <div className="upload-subtitle">Supports PDF and Word documents (.pdf, .doc, .docx) up to 50MB</div>
              </>
            ) : (
              <div className="file-preview">
                <div className="file-icon">
                  <HiDocument />
                </div>
                <div className="file-info">
                  <div className="file-name">{replyFile.name}</div>
                  <div className="file-size">{formatFileSize(replyFile.size)}</div>
                </div>
                <button
                  className="file-remove"
                  onClick={(e) => {
                    e.stopPropagation()
                    removeReplyFile()
                  }}
                  disabled={processing}
                >
                  <HiX />
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Annexure Files Section */}
        <div className="section-card">
          <h3 className="section-title-inline">Annexure Files (Optional)</h3>
          
          <div className="annexure-upload-area">
            <input
              ref={annexureInputRef}
              type="file"
              multiple
              accept=".xlsx,.xls,.pdf,.doc,.docx"
              onChange={handleAnnexureInput}
              style={{ display: 'none' }}
            />
            
            <button
              className="select-files-btn"
              onClick={() => annexureInputRef.current?.click()}
              disabled={processing}
            >
              <HiPaperClip />
              Select Annexure Files
            </button>

            {annexureFiles.length > 0 && (
              <div className="selected-files">
                <p className="files-count">{annexureFiles.length} file(s) selected</p>
                <div className="files-list">
                  {annexureFiles.map((file, index) => (
                    <div key={index} className="file-item">
                      <HiDocument className="file-icon-sm" />
                      <span className="file-name-sm">{file.name}</span>
                      <span className="file-size-sm">{formatFileSize(file.size)}</span>
                      <button
                        className="remove-btn-sm"
                        onClick={() => removeAnnexureFile(index)}
                        disabled={processing}
                      >
                        <HiX />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Process Button */}
        {replyFile && (
          <button
            className="upload-button-main"
            onClick={handleProcessAndValidate}
            disabled={processing}
          >
            <HiCloudUpload />
            <span>{processing ? 'Processing...' : 'Process & Validate'}</span>
          </button>
        )}

        {/* Error Message */}
        {error && (
          <div className="message error-message">
            <HiExclamation />
            <span>{error}</span>
          </div>
        )}

        {/* Success Message */}
        {storeSuccess && (
          <div className="message success-message">
            <HiCheckCircle />
            <div className="success-content">
              <div className="success-title">Successfully stored LAQ {storeSuccess.laq_number}</div>
              <div className="success-details">
                Stored {storeSuccess.qa_pairs_stored} Q&A pairs to database
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Upload