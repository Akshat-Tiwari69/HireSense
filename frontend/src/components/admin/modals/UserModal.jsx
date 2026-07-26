import { Button } from '../../ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../../ui/dialog';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Loader2 } from 'lucide-react';

const UserModal = ({
  userModalOpen,
  setUserModalOpen,
  editingUser,
  userForm,
  setUserForm,
  savingUser,
  handleSaveUser,
  sectors = [],
  currentUserRole,
}) => (
  <Dialog open={userModalOpen} onOpenChange={setUserModalOpen}>
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{editingUser ? 'Edit staff account' : 'Add staff account'}</DialogTitle>
        <DialogDescription>
          {editingUser ? 'Update profile details and access level.' : 'Create credentials for a hiring team member.'}
        </DialogDescription>
      </DialogHeader>

      <form
        className="space-y-5"
        onSubmit={(event) => {
          event.preventDefault();
          handleSaveUser();
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="staff-name">Name</Label>
          <Input
            id="staff-name"
            autoComplete="name"
            value={userForm.name}
            onChange={(event) => setUserForm({ ...userForm, name: event.target.value })}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="staff-email">Email</Label>
          <Input
            id="staff-email"
            type="email"
            autoComplete="email"
            value={userForm.email}
            onChange={(event) => setUserForm({ ...userForm, email: event.target.value })}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="staff-password">
            Password {editingUser ? <span className="font-normal text-muted-foreground">(leave blank to keep current)</span> : null}
          </Label>
          <Input
            id="staff-password"
            type="password"
            autoComplete="new-password"
            value={userForm.password}
            onChange={(event) => setUserForm({ ...userForm, password: event.target.value })}
            required={!editingUser}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="staff-role">Role</Label>
          <Select
            value={userForm.role}
            onValueChange={(role) => setUserForm({
              ...userForm,
              role,
              sector_id: ['recruiter', 'sector_admin'].includes(role) ? userForm.sector_id : '',
            })}
          >
            <SelectTrigger id="staff-role">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="interviewer">Interviewer</SelectItem>
              <SelectItem value="proctor">Proctor</SelectItem>
              <SelectItem value="recruiter">Recruiter</SelectItem>
              <SelectItem value="sector_admin">Sector administrator</SelectItem>
              {currentUserRole === 'super_admin' ? (
                <>
                  <SelectItem value="admin">Administrator</SelectItem>
                  <SelectItem value="super_admin">Super administrator</SelectItem>
                </>
              ) : null}
            </SelectContent>
          </Select>
        </div>

        {['recruiter', 'sector_admin'].includes(userForm.role) ? (
          <div className="space-y-2">
            <Label htmlFor="staff-sector">Sector</Label>
            <Select
              value={String(userForm.sector_id || '')}
              onValueChange={(sector_id) => setUserForm({ ...userForm, sector_id })}
              required
            >
              <SelectTrigger id="staff-sector" aria-required="true">
                <SelectValue placeholder="Select a sector" />
              </SelectTrigger>
              <SelectContent>
                {sectors.map((sector) => (
                  <SelectItem key={sector.id} value={String(sector.id)}>{sector.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">A sector assignment is required for this role.</p>
          </div>
        ) : null}

        <DialogFooter className="border-t pt-5">
          <Button type="button" variant="outline" onClick={() => setUserModalOpen(false)}>Cancel</Button>
          <Button type="submit" disabled={savingUser}>
            {savingUser ? <Loader2 className="animate-spin" /> : null}
            {savingUser ? 'Saving' : editingUser ? 'Save changes' : 'Create account'}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
);

export default UserModal;
