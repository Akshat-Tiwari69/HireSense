import React from 'react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { Badge } from '../../ui/badge';
import { TabsContent } from '../../ui/tabs';
import { Users, Plus, Search, Edit, Trash2 } from 'lucide-react';

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
}) => (
  <TabsContent value="users">
    <Card className="bg-white border-none shadow-md hover:shadow-lg transition-all duration-300">
      <CardHeader className="flex flex-row items-center justify-between border-b border-slate-200 pb-4">
        <div>
          <CardTitle className="text-slate-900">User Management</CardTitle>
          <CardDescription className="text-slate-600">Manage system users and their roles</CardDescription>
        </div>
        <Button onClick={() => { setEditingUser(null); setUserForm({ name: '', email: '', password: '', role: 'interviewer' }); setUserModalOpen(true); }} className="bg-indigo-600 hover:bg-indigo-700 shadow-md">
          <Plus className="w-4 h-4 mr-2" />
          Add User
        </Button>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="mb-4 flex items-center gap-2 bg-slate-50 rounded-lg p-3">
          <Search className="w-4 h-4 text-slate-500" />
          <Input
            placeholder="Search users by name or email..."
            value={userSearch}
            onChange={(e) => setUserSearch(e.target.value)}
            className="bg-transparent border-0 focus:ring-0 text-slate-900 placeholder:text-slate-500"
          />
        </div>

        {filteredUsers.length === 0 ? (
          <div className="text-center py-12">
            <Users className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500">No users found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 bg-slate-50 hover:bg-slate-50">
                  <TableHead className="text-slate-700 font-semibold">Name</TableHead>
                  <TableHead className="text-slate-700 font-semibold">Email</TableHead>
                  <TableHead className="text-slate-700 font-semibold">Role</TableHead>
                  <TableHead className="text-slate-700 font-semibold">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.map((user) => (
                  <TableRow key={user.id} className="border-slate-100 hover:bg-slate-50 transition-colors">
                    <TableCell className="text-slate-900 font-medium">{user.name}</TableCell>
                    <TableCell className="text-slate-600">{user.email}</TableCell>
                    <TableCell>
                      <Badge className={`${
                        user.role === 'admin' ? 'bg-red-600' :
                          user.role === 'proctor' ? 'bg-purple-600' :
                            'bg-blue-600'
                      } text-white shadow-sm`}>
                        {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => openEditUser(user)}
                          className="border-slate-300 text-slate-700 hover:bg-slate-50"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleDeleteUser(user.id)}
                          disabled={deletingUser === user.id}
                          className="opacity-90 hover:opacity-100"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  </TabsContent>
);

export default UsersTab;
