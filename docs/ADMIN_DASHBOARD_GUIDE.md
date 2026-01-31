# Admin Dashboard Guide

Complete documentation for the Admin Dashboard and administrative features.

---

## Overview

The Admin Dashboard provides system administrators with tools to manage users, job descriptions, and system configuration. Only users with the `admin` role can access these features.

**Route:** `/admin`

**Required Role:** `admin`

---

## Features

### User Management

Admins can perform full CRUD operations on system users.

**Capabilities:**
- View all registered users
- Create new users (interviewers, admins, proctors)
- Update user information and roles
- Delete users
- Reset passwords

### Job Description Management

Manage job openings that candidates apply for.

**Capabilities:**
- Create job descriptions
- Update requirements and skills
- Set minimum/maximum experience
- Activate/deactivate job postings

### System Statistics

Overview of platform usage and metrics.

---

## API Endpoints

### User Management

#### Get All Users

```
GET /api/admin/users
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "email": "interviewer@company.com",
      "name": "Jane Doe",
      "role": "interviewer",
      "created_at": "2026-01-15T10:30:00"
    },
    {
      "id": 2,
      "email": "admin@company.com",
      "name": "Admin User",
      "role": "admin",
      "created_at": "2026-01-10T09:00:00"
    }
  ],
  "total": 2
}
```

#### Create User

```
POST /api/admin/users
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "email": "newuser@company.com",
  "password": "securePassword123",
  "name": "New User",
  "role": "interviewer"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "User created successfully",
  "data": {
    "user_id": 3,
    "email": "newuser@company.com",
    "role": "interviewer"
  }
}
```

**Validation:**
- Email must be unique
- Password minimum 8 characters
- Role must be: `interviewer`, `admin`, or `proctor`

#### Update User

```
PUT /api/admin/users/:id
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "name": "Updated Name",
  "role": "proctor"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "User updated successfully",
  "data": {
    "id": 3,
    "email": "newuser@company.com",
    "name": "Updated Name",
    "role": "proctor"
  }
}
```

#### Delete User

```
DELETE /api/admin/users/:id
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "status": "success",
  "message": "User deleted successfully"
}
```

**Note:** Admins cannot delete themselves.

---

### Job Description Management

#### Get All Job Descriptions

```
GET /api/admin/job-descriptions
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "title": "Senior Software Engineer",
      "description": "Looking for an experienced developer...",
      "requirements": "5+ years experience, strong Python skills",
      "skills": "Python, React, AWS",
      "experience_min": 5,
      "experience_max": 10,
      "is_active": true,
      "created_at": "2026-01-15T10:30:00"
    }
  ]
}
```

#### Create Job Description

```
POST /api/admin/job-descriptions
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "title": "Full Stack Developer",
  "description": "Join our team as a full stack developer...",
  "requirements": "3+ years experience with modern web technologies",
  "skills": "Python, React, Node.js, PostgreSQL",
  "experience_min": 3,
  "experience_max": 7
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Job description created successfully",
  "data": {
    "id": 2,
    "title": "Full Stack Developer"
  }
}
```

#### Update Job Description

```
PUT /api/admin/job-descriptions/:id
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "is_active": false
}
```

#### Delete Job Description

```
DELETE /api/admin/job-descriptions/:id
Authorization: Bearer <admin_token>
```

---

### System Statistics

```
GET /api/admin/stats
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "users": {
      "total": 10,
      "interviewers": 5,
      "admins": 2,
      "proctors": 3
    },
    "candidates": {
      "total": 150,
      "pending": 45,
      "under_review": 30,
      "hired": 25,
      "rejected": 50
    },
    "assessments": {
      "total": 100,
      "completed": 85,
      "in_progress": 10,
      "cancelled": 5
    },
    "emails_sent": 450,
    "average_match_score": 72.5
  }
}
```

---

## Frontend Implementation

### AdminDashboardPage.jsx

The admin dashboard page provides a complete interface for all administrative functions.

**Tabs:**
1. **Users** - User management table
2. **Job Descriptions** - Job listing management
3. **Statistics** - System metrics

### User Management UI

```jsx
// User table with actions
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Email</TableHead>
      <TableHead>Role</TableHead>
      <TableHead>Created</TableHead>
      <TableHead>Actions</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {users.map(user => (
      <TableRow key={user.id}>
        <TableCell>{user.name}</TableCell>
        <TableCell>{user.email}</TableCell>
        <TableCell>
          <Badge variant={getRoleVariant(user.role)}>
            {user.role}
          </Badge>
        </TableCell>
        <TableCell>{formatDate(user.created_at)}</TableCell>
        <TableCell className="space-x-2">
          <Button size="sm" onClick={() => openEditDialog(user)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button 
            size="sm" 
            variant="destructive"
            onClick={() => handleDelete(user.id)}
            disabled={user.id === currentUser.id}
          >
            <Trash className="h-4 w-4" />
          </Button>
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

### Create User Dialog

```jsx
<Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Create New User</DialogTitle>
    </DialogHeader>
    
    <div className="space-y-4">
      <div>
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          value={newUser.name}
          onChange={(e) => setNewUser({...newUser, name: e.target.value})}
        />
      </div>
      
      <div>
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          value={newUser.email}
          onChange={(e) => setNewUser({...newUser, email: e.target.value})}
        />
      </div>
      
      <div>
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          value={newUser.password}
          onChange={(e) => setNewUser({...newUser, password: e.target.value})}
        />
      </div>
      
      <div>
        <Label htmlFor="role">Role</Label>
        <Select 
          value={newUser.role}
          onValueChange={(v) => setNewUser({...newUser, role: v})}
        >
          <SelectTrigger>
            <SelectValue placeholder="Select role" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="interviewer">Interviewer</SelectItem>
            <SelectItem value="proctor">Proctor</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
    
    <DialogFooter>
      <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
        Cancel
      </Button>
      <Button onClick={handleCreateUser}>Create User</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### Statistics Dashboard

```jsx
<div className="grid grid-cols-4 gap-4">
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <Users className="h-5 w-5" />
        Total Users
      </CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-3xl font-bold">{stats.users.total}</p>
      <div className="flex gap-2 mt-2">
        <Badge>{stats.users.interviewers} Interviewers</Badge>
        <Badge>{stats.users.proctors} Proctors</Badge>
        <Badge>{stats.users.admins} Admins</Badge>
      </div>
    </CardContent>
  </Card>
  
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <FileText className="h-5 w-5" />
        Candidates
      </CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-3xl font-bold">{stats.candidates.total}</p>
      <Progress 
        value={(stats.candidates.hired / stats.candidates.total) * 100} 
        className="mt-2"
      />
      <p className="text-sm text-gray-500 mt-1">
        {stats.candidates.hired} hired
      </p>
    </CardContent>
  </Card>
  
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <ClipboardList className="h-5 w-5" />
        Assessments
      </CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-3xl font-bold">{stats.assessments.total}</p>
      <p className="text-sm text-gray-500">
        {stats.assessments.completed} completed
      </p>
    </CardContent>
  </Card>
  
  <Card>
    <CardHeader>
      <CardTitle className="flex items-center gap-2">
        <Mail className="h-5 w-5" />
        Emails Sent
      </CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-3xl font-bold">{stats.emails_sent}</p>
    </CardContent>
  </Card>
</div>
```

---

## Backend Implementation

### admin_routes.py

```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from db_helpers import (
    get_all_users, create_user, update_user, delete_user,
    get_all_job_descriptions, create_job_description,
    update_job_description, delete_job_description
)
import bcrypt

admin_bp = Blueprint('admin', __name__)

def admin_required():
    """Decorator to require admin role"""
    def wrapper(fn):
        @jwt_required()
        def decorated(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({
                    'status': 'error',
                    'message': 'Admin access required'
                }), 403
            return fn(*args, **kwargs)
        decorated.__name__ = fn.__name__
        return decorated
    return wrapper

@admin_bp.route('/users', methods=['GET'])
@admin_required()
def list_users():
    """Get all users"""
    users = get_all_users()
    return jsonify({
        'status': 'success',
        'data': users,
        'total': len(users)
    })

@admin_bp.route('/users', methods=['POST'])
@admin_required()
def create_new_user():
    """Create a new user"""
    data = request.json
    
    # Validate
    required = ['email', 'password', 'name', 'role']
    for field in required:
        if not data.get(field):
            return jsonify({
                'status': 'error',
                'message': f'{field} is required'
            }), 400
    
    if data['role'] not in ['interviewer', 'admin', 'proctor']:
        return jsonify({
            'status': 'error',
            'message': 'Invalid role'
        }), 400
    
    # Hash password
    password_hash = bcrypt.hashpw(
        data['password'].encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    
    try:
        user_id = create_user(
            email=data['email'],
            password_hash=password_hash,
            role=data['role'],
            name=data['name']
        )
        
        return jsonify({
            'status': 'success',
            'message': 'User created successfully',
            'data': {'user_id': user_id}
        }), 201
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required()
def update_existing_user(user_id):
    """Update a user"""
    data = request.json
    current_user_id = get_jwt_identity()
    
    # Prevent role change for self
    if user_id == current_user_id and 'role' in data:
        return jsonify({
            'status': 'error',
            'message': 'Cannot change your own role'
        }), 400
    
    update_user(user_id, data)
    return jsonify({
        'status': 'success',
        'message': 'User updated successfully'
    })

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required()
def delete_existing_user(user_id):
    """Delete a user"""
    current_user_id = get_jwt_identity()
    
    if user_id == current_user_id:
        return jsonify({
            'status': 'error',
            'message': 'Cannot delete yourself'
        }), 400
    
    delete_user(user_id)
    return jsonify({
        'status': 'success',
        'message': 'User deleted successfully'
    })
```

---

## Security Considerations

### Role Verification

All admin endpoints verify the admin role via JWT claims:

```python
claims = get_jwt()
if claims.get('role') != 'admin':
    return jsonify({'status': 'error', 'message': 'Access denied'}), 403
```

### Self-Protection

Admins cannot:
- Delete their own account
- Change their own role
- This prevents accidental lockout

### Password Security

- Passwords hashed with bcrypt
- Minimum 8 characters enforced
- Salt automatically generated

### Audit Trail

All admin actions should be logged:
- User creation/modification/deletion
- Job description changes
- Include timestamp and admin user ID

---

## Best Practices

### User Management

1. **Create users with appropriate roles**
   - Interviewers: For recruiters who evaluate candidates
   - Proctors: For monitoring assessments
   - Admins: Sparingly, only for system administrators

2. **Regular access review**
   - Periodically review user list
   - Remove inactive accounts
   - Update roles as needed

### Job Descriptions

1. **Keep descriptions up-to-date**
   - Update requirements as needs change
   - Deactivate filled positions

2. **Clear skill requirements**
   - List specific technologies
   - Include experience ranges

---

## Troubleshooting

### "Admin access required"

- User role is not `admin`
- Check JWT token contains correct role claim
- Verify user's role in database

### Cannot delete user

- You cannot delete yourself
- Check if user exists
- Verify you have admin privileges

### User creation fails

- Email may already exist
- Password too short (min 8 chars)
- Invalid role specified

---

## Related Documentation

- [AUTH_GUIDE.md](AUTH_GUIDE.md) - Authentication system
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - User table schema
- [API_DOCS.md](API_DOCS.md) - Complete API reference

---

*Last Updated: January 2026*
*Version: 1.0*
