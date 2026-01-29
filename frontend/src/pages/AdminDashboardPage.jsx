import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  LogOut, Users, Database, Settings, Trash2, Edit, Plus, RefreshCw, 
  Shield, UserPlus, BarChart3, Table as TableIcon, Eye, RotateCcw
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import Logo from '../components/Logo';
import { api } from '../services/api';

const AdminDashboardPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  // State
  const [users, setUsers] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [dbStats, setDbStats] = useState(null);
  const [dbTables, setDbTables] = useState([]);
  const [envStatus, setEnvStatus] = useState({});
  const [selectedTable, setSelectedTable] = useState(null);
  const [tableData, setTableData] = useState({ data: [], columns: [] });
  const [loading, setLoading] = useState(true);
  
  // Modals
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({ name: '', email: '', password: '', role: 'interviewer' });
  
  const [candidateModalOpen, setCandidateModalOpen] = useState(false);
  const [editingCandidate, setEditingCandidate] = useState(null);
  const [candidateForm, setCandidateForm] = useState({ name: '', email: '', phone: '', status: 'Applied', match_score: 0 });

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      navigate('/login');
      return;
    }
    fetchAllData();
  }, [navigate]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [usersRes, candidatesRes, statsRes, tablesRes, envRes] = await Promise.all([
        api.get('/api/admin/users'),
        api.get('/api/admin/candidates'),
        api.get('/api/admin/db/stats'),
        api.get('/api/admin/db/tables'),
        api.get('/api/admin/settings/env')
      ]);
      
      setUsers(usersRes.data.data || []);
      setCandidates(candidatesRes.data.data || []);
      setDbStats(statsRes.data.data || {});
      setDbTables(tablesRes.data.data || []);
      setEnvStatus(envRes.data.data || {});
    } catch (err) {
      const message = err?.response?.data?.message || 'Failed to load admin data';
      if (err?.response?.status === 403) {
        toast({ variant: 'destructive', title: 'Access Denied', description: 'Admin role required' });
        navigate('/dashboard');
      } else {
        toast({ variant: 'destructive', title: 'Error', description: message });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    navigate('/login');
  };

  // User Management
  const handleSaveUser = async () => {
    try {
      if (editingUser) {
        await api.put(`/api/admin/users/${editingUser.id}`, userForm);
        toast({ title: 'Success', description: 'User updated successfully' });
      } else {
        await api.post('/api/admin/users', userForm);
        toast({ title: 'Success', description: 'User created successfully' });
      }
      setUserModalOpen(false);
      setEditingUser(null);
      setUserForm({ name: '', email: '', password: '', role: 'interviewer' });
      fetchAllData();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to save user' });
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      await api.delete(`/api/admin/users/${userId}`);
      toast({ title: 'Success', description: 'User deleted successfully' });
      fetchAllData();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to delete user' });
    }
  };

  const openEditUser = (user) => {
    setEditingUser(user);
    setUserForm({ name: user.name, email: user.email, password: '', role: user.role });
    setUserModalOpen(true);
  };

  // Candidate Management
  const handleSaveCandidate = async () => {
    try {
      await api.put(`/api/admin/candidates/${editingCandidate.id}`, candidateForm);
      toast({ title: 'Success', description: 'Candidate updated successfully' });
      setCandidateModalOpen(false);
      setEditingCandidate(null);
      fetchAllData();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to save candidate' });
    }
  };

  const handleDeleteCandidate = async (candidateId) => {
    if (!confirm('Are you sure you want to delete this candidate? This will also delete all their assessments.')) return;
    try {
      await api.delete(`/api/admin/candidates/${candidateId}`);
      toast({ title: 'Success', description: 'Candidate deleted successfully' });
      fetchAllData();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to delete candidate' });
    }
  };

  const handleResetCandidateStatus = async (candidateId) => {
    if (!confirm('Reset this candidate status to Applied?')) return;
    try {
      await api.post(`/api/admin/reset-candidate-status/${candidateId}`);
      toast({ title: 'Success', description: 'Candidate status reset to Applied' });
      fetchAllData();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to reset status' });
    }
  };

  const openEditCandidate = (candidate) => {
    setEditingCandidate(candidate);
    setCandidateForm({ 
      name: candidate.name, 
      email: candidate.email, 
      phone: candidate.phone || '',
      status: candidate.status || 'Applied',
      match_score: candidate.match_score || 0
    });
    setCandidateModalOpen(true);
  };

  // Database
  const fetchTableData = async (tableName) => {
    try {
      setSelectedTable(tableName);
      const res = await api.get(`/api/admin/db/tables/${tableName}`);
      setTableData({ data: res.data.data || [], columns: res.data.columns || [] });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load table data' });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
        <div className="text-white text-xl">Loading admin panel...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Logo size="default" />
            <Badge className="bg-red-600 text-white border-red-500">ADMIN</Badge>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={fetchAllData} className="border-slate-600 text-slate-300 hover:bg-slate-800">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button variant="ghost" onClick={handleLogout} className="text-slate-300 hover:text-red-400">
              <LogOut className="mr-2 w-4 h-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Total Users</p>
                  <p className="text-3xl font-bold text-white">{dbStats?.total_users || 0}</p>
                </div>
                <Users className="w-10 h-10 text-blue-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Total Candidates</p>
                  <p className="text-3xl font-bold text-white">{dbStats?.total_candidates || 0}</p>
                </div>
                <UserPlus className="w-10 h-10 text-green-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Assessments</p>
                  <p className="text-3xl font-bold text-white">{dbStats?.total_assessments || 0}</p>
                </div>
                <BarChart3 className="w-10 h-10 text-purple-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">DB Tables</p>
                  <p className="text-3xl font-bold text-white">{dbTables.length}</p>
                </div>
                <Database className="w-10 h-10 text-amber-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Tabs */}
        <Tabs defaultValue="users" className="space-y-6">
          <TabsList className="bg-slate-800 border-slate-700">
            <TabsTrigger value="users" className="data-[state=active]:bg-slate-700">
              <Users className="w-4 h-4 mr-2" />
              Users
            </TabsTrigger>
            <TabsTrigger value="candidates" className="data-[state=active]:bg-slate-700">
              <UserPlus className="w-4 h-4 mr-2" />
              Candidates
            </TabsTrigger>
            <TabsTrigger value="database" className="data-[state=active]:bg-slate-700">
              <Database className="w-4 h-4 mr-2" />
              Database
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-slate-700">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </TabsTrigger>
          </TabsList>

          {/* Users Tab */}
          <TabsContent value="users">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-white">User Management</CardTitle>
                  <CardDescription className="text-slate-400">Add, edit, or remove users</CardDescription>
                </div>
                <Button onClick={() => { setEditingUser(null); setUserForm({ name: '', email: '', password: '', role: 'interviewer' }); setUserModalOpen(true); }} className="bg-indigo-600 hover:bg-indigo-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Add User
                </Button>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-700">
                      <TableHead className="text-slate-300">ID</TableHead>
                      <TableHead className="text-slate-300">Name</TableHead>
                      <TableHead className="text-slate-300">Email</TableHead>
                      <TableHead className="text-slate-300">Role</TableHead>
                      <TableHead className="text-slate-300">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((user) => (
                      <TableRow key={user.id} className="border-slate-700">
                        <TableCell className="text-slate-300">{user.id}</TableCell>
                        <TableCell className="text-white font-medium">{user.name}</TableCell>
                        <TableCell className="text-slate-300">{user.email}</TableCell>
                        <TableCell>
                        <Badge className={
                          user.role === 'admin' ? 'bg-red-600' : 
                          user.role === 'proctor' ? 'bg-purple-600' : 
                          'bg-blue-600'
                        }>
                            {user.role}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button size="sm" variant="outline" onClick={() => openEditUser(user)} className="border-slate-600 text-slate-300 hover:bg-slate-700">
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant="destructive" onClick={() => handleDeleteUser(user.id)}>
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Candidates Tab */}
          <TabsContent value="candidates">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Candidate Management</CardTitle>
                <CardDescription className="text-slate-400">View, edit, or delete candidates</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-700">
                      <TableHead className="text-slate-300">ID</TableHead>
                      <TableHead className="text-slate-300">Name</TableHead>
                      <TableHead className="text-slate-300">Email</TableHead>
                      <TableHead className="text-slate-300">Score</TableHead>
                      <TableHead className="text-slate-300">Status</TableHead>
                      <TableHead className="text-slate-300">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {candidates.map((candidate) => (
                      <TableRow key={candidate.id} className="border-slate-700">
                        <TableCell className="text-slate-300">{candidate.id}</TableCell>
                        <TableCell className="text-white font-medium">{candidate.name}</TableCell>
                        <TableCell className="text-slate-300">{candidate.email}</TableCell>
                        <TableCell className="text-slate-300">{candidate.match_score || 0}%</TableCell>
                        <TableCell>
                          <Badge className={
                            candidate.status === 'Applied' ? 'bg-blue-600' :
                            candidate.status === 'Scheduled' ? 'bg-purple-600' :
                            candidate.status === 'Completed' ? 'bg-green-600' :
                            candidate.status === 'Rejected' ? 'bg-red-600' : 'bg-slate-600'
                          }>
                            {candidate.status || 'Applied'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex gap-2">
                            <Button size="sm" variant="outline" onClick={() => openEditCandidate(candidate)} className="border-slate-600 text-slate-300 hover:bg-slate-700">
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => handleResetCandidateStatus(candidate.id)} className="border-amber-600 text-amber-400 hover:bg-amber-900/50">
                              <RotateCcw className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant="destructive" onClick={() => handleDeleteCandidate(candidate.id)}>
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Database Tab */}
          <TabsContent value="database">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white text-lg">Tables</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {dbTables.map((table) => (
                    <Button
                      key={table}
                      variant={selectedTable === table ? 'default' : 'outline'}
                      className={`w-full justify-start ${selectedTable === table ? 'bg-indigo-600' : 'border-slate-600 text-slate-300 hover:bg-slate-700'}`}
                      onClick={() => fetchTableData(table)}
                    >
                      <TableIcon className="w-4 h-4 mr-2" />
                      {table}
                    </Button>
                  ))}
                </CardContent>
              </Card>
              
              <Card className="bg-slate-800/50 border-slate-700 lg:col-span-3">
                <CardHeader>
                  <CardTitle className="text-white">
                    {selectedTable ? `Table: ${selectedTable}` : 'Select a table'}
                  </CardTitle>
                  <CardDescription className="text-slate-400">
                    {selectedTable ? `Showing ${tableData.data.length} rows` : 'Click a table to view its data'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {selectedTable && tableData.columns.length > 0 ? (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow className="border-slate-700">
                            {tableData.columns.map((col) => (
                              <TableHead key={col} className="text-slate-300 whitespace-nowrap">{col}</TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {tableData.data.map((row, idx) => (
                            <TableRow key={idx} className="border-slate-700">
                              {tableData.columns.map((col) => (
                                <TableCell key={col} className="text-slate-300 max-w-xs truncate">
                                  {row[col] !== null ? String(row[col]).substring(0, 50) : 'NULL'}
                                  {String(row[col] || '').length > 50 && '...'}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <p className="text-slate-400 text-center py-8">Select a table from the left to view its data</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Environment Variables</CardTitle>
                <CardDescription className="text-slate-400">Status of configured environment variables</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(envStatus).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between p-4 bg-slate-900/50 rounded-lg">
                      <span className="text-slate-300 font-mono text-sm">{key}</span>
                      {value ? (
                        <Badge className="bg-green-600">
                          <Shield className="w-3 h-3 mr-1" />
                          {value}
                        </Badge>
                      ) : (
                        <Badge className="bg-red-600">Not Set</Badge>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* User Modal */}
      <Dialog open={userModalOpen} onOpenChange={setUserModalOpen}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">{editingUser ? 'Edit User' : 'Add New User'}</DialogTitle>
            <DialogDescription className="text-slate-400">
              {editingUser ? 'Update user details' : 'Create a new user account'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-slate-300">Name</Label>
              <Input 
                value={userForm.name} 
                onChange={(e) => setUserForm({...userForm, name: e.target.value})}
                className="bg-slate-900 border-slate-600 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Email</Label>
              <Input 
                type="email"
                value={userForm.email} 
                onChange={(e) => setUserForm({...userForm, email: e.target.value})}
                className="bg-slate-900 border-slate-600 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Password {editingUser && '(leave blank to keep current)'}</Label>
              <Input 
                type="password"
                value={userForm.password} 
                onChange={(e) => setUserForm({...userForm, password: e.target.value})}
                className="bg-slate-900 border-slate-600 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Role</Label>
              <Select value={userForm.role} onValueChange={(v) => setUserForm({...userForm, role: v})}>
                <SelectTrigger className="bg-slate-900 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  <SelectItem value="interviewer">Interviewer</SelectItem>
                  <SelectItem value="proctor">Proctor</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setUserModalOpen(false)} className="border-slate-600 text-slate-300">
              Cancel
            </Button>
            <Button onClick={handleSaveUser} className="bg-indigo-600 hover:bg-indigo-700">
              {editingUser ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Candidate Modal */}
      <Dialog open={candidateModalOpen} onOpenChange={setCandidateModalOpen}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">Edit Candidate</DialogTitle>
            <DialogDescription className="text-slate-400">Update candidate details</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-slate-300">Name</Label>
              <Input 
                value={candidateForm.name} 
                onChange={(e) => setCandidateForm({...candidateForm, name: e.target.value})}
                className="bg-slate-900 border-slate-600 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Email</Label>
              <Input 
                type="email"
                value={candidateForm.email} 
                onChange={(e) => setCandidateForm({...candidateForm, email: e.target.value})}
                className="bg-slate-900 border-slate-600 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Phone</Label>
              <Input 
                value={candidateForm.phone} 
                onChange={(e) => setCandidateForm({...candidateForm, phone: e.target.value})}
                className="bg-slate-900 border-slate-600 text-white"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Status</Label>
              <Select value={candidateForm.status} onValueChange={(v) => setCandidateForm({...candidateForm, status: v})}>
                <SelectTrigger className="bg-slate-900 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  <SelectItem value="Applied">Applied</SelectItem>
                  <SelectItem value="Scheduled">Scheduled</SelectItem>
                  <SelectItem value="Completed">Completed</SelectItem>
                  <SelectItem value="Rejected">Rejected</SelectItem>
                  <SelectItem value="Hired">Hired</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-slate-300">Match Score (%)</Label>
              <Input 
                type="number"
                min="0"
                max="100"
                value={candidateForm.match_score} 
                onChange={(e) => setCandidateForm({...candidateForm, match_score: parseInt(e.target.value) || 0})}
                className="bg-slate-900 border-slate-600 text-white"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCandidateModalOpen(false)} className="border-slate-600 text-slate-300">
              Cancel
            </Button>
            <Button onClick={handleSaveCandidate} className="bg-indigo-600 hover:bg-indigo-700">
              Update
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminDashboardPage;
