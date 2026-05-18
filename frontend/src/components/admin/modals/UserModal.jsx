import React from 'react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../../ui/dialog';
import { Label } from '../../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';

const UserModal = ({
  userModalOpen,
  setUserModalOpen,
  editingUser,
  userForm,
  setUserForm,
  savingUser,
  handleSaveUser,
}) => (
  <Dialog open={userModalOpen} onOpenChange={setUserModalOpen}>
    <DialogContent className="bg-white border-slate-200 shadow-md">
      <DialogHeader>
        <DialogTitle className="text-slate-900">{editingUser ? 'Edit User' : 'Add New User'}</DialogTitle>
        <DialogDescription className="text-slate-600">
          {editingUser ? 'Update user details' : 'Create a new user account'}
        </DialogDescription>
      </DialogHeader>
      <div className="space-y-4 py-4">
        <div className="space-y-2">
          <Label className="text-slate-700">Name</Label>
          <Input
            value={userForm.name}
            onChange={(e) => setUserForm({ ...userForm, name: e.target.value })}
            className="bg-white border-slate-300 text-slate-900"
          />
        </div>
        <div className="space-y-2">
          <Label className="text-slate-700">Email</Label>
          <Input
            type="email"
            value={userForm.email}
            onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
            className="bg-white border-slate-300 text-slate-900"
          />
        </div>
        <div className="space-y-2">
          <Label className="text-slate-700">Password {editingUser && '(leave blank to keep current)'}</Label>
          <Input
            type="password"
            value={userForm.password}
            onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
            className="bg-white border-slate-300 text-slate-900"
          />
        </div>
        <div className="space-y-2">
          <Label className="text-slate-700">Role</Label>
          <Select value={userForm.role} onValueChange={(v) => setUserForm({ ...userForm, role: v })}>
            <SelectTrigger className="bg-white border-slate-300 text-slate-900">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-white border-slate-200 shadow-md">
              <SelectItem value="interviewer">Interviewer</SelectItem>
              <SelectItem value="proctor">Proctor</SelectItem>
              <SelectItem value="admin">Admin</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={() => setUserModalOpen(false)} className="border-slate-300 text-slate-700">
          Cancel
        </Button>
        <Button onClick={handleSaveUser} disabled={savingUser} className="bg-indigo-600 hover:bg-indigo-700">
          {editingUser ? 'Update' : 'Create'}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);

export default UserModal;
