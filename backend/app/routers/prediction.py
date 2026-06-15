"""Phase 4: Failure Prediction and RUL Prediction API."""
import uuid
from datetime import datetime
from typing import Optional, List
import numpy as np

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Equipment, SensorData
from app.models.schemas.prediction_schemas import (
    FailurePredictionRequest, FailurePredictionResponse,
    RULPredictionRequest, RULPredictionResponse,
    DegradationResponse,
    RiskAssessmentResponse,
    EarlyWarningResponse, WarningListResponse,
    MaintenanceRecommendationResponse,
    EquipmentPrediction, EquipmentPredictionListResponse,
    PredictiveDashboardResponse,
    TrainModelRequest, TrainModelResponse,
    ModelInfo, ModelRegistryResponse
)
from app.prediction.failure_model import get_failure_predictor, train_initial_failure_model
from app.prediction.rul_model import get_rul_predictor, train_initial_rul_model
from app.prediction.predictive_services import (
    get_degradation_engine,
    get_warning_engine,
    get_risk_engine,
    get_recommendation_engine
)
from app.health.health_score import get_health_calculator

router = APIRouter(prefix="/api/prediction", tags=["Phase 4 - Failure Prediction & RUL"])


# ============ Failure Prediction ============

@router.post("/failure", response_model=FailurePredictionResponse)
async def predict_failure(
    request: FailurePredictionRequest
):
    """
    Predict equipment failure probability.
    
    Uses Random Forest or XGBoost classifier to predict
    the probability of failure based on sensor readings.
    """
    predictor = get_failure_predictor()
    
    # Prepare features
    features = np.array([[
        request.temperature,
        request.vibration,
        request.current,
        request.pressure,
        request.rpm
    ]])
    
    # Check if model is trained
    if not predictor.is_trained:
        # Try to train initial model
        try:
            train_initial_failure_model()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failure prediction model not trained: {str(e)}"
            )
    
    # Get prediction and explanation
    explanation = predictor.explain_prediction(features)
    
    # Determine risk level
    prob = explanation['failure_probability']
    if prob >= 0.8:
        risk_level = "Critical"
    elif prob >= 0.6:
        risk_level = "High"
    elif prob >= 0.4:
        risk_level = "Medium"
    else:
        risk_level = "Low"
    
    return FailurePredictionResponse(
        equipment_name=request.equipment_name,
        timestamp=datetime.now(),
        failure_probability=explanation['failure_probability'],
        risk_level=risk_level,
        confidence=explanation['confidence'],
        prediction=explanation['prediction'],
        reason=explanation['reason'],
        contributing_factors=explanation['contributing_factors'],
        feature_analysis=explanation['feature_analysis']
    )


@router.post("/rul", response_model=RULPredictionResponse)
async def predict_rul(
    request: RULPredictionRequest
):
    """
    Predict Remaining Useful Life (RUL).
    
    Estimates how many days of operation remain before
    equipment is expected to fail.
    """
    predictor = get_rul_predictor()
    
    # Prepare features
    features = np.array([[
        request.temperature,
        request.vibration,
        request.current,
        request.pressure,
        request.rpm
    ]])
    
    # Check if model is trained
    if not predictor.is_trained:
        try:
            train_initial_rul_model()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"RUL prediction model not trained: {str(e)}"
            )
    
    # Get prediction and explanation
    rul = int(predictor.predict(features)[0])
    explanation = predictor.explain_prediction(features)
    
    # Get confidence interval
    confidence = predictor.get_confidence_interval(features)
    
    return RULPredictionResponse(
        equipment_name=request.equipment_name,
        timestamp=datetime.now(),
        remaining_useful_life=rul,
        confidence_interval={
            'lower': int(confidence['lower'][0]),
            'upper': int(confidence['upper'][0]),
            'confidence': confidence['confidence']
        },
        explanation=explanation['explanation'],
        critical_factors=explanation['critical_factors'],
        warning_factors=explanation['warning_factors'],
        feature_analysis=explanation['feature_analysis']
    )


# ============ Degradation & Risk ============

@router.get("/degradation/{equipment_name}", response_model=DegradationResponse)
async def get_degradation(
    equipment_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get equipment degradation state."""
    # Get latest sensor data
    result = await db.execute(
        select(SensorData)
        .where(SensorData.equipment_name == equipment_name)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    sensor_data = result.scalar_one_or_none()
    
    if not sensor_data:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    # Get predictions
    failure_predictor = get_failure_predictor()
    rul_predictor = get_rul_predictor()
    
    features = np.array([[
        sensor_data.temperature or 75,
        sensor_data.vibration or 1.5,
        sensor_data.current or 20,
        sensor_data.pressure or 70,
        sensor_data.rpm or 1500
    ]])
    
    # Calculate health score
    health_calculator = get_health_calculator()
    readings = {
        'temperature': sensor_data.temperature or 75,
        'vibration': sensor_data.vibration or 1.5,
        'current': sensor_data.current or 20,
        'pressure': sensor_data.pressure or 70,
        'rpm': sensor_data.rpm or 1500
    }
    health = health_calculator.calculate_score(readings)
    
    # Get failure probability
    failure_prob = 0.5
    if failure_predictor.is_trained:
        failure_prob = float(failure_predictor.predict_proba(features)[0])
    
    # Get RUL
    rul_days = 60
    if rul_predictor.is_trained:
        rul_days = int(rul_predictor.predict(features)[0])
    
    # Calculate degradation
    degradation_engine = get_degradation_engine()
    degradation = degradation_engine.calculate_degradation(
        health_score=health.score,
        failure_probability=failure_prob,
        rul_days=rul_days
    )
    
    return DegradationResponse(
        equipment_name=equipment_name,
        timestamp=datetime.now(),
        level=degradation.level,
        score=degradation.score,
        factors=degradation.factors,
        explanation=degradation.explanation
    )


@router.get("/risk/{equipment_name}", response_model=RiskAssessmentResponse)
async def assess_risk(
    equipment_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Assess equipment risk level."""
    # Get latest sensor data
    result = await db.execute(
        select(SensorData)
        .where(SensorData.equipment_name == equipment_name)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    sensor_data = result.scalar_one_or_none()
    
    if not sensor_data:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    # Calculate predictions
    features = np.array([[
        sensor_data.temperature or 75,
        sensor_data.vibration or 1.5,
        sensor_data.current or 20,
        sensor_data.pressure or 70,
        sensor_data.rpm or 1500
    ]])
    
    # Health score
    health_calculator = get_health_calculator()
    readings = {
        'temperature': sensor_data.temperature or 75,
        'vibration': sensor_data.vibration or 1.5,
        'current': sensor_data.current or 20,
        'pressure': sensor_data.pressure or 70,
        'rpm': sensor_data.rpm or 1500
    }
    health = health_calculator.calculate_score(readings)
    
    # Failure probability
    failure_predictor = get_failure_predictor()
    failure_prob = 0.5
    if failure_predictor.is_trained:
        failure_prob = float(failure_predictor.predict_proba(features)[0])
    
    # RUL
    rul_predictor = get_rul_predictor()
    rul_days = 60
    if rul_predictor.is_trained:
        rul_days = int(rul_predictor.predict(features)[0])
    
    # Risk assessment
    risk_engine = get_risk_engine()
    risk = risk_engine.assess_risk(
        equipment_name=equipment_name,
        health_score=health.score,
        failure_probability=failure_prob,
        rul_days=rul_days
    )
    
    return RiskAssessmentResponse(
        equipment_name=equipment_name,
        timestamp=datetime.now(),
        overall_risk=risk.overall_risk,
        risk_score=risk.risk_score,
        health_score=health.score,
        failure_probability=risk.failure_probability,
        rul_days=risk.rul_days,
        explanation=risk.explanation,
        contributing_factors=risk.contributing_factors,
        confidence=risk.confidence
    )


# ============ Warnings & Recommendations ============

@router.get("/warnings", response_model=WarningListResponse)
async def get_warnings(
    equipment_name: Optional[str] = None,
    level: Optional[str] = None
):
    """Get active early warnings."""
    warning_engine = get_warning_engine()
    warnings = warning_engine.get_active_warnings(equipment_name, level)
    
    return WarningListResponse(
        warnings=[
            EarlyWarningResponse(
                warning_id=w.warning_id,
                equipment_name=w.equipment_name,
                level=w.level,
                reason=w.reason,
                failure_probability=w.failure_probability,
                rul_days=w.rul_days,
                timestamp=w.timestamp
            )
            for w in warnings
        ],
        total=len(warnings),
        critical_count=len([w for w in warnings if w.level == 'critical']),
        high_count=len([w for w in warnings if w.level == 'high'])
    )


@router.get("/recommendations/{equipment_name}")
async def get_recommendations(
    equipment_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get maintenance recommendations for equipment."""
    # Get latest sensor data
    result = await db.execute(
        select(SensorData)
        .where(SensorData.equipment_name == equipment_name)
        .order_by(SensorData.timestamp.desc())
        .limit(1)
    )
    sensor_data = result.scalar_one_or_none()
    
    if not sensor_data:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    # Calculate predictions
    features = np.array([[
        sensor_data.temperature or 75,
        sensor_data.vibration or 1.5,
        sensor_data.current or 20,
        sensor_data.pressure or 70,
        sensor_data.rpm or 1500
    ]])
    
    # Get predictions
    failure_predictor = get_failure_predictor()
    failure_prob = None
    if failure_predictor.is_trained:
        failure_prob = float(failure_predictor.predict_proba(features)[0])
    
    rul_predictor = get_rul_predictor()
    rul_days = None
    if rul_predictor.is_trained:
        rul_days = int(rul_predictor.predict(features)[0])
    
    # Generate recommendations
    rec_engine = get_recommendation_engine()
    recommendations = rec_engine.check_and_generate(
        equipment_name=equipment_name,
        failure_probability=failure_prob,
        rul_days=rul_days
    )
    
    return {
        "equipment_name": equipment_name,
        "recommendations": [
            {
                "recommendation_id": r.recommendation_id,
                "equipment_name": r.equipment_name,
                "priority": r.priority,
                "category": r.category,
                "action": r.action,
                "reason": r.reason,
                "triggered_by": r.triggered_by,
                "created_at": r.created_at.isoformat()
            }
            for r in recommendations
        ]
    }


# ============ Equipment Predictions ============

@router.get("/equipment-predictions", response_model=EquipmentPredictionListResponse)
async def get_equipment_predictions(
    db: AsyncSession = Depends(get_db)
):
    """Get predictions for all equipment based on LATEST live sensor data."""
    # Get all equipment
    result = await db.execute(select(Equipment))
    equipment_list = result.scalars().all()

    # Use max(created_at) subquery — same approach as live-status — to get the
    # most recently *inserted* row per equipment (not the one with highest fake timestamp)
    from sqlalchemy import func as _func
    subq = (
        select(SensorData.equipment_name, _func.max(SensorData.created_at).label("max_ca"))
        .group_by(SensorData.equipment_name)
        .subquery()
    )
    stmt = (
        select(SensorData)
        .join(subq, (SensorData.equipment_name == subq.c.equipment_name) &
                    (SensorData.created_at == subq.c.max_ca))
    )
    latest_rows = (await db.execute(stmt)).scalars().all()
    sensor_map = {row.equipment_name: row for row in latest_rows}

    # Ensure models are trained
    failure_predictor = get_failure_predictor()
    rul_predictor     = get_rul_predictor()
    if not failure_predictor.is_trained:
        try: train_initial_failure_model()
        except Exception: pass
    if not rul_predictor.is_trained:
        try: train_initial_rul_model()
        except Exception: pass

    health_calculator   = get_health_calculator()
    degradation_engine  = get_degradation_engine()
    warning_engine      = get_warning_engine()

    # Clear stale in-memory warnings so we don't accumulate forever
    warning_engine.clear_warnings()

    predictions = []

    for eq in equipment_list:
        sensor_data = sensor_map.get(eq.equipment_name)
        if not sensor_data:
            continue

        # Build feature vector from live readings (no silent fallback to hardcoded defaults)
        t   = sensor_data.temperature
        v   = sensor_data.vibration
        c   = sensor_data.current
        p   = sensor_data.pressure
        rpm = sensor_data.rpm

        if any(x is None for x in [t, v, c, p, rpm]):
            continue  # Skip equipment with incomplete sensor data

        features = np.array([[float(t), float(v), float(c), float(p), float(rpm)]])

        # Health score from live readings
        readings = {'temperature': float(t), 'vibration': float(v),
                    'current': float(c), 'pressure': float(p), 'rpm': float(rpm)}
        health = health_calculator.calculate_score(readings)

        # Failure probability
        failure_prob = 0.0
        if failure_predictor.is_trained:
            failure_prob = float(failure_predictor.predict_proba(features)[0])

        # RUL
        rul_days = 100
        if rul_predictor.is_trained:
            rul_days = int(rul_predictor.predict(features)[0])

        # Risk level derived from live values
        if failure_prob >= 0.7 or rul_days < 15 or health.score < 40:
            risk_level = "Critical"
        elif failure_prob >= 0.5 or rul_days < 30 or health.score < 60:
            risk_level = "High"
        elif failure_prob >= 0.3 or rul_days < 60 or health.score < 80:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # Degradation
        degradation = degradation_engine.calculate_degradation(
            health_score=health.score,
            failure_probability=failure_prob,
            rul_days=rul_days
        )

        # Generate fresh warnings
        warning_engine.check_and_generate_warnings(
            equipment_name=eq.equipment_name,
            failure_probability=failure_prob,
            rul_days=rul_days
        )

        predictions.append(EquipmentPrediction(
            equipment_name=eq.equipment_name,
            health_score=health.score,
            failure_probability=round(failure_prob * 100, 1),
            rul_days=rul_days,
            risk_level=risk_level,
            degradation_level=degradation.level,
            anomaly_detected=health.score < 50,
            last_updated=sensor_data.created_at or datetime.now()
        ))

    # Sort by risk level
    risk_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
    predictions.sort(key=lambda x: risk_order.get(x.risk_level, 4))

    return EquipmentPredictionListResponse(
        predictions=predictions,
        total=len(predictions),
        critical_count=len([p for p in predictions if p.risk_level == 'Critical']),
        high_risk_count=len([p for p in predictions if p.risk_level == 'High'])
    )


# ============ Dashboard ============

@router.get("/dashboard", response_model=PredictiveDashboardResponse)
async def get_predictive_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """Get predictive maintenance dashboard data."""
    # Get equipment predictions
    predictions_response = await get_equipment_predictions(db)
    predictions = predictions_response.predictions
    # Get warnings
    warning_engine = get_warning_engine()
    warnings = warning_engine.get_active_warnings()[:10]
    
    # Calculate stats
    avg_failure_prob = sum(p.failure_probability for p in predictions) / len(predictions) if predictions else 0
    avg_rul = sum(p.rul_days for p in predictions) / len(predictions) if predictions else 0
    
    return PredictiveDashboardResponse(
        total_equipment=len(predictions),
        critical_risk_count=len([p for p in predictions if p.risk_level == 'Critical']),
        high_risk_count=len([p for p in predictions if p.risk_level == 'High']),
        medium_risk_count=len([p for p in predictions if p.risk_level == 'Medium']),
        low_risk_count=len([p for p in predictions if p.risk_level == 'Low']),
        critical_alerts=[
            EarlyWarningResponse(
                warning_id=w.warning_id,
                equipment_name=w.equipment_name,
                level=w.level,
                reason=w.reason,
                failure_probability=w.failure_probability,
                rul_days=w.rul_days,
                timestamp=w.timestamp
            )
            for w in warnings[:5]
        ],
        equipment_predictions=predictions[:20],
        average_failure_probability=round(avg_failure_prob, 1),
        average_rul_days=round(avg_rul, 1)
    )


# ============ Model Training ============

@router.post("/train-failure", response_model=TrainModelResponse)
async def train_failure_model():
    """Train failure prediction model."""
    try:
        # Train with synthetic data (in production, use real data)
        metrics = train_initial_failure_model()
        
        if metrics:
            return TrainModelResponse(
                status="success",
                model_name="failure_model",
                model_type="failure",
                metrics=metrics,
                trained_at=datetime.now()
            )
        else:
            return TrainModelResponse(
                status="already_trained",
                model_name="failure_model",
                model_type="failure",
                metrics={},
                trained_at=datetime.now()
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train-rul", response_model=TrainModelResponse)
async def train_rul_model():
    """Train RUL prediction model."""
    try:
        metrics = train_initial_rul_model()
        
        if metrics:
            return TrainModelResponse(
                status="success",
                model_name="rul_model",
                model_type="rul",
                metrics=metrics,
                trained_at=datetime.now()
            )
        else:
            return TrainModelResponse(
                status="already_trained",
                model_name="rul_model",
                model_type="rul",
                metrics={},
                trained_at=datetime.now()
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-metrics")
async def get_model_metrics():
    """Get metrics for both models."""
    failure_predictor = get_failure_predictor()
    rul_predictor = get_rul_predictor()
    
    return {
        "failure_model": {
            "trained": failure_predictor.is_trained,
            "model_type": failure_predictor.model_type,
            "metrics": failure_predictor.get_metrics()
        },
        "rul_model": {
            "trained": rul_predictor.is_trained,
            "model_type": rul_predictor.model_type,
            "metrics": rul_predictor.get_metrics()
        }
    }