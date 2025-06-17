import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

# Add the project root to sys.path to allow importing Macronizer
# Vercel typically runs the script from the directory it's in (e.g., /var/task/api/)
# So, ../ should point to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from macronizer import Macronizer, SCANSIONS
except ImportError as e:
    # This will help debug if the path adjustment is not working as expected on Vercel
    raise ImportError(f"Could not import Macronizer. sys.path: {sys.path}, project_root: {project_root}, error: {e}")

app = FastAPI()

# Initialize Macronizer globally to reuse the instance (and its loaded models/db)
# This is generally recommended for performance in serverless functions
# Ensure macronizer.py and its dependencies (db, models) are in the correct relative paths
try:
    macronizer_instance = Macronizer()
except Exception as e:
    # If Macronizer fails to initialize, the app won't start, which is a critical error.
    # This helps in debugging issues with finding DB, RFTagger, Morpheus, etc.
    raise RuntimeError(f"Failed to initialize Macronizer: {e}")

class MacronizeRequest(BaseModel):
    text_to_macronize: str = Field(..., example="Arma virumque cano, Troiae qui primus ab oris.")
    domacronize: Optional[bool] = True
    alsomaius: Optional[bool] = False
    scan_option_index: Optional[int] = Field(0, ge=0) # Index for SCANSIONS list
    performitoj: Optional[bool] = False
    performutov: Optional[bool] = False

class MacronizeResponse(BaseModel):
    macronized_text: str
    original_text: str
    options_used: dict

@app.post("/api/macronize", response_model=MacronizeResponse)
async def macronize_text_endpoint(request: MacronizeRequest):
    if request.scan_option_index >= len(SCANSIONS):
        raise HTTPException(status_code=400, detail=f"Invalid scan_option_index. Must be less than {len(SCANSIONS)}.")

    try:
        # The Macronizer class methods settext/gettext or the combined macronize might be better
        # macronize.py's main execution calls:
        # macronizer.settext(texttomacronize)
        # if scan > 0:
        #     macronizer.scan(SCANSIONS[scan][1])
        # macronizedtext = macronizer.gettext(domacronize, alsomaius, performutov, performitoj, markambigs=False)

        macronizer_instance.settext(request.text_to_macronize)

        selected_scan_option = []
        if request.scan_option_index > 0 and request.scan_option_index < len(SCANSIONS):
            selected_scan_option = SCANSIONS[request.scan_option_index][1]
            if selected_scan_option: # Ensure it's not empty
                 macronizer_instance.scan(selected_scan_option)

        processed_text = macronizer_instance.gettext(
            domacronize=request.domacronize,
            alsomaius=request.alsomaius,
            performutov=request.performutov,
            performitoj=request.performitoj,
            markambigs=False # API will return plain text, not HTML with ambiguity spans
        )

        return MacronizeResponse(
            macronized_text=processed_text,
            original_text=request.text_to_macronize,
            options_used={
                "domacronize": request.domacronize,
                "alsomaius": request.alsomaius,
                "scan_option_index": request.scan_option_index,
                "scan_description": SCANSIONS[request.scan_option_index][0] if request.scan_option_index < len(SCANSIONS) else "N/A",
                "performitoj": request.performitoj,
                "performutov": request.performutov,
            }
        )
    except Exception as e:
        # Log the exception details for debugging on Vercel
        print(f"Error during macronization: {e}") # This will go to Vercel logs
        # Also include type of exception for clarity
        print(f"Exception type: {type(e).__name__}")
        # Potentially re-raise or return a more specific error
        # For now, a generic 500 error
        raise HTTPException(status_code=500, detail=f"An error occurred during macronization: {type(e).__name__} - {str(e)}")

# Vercel expects the FastAPI app instance to be named 'app' by default if it's in index.py at the root of /api
# To run locally for testing: uvicorn api.index:app --reload
