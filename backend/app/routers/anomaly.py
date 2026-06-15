"""Phase 3: Anomaly Detection and Equipment Health Monitoring API."""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Equipment, SensorData
from app.models.schemas.anomaly_schemas import (
    SensorDataCreate, SensorDataResponse, SensorDataListResponse,
    PredictionRequest, PredictionResponse,
    EquipmentHealthResponse, HealthStatusResponse,
    AlertResponse, AlertListResponse, AlertAcknowledgeRequest, AlertSummaryResponse,
    HealthScoreDetailResponse, HealthFactorResponse,
    DashboardResponse, DashboardHealthSummary, DashboardSensorTrend
)
from app.health.prediction_service import get_prediction_service, PredictionService
from app.health.alert_engine import get_alert_engine, AlertEngine
from app.health.health_score import get_health_calculator, get_risk_classifier

router = APIRouter(prefix="/api/anomaly", tags=["Phase 3 - Anomaly Detection & Health Monitoring"])


# ============ Prediction Endpoints ============

@router.post("/predict", response_model=PredictionResponse)
async def predict_anomaly(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Predict anomaly and calculate health score for given sensor readings.
    
    This endpoint performs:
    1. Anomaly detection using Isolation Forest
    2. Health score calculation (0-100)
    3. Risk level classification
    4. Alert generation
    """
    service = get_prediction_service()
    
    result = service.predict(
        equipment_name=request.equipment_name,
        temperature=request.temperature,
        vibration=request.vibration,
        current=request.current,
        pressure=request.pressure,
        rpm=request.rpm,
        include_explanation=True
    )
    
    return PredictionResponse(
        equipment_name=result.equipment_name,
        timestamp=result.timestamp,
        anomaly=result.anomaly,
        anomaly_score=result.anomaly_score,
        health_score=result.health_score,
        health_status=result.health_status,
        risk_level=result.risk_level,
        message=result.message,
        recommendations=result.recommendations,
        alerts=result.alerts,
        explanation=result.explanation,
        sensor_readings=result.sensor_readings
    )


@router.post("/predict-bulk", response_model=List[PredictionResponse])
async def predict_bulk(
    readings: List[PredictionRequest],
    db: AsyncSession = Depends(get_db)
):
    """Predict anomalies for multiple sensor readings."""
    service = get_prediction_service()
    results = []
    
    for request in readings:
        result = service.predict(
            equipment_name=request.equipment_name,
            temperature=request.temperature,
            vibration=request.vibration,
            current=request.current,
            pressure=request.pressure,
            rpm=request.rpm,
            include_explanation=False
        )
        
        results.append(PredictionResponse(
            equipment_name=result.equipment_name,
            timestamp=result.timestamp,
            anomaly=result.anomaly,
            anomaly_score=result.anomaly_score,
            health_score=result.health_score,
            health_status=result.health_status,
            risk_level=result.risk_level,
            message=result.message,
            recommendations=result.recommendations,
            alerts=result.alerts,
            explanation=result.explanation,
            sensor_readings=result.sensor_readings
        ))
    
    return results


# ============ Health Score Endpoints ============

@router.get("/health-score", response_model=HealthScoreDetailResponse)
async def get_health_score_detail(
    temperature: float = Query(...),
    vibration: float = Query(...),
    current: float = Query(...),
    pressure: float = Query(...),
    rpm: float = Query(...)
):
    """
    Calculate detailed health score for given sensor readings.
    
    Returns:
    - Overall health score (0-100)
    - Individual factor scores
    - Status and recommendations
    """
    calculator = get_health_calculator()
    
    readings = {
        'temperature': temperature,
        'vibration': vibration,
        'current': current,
        'pressure': pressure,
        'rpm': rpm
    }
    
    result = calculator.calculate_score(readings)
    
    # Convert factors to response format
    factor_details = calculator.calculate_factors_from_raw(readings)
    factors_response = {}
    
    for feature, detail in factor_details.items():
        factors_response[feature] = HealthFactorResponse(**detail)
    
    return HealthScoreDetailResponse(
        score=result.score,
        status=result.status,
        risk_level=result.risk_level,
        factors=factors_response,
        explanation=result.explanation,
        recommendations=result.recommendations
    )


# ============ Health Status Endpoints ============

@router.get("/health-status", response_model=HealthStatusResponse)
async def get_health_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get health status for all equipment.
    
    Returns overall health statistics and per-equipment status.
    """
    # Get all equipment
    result = await db.execute(select(Equipment))
    equipment_list = result.scalars().all()
    
    # Get recent sensor data for each equipment
    equipment_health = []
    status_counts = defaultdict(int)
    
    for eq in equipment_list:
        # Get recent sensor readings
        sensor_result = await db.execute(
            select(SensorData)
            .where(SensorData.equipment_name == eq.equipment_name)
            .order_by(desc(SensorData.timestamp))
            .limit(10)
        )
        recent_readings = sensor_result.scalars().all()
        
        # Calculate health
        service = get_prediction_service()
        
        if recent_readings:
            readings_list = [
                {
                    'temperature': r.temperature or 75,
                    'vibration': r.vibration or 1.5,
                    'current': r.current or 20,
                    'pressure': r.pressure or 70,
                    'rpm': r.rpm or 1500
                }
                for r in recent_readings
            ]
            health = service.get_equipment_health(eq.equipment_name, readings_list)
            latest_reading = recent_readings[0]
        else:
            health = {
                'equipment_name': eq.equipment_name,
                'status': 'unknown',
                'health_score': 100,
                'trend': 'stable'
            }
            latest_reading = None
        
        status_counts[health['status']] += 1
        
        equipment_health.append(EquipmentHealthResponse(
            equipment_name=health['equipment_name'],
            health_score=health.get('health_score', 100),
            health_status=health.get('status', 'unknown').capitalize(),
            risk_level='Low' if health.get('health_score', 100) > 75 else 'High' if health.get('health_score', 100) > 50 else 'Critical',
            status=health.get('status', 'unknown'),
            trend=health.get('trend', 'stable'),
            anomaly_count=health.get('anomaly_count', 0),
            total_readings=health.get('total_readings', 0),
            last_updated=latest_reading.timestamp if latest_reading else datetime.now()
        ))
    
    total = len(equipment_list)
    healthy_count = status_counts.get('healthy', 0)
    overall_percentage = (healthy_count / total * 100) if total > 0 else 100
    
    return HealthStatusResponse(
        total_equipment=total,
        healthy_count=healthy_count,
        fair_count=status_counts.get('fair', 0),
        poor_count=status_counts.get('poor', 0),
        critical_count=status_counts.get('critical', 0),
        equipment=equipment_health,
        overall_health_percentage=overall_percentage
    )


@router.get("/equipment-health/{equipment_name}", response_model=EquipmentHealthResponse)
async def get_equipment_health(
    equipment_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get health status for specific equipment."""
    # Get recent sensor readings
    result = await db.execute(
        select(SensorData)
        .where(SensorData.equipment_name == equipment_name)
        .order_by(desc(SensorData.timestamp))
        .limit(20)
    )
    recent_readings = result.scalars().all()
    
    if not recent_readings:
        return EquipmentHealthResponse(
            equipment_name=equipment_name,
            health_score=100,
            health_status='Unknown',
            risk_level='Low',
            status='no_data',
            trend='stable',
            anomaly_count=0,
            total_readings=0,
            last_updated=datetime.now()
        )
    
    # Calculate health
    service = get_prediction_service()
    readings_list = [
        {
            'temperature': r.temperature or 75,
            'vibration': r.vibration or 1.5,
            'current': r.current or 20,
            'pressure': r.pressure or 70,
            'rpm': r.rpm or 1500
        }
        for r in recent_readings
    ]
    health = service.get_equipment_health(equipment_name, readings_list)
    
    return EquipmentHealthResponse(
        equipment_name=health['equipment_name'],
        health_score=health.get('health_score', 100),
        health_status=health.get('status', 'unknown').capitalize(),
        risk_level='Low' if health.get('health_score', 100) > 75 else 'High' if health.get('health_score', 100) > 50 else 'Critical',
        status=health.get('status', 'unknown'),
        trend=health.get('trend', 'stable'),
        anomaly_count=health.get('anomaly_count', 0),
        total_readings=health.get('total_readings', 0),
        last_updated=recent_readings[0].timestamp if recent_readings else datetime.now()
    )


# ============ Alert Endpoints ============

@router.get("/alerts", response_model=AlertListResponse)
async def get_alerts(
    equipment_name: Optional[str] = None,
    alert_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """
    Get equipment alerts.
    
    Filter by equipment, alert type, and status.
    """
    alert_engine = get_alert_engine()
    
    # Get active alerts
    alerts = alert_engine.get_active_alerts(
        equipment_name=equipment_name,
        alert_type=alert_type,
        limit=limit
    )
    
    # Filter by status if specified
    if status:
        alerts = [a for a in alerts if a.status == status]
    
    # Convert to response format
    alert_responses = [
        AlertResponse(
            alert_id=a.alert_id,
            equipment_name=a.equipment_name,
            alert_type=a.alert_type,
            severity=a.severity,
            message=a.message,
            timestamp=a.timestamp,
            status=a.status,
            source=a.source,
            sensor_readings=a.sensor_readings,
            health_score=a.health_score
        )
        for a in alerts
    ]
    
    critical_count = len([a for a in alerts if a.alert_type == 'critical'])
    
    return AlertListResponse(
        alerts=alert_responses,
        total=len(alert_responses),
        active_count=len([a for a in alerts if a.status == 'active']),
        critical_count=critical_count
    )


@router.post("/alerts/acknowledge")
async def acknowledge_alert(
    request: AlertAcknowledgeRequest
):
    """Acknowledge an alert."""
    alert_engine = get_alert_engine()
    success = alert_engine.acknowledge_alert(request.alert_id, request.acknowledged_by)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"status": "acknowledged", "alert_id": request.alert_id}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Mark an alert as resolved."""
    alert_engine = get_alert_engine()
    success = alert_engine.resolve_alert(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"status": "resolved", "alert_id": alert_id}


@router.get("/alerts/summary", response_model=AlertSummaryResponse)
async def get_alert_summary():
    """Get summary of all alerts."""
    alert_engine = get_alert_engine()
    summary = alert_engine.get_alert_summary()
    
    return AlertSummaryResponse(**summary)


# ============ Sensor Data Endpoints ============

@router.post("/sensor-data", response_model=SensorDataResponse)
async def create_sensor_data(
    request: SensorDataCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create new sensor data entry and trigger health analysis.
    
    This will:
    1. Store the sensor reading
    2. Run anomaly detection
    3. Calculate health score
    4. Generate alerts if needed
    """
    # Create sensor data
    sensor_id = str(uuid.uuid4())
    timestamp = request.timestamp or datetime.now()
    
    sensor_data = SensorData(
        sensor_id=sensor_id,
        equipment_name=request.equipment_name,
        temperature=request.temperature,
        vibration=request.vibration,
        current=request.current,
        pressure=request.pressure,
        rpm=request.rpm,
        timestamp=timestamp
    )
    
    db.add(sensor_data)
    await db.commit()
    await db.refresh(sensor_data)
    
    # Run prediction (alerts will be stored in alert engine)
    if all(v is not None for v in [request.temperature, request.vibration, 
                                    request.current, request.pressure, request.rpm]):
        service = get_prediction_service()
        service.predict(
            equipment_name=request.equipment_name,
            temperature=request.temperature,
            vibration=request.vibration,
            current=request.current,
            pressure=request.pressure,
            rpm=request.rpm,
            include_explanation=False
        )
    
    return SensorDataResponse(
        sensor_id=sensor_data.sensor_id,
        equipment_name=sensor_data.equipment_name,
        temperature=sensor_data.temperature,
        vibration=sensor_data.vibration,
        current=sensor_data.current,
        pressure=sensor_data.pressure,
        rpm=sensor_data.rpm,
        timestamp=sensor_data.timestamp,
        created_at=sensor_data.created_at
    )


@router.get("/sensor-data", response_model=SensorDataListResponse)
async def get_sensor_data(
    equipment_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get sensor data with filtering and pagination."""
    query = select(SensorData)
    
    if equipment_name:
        query = query.where(SensorData.equipment_name == equipment_name)
    if start_date:
        query = query.where(SensorData.timestamp >= start_date)
    if end_date:
        query = query.where(SensorData.timestamp <= end_date)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.order_by(desc(SensorData.timestamp))
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    data = result.scalars().all()
    
    return SensorDataListResponse(
        data=[
            SensorDataResponse(
                sensor_id=s.sensor_id,
                equipment_name=s.equipment_name,
                temperature=s.temperature,
                vibration=s.vibration,
                current=s.current,
                pressure=s.pressure,
                rpm=s.rpm,
                timestamp=s.timestamp,
                created_at=s.created_at
            )
            for s in data
        ],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/sensor-data/latest")
async def get_latest_sensor_data(
    equipment_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the latest sensor reading for equipment."""
    result = await db.execute(
        select(SensorData)
        .where(SensorData.equipment_name == equipment_name)
        .order_by(desc(SensorData.timestamp))
        .limit(1)
    )
    data = result.scalar_one_or_none()
    
    if not data:
        raise HTTPException(status_code=404, detail="No sensor data found")
    
    return {
        "sensor_id": data.sensor_id,
        "equipment_name": data.equipment_name,
        "temperature": data.temperature,
        "vibration": data.vibration,
        "current": data.current,
        "pressure": data.pressure,
        "rpm": data.rpm,
        "timestamp": data.timestamp
    }


# ============ Dashboard Endpoint ============

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete dashboard data for health monitoring.
    
    Returns:
    - Health summary statistics
    - Recent alerts
    - Equipment health status
    - Sensor trends
    """
    alert_engine = get_alert_engine()
    
    # Get recent alerts
    recent_alerts = alert_engine.get_active_alerts(limit=10)
    alert_responses = [
        AlertResponse(
            alert_id=a.alert_id,
            equipment_name=a.equipment_name,
            alert_type=a.alert_type,
            severity=a.severity,
            message=a.message,
            timestamp=a.timestamp,
            status=a.status,
            source=a.source,
            sensor_readings=a.sensor_readings,
            health_score=a.health_score
        )
        for a in recent_alerts
    ]
    
    # Get health status
    health_status = await get_health_status(db)
    
    # Get sensor trends
    result = await db.execute(
        select(SensorData)
        .order_by(desc(SensorData.timestamp))
        .limit(100)
    )
    sensor_data = result.scalars().all()
    
    sensor_trends = []
    for s in sensor_data:
        # Calculate health score for each reading
        health_score = None
        if all(v is not None for v in [s.temperature, s.vibration, s.current, s.pressure, s.rpm]):
            calculator = get_health_calculator()
            health = calculator.calculate_score({
                'temperature': s.temperature,
                'vibration': s.vibration,
                'current': s.current,
                'pressure': s.pressure,
                'rpm': s.rpm
            })
            health_score = health.score
        
        sensor_trends.append(DashboardSensorTrend(
            equipment_name=s.equipment_name,
            timestamp=s.timestamp,
            temperature=s.temperature,
            vibration=s.vibration,
            current=s.current,
            pressure=s.pressure,
            rpm=int(round(s.rpm)) if s.rpm is not None else None,
            health_score=health_score
        ))
    
    # Calculate health summary
    avg_health = sum(e.health_score for e in health_status.equipment) / len(health_status.equipment) if health_status.equipment else 100
    
    health_summary = DashboardHealthSummary(
        total_equipment=health_status.total_equipment,
        healthy_percentage=health_status.overall_health_percentage,
        average_health_score=int(avg_health),
        active_alerts=alert_engine.get_alert_summary()['active'],
        critical_alerts=alert_engine.get_alert_summary()['critical_count'],
        anomalies_detected=len([e for e in health_status.equipment if e.anomaly_count > 0])
    )
    
    return DashboardResponse(
        health_summary=health_summary,
        recent_alerts=alert_responses,
        equipment_health=health_status.equipment,
        sensor_trends=sensor_trends
    )


# ============ Model Training Endpoint ============

@router.post("/train-model")
async def train_anomaly_model():
    """
    Retrain the anomaly detection model.
    
    This should be called periodically to update the model with new data.
    """
    from app.anomaly_detection.detector import train_initial_model
    
    try:
        metrics = train_initial_model()
        return {
            "status": "success",
            "message": "Model trained successfully",
            "metrics": metrics
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }