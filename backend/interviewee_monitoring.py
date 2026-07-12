"""Candidate monitoring endpoints for violations and assessment time sync."""

from __future__ import annotations

import base64
import binascii
import contextlib
import logging
import os
import re
import uuid

from flask import Blueprint, jsonify, request

from assessment_db import (
    get_assessment_by_id,
    get_assessment_time_elapsed,
    update_assessment_time_elapsed,
    verify_assessment_access_token,
)
from proctoring_db import record_proctoring_violation_with_count
from storage_config import get_upload_subdirectory


logger = logging.getLogger(__name__)
interviewee_monitoring_bp = Blueprint("interviewee_monitoring", __name__)

ASSESSMENT_DURATION_SECONDS = 3_600
MAX_SCREENSHOT_BYTES = 5 * 1024 * 1024
VALID_SEVERITIES = frozenset({"low", "medium", "high", "critical"})
VIOLATION_TYPE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
SCREENSHOT_DATA_PATTERN = re.compile(
    r"^data:image/(?P<format>jpeg|jpg|png|webp);base64,(?P<data>.+)$",
    re.IGNORECASE | re.DOTALL,
)


def _check_assessment_token(assessment_id: int):
    token = request.headers.get("X-Assessment-Token", "")
    if not verify_assessment_access_token(token, assessment_id):
        return jsonify({"status": "error", "message": "Invalid or missing assessment token"}), 403
    return None


def _parse_json_object():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({"status": "error", "message": "A JSON object is required"}), 400)
    return data, None


def _decode_screenshot(screenshot_data):
    if not isinstance(screenshot_data, str) or not screenshot_data:
        raise ValueError("screenshot must be a base64 image string")

    match = SCREENSHOT_DATA_PATTERN.fullmatch(screenshot_data)
    if match:
        encoded = match.group("data")
        image_format = match.group("format").lower()
        extension = "jpg" if image_format in {"jpeg", "jpg"} else image_format
    else:
        encoded = screenshot_data
        extension = "jpg"

    # Reject oversized input before allocating the decoded byte buffer.
    if len(encoded) > ((MAX_SCREENSHOT_BYTES + 2) // 3) * 4 + 4:
        raise ValueError("screenshot must not exceed 5 MB")
    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("screenshot is not valid base64") from exc
    if not image_bytes:
        raise ValueError("screenshot image is empty")
    if len(image_bytes) > MAX_SCREENSHOT_BYTES:
        raise ValueError("screenshot must not exceed 5 MB")
    return image_bytes, extension


def _save_screenshot(assessment_id, image_bytes, extension):
    screenshots_dir = get_upload_subdirectory("violations", create=True)
    filename = f"violation_{assessment_id}_{uuid.uuid4().hex}.{extension}"
    filepath = screenshots_dir / filename
    # Exclusive creation prevents an accidental overwrite even under concurrency.
    try:
        with filepath.open("xb") as screenshot_file:
            screenshot_file.write(image_bytes)
    except OSError:
        with contextlib.suppress(OSError):
            filepath.unlink()
        raise
    return f"/uploads/violations/{filename}", filepath


@interviewee_monitoring_bp.route("/assessment/<int:assessment_id>/violation", methods=["POST"])
def report_violation(assessment_id):
    screenshot_path = None
    try:
        token_error = _check_assessment_token(assessment_id)
        if token_error:
            return token_error

        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({"status": "error", "message": "Assessment not found"}), 404
        if assessment.get("status") not in {"started", "in_progress"}:
            return jsonify({"status": "error", "message": "Assessment is not active"}), 409

        data, parse_error = _parse_json_object()
        if parse_error:
            return parse_error

        violation_type = data.get("violation_type")
        if not isinstance(violation_type, str):
            return jsonify({"status": "error", "message": "violation_type is required"}), 400
        violation_type = violation_type.strip().lower()
        if not VIOLATION_TYPE_PATTERN.fullmatch(violation_type):
            return jsonify({
                "status": "error",
                "message": "violation_type must use 1-64 lowercase letters, numbers, hyphens, or underscores",
            }), 400

        description = data.get("description", "")
        if not isinstance(description, str) or len(description) > 2_000:
            return jsonify({
                "status": "error",
                "message": "description must be a string of at most 2000 characters",
            }), 400

        severity = data.get("severity", "medium")
        if not isinstance(severity, str) or severity.strip().lower() not in VALID_SEVERITIES:
            return jsonify({
                "status": "error",
                "message": f"severity must be one of: {', '.join(sorted(VALID_SEVERITIES))}",
            }), 400
        severity = severity.strip().lower()

        screenshot_url = None
        screenshot_data = data.get("screenshot")
        if screenshot_data is not None:
            try:
                image_bytes, extension = _decode_screenshot(screenshot_data)
            except ValueError as exc:
                return jsonify({"status": "error", "message": str(exc)}), 400
            try:
                screenshot_url, screenshot_path = _save_screenshot(
                    assessment_id, image_bytes, extension
                )
            except OSError:
                # Recording the security event is more important than its optional image.
                logger.exception("Could not persist violation screenshot for assessment %s", assessment_id)

        violation_id, violation_count = record_proctoring_violation_with_count(
            assessment_id=assessment_id,
            violation_type=violation_type,
            description=description,
            severity=severity,
            screenshot_url=screenshot_url,
        )
        logger.info(
            "Violation recorded for assessment %s: %s (%s); total=%s",
            assessment_id,
            violation_type,
            severity,
            violation_count,
        )
        return jsonify({
            "status": "success",
            "message": "Violation recorded",
            "data": {
                "violation_id": violation_id,
                "total_violations": violation_count,
                "screenshot_saved": screenshot_url is not None,
            },
        }), 201
    except Exception:
        # A database failure after writing the file must not leave an orphan.
        if screenshot_path is not None:
            with contextlib.suppress(OSError):
                os.remove(screenshot_path)
        logger.exception("Failed to record violation for assessment %s", assessment_id)
        return jsonify({"status": "error", "message": "Failed to record violation"}), 500


@interviewee_monitoring_bp.route("/assessment/<int:assessment_id>/sync-time", methods=["POST"])
def sync_assessment_time(assessment_id):
    try:
        token_error = _check_assessment_token(assessment_id)
        if token_error:
            return token_error

        assessment = get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({"status": "error", "message": "Assessment not found"}), 404
        if assessment.get("status") not in {"started", "in_progress"}:
            return jsonify({"status": "error", "message": "Assessment is not active"}), 409

        data, parse_error = _parse_json_object()
        if parse_error:
            return parse_error
        submitted_elapsed = data.get("time_elapsed_seconds")
        if isinstance(submitted_elapsed, bool):
            return jsonify({"status": "error", "message": "time_elapsed_seconds must be an integer"}), 400
        try:
            submitted_elapsed = int(submitted_elapsed)
        except (TypeError, ValueError):
            return jsonify({"status": "error", "message": "time_elapsed_seconds must be an integer"}), 400
        if not 0 <= submitted_elapsed <= ASSESSMENT_DURATION_SECONDS:
            return jsonify({
                "status": "error",
                "message": f"time_elapsed_seconds must be between 0 and {ASSESSMENT_DURATION_SECONDS}",
            }), 400

        current_elapsed = int(get_assessment_time_elapsed(assessment_id) or 0)
        authoritative_elapsed = max(current_elapsed, submitted_elapsed)
        if authoritative_elapsed != current_elapsed:
            update_assessment_time_elapsed(assessment_id, authoritative_elapsed)

        remaining = max(0, ASSESSMENT_DURATION_SECONDS - authoritative_elapsed)
        return jsonify({
            "status": "success",
            "message": "Time synced",
            "data": {
                "server_elapsed_seconds": authoritative_elapsed,
                "server_remaining_seconds": remaining,
            },
        }), 200
    except Exception:
        logger.exception("Failed to sync time for assessment %s", assessment_id)
        return jsonify({"status": "error", "message": "Failed to sync time"}), 500
