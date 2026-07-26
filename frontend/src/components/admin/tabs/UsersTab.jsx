import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Input } from '../../ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { TabsContent } from '../../ui/tabs';
import { Edit, Loader2, Plus, Search, Trash2, Users } from 'lucide-react';

const roleClasses = {
  admin: 'border-blue-200 bg-blue-50 text-blue-700',
  interviewer: 'border-slate-200 bg-slate-50 text-slate-700',
  proctor: 'border-amber-200 bg-amber-50 text-amber-700',
  recruiter: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  sector_admin: 'border-cyan-200 bg-cyan-50 text-cyan-700',
  super_admin: 'border-blue-200 bg-blue-50 text-blue-700',
};

const UsersTab = ({
  filteredUsers,
  userSearch,
  setUserSearch,
  deletingUser,
  openEditUser,
  handleDeleteUser,
  setEditingUser,
  setUserForm,
  setUserModalOpen,
  currentUserRole,
}) => (
  <TabsContent value="users">
    <Card>
      <CardHeader className="gap-4 border-b sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <CardTitle>Staff access</CardTitle>
            <Badge variant="outline" className="border-slate-200 bg-slate-50 text-slate-600">
              {filteredUsers.length}
            </Badge>
          </div>
          <CardDescription>Create accounts and keep access aligned with each hiring role.</CardDescription>
        </div>
        <Button
          onClick={() => {
            setEditingUser(null);
            setUserForm({ name: '', email: '', password: '', role: 'interviewer', sector_id: '' });
            setUserModalOpen(true);
          }}
        >
          <Plus />
          Add staff member
        </Button>
      </CardHeader>

      <CardContent className="pt-5">
        <div className="relative mb-5 max-w-md">
          <label htmlFor="staff-search" className="sr-only">Search staff</label>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            id="staff-search"
            type="search"
            placeholder="Search by name or email"
            value={userSearch}
            onChange={(event) => setUserSearch(event.target.value)}
            className="pl-9"
          />
        </div>

        {filteredUsers.length === 0 ? (
          <div className="flex min-h-56 flex-col items-center justify-center rounded-lg border border-dashed px-6 text-center">
            <span className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-muted-foreground">
              <Users className="h-5 w-5" />
            </span>
            <p className="font-medium text-foreground">No staff accounts found</p>
            <p className="mt-1 text-sm text-muted-foreground">Try a different search or add a staff member.</p>
          </div>
        ) : (
          <Table className="min-w-[680px]" aria-label="Staff accounts">
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredUsers.map((staffMember) => (
                <TableRow key={staffMember.id}>
                  <TableCell className="font-medium text-foreground">{staffMember.name || 'Unnamed user'}</TableCell>
                  <TableCell className="text-muted-foreground">{staffMember.email}</TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={`capitalize ${roleClasses[staffMember.role] || roleClasses.interviewer}`}
                    >
                      {(staffMember.role || 'interviewer').replaceAll('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex justify-end gap-2">
                      <Button
                        type="button"
                        size="icon"
                        variant="outline"
                        onClick={() => openEditUser(staffMember)}
                        disabled={currentUserRole !== 'super_admin' && ['admin', 'super_admin'].includes(staffMember.role)}
                        aria-label={`Edit ${staffMember.name || 'staff member'}`}
                        title="Edit staff member"
                      >
                        <Edit />
                      </Button>
                      <Button
                        type="button"
                        size="icon"
                        variant="ghost"
                        onClick={() => handleDeleteUser(staffMember.id)}
                        disabled={
                          deletingUser === staffMember.id
                          || (currentUserRole !== 'super_admin' && ['admin', 'super_admin'].includes(staffMember.role))
                        }
                        className="text-red-600 hover:bg-red-50 hover:text-red-700"
                        aria-label={`Delete ${staffMember.name || 'staff member'}`}
                        title="Delete staff member"
                      >
                        {deletingUser === staffMember.id ? <Loader2 className="animate-spin" /> : <Trash2 />}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  </TabsContent>
);

export default UsersTab;
