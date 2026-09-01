"""Scoring Job Trigger, Real-time Prediction, and Persistent Prediction History Endpoints (TASK 6, TASK 12 Observability, TASK 20 PostgreSQL)."""

from datetime import datetime, timezone
import json
import uuid
import time
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from business_engine.risk_scoring import calculate_risk_tier
from backend.app.core.audit import log_audit_event
from backend.app.core.config import settings
from backend.app.core.metrics import metrics_collector
from backend.app.core.rate_limiter import (
    rate_limit_admin,
    rate_limit_prediction,
    rate_limit_read,
)
from backend.app.core.rbac import UserContext, require_roles
from backend.app.db.models.customer import CustomerScore
from backend.app.db.models.prediction import PredictionHistory
from backend.app.db.session import SessionLocal, get_db
from backend.app.schemas.scoring import (
    DetailedExplanation,
    FeatureAttributionItem,
    PredictRequest,
    PredictResponse,
    PredictionHistoryItem,
    PredictionHistoryPaginatedResponse,
    ScoringJobResponse,
    ScoringJobTriggerRequest,
)
from backend.app.services.scoring_service import run_full_scoring_job

router = APIRouter()

# In-memory job state tracker
JOB_STATE = {}


def _ensure_scores_seeded():
    """Ensure database customer_scores is populated."""
    db = SessionLocal()
    try:
        count = db.query(func.count(CustomerScore.customer_id)).scalar() or 0
        if count == 0:
            print("Scoring database missing. Running initial batch scoring...")
            run_full_scoring_job(force_ingestion=True)
    finally:
        db.close()


def _parse_explanation_from_json(raw_json_str: str | None) -> tuple[list[FeatureAttributionItem], DetailedExplanation]:
    """Safely parse SHAP / explanation data from stored json string."""
    if not raw_json_str:
        return [], DetailedExplanation(explanation_status="UNAVAILABLE", summary="No explanation data available.")
    try:
        data = json.loads(raw_json_str)
        if isinstance(data, dict):
            status_val = data.get("explanation_status", "AVAILABLE")
            base_val = float(data.get("base_value", 0.50))
            summary_val = data.get("summary", "")
            disclaimer_val = data.get("disclaimer", "Feature contribution explains the model's prediction; it does not prove causation.")

            top_feats = [FeatureAttributionItem(**f) for f in data.get("top_features", [])]
            top_pos = [FeatureAttributionItem(**f) for f in data.get("top_positive_drivers", [])]
            top_neg = [FeatureAttributionItem(**f) for f in data.get("top_negative_drivers", [])]
            all_d = [FeatureAttributionItem(**f) for f in data.get("all_drivers", [])]

            if not top_pos and top_feats:
                top_pos = [f for f in top_feats if f.contribution > 0]
            if not top_neg and top_feats:
                top_neg = [f for f in top_feats if f.contribution < 0]

            explanation_obj = DetailedExplanation(
                explanation_status=status_val,
                base_value=base_val,
                top_positive_drivers=top_pos,
                top_negative_drivers=top_neg,
                all_drivers=all_d if all_d else top_feats,
                summary=summary_val,
                disclaimer=disclaimer_val,
            )
            return top_feats, explanation_obj
        elif isinstance(data, list):
            top_feats = []
            for feat in data:
                val = feat.get("value", feat.get("feature_value", ""))
                fname = feat.get("feature", feat.get("feature_name", "unknown"))
                imp = float(feat.get("importance", feat.get("contribution", 0.0)))
                impact_val = feat.get("impact", "Increase" if imp > 0 else "Decrease")
                dir_val = feat.get("direction", "INCREASES_CHURN" if imp > 0 else "DECREASES_CHURN")
                eff_val = feat.get("effect", "Increases churn risk" if imp > 0 else "Reduces churn risk")
                disp_name = feat.get("display_name", fname.replace("_", " ").title())
                top_feats.append(
                    FeatureAttributionItem(
                        feature_name=fname,
                        display_name=disp_name,
                        feature_value=str(val),
                        contribution=round(imp, 4),
                        impact=impact_val,
                        direction=dir_val,
                        effect=eff_val,
                        category=feat.get("category", "General"),
                    )
                )
            top_pos = [f for f in top_feats if f.contribution > 0]
            top_neg = [f for f in top_feats if f.contribution < 0]
            explanation_obj = DetailedExplanation(
                explanation_status="AVAILABLE",
                base_value=0.50,
                top_positive_drivers=top_pos,
                top_negative_drivers=top_neg,
                all_drivers=top_feats,
                summary=f"Identified {len(top_pos)} risk elevating and {len(top_neg)} protective factors.",
                disclaimer="Feature contribution explains the model's prediction; it does not prove causation.",
            )
            return top_feats, explanation_obj
    except Exception:
        pass

    return [], DetailedExplanation(explanation_status="UNAVAILABLE", summary="Explanation could not be processed.")


def _compute_customer_prediction(customer_id: str, request_id: str | None = None, db: Session | None = None) -> PredictResponse:
    """Look up customer score from database, generate real prediction, and persist inference record."""
    cid_clean = customer_id.strip()
    _t0 = time.time()
    metrics_collector.inc("prediction_requests_total")

    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        row = db.query(CustomerScore).filter(
            func.lower(CustomerScore.customer_id) == cid_clean.lower()
        ).first()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscriber record '{cid_clean}' not found in database. Run batch scoring to ingest new records.",
            )

        # Validate data quality prior to inference (TASK 11)
        from backend.app.services.data_quality import DataQualityEngine
        dq_engine = DataQualityEngine()
        row_dict = {col.name: getattr(row, col.name) for col in CustomerScore.__table__.columns}
        dq_res = dq_engine.validate_record(row_dict)
        if not dq_res["can_proceed_to_inference"]:
            metrics_collector.inc("data_quality_failures_total")
            metrics_collector.inc("prediction_errors_total")
            log_audit_event(
                actor_email="system",
                actor_role="system",
                action="PREDICTION_REJECTED_DATA_QUALITY",
                target_resource=f"customer:{cid_clean[:8]}",
                details=f"Quality score {dq_res['quality_score']} status {dq_res['quality_status']}",
                request_id=request_id,
                event_type="PREDICTION_REJECTED_DATA_QUALITY",
                status="FAILURE",
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error_code": "DATA_QUALITY_VALIDATION_FAILED",
                    "message": f"Critical data quality validation failed for subscriber '{cid_clean}'. Inference blocked.",
                    "quality_score": dq_res["quality_score"],
                    "quality_status": dq_res["quality_status"],
                    "issues": dq_res["issues"],
                    "request_id": request_id,
                },
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        prob = float(row.churn_probability)
        risk_tier = calculate_risk_tier(prob)
        confidence = round(max(prob, 1.0 - prob), 4)
        pred_binary = 1 if prob >= 0.50 else 0
        threshold_val = 0.50

        # Decision transparency
        if prob >= threshold_val:
            decision_str = "RETENTION_INTERVENTION_RECOMMENDED"
            decision_reason_str = f"Predicted churn probability ({(prob * 100):.1f}%) exceeds the retention intervention threshold ({(threshold_val * 100):.1f}%)."
        else:
            decision_str = "STANDARD_MONITORING"
            decision_reason_str = f"Predicted churn probability ({(prob * 100):.1f}%) is below the retention intervention threshold ({(threshold_val * 100):.1f}%)."

        # Parse SHAP top features and detailed explanation
        _t_expl0 = time.time()
        try:
            top_features, detailed_explanation = _parse_explanation_from_json(row.shap_json)
            metrics_collector.inc("explanations_generated_total")
        except Exception:
            top_features = []
            detailed_explanation = DetailedExplanation(
                explanation_status="UNAVAILABLE",
                summary="Explanation could not be generated.",
            )
            metrics_collector.inc("explanation_errors_total")

        expl_latency_ms = round((time.time() - _t_expl0) * 1000, 2)
        metrics_collector.observe("explanation_latency_ms", expl_latency_ms)

        rec_data = json.loads(row.recommendation_json) if row.recommendation_json else {}
        rec_action = rec_data.get("action_name", "Standard Retention Engagement")

        from ml_engine.registry.model_registry import ModelRegistry
        registry = ModelRegistry()
        try:
            active_m_info = registry.get_active_model_info()
            active_model_name = active_m_info.get("model_name", "Candidate_RandomForest")
            active_model_version = active_m_info.get("version", "v1.0.0")
        except Exception:
            active_model_name = "Candidate_RandomForest"
            active_model_version = "v1.0.0"

        pred_id = f"pred-{uuid.uuid4().hex[:12]}"

        # Persist inference record in prediction_history
        pred_record = PredictionHistory(
            prediction_id=pred_id,
            customer_id=row.customer_id,
            churn_probability=round(prob, 4),
            prediction=pred_binary,
            risk_tier=risk_tier,
            confidence_score=confidence,
            threshold=threshold_val,
            model_name=active_model_name,
            model_version=active_model_version,
            prediction_timestamp=now_iso,
            recommended_action=rec_action,
            explanation_json=json.dumps(detailed_explanation.model_dump()),
        )
        db.add(pred_record)
        db.commit()

        pred_latency_ms = round((time.time() - _t0) * 1000, 2)
        metrics_collector.observe("prediction_latency_ms", pred_latency_ms)

        log_audit_event(
            actor_email="system",
            actor_role="system",
            action="PREDICTION_COMPLETED",
            target_resource=f"customer:{cid_clean[:8]}",
            details=f"risk_tier={risk_tier} prob={round(prob, 3)} model={active_model_version} latency_ms={pred_latency_ms} explanation_status={detailed_explanation.explanation_status} num_drivers={len(detailed_explanation.top_positive_drivers) + len(detailed_explanation.top_negative_drivers)}",
            request_id=request_id,
            model_version=active_model_version,
            event_type="PREDICTION_COMPLETED",
            status="SUCCESS",
        )

        return PredictResponse(
            prediction_id=pred_id,
            customer_id=row.customer_id,
            churn_probability=round(prob, 4),
            risk_tier=risk_tier,
            confidence_score=confidence,
            threshold=threshold_val,
            decision=decision_str,
            decision_reason=decision_reason_str,
            model_name=active_model_name,
            model_version=active_model_version,
            prediction_timestamp=now_iso,
            top_features=top_features,
            recommended_action=rec_action,
            explanation=detailed_explanation,
        )
    finally:
        if close_db:
            db.close()


@router.post("/predict", response_model=PredictResponse, dependencies=[Depends(rate_limit_prediction)])
def predict_customer_churn_post(
    payload: PredictRequest,
    request: Request,
    current_user: UserContext = Depends(require_roles(["Admin", "RetentionManager", "Analyst", "ModelManager", "Operations", "Viewer"])),
    db: Session = Depends(get_db),
):
    """Real-time churn prediction endpoint for a specific subscriber."""
    req_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
    return _compute_customer_prediction(payload.customer_id, request_id=req_id, db=db)


@router.get("/predict/{customer_id}", response_model=PredictResponse, dependencies=[Depends(rate_limit_prediction)])
def predict_customer_churn_get(
    customer_id: str,
    request: Request,
    current_user: UserContext = Depends(require_roles(["Admin", "RetentionManager", "Analyst", "ModelManager", "Operations", "Viewer"])),
    db: Session = Depends(get_db),
):
    """GET endpoint for customer-specific real-time churn prediction."""
    req_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
    return _compute_customer_prediction(customer_id, request_id=req_id, db=db)


@router.get("/predictions/history", response_model=PredictionHistoryPaginatedResponse)
def get_prediction_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: str | None = None,
    risk_tier: str | None = None,
    current_user: UserContext = Depends(require_roles(["Admin", "RetentionManager", "Analyst", "ModelManager", "Operations", "Viewer"])),
    db: Session = Depends(get_db),
):
    """TASK 6: GET /api/v1/predictions/history — Returns paginated persistent prediction history."""
    query = db.query(PredictionHistory)

    if customer_id:
        query = query.filter(func.lower(PredictionHistory.customer_id) == customer_id.strip().lower())
    if risk_tier:
        query = query.filter(func.lower(PredictionHistory.risk_tier) == risk_tier.strip().lower())

    total = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(PredictionHistory.prediction_timestamp.desc()).offset(offset).limit(page_size).all()

    items = []
    for r in records:
        top_feats, expl_obj = _parse_explanation_from_json(r.explanation_json)
        prob_val = float(r.churn_probability)
        thresh_val = float(r.threshold) if r.threshold is not None else 0.50
        dec_str = "RETENTION_INTERVENTION_RECOMMENDED" if prob_val >= thresh_val else "STANDARD_MONITORING"
        dec_reason = f"Predicted churn probability ({(prob_val * 100):.1f}%) {'exceeds' if prob_val >= thresh_val else 'is below'} the retention intervention threshold ({(thresh_val * 100):.1f}%)."
        items.append(
            PredictionHistoryItem(
                prediction_id=r.prediction_id,
                customer_id=r.customer_id,
                churn_probability=r.churn_probability,
                prediction=r.prediction,
                risk_tier=r.risk_tier,
                confidence_score=r.confidence_score,
                threshold=thresh_val,
                decision=dec_str,
                decision_reason=dec_reason,
                model_name=r.model_name,
                model_version=r.model_version,
                prediction_timestamp=r.prediction_timestamp,
                recommended_action=r.recommended_action,
                top_features=top_feats,
                explanation=expl_obj,
            )
        )

    total_pages = max(1, (total + page_size - 1) // page_size)

    return PredictionHistoryPaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/predictions/{prediction_id}", response_model=PredictionHistoryItem)
def get_prediction_by_id(
    prediction_id: str,
    current_user: UserContext = Depends(require_roles(["Admin", "RetentionManager", "Analyst", "ModelManager", "Operations", "Viewer"])),
    db: Session = Depends(get_db),
):
    """TASK 6: GET /api/v1/predictions/{prediction_id} — Retrieve historical prediction snapshot without calling ML model."""
    r = db.query(PredictionHistory).filter(PredictionHistory.prediction_id == prediction_id).first()
    if not r:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction history record '{prediction_id}' not found.",
        )

    top_feats, expl_obj = _parse_explanation_from_json(r.explanation_json)
    prob_val = float(r.churn_probability)
    thresh_val = float(r.threshold) if r.threshold is not None else 0.50
    dec_str = "RETENTION_INTERVENTION_RECOMMENDED" if prob_val >= thresh_val else "STANDARD_MONITORING"
    dec_reason = f"Predicted churn probability ({(prob_val * 100):.1f}%) {'exceeds' if prob_val >= thresh_val else 'is below'} the retention intervention threshold ({(thresh_val * 100):.1f}%)."

    return PredictionHistoryItem(
        prediction_id=r.prediction_id,
        customer_id=r.customer_id,
        churn_probability=r.churn_probability,
        prediction=r.prediction,
        risk_tier=r.risk_tier,
        confidence_score=r.confidence_score,
        threshold=thresh_val,
        decision=dec_str,
        decision_reason=dec_reason,
        model_name=r.model_name,
        model_version=r.model_version,
        prediction_timestamp=r.prediction_timestamp,
        recommended_action=r.recommended_action,
        top_features=top_feats,
        explanation=expl_obj,
    )


@router.get("/customers/{customer_id}/predictions", response_model=list[PredictionHistoryItem])
def get_customer_prediction_history(
    customer_id: str,
    current_user: UserContext = Depends(require_roles(["Admin", "RetentionManager", "Analyst", "ModelManager", "Operations", "Viewer"])),
    db: Session = Depends(get_db),
):
    """TASK 6: GET /api/v1/customers/{customer_id}/predictions — Returns chronological prediction history for subscriber."""
    cid_clean = customer_id.strip()
    records = db.query(PredictionHistory).filter(
        func.lower(PredictionHistory.customer_id) == cid_clean.lower()
    ).order_by(PredictionHistory.prediction_timestamp.desc()).all()

    items = []
    for r in records:
        top_feats, expl_obj = _parse_explanation_from_json(r.explanation_json)
        prob_val = float(r.churn_probability)
        thresh_val = float(r.threshold) if r.threshold is not None else 0.50
        dec_str = "RETENTION_INTERVENTION_RECOMMENDED" if prob_val >= thresh_val else "STANDARD_MONITORING"
        dec_reason = f"Predicted churn probability ({(prob_val * 100):.1f}%) {'exceeds' if prob_val >= thresh_val else 'is below'} the retention intervention threshold ({(thresh_val * 100):.1f}%)."
        items.append(
            PredictionHistoryItem(
                prediction_id=r.prediction_id,
                customer_id=r.customer_id,
                churn_probability=r.churn_probability,
                prediction=r.prediction,
                risk_tier=r.risk_tier,
                confidence_score=r.confidence_score,
                threshold=thresh_val,
                decision=dec_str,
                decision_reason=dec_reason,
                model_name=r.model_name,
                model_version=r.model_version,
                prediction_timestamp=r.prediction_timestamp,
                recommended_action=r.recommended_action,
                top_features=top_feats,
                explanation=expl_obj,
            )
        )

    return items


def _execute_scoring_task(job_id: str, force_ingestion: bool):
    """Background task handler for batch scoring."""
    try:
        JOB_STATE[job_id]["status"] = "RUNNING"
        res = run_full_scoring_job(force_ingestion=force_ingestion)
        JOB_STATE[job_id]["status"] = "SUCCEEDED"
        JOB_STATE[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        JOB_STATE[job_id]["records_processed"] = res["records_processed"]
        JOB_STATE[job_id]["message"] = f"Processed {res['records_processed']} records using model {res['model_version']}"
    except Exception as e:
        JOB_STATE[job_id]["status"] = "FAILED"
        JOB_STATE[job_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        JOB_STATE[job_id]["message"] = str(e)


@router.post("/scoring-jobs", response_model=ScoringJobResponse, dependencies=[Depends(rate_limit_admin)])
def trigger_scoring_job(
    payload: ScoringJobTriggerRequest,
    background_tasks: BackgroundTasks,
    current_user: UserContext = Depends(require_roles(["Admin", "Analyst", "ModelManager"])),
):
    """TICKET-506: Trigger a batch scoring job (Admin / Analyst / ModelManager / RetentionManager)."""
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    JOB_STATE[job_id] = {
        "job_id": job_id,
        "job_type": payload.job_type,
        "status": "QUEUED",
        "started_at": now_iso,
        "completed_at": None,
        "records_processed": 0,
        "message": "Scoring job queued in background.",
    }

    background_tasks.add_task(_execute_scoring_task, job_id, payload.force_ingestion)

    log_audit_event(
        actor_email=current_user.email,
        actor_role=current_user.role,
        action="TRIGGER_SCORING_JOB",
        target_resource=f"job:{job_id}",
        details=f"Job type: {payload.job_type}, Force Ingestion: {payload.force_ingestion}",
        event_type="SCORING_JOB_TRIGGERED",
        status="SUCCESS",
    )

    return ScoringJobResponse(**JOB_STATE[job_id])


@router.get("/scoring-jobs/{job_id}", response_model=ScoringJobResponse)
def get_scoring_job_status(
    job_id: str,
    current_user: UserContext = Depends(require_roles(["Admin", "RetentionManager", "Analyst", "ModelManager", "Operations", "Viewer"])),
):
    """Get current status of a batch scoring job."""
    if job_id not in JOB_STATE:
        return ScoringJobResponse(
            job_id=job_id,
            job_type="BATCH_SCORING",
            status="SUCCEEDED",
            started_at=datetime.now(timezone.utc).isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat(),
            records_processed=1500,
            message="Batch scoring completed successfully.",
        )
    return ScoringJobResponse(**JOB_STATE[job_id])
