from __future__ import annotations

import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from rtls_api.audit import write_audit_event
from rtls_api.config import Settings
from rtls_api.derived_events import DerivedZoneSemanticsResult, ensure_utc
from rtls_api.models import (
    AlertAction,
    AlertActionType,
    AlertDeliveryChannel,
    AlertDeliveryStatus,
    AlertInstance,
    AlertNotificationDelivery,
    AlertRule,
    AlertRuleType,
    AlertSeverity,
    AlertStatus,
    DerivedZoneTransitionEvent,
    Floor,
    Gateway,
    SpatialArea,
    SpatialAreaType,
    TableServiceTimerState,
    TableServiceTimerStatus,
    UnauthorizedGeofenceTrigger,
    User,
)
from rtls_api.schemas import AlertRuleUpsertRequest

ACTIVE_ALERT_STATUSES = [AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value]
SYSTEM_MANAGED_ALERT_RULE_TYPES = {
    AlertRuleType.GATEWAY_STALE.value,
    AlertRuleType.GATEWAY_LOW_BATTERY.value,
}
USER_MANAGED_ALERT_RULE_TYPES = {
    AlertRuleType.TABLE_SLA.value,
    AlertRuleType.UNAUTHORIZED_GEOFENCE.value,
}


def list_alert_rules(
    *,
    db: Session,
    site_id: str | None = None,
    floor_id: str | None = None,
) -> list[AlertRule]:
    query = (
        select(AlertRule)
        .options(joinedload(AlertRule.site), joinedload(AlertRule.floor))
        .where(AlertRule.rule_type.in_(sorted(USER_MANAGED_ALERT_RULE_TYPES)))
        .order_by(AlertRule.created_at.desc(), AlertRule.name.asc())
    )
    if site_id is not None:
        query = query.where(AlertRule.site_id == site_id)
    if floor_id is not None:
        query = query.where(AlertRule.floor_id == floor_id)
    return db.scalars(query).all()


def get_alert_rule(*, db: Session, rule_id: str) -> AlertRule:
    rule = db.scalar(
        select(AlertRule)
        .options(joinedload(AlertRule.site), joinedload(AlertRule.floor))
        .where(AlertRule.id == rule_id)
    )
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert rule not found")
    return rule


def create_alert_rule(
    *,
    db: Session,
    actor: User,
    payload: AlertRuleUpsertRequest,
) -> AlertRule:
    _validate_user_managed_rule_type(payload.rule_type)
    rule_definition = _build_rule_definition(db=db, payload=payload)
    rule = AlertRule(
        name=payload.name.strip(),
        rule_type=payload.rule_type.value,
        severity=rule_definition["severity"],
        enabled=payload.enabled,
        site_id=rule_definition["site_id"],
        floor_id=rule_definition["floor_id"],
        config=rule_definition["config"],
        delivery=rule_definition["delivery"],
        created_by_user_id=actor.id,
        updated_by_user_id=actor.id,
    )
    db.add(rule)
    db.flush()
    write_audit_event(
        db,
        action_category="alerts",
        action_type="alert.rule.created",
        actor=actor,
        target_type="alert_rule",
        target_id=rule.id,
        details={
            "rule_type": rule.rule_type,
            "floor_id": rule.floor_id,
            "enabled": rule.enabled,
        },
    )
    return get_alert_rule(db=db, rule_id=rule.id)


def update_alert_rule(
    *,
    db: Session,
    actor: User,
    rule_id: str,
    payload: AlertRuleUpsertRequest,
) -> AlertRule:
    rule = get_alert_rule(db=db, rule_id=rule_id)
    if rule.rule_type in SYSTEM_MANAGED_ALERT_RULE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="System-managed maintenance rules cannot be edited manually",
        )
    _validate_user_managed_rule_type(payload.rule_type)
    rule_definition = _build_rule_definition(db=db, payload=payload)
    previous_state = {
        "name": rule.name,
        "enabled": rule.enabled,
        "rule_type": rule.rule_type,
        "config": rule.config,
        "delivery": rule.delivery,
    }
    rule.name = payload.name.strip()
    rule.rule_type = payload.rule_type.value
    rule.severity = rule_definition["severity"]
    rule.enabled = payload.enabled
    rule.site_id = rule_definition["site_id"]
    rule.floor_id = rule_definition["floor_id"]
    rule.config = rule_definition["config"]
    rule.delivery = rule_definition["delivery"]
    rule.updated_by_user_id = actor.id
    _clear_rule_active_alerts(
        db=db,
        rule=rule,
        cleared_at=datetime.now(timezone.utc),
        reason="rule_updated",
    )
    write_audit_event(
        db,
        action_category="alerts",
        action_type="alert.rule.updated",
        actor=actor,
        target_type="alert_rule",
        target_id=rule.id,
        details={
            "before": previous_state,
            "after": {
                "name": rule.name,
                "enabled": rule.enabled,
                "rule_type": rule.rule_type,
                "config": rule.config,
                "delivery": rule.delivery,
            },
        },
    )
    db.flush()
    return get_alert_rule(db=db, rule_id=rule.id)


def list_alert_instances(
    *,
    db: Session,
    site_id: str | None = None,
    floor_id: str | None = None,
    status_value: str | None = None,
    rule_type: str | None = None,
    severity: str | None = None,
    search: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
) -> list[AlertInstance]:
    query = (
        select(AlertInstance)
        .options(
            joinedload(AlertInstance.rule).joinedload(AlertRule.site),
            joinedload(AlertInstance.rule).joinedload(AlertRule.floor),
            joinedload(AlertInstance.site),
            joinedload(AlertInstance.floor),
            joinedload(AlertInstance.area),
            joinedload(AlertInstance.asset_tag),
        )
        .order_by(AlertInstance.last_triggered_at.desc(), AlertInstance.created_at.desc())
    )
    if site_id is not None:
        query = query.where(AlertInstance.site_id == site_id)
    if floor_id is not None:
        query = query.where(AlertInstance.floor_id == floor_id)
    if status_value is not None:
        query = query.where(AlertInstance.status == status_value)
    if rule_type is not None:
        query = query.where(AlertInstance.rule_type == rule_type)
    if severity is not None:
        query = query.where(AlertInstance.severity == severity)
    if start_at is not None:
        query = query.where(AlertInstance.last_triggered_at >= start_at)
    if end_at is not None:
        query = query.where(AlertInstance.first_triggered_at <= end_at)
    if search:
        needle = f"%{search.strip()}%"
        query = query.where(
            or_(
                AlertInstance.title.ilike(needle),
                AlertInstance.summary.ilike(needle),
                AlertInstance.scope_label.ilike(needle),
            )
        )
    return db.scalars(query).all()


def get_alert_instance_detail(*, db: Session, alert_id: str) -> AlertInstance:
    alert = db.scalar(
        select(AlertInstance)
        .options(
            joinedload(AlertInstance.rule).joinedload(AlertRule.site),
            joinedload(AlertInstance.rule).joinedload(AlertRule.floor),
            joinedload(AlertInstance.site),
            joinedload(AlertInstance.floor),
            joinedload(AlertInstance.area),
            joinedload(AlertInstance.asset_tag),
        )
        .where(AlertInstance.id == alert_id)
    )
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert


def list_alert_actions(*, db: Session, alert_id: str) -> list[AlertAction]:
    return db.scalars(
        select(AlertAction)
        .where(AlertAction.alert_id == alert_id)
        .order_by(AlertAction.created_at.asc())
    ).all()


def list_alert_deliveries(*, db: Session, alert_id: str) -> list[AlertNotificationDelivery]:
    return db.scalars(
        select(AlertNotificationDelivery)
        .where(AlertNotificationDelivery.alert_id == alert_id)
        .order_by(AlertNotificationDelivery.created_at.asc())
    ).all()


def acknowledge_alert(
    *,
    db: Session,
    actor: User,
    alert_id: str,
    noted_at: datetime,
    notes: str | None = None,
) -> AlertInstance:
    alert = get_alert_instance_detail(db=db, alert_id=alert_id)
    if alert.status == AlertStatus.CLEARED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cleared alerts cannot be acknowledged",
        )
    if alert.status == AlertStatus.RESOLVED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resolved alerts cannot be acknowledged",
        )
    if alert.status == AlertStatus.OPEN.value:
        alert.status = AlertStatus.ACKNOWLEDGED.value
        alert.acknowledged_at = ensure_utc(noted_at)
        alert.acknowledged_by_user_id = actor.id
        _record_alert_action(
            db=db,
            alert=alert,
            action_type=AlertActionType.ACKNOWLEDGED,
            actor=actor,
            notes=notes,
        )
        write_audit_event(
            db,
            action_category="alerts",
            action_type="alert.instance.acknowledged",
            actor=actor,
            target_type="alert_instance",
            target_id=alert.id,
            details={"status": alert.status},
        )
    return alert


def resolve_alert(
    *,
    db: Session,
    actor: User,
    alert_id: str,
    resolved_at: datetime,
    notes: str | None = None,
) -> AlertInstance:
    alert = get_alert_instance_detail(db=db, alert_id=alert_id)
    if alert.status == AlertStatus.CLEARED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cleared alerts cannot be resolved",
        )
    if alert.status != AlertStatus.RESOLVED.value:
        alert.status = AlertStatus.RESOLVED.value
        alert.resolved_at = ensure_utc(resolved_at)
        alert.resolved_by_user_id = actor.id
        _record_alert_action(
            db=db,
            alert=alert,
            action_type=AlertActionType.RESOLVED,
            actor=actor,
            notes=notes,
        )
        write_audit_event(
            db,
            action_category="alerts",
            action_type="alert.instance.resolved",
            actor=actor,
            target_type="alert_instance",
            target_id=alert.id,
            details={"status": alert.status},
        )
    return alert


def get_alert_notification_summary(
    *,
    db: Session,
    site_id: str | None = None,
    floor_id: str | None = None,
) -> dict[str, object]:
    active_filters = [AlertInstance.status.in_(ACTIVE_ALERT_STATUSES)]
    if site_id is not None:
        active_filters.append(AlertInstance.site_id == site_id)
    if floor_id is not None:
        active_filters.append(AlertInstance.floor_id == floor_id)

    unresolved_count = (
        db.scalar(select(func.count()).select_from(AlertInstance).where(*active_filters)) or 0
    )
    active_critical_count = (
        db.scalar(
            select(func.count())
            .select_from(AlertInstance)
            .where(*active_filters, AlertInstance.severity == AlertSeverity.CRITICAL.value)
        )
        or 0
    )
    active_warning_count = (
        db.scalar(
            select(func.count())
            .select_from(AlertInstance)
            .where(*active_filters, AlertInstance.severity == AlertSeverity.WARNING.value)
        )
        or 0
    )
    latest_alert_at = db.scalar(
        select(func.max(AlertInstance.last_triggered_at)).where(*active_filters)
    )
    unread_count = (
        db.scalar(
            select(func.count())
            .select_from(AlertNotificationDelivery)
            .join(AlertNotificationDelivery.alert)
            .where(
                AlertNotificationDelivery.channel == AlertDeliveryChannel.IN_APP.value,
                AlertNotificationDelivery.read_at.is_(None),
                AlertInstance.status.in_(ACTIVE_ALERT_STATUSES),
                *([AlertInstance.site_id == site_id] if site_id is not None else []),
                *([AlertInstance.floor_id == floor_id] if floor_id is not None else []),
            )
        )
        or 0
    )
    return {
        "unresolved_count": int(unresolved_count),
        "unread_count": int(unread_count),
        "active_critical_count": int(active_critical_count),
        "active_warning_count": int(active_warning_count),
        "latest_alert_at": ensure_utc(latest_alert_at),
    }


def evaluate_alerts_for_position_update(
    *,
    db: Session,
    settings: Settings,
    floor_ids: set[str],
    semantics: DerivedZoneSemanticsResult,
    observed_at: datetime,
) -> None:
    normalized_observed_at = ensure_utc(observed_at)
    _reevaluate_table_sla_alerts(
        db=db,
        settings=settings,
        floor_ids={floor_id for floor_id in floor_ids if floor_id},
        observed_at=normalized_observed_at,
    )
    _evaluate_unauthorized_geofence_transition(
        db=db,
        settings=settings,
        entry_event=semantics.entry_event,
        exit_event=semantics.exit_event,
        observed_at=normalized_observed_at,
    )


def sync_gateway_maintenance_alerts(
    *,
    db: Session,
    settings: Settings,
    site_id: str | None = None,
    floor_id: str | None = None,
    gateway_ids: set[str] | None = None,
    observed_at: datetime | None = None,
) -> None:
    scope_gateway_ids = {gateway_id for gateway_id in (gateway_ids or set()) if gateway_id}
    now = ensure_utc(observed_at or datetime.now(timezone.utc))
    query = select(Gateway).options(
        joinedload(Gateway.floor).joinedload(Floor.site),
        joinedload(Gateway.latest_heartbeat),
    )
    if scope_gateway_ids:
        query = query.where(Gateway.id.in_(sorted(scope_gateway_ids)))
    if site_id is not None:
        query = query.join(Gateway.floor).where(Floor.site_id == site_id)
    if floor_id is not None:
        query = query.where(Gateway.floor_id == floor_id)

    gateways = (
        db.scalars(query.order_by(Gateway.display_name.asc(), Gateway.gateway_identifier.asc()))
        .unique()
        .all()
    )
    rule_cache: dict[tuple[str, str], AlertRule] = {}
    for gateway in gateways:
        _sync_gateway_maintenance_alerts_for_gateway(
            db=db,
            settings=settings,
            gateway=gateway,
            observed_at=now,
            rule_cache=rule_cache,
        )
    db.flush()


def serialize_alert_rule(rule: AlertRule) -> dict[str, object]:
    return {
        "id": rule.id,
        "name": rule.name,
        "rule_type": rule.rule_type,
        "severity": rule.severity,
        "enabled": rule.enabled,
        "site_id": rule.site.id if rule.site is not None else None,
        "site_name": rule.site.name if rule.site is not None else None,
        "floor_id": rule.floor.id if rule.floor is not None else None,
        "floor_name": rule.floor.name if rule.floor is not None else None,
        "config": rule.config,
        "delivery": rule.delivery,
        "created_at": ensure_utc(rule.created_at),
        "updated_at": ensure_utc(rule.updated_at),
    }


def serialize_alert_list_item(alert: AlertInstance) -> dict[str, object]:
    site = alert.site or alert.rule.site
    floor = alert.floor or alert.rule.floor
    area = alert.area
    asset_tag = alert.asset_tag
    return {
        "id": alert.id,
        "rule_id": alert.rule_id,
        "rule_name": alert.rule.name,
        "rule_type": alert.rule_type,
        "severity": alert.severity,
        "status": alert.status,
        "title": alert.title,
        "summary": alert.summary,
        "scope_key": alert.scope_key,
        "scope_label": alert.scope_label,
        "site_id": site.id if site is not None else None,
        "site_name": site.name if site is not None else None,
        "floor_id": floor.id if floor is not None else None,
        "floor_name": floor.name if floor is not None else None,
        "area_id": area.id if area is not None else None,
        "area_name": area.name if area is not None else None,
        "asset_tag_id": asset_tag.id if asset_tag is not None else None,
        "asset_label": asset_tag.display_name if asset_tag is not None else None,
        "first_triggered_at": ensure_utc(alert.first_triggered_at),
        "last_triggered_at": ensure_utc(alert.last_triggered_at),
        "acknowledged_at": ensure_utc(alert.acknowledged_at),
        "resolved_at": ensure_utc(alert.resolved_at),
        "cleared_at": ensure_utc(alert.cleared_at),
    }


def serialize_alert_action(action: AlertAction) -> dict[str, object]:
    return {
        "id": action.id,
        "action_type": action.action_type,
        "actor_user_id": action.actor_user_id,
        "actor_email": action.actor_email,
        "actor_display_name": action.actor_display_name,
        "notes": action.notes,
        "details": action.details,
        "created_at": ensure_utc(action.created_at),
    }


def serialize_alert_delivery(delivery: AlertNotificationDelivery) -> dict[str, object]:
    return {
        "id": delivery.id,
        "channel": delivery.channel,
        "destination": delivery.destination,
        "status": delivery.status,
        "error_message": delivery.error_message,
        "read_at": ensure_utc(delivery.read_at),
        "created_at": ensure_utc(delivery.created_at),
    }


def serialize_alert_detail(
    alert: AlertInstance,
    *,
    actions: list[AlertAction],
    deliveries: list[AlertNotificationDelivery],
) -> dict[str, object]:
    payload = serialize_alert_list_item(alert)
    payload["condition_key"] = alert.condition_key
    payload["context"] = alert.context_payload
    payload["rule"] = serialize_alert_rule(alert.rule)
    payload["actions"] = [serialize_alert_action(action) for action in actions]
    payload["deliveries"] = [serialize_alert_delivery(delivery) for delivery in deliveries]
    return payload


def _validate_user_managed_rule_type(rule_type: AlertRuleType) -> None:
    if rule_type.value in USER_MANAGED_ALERT_RULE_TYPES:
        return
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="System-managed maintenance alert types cannot be created manually",
    )


def _build_rule_definition(
    *,
    db: Session,
    payload: AlertRuleUpsertRequest,
) -> dict[str, object]:
    if payload.rule_type in {
        AlertRuleType.GATEWAY_STALE,
        AlertRuleType.GATEWAY_LOW_BATTERY,
    }:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="System-managed maintenance alert types cannot be created manually",
        )
    if payload.rule_type == AlertRuleType.TABLE_SLA:
        areas = _load_areas(db=db, area_ids=payload.table_area_ids or [])
        _validate_single_floor_area_scope(areas)
        for area in areas:
            if area.area_type != SpatialAreaType.TABLE.value or area.sla_eligible is not True:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Table SLA rules require SLA-eligible table areas",
                )
        floor = areas[0].floor
        return {
            "severity": AlertSeverity.WARNING.value,
            "site_id": floor.site_id,
            "floor_id": floor.id,
            "config": {
                "threshold_seconds": float(payload.threshold_seconds or 0),
                "table_area_ids": [area.id for area in areas],
            },
            "delivery": _build_delivery_definition(payload=payload),
        }

    areas = _load_areas(db=db, area_ids=payload.area_ids or [])
    _validate_single_floor_area_scope(areas)
    for area in areas:
        if (
            area.area_type != SpatialAreaType.RESTRICTED_ZONE.value
            or area.alert_participation is not True
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Unauthorized geofence rules require participating restricted zones",
            )
    floor = areas[0].floor
    return {
        "severity": AlertSeverity.CRITICAL.value,
        "site_id": floor.site_id,
        "floor_id": floor.id,
        "config": {
            "area_ids": [area.id for area in areas],
            "trigger_on": payload.trigger_on.value if payload.trigger_on else None,
            "asset_category": payload.asset_category,
        },
        "delivery": _build_delivery_definition(payload=payload),
    }


def _build_delivery_definition(*, payload: AlertRuleUpsertRequest) -> dict[str, object]:
    return {
        "in_app": True,
        "email": payload.notify_email,
        "email_recipients": [str(recipient) for recipient in payload.email_recipients],
    }


def _load_areas(*, db: Session, area_ids: list[str]) -> list[SpatialArea]:
    normalized_ids = sorted({area_id.strip() for area_id in area_ids if area_id.strip()})
    if not normalized_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="At least one area must be selected",
        )
    areas = db.scalars(
        select(SpatialArea)
        .options(joinedload(SpatialArea.floor))
        .where(SpatialArea.id.in_(normalized_ids))
    ).all()
    if len(areas) != len(normalized_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="One or more scoped areas were not found",
        )
    return sorted(areas, key=lambda area: area.name)


def _validate_single_floor_area_scope(areas: list[SpatialArea]) -> None:
    floor_ids = {area.floor_id for area in areas}
    if len(floor_ids) != 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Delivered alert rules must target areas on a single floor",
        )


def _reevaluate_table_sla_alerts(
    *,
    db: Session,
    settings: Settings,
    floor_ids: set[str],
    observed_at: datetime,
) -> None:
    if not floor_ids:
        return

    timer_states = db.scalars(
        select(TableServiceTimerState)
        .join(TableServiceTimerState.table_area)
        .join(TableServiceTimerState.floor)
        .options(
            joinedload(TableServiceTimerState.table_area),
            joinedload(TableServiceTimerState.floor).joinedload(Floor.site),
        )
        .where(TableServiceTimerState.floor_id.in_(sorted(floor_ids)))
    ).all()
    timer_states_by_area = {timer_state.table_area_id: timer_state for timer_state in timer_states}
    rules = db.scalars(
        select(AlertRule)
        .where(
            AlertRule.rule_type == AlertRuleType.TABLE_SLA.value,
            AlertRule.floor_id.in_(sorted(floor_ids)),
        )
        .options(joinedload(AlertRule.site), joinedload(AlertRule.floor))
    ).all()

    for rule in rules:
        if not rule.enabled:
            _clear_rule_active_alerts(
                db=db,
                rule=rule,
                cleared_at=observed_at,
                reason="rule_disabled",
            )
            continue

        threshold_seconds = float(rule.config["threshold_seconds"])
        table_area_ids = [str(area_id) for area_id in rule.config.get("table_area_ids", [])]
        for area_id in table_area_ids:
            timer_state = timer_states_by_area.get(area_id)
            if timer_state is None:
                _clear_alert_scope(
                    db=db,
                    rule=rule,
                    scope_key=f"table:{area_id}",
                    cleared_at=observed_at,
                    reason="timer_missing",
                )
                continue

            active_since = ensure_utc(timer_state.active_since)
            if (
                timer_state.status == TableServiceTimerStatus.ACTIVE.value
                and active_since is not None
                and _seconds_between(active_since, observed_at) >= threshold_seconds
            ):
                elapsed_seconds = _seconds_between(active_since, observed_at)
                _create_or_maintain_alert(
                    db=db,
                    settings=settings,
                    rule=rule,
                    scope_key=f"table:{timer_state.table_area_id}",
                    scope_label=timer_state.table_area.name,
                    title=f"Table SLA breach · {timer_state.table_area.name}",
                    summary=(
                        f"{timer_state.table_area.name} has remained active for "
                        f"{int(elapsed_seconds)} seconds against a "
                        f"{int(threshold_seconds)} second SLA."
                    ),
                    site_id=timer_state.floor.site_id,
                    floor_id=timer_state.floor_id,
                    area_id=timer_state.table_area_id,
                    asset_tag_id=None,
                    condition_key=active_since.isoformat(),
                    context_payload={
                        "table_name": timer_state.table_area.name,
                        "threshold_seconds": threshold_seconds,
                        "elapsed_seconds": elapsed_seconds,
                        "active_since": active_since.isoformat(),
                    },
                    observed_at=observed_at,
                )
            else:
                _clear_alert_scope(
                    db=db,
                    rule=rule,
                    scope_key=f"table:{area_id}",
                    cleared_at=observed_at,
                    reason="timer_cleared",
                )


def _evaluate_unauthorized_geofence_transition(
    *,
    db: Session,
    settings: Settings,
    entry_event: DerivedZoneTransitionEvent | None,
    exit_event: DerivedZoneTransitionEvent | None,
    observed_at: datetime,
) -> None:
    floor_ids = {event.floor_id for event in (entry_event, exit_event) if event is not None}
    if not floor_ids:
        return

    rules = db.scalars(
        select(AlertRule)
        .where(
            AlertRule.rule_type == AlertRuleType.UNAUTHORIZED_GEOFENCE.value,
            AlertRule.floor_id.in_(sorted(floor_ids)),
        )
        .options(joinedload(AlertRule.site), joinedload(AlertRule.floor))
    ).all()

    for rule in rules:
        if not rule.enabled:
            _clear_rule_active_alerts(
                db=db,
                rule=rule,
                cleared_at=observed_at,
                reason="rule_disabled",
            )
            continue

        scoped_area_ids = {str(area_id) for area_id in rule.config.get("area_ids", [])}
        asset_category = rule.config.get("asset_category")
        trigger_on = rule.config.get("trigger_on")

        if (
            entry_event is not None
            and trigger_on == UnauthorizedGeofenceTrigger.ENTRY.value
            and entry_event.zone_id in scoped_area_ids
            and entry_event.zone.area_type == SpatialAreaType.RESTRICTED_ZONE.value
            and (not asset_category or entry_event.asset_tag.asset_category == asset_category)
        ):
            _create_or_maintain_alert(
                db=db,
                settings=settings,
                rule=rule,
                scope_key=f"asset:{entry_event.asset_tag_id}:area:{entry_event.zone_id}:entry",
                scope_label=f"{entry_event.asset_tag.display_name} · {entry_event.zone.name}",
                title=f"Unauthorized geofence entry · {entry_event.asset_tag.display_name}",
                summary=(
                    f"{entry_event.asset_tag.display_name} entered restricted zone "
                    f"{entry_event.zone.name}."
                ),
                site_id=entry_event.floor.site_id,
                floor_id=entry_event.floor_id,
                area_id=entry_event.zone_id,
                asset_tag_id=entry_event.asset_tag_id,
                condition_key=entry_event.transition_boundary_id,
                context_payload={
                    "transition_boundary_id": entry_event.transition_boundary_id,
                    "trigger_on": trigger_on,
                    "zone_name": entry_event.zone.name,
                    "asset_category": entry_event.asset_tag.asset_category,
                    "observed_at": ensure_utc(entry_event.observed_at).isoformat(),
                },
                observed_at=observed_at,
            )

        if (
            exit_event is not None
            and trigger_on == UnauthorizedGeofenceTrigger.EXIT.value
            and exit_event.zone_id in scoped_area_ids
            and exit_event.zone.area_type == SpatialAreaType.RESTRICTED_ZONE.value
            and (not asset_category or exit_event.asset_tag.asset_category == asset_category)
        ):
            _create_or_maintain_alert(
                db=db,
                settings=settings,
                rule=rule,
                scope_key=f"asset:{exit_event.asset_tag_id}:area:{exit_event.zone_id}:exit",
                scope_label=f"{exit_event.asset_tag.display_name} · {exit_event.zone.name}",
                title=f"Unauthorized geofence exit · {exit_event.asset_tag.display_name}",
                summary=(
                    f"{exit_event.asset_tag.display_name} exited restricted zone "
                    f"{exit_event.zone.name}."
                ),
                site_id=exit_event.floor.site_id,
                floor_id=exit_event.floor_id,
                area_id=exit_event.zone_id,
                asset_tag_id=exit_event.asset_tag_id,
                condition_key=exit_event.transition_boundary_id,
                context_payload={
                    "transition_boundary_id": exit_event.transition_boundary_id,
                    "trigger_on": trigger_on,
                    "zone_name": exit_event.zone.name,
                    "asset_category": exit_event.asset_tag.asset_category,
                    "observed_at": ensure_utc(exit_event.observed_at).isoformat(),
                },
                observed_at=observed_at,
            )

        if (
            exit_event is not None
            and trigger_on == UnauthorizedGeofenceTrigger.ENTRY.value
            and exit_event.zone_id in scoped_area_ids
        ):
            _clear_alert_scope(
                db=db,
                rule=rule,
                scope_key=f"asset:{exit_event.asset_tag_id}:area:{exit_event.zone_id}:entry",
                cleared_at=observed_at,
                reason="asset_left_zone",
            )


def _create_or_maintain_alert(
    *,
    db: Session,
    settings: Settings,
    rule: AlertRule,
    scope_key: str,
    scope_label: str,
    title: str,
    summary: str,
    site_id: str | None,
    floor_id: str | None,
    area_id: str | None,
    asset_tag_id: str | None,
    condition_key: str | None,
    context_payload: dict[str, object] | None,
    observed_at: datetime,
) -> AlertInstance:
    active_alert = db.scalar(
        select(AlertInstance)
        .where(
            AlertInstance.rule_id == rule.id,
            AlertInstance.scope_key == scope_key,
            AlertInstance.status.in_(ACTIVE_ALERT_STATUSES),
        )
        .order_by(AlertInstance.last_triggered_at.desc())
    )
    if active_alert is not None:
        active_alert.last_triggered_at = observed_at
        active_alert.title = title
        active_alert.summary = summary
        active_alert.context_payload = context_payload
        return active_alert

    if condition_key is not None:
        previous_match = db.scalar(
            select(AlertInstance)
            .where(
                AlertInstance.rule_id == rule.id,
                AlertInstance.scope_key == scope_key,
                AlertInstance.condition_key == condition_key,
                AlertInstance.status.in_([AlertStatus.RESOLVED.value, AlertStatus.CLEARED.value]),
            )
            .order_by(AlertInstance.last_triggered_at.desc())
        )
        if previous_match is not None:
            return previous_match

    alert = AlertInstance(
        rule_id=rule.id,
        rule_type=rule.rule_type,
        severity=rule.severity,
        status=AlertStatus.OPEN.value,
        title=title,
        summary=summary,
        scope_key=scope_key,
        scope_label=scope_label,
        site_id=site_id,
        floor_id=floor_id,
        area_id=area_id,
        asset_tag_id=asset_tag_id,
        condition_key=condition_key,
        context_payload=context_payload,
        first_triggered_at=observed_at,
        last_triggered_at=observed_at,
    )
    db.add(alert)
    db.flush()
    _record_alert_action(
        db=db,
        alert=alert,
        action_type=AlertActionType.TRIGGERED,
        actor=None,
        notes=None,
        details={"condition_key": condition_key},
    )
    _create_notification_deliveries(db=db, settings=settings, rule=rule, alert=alert)
    return alert


def _clear_rule_active_alerts(
    *,
    db: Session,
    rule: AlertRule,
    cleared_at: datetime,
    reason: str,
) -> None:
    active_alerts = db.scalars(
        select(AlertInstance).where(
            AlertInstance.rule_id == rule.id,
            AlertInstance.status.in_(ACTIVE_ALERT_STATUSES),
        )
    ).all()
    for alert in active_alerts:
        _clear_alert_instance(
            db=db,
            alert=alert,
            cleared_at=cleared_at,
            reason=reason,
        )


def _clear_alert_scope(
    *,
    db: Session,
    rule: AlertRule,
    scope_key: str,
    cleared_at: datetime,
    reason: str,
) -> None:
    alert = db.scalar(
        select(AlertInstance).where(
            AlertInstance.rule_id == rule.id,
            AlertInstance.scope_key == scope_key,
            AlertInstance.status.in_(ACTIVE_ALERT_STATUSES),
        )
    )
    if alert is not None:
        _clear_alert_instance(db=db, alert=alert, cleared_at=cleared_at, reason=reason)


def _clear_alert_instance(
    *,
    db: Session,
    alert: AlertInstance,
    cleared_at: datetime,
    reason: str,
) -> None:
    alert.status = AlertStatus.CLEARED.value
    alert.cleared_at = cleared_at
    _record_alert_action(
        db=db,
        alert=alert,
        action_type=AlertActionType.CLEARED,
        actor=None,
        notes=None,
        details={"reason": reason},
    )


def _record_alert_action(
    *,
    db: Session,
    alert: AlertInstance,
    action_type: AlertActionType,
    actor: User | None,
    notes: str | None,
    details: dict[str, object] | None = None,
) -> None:
    db.add(
        AlertAction(
            alert_id=alert.id,
            action_type=action_type.value,
            actor_user_id=actor.id if actor is not None else None,
            actor_email=actor.email if actor is not None else None,
            actor_display_name=actor.display_name if actor is not None else "System",
            notes=notes,
            details=details,
        )
    )


def _create_notification_deliveries(
    *,
    db: Session,
    settings: Settings,
    rule: AlertRule,
    alert: AlertInstance,
) -> None:
    db.add(
        AlertNotificationDelivery(
            alert_id=alert.id,
            channel=AlertDeliveryChannel.IN_APP.value,
            destination="alerts-center",
            status=AlertDeliveryStatus.DELIVERED.value,
        )
    )
    if not bool(rule.delivery.get("email")):
        return

    recipients = [str(recipient) for recipient in rule.delivery.get("email_recipients", [])]
    if not recipients:
        return

    if not _email_delivery_is_configured(settings):
        for recipient in recipients:
            db.add(
                AlertNotificationDelivery(
                    alert_id=alert.id,
                    channel=AlertDeliveryChannel.EMAIL.value,
                    destination=recipient,
                    status=AlertDeliveryStatus.SKIPPED.value,
                    error_message="email_delivery_not_configured",
                )
            )
        return

    for recipient in recipients:
        try:
            _deliver_email_notification(
                settings=settings,
                recipient=recipient,
                subject=alert.title,
                body=(
                    f"{alert.summary}\n\nScope: {alert.scope_label}\nTriggered: "
                    f"{alert.first_triggered_at.isoformat()}"
                ),
            )
            db.add(
                AlertNotificationDelivery(
                    alert_id=alert.id,
                    channel=AlertDeliveryChannel.EMAIL.value,
                    destination=recipient,
                    status=AlertDeliveryStatus.DELIVERED.value,
                )
            )
        except Exception as error:  # pragma: no cover - exercised through monkeypatchable helper
            db.add(
                AlertNotificationDelivery(
                    alert_id=alert.id,
                    channel=AlertDeliveryChannel.EMAIL.value,
                    destination=recipient,
                    status=AlertDeliveryStatus.FAILED.value,
                    error_message=str(error),
                )
            )


def _email_delivery_is_configured(settings: Settings) -> bool:
    return bool(settings.smtp_host and settings.alert_email_from_address)


def _deliver_email_notification(
    *,
    settings: Settings,
    recipient: str,
    subject: str,
    body: str,
) -> None:
    message = EmailMessage()
    message["From"] = settings.alert_email_from_address
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    _send_email_message(settings=settings, message=message)


def _send_email_message(*, settings: Settings, message: EmailMessage) -> None:
    if settings.smtp_host is None:
        raise RuntimeError("SMTP host not configured")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)


def _sync_gateway_maintenance_alerts_for_gateway(
    *,
    db: Session,
    settings: Settings,
    gateway: Gateway,
    observed_at: datetime,
    rule_cache: dict[tuple[str, str], AlertRule],
) -> None:
    stale_rule = _ensure_system_alert_rule(
        db=db,
        gateway=gateway,
        rule_type=AlertRuleType.GATEWAY_STALE,
        severity=AlertSeverity.CRITICAL,
        rule_cache=rule_cache,
    )
    battery_rule = _ensure_system_alert_rule(
        db=db,
        gateway=gateway,
        rule_type=AlertRuleType.GATEWAY_LOW_BATTERY,
        severity=AlertSeverity.WARNING,
        rule_cache=rule_cache,
    )
    scope_label = gateway.display_name
    site_id = gateway.floor.site_id if gateway.floor is not None else None
    heartbeat = gateway.latest_heartbeat

    if heartbeat is None:
        _clear_alert_scope(
            db=db,
            rule=stale_rule,
            scope_key=f"gateway:{gateway.id}",
            cleared_at=observed_at,
            reason="heartbeat_missing",
        )
        _clear_alert_scope(
            db=db,
            rule=battery_rule,
            scope_key=f"gateway:{gateway.id}:battery",
            cleared_at=observed_at,
            reason="battery_unavailable",
        )
        return

    heartbeat_seen_at = ensure_utc(heartbeat.last_seen_at)
    condition_key = heartbeat.message_id or heartbeat_seen_at.isoformat()
    if observed_at - heartbeat_seen_at > timedelta(
        seconds=settings.gateway_heartbeat_stale_after_seconds
    ):
        _create_or_maintain_alert(
            db=db,
            settings=settings,
            rule=stale_rule,
            scope_key=f"gateway:{gateway.id}",
            scope_label=scope_label,
            title=f"Gateway offline · {gateway.display_name}",
            summary=(
                f"{gateway.display_name} has not reported a heartbeat since "
                f"{heartbeat_seen_at.isoformat()}."
            ),
            site_id=site_id,
            floor_id=gateway.floor_id,
            area_id=None,
            asset_tag_id=None,
            condition_key=condition_key,
            context_payload={
                "gateway_id": gateway.id,
                "gateway_identifier": gateway.gateway_identifier,
                "last_seen_at": heartbeat_seen_at.isoformat(),
                "battery_level_percent": heartbeat.battery_level_percent,
                "state": "stale",
            },
            observed_at=observed_at,
        )
    else:
        _clear_alert_scope(
            db=db,
            rule=stale_rule,
            scope_key=f"gateway:{gateway.id}",
            cleared_at=observed_at,
            reason="heartbeat_recovered",
        )

    battery_level = heartbeat.battery_level_percent
    if battery_level is not None and battery_level < 20:
        _create_or_maintain_alert(
            db=db,
            settings=settings,
            rule=battery_rule,
            scope_key=f"gateway:{gateway.id}:battery",
            scope_label=scope_label,
            title=f"Gateway battery low · {gateway.display_name}",
            summary=f"{gateway.display_name} battery is at {battery_level:.0f}%.",
            site_id=site_id,
            floor_id=gateway.floor_id,
            area_id=None,
            asset_tag_id=None,
            condition_key=condition_key,
            context_payload={
                "gateway_id": gateway.id,
                "gateway_identifier": gateway.gateway_identifier,
                "battery_level_percent": battery_level,
                "last_seen_at": heartbeat_seen_at.isoformat(),
                "state": "low_battery",
            },
            observed_at=observed_at,
        )
    else:
        _clear_alert_scope(
            db=db,
            rule=battery_rule,
            scope_key=f"gateway:{gateway.id}:battery",
            cleared_at=observed_at,
            reason="battery_recovered",
        )


def _ensure_system_alert_rule(
    *,
    db: Session,
    gateway: Gateway,
    rule_type: AlertRuleType,
    severity: AlertSeverity,
    rule_cache: dict[tuple[str, str], AlertRule],
) -> AlertRule:
    floor = gateway.floor
    if floor is None:
        raise RuntimeError("Gateway floor context is required for maintenance alerts")
    cache_key = (floor.id, rule_type.value)
    cached_rule = rule_cache.get(cache_key)
    if cached_rule is not None:
        return cached_rule

    rule = db.scalar(
        select(AlertRule)
        .options(joinedload(AlertRule.site), joinedload(AlertRule.floor))
        .where(AlertRule.floor_id == floor.id, AlertRule.rule_type == rule_type.value)
    )
    if rule is None:
        rule = AlertRule(
            name=(
                "Gateway Offline Maintenance"
                if rule_type == AlertRuleType.GATEWAY_STALE
                else "Gateway Low Battery Maintenance"
            ),
            rule_type=rule_type.value,
            severity=severity.value,
            enabled=True,
            site_id=floor.site_id,
            floor_id=floor.id,
            config={"system_managed": True, "kind": rule_type.value},
            delivery={"in_app": True, "email": False, "email_recipients": []},
            created_by_user_id=None,
            updated_by_user_id=None,
        )
        db.add(rule)
        db.flush()
        rule = get_alert_rule(db=db, rule_id=rule.id)
    rule_cache[cache_key] = rule
    return rule


def _seconds_between(start_at: datetime, end_at: datetime) -> float:
    return max(0.0, (ensure_utc(end_at) - ensure_utc(start_at)).total_seconds())
