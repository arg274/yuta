from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from ml.model_manager import ModelManager
from model.geomorph_web import GeomorphRequest
from process import process_file, process_request


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading models...")
    ModelManager().load_models()
    yield
    print("Shutting down...")


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/analyze/file")
async def analyze_file(file: UploadFile):
    try:
        response = await process_file(file)

        if response is None:
            raise HTTPException(status_code=400, detail="Could not process the file.")

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@app.post("/analyze/json")
async def analyze_json(geomorph_request: GeomorphRequest):
    try:
        response = await process_request(geomorph_request)

        if response is None:
            raise HTTPException(
                status_code=400, detail="Could not process the request."
            )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )
