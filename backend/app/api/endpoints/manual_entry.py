from fastapi import APIRouter, Request, UploadFile, File, HTTPException
import logging
from pathlib import Path
import json
import shutil
from typing import List

from app.services.config import Config
from app.services.embeddings import EmbeddingService
from app.services.database import LAQDatabase, DatabaseError
from app.services.excel_processor import ExcelProcessor, ExcelProcessingError

router = APIRouter()

logger = logging.getLogger(__name__)


def chunk_text(text: str, max_chars: int = 800) -> List[str]:
    parts = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        parts.append(text[start:end])
        start = end
    return parts


@router.post("/", status_code=200)
async def manual_entry(request: Request):
    """
    Accept manual LAQ entries as multipart form-data with:
    - `payload`: JSON string containing LAQ fields and nested QA structure.
      Expected format mirrors frontend payload: { title, laq_type, laq_number, mla_name, date, qa_pairs: [ { question, replies: [ { text, files: ["filename1", ...] } ], followUps: [...] } ] }
    - uploaded files (optional): include files referenced by their original filenames in payload (matching names).

    Notes:
    - For replies with no files: store a single chunk (Q+A) with metadata and embedding.
    - For replies with files (excel): extract excel content, chunk it, and store each chunk with question/answer and LAQ metadata.
    """

    form = await request.form()
    if "payload" not in form:
        raise HTTPException(status_code=400, detail="Missing 'payload' form field (JSON string).")

    try:
        payload = json.loads(form.get("payload"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload JSON: {e}")

    # Log basic payload info (avoid logging raw file content)
    try:
        qa_count = len(payload.get("qa_pairs", []))
    except Exception:
        qa_count = 0
    logger.info("Received manual LAQ payload: title=%s laq_number=%s qa_pairs=%d", payload.get("title"), payload.get("laq_number"), qa_count)
    logger.debug("Full manual LAQ payload: %s", json.dumps(payload))

    # Save uploaded files to temp dir and map by filename
    upload_dir = Path("./uploads/manual")
    upload_dir.mkdir(parents=True, exist_ok=True)

    uploaded_files = {}
    # form can contain UploadFile instances under other keys
    for key, value in form.multi_items():
        # value may be UploadFile or str
        if isinstance(value, UploadFile):
            dest = upload_dir / value.filename
            try:
                with dest.open("wb") as buffer:
                    shutil.copyfileobj(value.file, buffer)
                uploaded_files[value.filename] = str(dest)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to save uploaded file {value.filename}: {e}")

    # Log which files were saved (names only)
    logger.info("Uploaded files saved: %s", list(uploaded_files.keys()))

    # Initialize services
    config = Config()
    embed_service = EmbeddingService(config)
    db = LAQDatabase(config)
    excel_processor = ExcelProcessor()

    laq_title = payload.get("title")
    laq_type = payload.get("laq_type")
    laq_number = payload.get("laq_number")
    mla_name = payload.get("mla_name")
    date = payload.get("date")
    minister = payload.get("minister") or payload.get("minister_name") or "N/A"

    stored_docs = 0

    try:
        # Iterate top-level questions only
        qa_pairs = payload.get("qa_pairs", [])

        diagnostics = {
            "received_questions": len(qa_pairs),
            "uploaded_files": list(uploaded_files.keys()),
            "stored_ids": [],
            "skipped": [],
        }
        for qi, qa in enumerate(qa_pairs, start=1):
            question = qa.get("question", "")
            # replies is a list
            replies = qa.get("replies", [])

            for ri, reply in enumerate(replies, start=1):
                text = (reply.get("text") or "").strip()
                # frontend may send files as list of filenames or list of dicts ({name,size,type})
                raw_files = reply.get("files", []) or []
                file_names = []
                for f in raw_files:
                    if isinstance(f, dict):
                        name = f.get("name")
                    else:
                        name = f
                    if name:
                        file_names.append(name)

                if not file_names:
                    # Standalone reply -> single chunk using Q+A
                    content_text = f"Q: {question}\nA: {text}"
                    # Compose metadata
                    metadata = {
                        "source": "manual",
                        "laq_title": laq_title,
                        "laq_type": laq_type,
                        "laq_number": str(laq_number),
                        "mla_name": mla_name,
                        "date": date,
                        "minister": minister,
                        "question": question[: config.metadata_max_length],
                        "answer": text[: config.metadata_max_length],
                        "attachments": json.dumps([]),
                        "qa_index": f"q{qi}_r{ri}",
                    }
                    # Embed and store
                    emb = embed_service.embed_text(f"Question: {question}\nAnswer: {text}")
                    # store using raw collection API to construct id
                    doc_id = f"manual_{laq_number}_q{qi}_r{ri}"
                    # ensure uniqueness
                    if db._id_exists(doc_id):
                        # append suffix
                        suffix = 1
                        base = doc_id
                        while db._id_exists(f"{base}_{suffix}"):
                            suffix += 1
                        doc_id = f"{base}_{suffix}"

                    try:
                        db.collection.add(
                            ids=[doc_id],
                            embeddings=[emb],
                            metadatas=[metadata],
                            documents=[content_text],
                        )
                        stored_docs += 1
                        diagnostics["stored_ids"].append(doc_id)
                    except Exception as e:
                        diagnostics["skipped"].append({"id": doc_id, "reason": str(e)})

                else:
                    # There are attached files -> handle annexures (Excel primarily)
                    for fname in file_names:
                        file_path = uploaded_files.get(fname)
                        if not file_path:
                            # skip missing file but warn
                            print(f"⚠️ Attached file '{fname}' not uploaded; skipping")
                            continue

                        p = Path(file_path)
                        if p.suffix.lower() in (".xls", ".xlsx", ".csv"):
                            try:
                                annex = excel_processor.process_excel(str(p))
                                # Convert annexure content to text and chunk
                                full_text = annex.to_text(max_chars=None)
                                chunks = chunk_text(full_text, max_chars=1000)

                                # For each chunk, create metadata including question/answer
                                texts = []
                                metas = []
                                ids = []
                                for ci, chunk in enumerate(chunks, start=1):
                                    doc_text = chunk
                                    meta = {
                                        "source": "manual_annexure",
                                        "laq_title": laq_title,
                                        "laq_type": laq_type,
                                        "laq_number": str(laq_number),
                                        "mla_name": mla_name,
                                        "date": date,
                                        "minister": minister,
                                        "question": question[: config.metadata_max_length],
                                        "answer": text[: config.metadata_max_length],
                                        "annexure_file": annex.file_name,
                                        "annexure_sheet": annex.sheets[0]["name"] if annex.sheets else "",
                                        "qa_index": f"q{qi}_r{ri}",
                                    }
                                    texts.append(doc_text)
                                    metas.append(meta)
                                    ids.append(f"manual_{laq_number}_q{qi}_r{ri}_annex_{p.stem}_{ci}")

                                # Create embeddings batch
                                embeddings = embed_service.embed_batch([f"{t}" for t in texts])

                                # Add to collection using collection.add
                                try:
                                    db.collection.add(ids=ids, embeddings=embeddings, metadatas=metas, documents=texts)
                                    stored_docs += len(ids)
                                    diagnostics["stored_ids"].extend(ids)
                                except Exception as e:
                                    diagnostics["skipped"].append({"ids": ids, "reason": str(e)})

                            except ExcelProcessingError as e:
                                print(f"⚠️ Failed to process excel {fname}: {e}")
                                continue
                        else:
                            # For non-excel annexures, store a small metadata entry referencing file
                            content_text = f"Annexure reference: {fname}"
                            metadata = {
                                "source": "manual_annexure_ref",
                                "laq_title": laq_title,
                                "laq_type": laq_type,
                                "laq_number": str(laq_number),
                                "mla_name": mla_name,
                                "date": date,
                                "minister": minister,
                                "question": question[: config.metadata_max_length],
                                "answer": text[: config.metadata_max_length],
                                "annexure_file": fname,
                                "qa_index": f"q{qi}_r{ri}",
                            }
                            emb = embed_service.embed_text(content_text)
                            doc_id = f"manual_{laq_number}_q{qi}_r{ri}_file_{p.stem}"
                            if db._id_exists(doc_id):
                                suffix = 1
                                base = doc_id
                                while db._id_exists(f"{base}_{suffix}"):
                                    suffix += 1
                                doc_id = f"{base}_{suffix}"
                            try:
                                db.collection.add(ids=[doc_id], embeddings=[emb], metadatas=[metadata], documents=[content_text])
                                stored_docs += 1
                                diagnostics["stored_ids"].append(doc_id)
                            except Exception as e:
                                diagnostics["skipped"].append({"id": doc_id, "reason": str(e)})

        return {"success": True, "stored_documents": stored_docs, "diagnostics": diagnostics}

    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
