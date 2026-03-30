from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rtls_api.alerts import (
    acknowledge_alert,
    create_alert_rule,
    evaluate_alerts_for_position_update,
    get_alert_instance_detail,
    get_alert_notification_summary,
    get_alert_rule,
    list_alert_actions,
    list_alert_deliveries,
    list_alert_instances,
    list_alert_rules,
    resolve_alert,
    serialize_alert_detail,
    serialize_alert_list_item,
    serialize_alert_rule,
    sync_gateway_maintenance_alerts,
    update_alert_rule,
)
from rtls_api.auth import get_current_user, get_settings
from rtls_api.config import Settings
from rtls_api.db import get_db
from rtls_api.derived_events import DerivedZoneSemanticsResult
from rtls_api.models import User
from rtls_api.schemas import (
    AlertActionRequest,
    AlertDetailResponse,
    AlertListItemResponse,
    AlertNotificationSummaryResponse,
    AlertRuleResponse,
    AlertRuleUpsertRequest,
)

ALERT_ROUTER = APIRouter(prefix="/api/alerts", tags=["alerts"])


@ALERT_ROUTER.get("/summary", response_model=AlertNotificationSummaryResponse)
def read_alert_summary(
    site_id: str | None = None,
    floor_id: str | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: User = Depends(get_current_user),
) -> AlertNotificationSummaryResponse:
    sync_gateway_maintenance_alerts(
        db=db,
        settings=settings,
        site_id=site_id,
        floor_id=floor_id,
    )
    payload = AlertNotificationSummaryResponse.model_validate(
        get_alert_notification_summary(db=db, site_id=site_id, floor_id=floor_id)
    )
    db.commit()
    return payload


@ALERT_ROUTER.get("/rules", response_model=list[AlertRuleResponse])
def read_alert_rules(
    site_id: str | None = None,
    floor_id: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AlertRuleResponse]:
    return [
        AlertRuleResponse.model_validate(serialize_alert_rule(rule))
        for rule in list_alert_rules(db=db, site_id=site_id, floor_id=floor_id)
    ]


@ALERT_ROUTER.post("/rules", response_model=AlertRuleResponse)
def create_rule(
    payload: AlertRuleUpsertRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: User = Depends(get_current_user),
) -> AlertRuleResponse:
    rule = create_alert_rule(db=db, actor=actor, payload=payload)
    if rule.floor_id is not None:
        evaluate_alerts_for_position_update(
            db=db,
            settings=settings,
            floor_ids={rule.floor_id},
            semantics=DerivedZoneSemanticsResult(),
            observed_at=datetime.now(timezone.utc),
        )
    db.commit()
    return AlertRuleResponse.model_validate(serialize_alert_rule(rule))


@ALERT_ROUTER.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
def update_rule(
    rule_id: str,
    payload: AlertRuleUpsertRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    actor: User = Depends(get_current_user),
) -> AlertRuleResponse:
    rule = update_alert_rule(db=db, actor=actor, rule_id=rule_id, payload=payload)
    if rule.floor_id is not None:
        evaluate_alerts_for_position_update(
            db=db,
            settings=settings,
            floor_ids={rule.floor_id},
            semantics=DerivedZoneSemanticsResult(),
            observed_at=datetime.now(timezone.utc),
        )
    db.commit()
    refreshed = get_alert_rule(db=db, rule_id=rule.id)
    return AlertRuleResponse.model_validate(serialize_alert_rule(refreshed))


@ALERT_ROUTER.get("", response_model=list[AlertListItemResponse])
def read_alerts(
    site_id: str | None = None,
    floor_id: str | None = None,
    status_value: str | None = None,
    rule_type: str | None = None,
    severity: str | None = None,
    search: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: User = Depends(get_current_user),
) -> list[AlertListItemResponse]:
    sync_gateway_maintenance_alerts(
        db=db,
        settings=settings,
        site_id=site_id,
        floor_id=floor_id,
    )
    alerts = list_alert_instances(
        db=db,
        site_id=site_id,
        floor_id=floor_id,
        status_value=status_value,
        rule_type=rule_type,
        severity=severity,
        search=search,
        start_at=start_at,
        end_at=end_at,
    )
    payload = [
        AlertListItemResponse.model_validate(serialize_alert_list_item(alert))
        for alert in alerts
    ]
    db.commit()
    return payload


@ALERT_ROUTER.get("/{alert_id}", response_model=AlertDetailResponse)
def read_alert_detail(
    alert_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: User = Depends(get_current_user),
) -> AlertDetailResponse:
    alert = get_alert_instance_detail(db=db, alert_id=alert_id)
    sync_gateway_maintenance_alerts(
        db=db,
        settings=settings,
        site_id=alert.site_id,
        floor_id=alert.floor_id,
    )
    alert = get_alert_instance_detail(db=db, alert_id=alert_id)
    actions = list_alert_actions(db=db, alert_id=alert.id)
    deliveries = list_alert_deliveries(db=db, alert_id=alert.id)
    payload = AlertDetailResponse.model_validate(
        serialize_alert_detail(alert, actions=actions, deliveries=deliveries)
    )
    db.commit()
    return payload


@ALERT_ROUTER.post("/{alert_id}/acknowledge", response_model=AlertDetailResponse)
def acknowledge_alert_instance(
    alert_id: str,
    payload: AlertActionRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> AlertDetailResponse:
    alert = acknowledge_alert(
        db=db,
        actor=actor,
        alert_id=alert_id,
        noted_at=datetime.now(timezone.utc),
        notes=payload.notes,
    )
    db.commit()
    refreshed = get_alert_instance_detail(db=db, alert_id=alert.id)
    actions = list_alert_actions(db=db, alert_id=alert.id)
    deliveries = list_alert_deliveries(db=db, alert_id=alert.id)
    return AlertDetailResponse.model_validate(
        serialize_alert_detail(refreshed, actions=actions, deliveries=deliveries)
    )


@ALERT_ROUTER.post("/{alert_id}/resolve", response_model=AlertDetailResponse)
def resolve_alert_instance(
    alert_id: str,
    payload: AlertActionRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
) -> AlertDetailResponse:
    alert = resolve_alert(
        db=db,
        actor=actor,
        alert_id=alert_id,
        resolved_at=datetime.now(timezone.utc),
        notes=payload.notes,
    )
    db.commit()
    refreshed = get_alert_instance_detail(db=db, alert_id=alert.id)
    actions = list_alert_actions(db=db, alert_id=alert.id)
    deliveries = list_alert_deliveries(db=db, alert_id=alert.id)
    return AlertDetailResponse.model_validate(
        serialize_alert_detail(refreshed, actions=actions, deliveries=deliveries)
    )
