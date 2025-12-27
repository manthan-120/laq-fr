from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import UploadFile, File

app = FastAPI()

# Allow your frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock /api/laqs
@app.get("/api/laqs")
def get_laqs():
    return [
        {
            "laq_no": 101,
            "year": 2023,
            "mla_name": "Shri Ram Naik",
            "department": "Education",
            "demand_no": 12,
            "type": "Starred",
            "cutmotion": "No",
            "duplicate": False,
            "date": "2023-01-15",
            "question": "What is the current budget allocation?"
        },
        {
            "laq_no": 102,
            "year": 2023,
            "mla_name": "Smt Asha Sawant",
            "department": "Health",
            "demand_no": 8,
            "type": "Unstarred",
            "cutmotion": "Yes",
            "duplicate": True,
            "date": "2023-02-10",
            "question": "Provide district-wise statistics of healthcare infrastructure."
        }
    ]

# Mock /api/database/info
@app.get("/api/database/info")
def get_database_info():
    return {
        "total_documents": 2,
        "starred": 1,
        "unstarred": 1,
        "departments": 2
    }

# Mock /api/search
@app.post("/api/search")
def search_laqs():
    return {
        "query": "budget",
        "results": [
            {
                "question": "What is the current budget allocation?",
                "answer": "The budget allocation is X crores.",
                "metadata": {
                    "laq_num": 101,
                    "minister": "Shri Ram Naik",
                    "date": "2023-01-15",
                    "department": "Education"
                },
                "similarity_score": 0.95
            }
        ],
        "total_results": 1
    }

# Mock /api/upload
@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "status": "uploaded",
        "message": "Mock upload successful"
    }




# Mock /api/chat
@app.post("/api/chat")
def chat_laqs():
    return {
        "question": "What is the budget?",
        "answer": "The budget allocation is X crores.",
        "sources": [
            {
                "metadata": {
                    "laq_num": 101,
                    "department": "Education"
                }
            }
        ]
    }