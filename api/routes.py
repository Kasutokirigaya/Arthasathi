"""FastAPI route handlers for the AarthSaathi Financial Orchestrator API."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from loguru import logger

from config.settings import Settings
from .dependencies import get_settings, require_scopes
from .auth import SCOPE_EDUCATION_AGENT, SCOPE_BUDGET_CALCULATION, SCOPE_INCOME_CLASSIFICATION, SCOPE_READINESS_SCORING, SCOPE_GUARDRAILS_FILTER, SCOPE_ORCHESTRATOR_FULL, SCOPE_STATUS_READ

# Import the orchestrator and agent functions
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator.graph import graph, create_initial_state
from agents.education_agent import get_education
from engines.calculation import calculate_budget
from engines.bifurcation import classify_income
from engines.readiness_score import calculate_readiness_score
from layers.guardrails import filter_content, run_guardrails

router = APIRouter()


# =============================================================================
# Health & Status Endpoints
# =============================================================================
@router.get("/")
async def root(
    settings: Settings = Depends(get_settings),
    _auth=Depends(require_scopes(SCOPE_STATUS_READ))
):
    """Root endpoint."""
    return {
        "status": "ok",
        "service": "AarthSaathi Financial Orchestrator API",
        "version": "1.0.0"
    }


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# =============================================================================
# Individual Component Endpoints
# =============================================================================
@router.post("/agents/education")
async def education_agent(
    concept: str,
    readiness: str = "stabilize_first",
    income_type: str = "fixed",
    language: str = "english",
    _auth=Depends(require_scopes(SCOPE_EDUCATION_AGENT))
):
    """
    Explain a financial concept using the Education Agent.
    """
    try:
        result = get_education(
            concept=concept,
            readiness=readiness,
            income_type=income_type,
            language=language
        )
        return result
    except Exception as e:
        logger.error(f"Education agent error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/engines/budget")
async def budget_calculation(
    income: dict,
    obligations: dict,
    _auth=Depends(require_scopes(SCOPE_BUDGET_CALCULATION))
):
    """
    Calculate realistic monthly budget.
    """
    try:
        result = calculate_budget(income=income, obligations=obligations)
        return result
    except Exception as e:
        logger.error(f"Budget calculation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/engines/income-classification")
async def income_classification(
    income: dict,
    _auth=Depends(require_scopes(SCOPE_INCOME_CLASSIFICATION))
):
    """
    Classify income type (fixed, variable, mixed).
    """
    try:
        result = classify_income(income=income)
        return result
    except Exception as e:
        logger.error(f"Income classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/engines/readiness-scoring")
async def readiness_scoring(
    budget_result: dict,
    income_result: dict,
    emergency_data: dict = None,
    _auth=Depends(require_scopes(SCOPE_READINESS_SCORING))
):
    """
    Calculate financial readiness score.
    """
    try:
        result = calculate_readiness_score(
            budget_result=budget_result,
            income_result=income_result,
            emergency_data=emergency_data or {}
        )
        return result
    except Exception as e:
        logger.error(f"Readiness scoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/layers/guardrails")
async def guardrails_filter(
    budget_result: dict,
    income_result: dict,
    readiness_result: dict,
    _auth=Depends(require_scopes(SCOPE_GUARDRAILS_FILTER))
):
    """
    Run guardrails safety check on financial advice.
    """
    try:
        result = run_guardrails(
            budget_result=budget_result,
            income_result=income_result,
            readiness_result=readiness_result
        )
        return result
    except Exception as e:
        logger.error(f"Guardrails filter error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Orchestrator Endpoint
# =============================================================================
@router.post("/orchestrator/run")
async def run_orchestrator(
    income: dict,
    obligations: dict,
    emergency_data: dict = None,
    _auth=Depends(require_scopes(SCOPE_ORCHESTRATOR_FULL))
):
    """
    Run the full financial orchestrator pipeline.
    """
    try:
        # Create initial state
        initial_state = create_initial_state(
            income=income,
            obligations=obligations,
            emergency_data=emergency_data or {}
        )

        # Run the orchestrator graph
        result = graph.invoke(initial_state)

        return {
            "pipeline_status": result["pipeline_status"],
            "errors": result["errors"],
            "budget_result": result["budget_result"],
            "income_result": result["income_result"],
            "readiness_result": result["readiness_result"],
            "guardrails_result": result["guardrails_result"]
        }
    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Compatibility Probes (HEAD/OPTIONS)
# =============================================================================
def _probe_response(allow: str) -> Response:
    """Return an empty success response for compatibility probes."""
    return Response(status_code=204, headers={"Allow": allow})


@router.api_route("/agents/education", methods=["HEAD", "OPTIONS"])
async def probe_education_agent(_auth=Depends(require_scopes(SCOPE_EDUCATION_AGENT))):
    """Respond to compatibility probes for the education agent endpoint."""
    return _probe_response("POST, HEAD, OPTIONS")


@router.api_route("/engines/budget", methods=["HEAD", "OPTIONS"])
async def probe_budget_calculation(_auth=Depends(require_scopes(SCOPE_BUDGET_CALCULATION))):
    """Respond to compatibility probes for the budget calculation endpoint."""
    return _probe_response("POST, HEAD, OPTIONS")


@router.api_route("/engines/income-classification", methods=["HEAD", "OPTIONS"])
async def probe_income_classification(_auth=Depends(require_scopes(SCOPE_INCOME_CLASSIFICATION))):
    """Respond to compatibility probes for the income classification endpoint."""
    return _probe_response("POST, HEAD, OPTIONS")


@router.api_route("/engines/readiness-scoring", methods=["HEAD", "OPTIONS"])
async def probe_readiness_scoring(_auth=Depends(require_scopes(SCOPE_READINESS_SCORING))):
    """Respond to compatibility probes for the readiness scoring endpoint."""
    return _probe_response("POST, HEAD, OPTIONS")


@router.api_route("/layers/guardrails", methods=["HEAD", "OPTIONS"])
async def probe_guardrails_filter(_auth=Depends(require_scopes(SCOPE_GUARDRAILS_FILTER))):
    """Respond to compatibility probes for the guardrails filter endpoint."""
    return _probe_response("POST, HEAD, OPTIONS")


@router.api_route("/orchestrator/run", methods=["HEAD", "OPTIONS"])
async def probe_orchestrator(_auth=Depends(require_scopes(SCOPE_ORCHESTRATOR_FULL))):
    """Respond to compatibility probes for the orchestrator endpoint."""
    return _probe_response("POST, HEAD, OPTIONS")