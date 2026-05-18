"""
Admin user management routes — CRUD for platform users.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from db_config import get_connection, return_connection
from auth import hash_password, validate_email
from admin_middleware import require_admin_role

logger = logging.getLogger(__name__)

admin_users_bp = Blueprint('admin_users', __name__)


@admin_users_bp.route('/users', methods=['GET'])
@jwt_required()
@require_admin_role
def get_all_users():
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role, created_at FROM users ORDER BY id")
        rows = cursor.fetchall()

        users = [{
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'role': row[3],
            'created_at': row[4]
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
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'interviewer')

        if not all([name, email, password]):
            return jsonify({'status': 'error', 'message': 'Name, email, and password are required'}), 400

        if not validate_email(email):
            return jsonify({'status': 'error', 'message': 'Invalid email format'}), 400

        if len(password) < 8:
            return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters'}), 400

        if role not in ['interviewer', 'admin', 'proctor']:
            return jsonify({'status': 'error', 'message': 'Invalid role. Must be interviewer, proctor, or admin'}), 400

        admin_email = get_jwt_identity()
        logger.info(f"[ADMIN ACTION] {admin_email} creating new user: {email} with role: {role}")

        password_hash = hash_password(password)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, %s) RETURNING id",
            (name, email, password_hash, role)
        )
        result = cursor.fetchone()
        user_id = result[0] if result else None
        conn.commit()
        conn.close()

        logger.info(f"[ADMIN ACTION] {admin_email} successfully created user ID: {user_id} ({email})")

        return jsonify({
            'status': 'success',
            'message': 'User created successfully',
            'data': {'id': user_id, 'name': name, 'email': email, 'role': role}
        }), 201
    except Exception as e:
        if 'unique constraint' in str(e).lower() or 'duplicate' in str(e).lower():
            return jsonify({'status': 'error', 'message': 'Email already exists'}), 409
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_users_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@require_admin_role
def update_user(user_id):
    try:
        admin_email = get_jwt_identity()
        data = request.get_json()

        logger.info(f"[ADMIN ACTION] {admin_email} updating user ID: {user_id} with data: {list(data.keys())}")

        conn = get_connection()
        cursor = conn.cursor()

        from psycopg2 import sql as psql
        field_names = []
        values = []

        if 'name' in data:
            field_names.append('name')
            values.append(data['name'])
        if 'email' in data:
            if not validate_email(data['email']):
                return jsonify({'status': 'error', 'message': 'Invalid email format'}), 400
            field_names.append('email')
            values.append(data['email'])
        if 'role' in data:
            if data['role'] not in ['interviewer', 'admin', 'proctor']:
                return jsonify({'status': 'error', 'message': 'Invalid role. Must be interviewer, proctor, or admin'}), 400
            field_names.append('role')
            values.append(data['role'])
        if 'password' in data and data['password']:
            if len(data['password']) < 8:
                return jsonify({'status': 'error', 'message': 'Password must be at least 8 characters'}), 400
            field_names.append('password_hash')
            values.append(hash_password(data['password']))

        if not field_names:
            return jsonify({'status': 'error', 'message': 'No fields to update'}), 400

        values.append(user_id)
        set_clause = psql.SQL(', ').join(
            [psql.SQL("{} = %s").format(psql.Identifier(f)) for f in field_names]
        )
        query = psql.SQL("UPDATE users SET {} WHERE id = %s").format(set_clause)
        cursor.execute(query, values)
        conn.commit()
        conn.close()

        logger.info(f"[ADMIN ACTION] {admin_email} successfully updated user ID: {user_id}")

        return jsonify({'status': 'success', 'message': 'User updated successfully'}), 200
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to update user ID {user_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


@admin_users_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@require_admin_role
def delete_user(user_id):
    try:
        admin_email = get_jwt_identity()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT email, role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            return jsonify({'status': 'error', 'message': 'User not found'}), 404

        user_email, user_role = user[0], user[1]
        logger.warning(f"[ADMIN ACTION] {admin_email} deleting user ID: {user_id} ({user_email}, role: {user_role})")

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        conn.close()

        logger.info(f"[ADMIN ACTION] {admin_email} successfully deleted user ID: {user_id}")

        return jsonify({'status': 'success', 'message': 'User deleted successfully'}), 200
    except Exception as e:
        logger.error(f"[ADMIN ERROR] Failed to delete user ID {user_id}: {str(e)}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
