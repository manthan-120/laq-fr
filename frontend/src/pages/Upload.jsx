/**
 * Upload page component
 */

import { useState, useRef } from 'react'
import { HiCloudUpload, HiDocument, HiCheckCircle, HiExclamation, HiX } from 'react-icons/hi'
import { uploadPDF } from '../services/api'
import './Upload.css'

function Upload() {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(null)
  const [uploadError, setUploadError] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef(null)

  // Annexure upload states
  const [annexureFile, setAnnexureFile] = useState(null)
  const [annexureUploading, setAnnexureUploading] = useState(false)
  const [annexureSuccess, setAnnexureSuccess] = useState(null)
  const [annexureError, setAnnexureError] = useState(null)
  const annexureInputRef = useRef(null)

  // Manual annexure upload (for new annexures not referenced in PDF)
  const [manualAnnexureFile, setManualAnnexureFile] = useState(null)
  const [manualAnnexureLaq, setManualAnnexureLaq] = useState('')
  const [manualAnnexureUploading, setManualAnnexureUploading] = useState(false)
  const [manualAnnexureSuccess, setManualAnnexureSuccess] = useState(null)
  const [manualAnnexureError, setManualAnnexureError] = useState(null)
  const manualAnnexureInputRef = useRef(null)

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
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = (selectedFile) => {
    // Validate file type
    if (!selectedFile.name.toLowerCase().endsWith('.pdf')) {
      setUploadError('Please select a PDF file')
      return
    }

    // Validate file size (50MB limit)
    const maxSize = 50 * 1024 * 1024 // 50MB
    if (selectedFile.size > maxSize) {
      setUploadError('File size must be less than 50MB')
      return
    }

    setFile(selectedFile)
    setUploadError(null)
    setUploadSuccess(null)
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setUploadError(null)

    try {
      const result = await uploadPDF(file)
      setUploadSuccess(result)
      setFile(null)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    } catch (error) {
      setUploadError(error.response?.data?.detail || error.message || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleRemoveFile = () => {
    setFile(null)
    setUploadError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  // Check if PDF has annexure references
  const hasAnnexureReferences = () => {
    return uploadSuccess && uploadSuccess.laq_data && uploadSuccess.laq_data.attachments && uploadSuccess.laq_data.attachments.length > 0
  }

  const handleAnnexureFile = (selectedFile) => {
    // Validate file type
    if (!selectedFile.name.toLowerCase().endsWith('.xlsx') && !selectedFile.name.toLowerCase().endsWith('.xls')) {
      setAnnexureError('Please select an Excel file (.xls or .xlsx)')
      return
    }

    setAnnexureFile(selectedFile)
    setAnnexureError(null)
    setAnnexureSuccess(null)
  }

  const handleAnnexureUpload = async () => {
    if (!annexureFile || !uploadSuccess) return

    setAnnexureUploading(true)
    setAnnexureError(null)

    try {
      const formData = new FormData()
      formData.append('file', annexureFile)
      formData.append('laq_number', uploadSuccess.laq_data.laq_number)

      const response = await fetch('http://localhost:8000/api/annexure/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const result = await response.json()
      setAnnexureSuccess(result)
      setAnnexureFile(null)
      if (annexureInputRef.current) {
        annexureInputRef.current.value = ''
      }
    } catch (error) {
      setAnnexureError(error.message || 'Annexure upload failed')
    } finally {
      setAnnexureUploading(false)
    }
  }

  const handleRemoveAnnexureFile = () => {
    setAnnexureFile(null)
    setAnnexureError(null)
    if (annexureInputRef.current) {
      annexureInputRef.current.value = ''
    }
  }

  // Manual annexure handlers (when user wants to upload a new annexure and must specify LAQ number)
  const handleManualAnnexureFile = (selectedFile) => {
    if (!selectedFile.name.toLowerCase().endsWith('.xlsx') && !selectedFile.name.toLowerCase().endsWith('.xls')) {
      setManualAnnexureError('Please select an Excel file (.xls or .xlsx)')
      return
    }
    setManualAnnexureFile(selectedFile)
    setManualAnnexureError(null)
    setManualAnnexureSuccess(null)
  }

  const handleManualAnnexureUpload = async () => {
    if (!manualAnnexureFile) {
      setManualAnnexureError('Select an annexure file')
      return
    }
    if (!manualAnnexureLaq.trim()) {
      setManualAnnexureError('Enter LAQ number')
      return
    }

    setManualAnnexureUploading(true)
    setManualAnnexureError(null)

    try {
      const formData = new FormData()
      formData.append('file', manualAnnexureFile)
      formData.append('laq_number', manualAnnexureLaq.trim())

      const response = await fetch('http://localhost:8000/api/annexure/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const result = await response.json()
      setManualAnnexureSuccess(result)
      setManualAnnexureFile(null)
      if (manualAnnexureInputRef.current) {
        manualAnnexureInputRef.current.value = ''
      }
    } catch (error) {
      setManualAnnexureError(error.message || 'Annexure upload failed')
    } finally {
      setManualAnnexureUploading(false)
    }
  }

  const handleRemoveManualAnnexureFile = () => {
    setManualAnnexureFile(null)
    setManualAnnexureError(null)
    if (manualAnnexureInputRef.current) {
      manualAnnexureInputRef.current.value = ''
    }
  }

  return (
    <div className="upload-page">
      <div className="upload-container">
        {/* Upload Zone */}
        <div
          className={`upload-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => !file && fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileInput}
            style={{ display: 'none' }}
          />

          {!file ? (
            <>
              <div className="upload-icon">
                <HiCloudUpload />
              </div>
              <div className="upload-title">Drop file here or click to browse</div>
              <div className="upload-subtitle">Supports LAQ PDFs up to 50MB</div>
            </>
          ) : (
            <div className="file-preview">
              <div className="file-icon">
                <HiDocument />
              </div>
              <div className="file-info">
                <div className="file-name">{file.name}</div>
                <div className="file-size">{formatFileSize(file.size)}</div>
              </div>
              <button
                className="file-remove"
                onClick={(e) => {
                  e.stopPropagation()
                  handleRemoveFile()
                }}
                disabled={uploading}
              >
                <HiX />
              </button>
            </div>
          )}
        </div>

        {/* Upload Button */}
        {file && (
          <button
            className="upload-button"
            onClick={handleUpload}
            disabled={uploading}
          >
            <HiCloudUpload />
            <span>{uploading ? 'Processing...' : 'Upload and Process PDF'}</span>
          </button>
        )}

        {/* Error Message */}
        {uploadError && (
          <div className="message error-message">
            <HiExclamation />
            <span>{uploadError}</span>
          </div>
        )}

        {/* Success Message */}
        {uploadSuccess && (
          <div className="message success-message">
            <HiCheckCircle />
            <div className="success-content">
              <div className="success-title">Successfully processed {uploadSuccess.pdf_name}</div>
              <div className="success-details">
                Extracted {uploadSuccess.qa_pairs_extracted} Q&A pairs
              </div>
            </div>
          </div>
        )}

        {/* Extracted Data Preview */}
        {uploadSuccess && uploadSuccess.laq_data && (
          <div className="extracted-data">
            <div className="section-header">
              <h3 className="section-title">Extracted LAQ Data</h3>
            </div>

            <div className="laq-metadata">
              <div className="metadata-item">
                <span className="metadata-label">Title:</span>
                <span className="metadata-value">{uploadSuccess.laq_data.pdf_title}</span>
              </div>
              <div className="metadata-item">
                <span className="metadata-label">LAQ Number:</span>
                <span className="metadata-value">{uploadSuccess.laq_data.laq_number}</span>
              </div>
              <div className="metadata-item">
                <span className="metadata-label">Type:</span>
                <span className="metadata-value">{uploadSuccess.laq_data.laq_type}</span>
              </div>
              <div className="metadata-item">
                <span className="metadata-label">Minister:</span>
                <span className="metadata-value">{uploadSuccess.laq_data.minister}</span>
              </div>
              <div className="metadata-item">
                <span className="metadata-label">Date:</span>
                <span className="metadata-value">{uploadSuccess.laq_data.date}</span>
              </div>
            </div>

            <div className="qa-pairs">
              <h4 className="qa-title">Q&A Pairs ({uploadSuccess.laq_data.qa_pairs.length})</h4>
              {uploadSuccess.laq_data.qa_pairs.slice(0, 3).map((qa, index) => (
                <div key={index} className="qa-pair">
                  <div className="question">
                    <strong>Q{index + 1}:</strong> {qa.question}
                  </div>
                  <div className="answer">
                    <strong>A:</strong> {qa.answer}
                  </div>
                </div>
              ))}
              {uploadSuccess.laq_data.qa_pairs.length > 3 && (
                <div className="qa-more">
                  +{uploadSuccess.laq_data.qa_pairs.length - 3} more Q&A pairs
                </div>
              )}
            </div>
          </div>
        )}

        {/* Annexure Upload Section - Shows if PDF has attachments/annexure references */}
        {hasAnnexureReferences() && (
          <div className="annexure-section">
            <div className="section-header">
              <h3 className="section-title">📎 Upload Annexures</h3>
              <p className="section-subtitle">
                This LAQ references {uploadSuccess.laq_data.attachments.length} annexure(s): {uploadSuccess.laq_data.attachments.join(', ')}
              </p>
            </div>

            <div className="annexure-upload-zone">
              <input
                ref={annexureInputRef}
                type="file"
                accept=".xls,.xlsx"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleAnnexureFile(e.target.files[0])
                  }
                }}
                style={{ display: 'none' }}
              />

              {!annexureFile ? (
                <div
                  className="upload-zone annexure-drop-zone"
                  onClick={() => annexureInputRef.current?.click()}
                >
                  <div className="upload-icon">
                    <HiCloudUpload />
                  </div>
                  <div className="upload-title">Drop Excel file here or click to browse</div>
                  <div className="upload-subtitle">Name format: 123_annexure.xlsx (auto-fills LAQ {uploadSuccess.laq_data.laq_number})</div>
                </div>
              ) : (
                <div className="file-preview">
                  <div className="file-icon">
                    <HiDocument />
                  </div>
                  <div className="file-info">
                    <div className="file-name">{annexureFile.name}</div>
                    <div className="file-size">{formatFileSize(annexureFile.size)}</div>
                  </div>
                  <button
                    className="file-remove"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRemoveAnnexureFile()
                    }}
                    disabled={annexureUploading}
                  >
                    <HiX />
                  </button>
                </div>
              )}
            </div>

            {annexureFile && (
              <button
                className="upload-button annexure-upload-button"
                onClick={handleAnnexureUpload}
                disabled={annexureUploading}
              >
                <HiCloudUpload />
                <span>{annexureUploading ? 'Uploading...' : 'Upload Annexure'}</span>
              </button>
            )}

            {annexureError && (
              <div className="message error-message">
                <HiExclamation />
                <span>{annexureError}</span>
              </div>
            )}

            {annexureSuccess && (
              <div className="message success-message">
                <HiCheckCircle />
                <div className="success-content">
                  <div className="success-title">Annexure uploaded successfully</div>
                  <div className="success-details">
                    Label: {annexureSuccess.annexure_label} | ID: {annexureSuccess.stored_id}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Manual Annexure Upload (user provides LAQ number) */}
        <div className="annexure-section">
          <div className="section-header">
            <h3 className="section-title">➕ Upload Annexure for Another LAQ</h3>
            <p className="section-subtitle">Use this if you need to add a new annexure and know the LAQ number.</p>
          </div>

          <div className="manual-annexure-form">
            <input
              type="text"
              placeholder="Enter LAQ Number"
              value={manualAnnexureLaq}
              onChange={(e) => setManualAnnexureLaq(e.target.value)}
              className="manual-annexure-input"
            />

            <div className="annexure-upload-zone">
              <input
                ref={manualAnnexureInputRef}
                type="file"
                accept=".xls,.xlsx"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleManualAnnexureFile(e.target.files[0])
                  }
                }}
                style={{ display: 'none' }}
              />

              {!manualAnnexureFile ? (
                <div
                  className="upload-zone annexure-drop-zone"
                  onClick={() => manualAnnexureInputRef.current?.click()}
                >
                  <div className="upload-icon">
                    <HiCloudUpload />
                  </div>
                  <div className="upload-title">Drop Excel file here or click to browse</div>
                  <div className="upload-subtitle">Provide LAQ number above</div>
                </div>
              ) : (
                <div className="file-preview">
                  <div className="file-icon">
                    <HiDocument />
                  </div>
                  <div className="file-info">
                    <div className="file-name">{manualAnnexureFile.name}</div>
                    <div className="file-size">{formatFileSize(manualAnnexureFile.size)}</div>
                  </div>
                  <button
                    className="file-remove"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRemoveManualAnnexureFile()
                    }}
                    disabled={manualAnnexureUploading}
                  >
                    <HiX />
                  </button>
                </div>
              )}
            </div>

            {manualAnnexureFile && (
              <button
                className="upload-button annexure-upload-button"
                onClick={handleManualAnnexureUpload}
                disabled={manualAnnexureUploading}
              >
                <HiCloudUpload />
                <span>{manualAnnexureUploading ? 'Uploading...' : 'Upload Annexure'}</span>
              </button>
            )}

            {manualAnnexureError && (
              <div className="message error-message">
                <HiExclamation />
                <span>{manualAnnexureError}</span>
              </div>
            )}

            {manualAnnexureSuccess && (
              <div className="message success-message">
                <HiCheckCircle />
                <div className="success-content">
                  <div className="success-title">Annexure uploaded successfully</div>
                  <div className="success-details">
                    LAQ: {manualAnnexureLaq || 'N/A'} | Label: {manualAnnexureSuccess.annexure_label} | ID: {manualAnnexureSuccess.stored_id}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Info Section */}
       
      </div>
    </div>
  )
}

export default Upload
