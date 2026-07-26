"""
Admin user management routes — CRUD for platform users.
"""

import logging
import psycopg2
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from db_config import get_connection, return_connection
from auth import VALID_ROLES, hash_password, validate_email
from admin_middleware import require_admin_role

logger = logging.getLogger(__name__)

admin_users_bp = Blueprint('admin_users', __name__)

_PRIVILEGED_ROLES = {'admin', 'super_admin'}
_SECTOR_SCOPED_ROLES = {'recruiter', 'sector_admin'}


def _is_super_admin():
    return get_jwt().get('role') == 'super_admin'


def _sector_id_for_role(value, role):
    if role not in _SECTOR_SCOPED_ROLES:
        return None
    try:
        sector_id = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError('sector_id is required for this role') from exc
    if isinstance(value, bool) or sector_id <= 0:
        raise ValueError('sector_id is required for this role')
    return sector_id


@admin_users_bp.route('/users', methods=['GET'])
@jwt_required()
@require_admin_role
def get_all_users():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, email, role, sector_id, created_at FROM users ORDER BY id"
        )
        rows = cursor.fetchall()

        users = [{
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'role': row[3],
            'sector_id': row[4],
            'created_at': row[5]
        } for row in rows]

        return jsonify({'status': 'success', 'data': users}), 200
    except Exception:
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    finally:
        if conn:
            return_connection(conn)


@admin_users_bp.route('/users', methods=['POST'])
@jwt_required()
@require_admin_role
def create_user():
    conn = None
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'status': 'error', 'message': 'A JSON object is required'}), 400

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'interviewer')

        if not all(isinstance(value, str) for value in (name, email, password, role)):
            return jsonify({'status': 'error', 'message': 'User fields must be strings'}), 400

        name = name.strip()
        email = email.strip().lower()
        role = role.strip().lower()

        if not all([name, email, password]):
            return jsonify({'status': 'error', 'message': 'Name, email, and password are required'}), 400

        if not validate_email(email):
            return jsonify({'status': 'error', 'message': 'Invalid email format'}), 400

        if len(password) < 8 or len(password) > 128:
            return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters'}), 400

        if role not in VALID_ROLES:
            return jsonify({'status': 'error', 'message': 'Invalid role'}), 400

        if role in _PRIVILEGED_ROLES and not _is_super_admin():
            return jsonify({
                'status': 'error',
                'message': 'Only super admins can create privileged users'
            }), 403

        try:
            sector_id = _sector_id_for_role(data.get('sector_id'), role)
        except ValueError as exc:
            return jsonify({'status': 'error', 'message': str(exc)}), 400

        actor_id = get_jwt_identity()
        logger.info("[ADMIN ACTION] user %s creating role %s", actor_id, role)

        password_hash = hash_password(password)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role, sector_id) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (name, email, password_hash, role, sector_id)
        )
        result = cursor.fetchone()
        user_id = result[0] if result else None
        conn.commit()

        logger.info("[ADMIN ACTION] user %s created user %s", actor_id, user_id)

        return jsonify({
            'status': 'success',
            'message': 'User created successfully',
            'data': {
                'id': user_id,
                'name': name,
                'email': email,
                'role': role,
                'sector_id': sector_id,
            }
        }), 201
    except psycopg2.errors.ForeignKeyViolation:
        if conn:
            conn.rollback()
        return jsonify({
            'status': 'error',
            'message': 'sector_id does not reference an existing sector',
        }), 400
    except psycopg2.IntegrityError:
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'message': 'Email already exists'}), 409
    except Exception:
        if conn:
            conn.rollback()
        logger.exception("[ADMIN ERROR] Failed to create user")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    finally:
        if conn:
            return_connection(conn)


@admin_users_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@require_admin_role
def update_user(user_id):
    conn = None
    try:
        actor_id = get_jwt_identity()
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'status': 'error', 'message': 'A JSON object is required'}), 400

        unknown_fields = set(data) - {'name', 'email', 'role', 'password', 'sector_id'}
        if unknown_fields:
            return jsonify({'status': 'error', 'message': 'Unsupported user fields'}), 400

        logger.info("[ADMIN ACTION] user %s updating user %s fields=%s", actor_id, user_id, sorted(data))

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role, sector_id FROM users WHERE id = %s", (user_id,))
        target = cursor.fetchone()
        if not target:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        if target[0] in _PRIVILEGED_ROLES and not _is_super_admin():
            return jsonify({
                'status': 'error',
                'message': 'Only super admins can modify privileged users'
            }), 403

        from psycopg2 import sql as psql
        field_names = []
        values = []

        if 'name' in data:
            if not isinstance(data['name'], str) or not data['name'].strip():
                return jsonify({'status': 'error', 'message': 'Name must be a non-empty string'}), 400
            field_names.append('name')
            values.append(data['name'].strip())
        if 'email' in data:
            if not isinstance(data['email'], str) or not validate_email(data['email'].strip().lower()):
                return jsonify({'status': 'error', 'message': 'Invalid email format'}), 400
            field_names.append('email')
            values.append(data['email'].strip().lower())
        if 'role' in data:
            if not isinstance(data['role'], str) or data['role'].strip().lower() not in VALID_ROLES:
                return jsonify({'status': 'error', 'message': 'Invalid role'}), 400
            requested_role = data['role'].strip().lower()
            if requested_role in _PRIVILEGED_ROLES and not _is_super_admin():
                return jsonify({
                    'status': 'error',
                    'message': 'Only super admins can assign privileged roles'
                }), 403
            field_names.append('role')
            values.append(requested_role)
        else:
            requested_role = target[0]

        if 'role' in data or 'sector_id' in data:
            try:
                sector_id = _sector_id_for_role(
                    data.get('sector_id', target[1]),
                    requested_role,
                )
            except ValueError as exc:
                return jsonify({'status': 'error', 'message': str(exc)}), 400
            field_names.append('sector_id')
            values.append(sector_id)
        if 'password' in data and data['password']:
            if not isinstance(data['password'], str) or not 8 <= len(data['password']) <= 128:
                return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters'}), 400
            field_names.append('password_hash')
            values.append(hash_password(data['password']))

        if not field_names:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        values.append(user_id)
        set_clause = psql.SQL(', ').join(
            [psql.SQL("{} = %s").format(psql.Identifier(f)) for f in field_names]
        )
        query = psql.SQL("UPDATE users SET {}, updated_at = CURRENT_TIMESTAMP WHERE id = %s").format(set_clause)
        cursor.execute(query, values)
        conn.commit()

        logger.info("[ADMIN ACTION] user %s updated user %s", actor_id, user_id)

        return jsonify({'status': 'success', 'message': 'User updated successfully'}), 200
    except psycopg2.errors.ForeignKeyViolation:
        if conn:
            conn.rollback()
        return jsonify({
            'status': 'error',
            'message': 'sector_id does not reference an existing sector',
        }), 400
    except psycopg2.IntegrityError:
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'message': 'Email already exists'}), 409
    except Exception:
        if conn:
            conn.rollback()
        logger.exception("[ADMIN ERROR] Failed to update user %s", user_id)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    finally:
        if conn:
            return_connection(conn)


@admin_users_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@require_admin_role
def delete_user(user_id):
    conn = None
    try:
        actor_id = get_jwt_identity()
        if str(user_id) == str(actor_id):
            return jsonify({'status': 'error', 'message': 'You cannot delete your own account'}), 400

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        user_role = user[0]
        if user_role in _PRIVILEGED_ROLES and not _is_super_admin():
            return jsonify({
                'status': 'error',
                'message': 'Only super admins can delete privileged users'
            }), 403

        logger.warning(
            "[ADMIN ACTION] user %s deleting user %s with role %s",
            actor_id,
            user_id,
            user_role,
        )

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

        logger.info("[ADMIN ACTION] user %s deleted user %s", actor_id, user_id)

        return jsonify({'status': 'success', 'message': 'User deleted successfully'}), 200
    except psycopg2.errors.ForeignKeyViolation:
        if conn:
            conn.rollback()
        return jsonify({
            'status': 'error',
            'message': "Reassign this user's active hiring work before deleting the account",
        }), 409
    except Exception:
        if conn:
            conn.rollback()
        logger.exception("[ADMIN ERROR] Failed to delete user %s", user_id)
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    finally:
        if conn:
            return_connection(conn)
