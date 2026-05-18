import React from 'react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { Badge } from '../../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { TabsContent } from '../../ui/tabs';
import { UserPlus, Search, Edit, RotateCcw, Briefcase, Trash2, Loader2 } from 'lucide-react';

const CandidatesTab = ({
  filteredCandidates,
  candidateSearch,
  setCandidateSearch,
  candidateStatusFilter,
  setCandidateStatusFilter,
  candidateStatuses,
  deletingCandidate,
  resettingStatus,
  matchingCandidate,
  openEditCandidate,
  handleResetCandidateStatus,
  handleMatchCandidate,
  handleDeleteCandidate,
}) => (
  <TabsContent value="candidates">
    <Card className="bg-white border-none shadow-md hover:shadow-lg transition-all duration-300">
      <CardHeader className="flex flex-row items-center justify-between border-b border-slate-200 pb-4">
        <div>
          <CardTitle className="text-slate-900">Candidate Management</CardTitle>
          <CardDescription className="text-slate-600">View, edit, or manage candidate applications</CardDescription>
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
          <div className="col-span-2 flex items-center gap-2 bg-slate-50 rounded-lg p-3">
            <Search className="w-4 h-4 text-slate-500" />
            <Input
              placeholder="Search candidates..."
              value={candidateSearch}
              onChange={(e) => setCandidateSearch(e.target.value)}
              className="bg-transparent border-0 focus:ring-0 text-slate-900 placeholder:text-slate-500"
            />
          </div>
          <Select value={candidateStatusFilter} onValueChange={setCandidateStatusFilter}>
            <SelectTrigger className="bg-slate-50 border-slate-200">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              {candidateStatuses.map(status => (
                <SelectItem key={status} value={status}>{status}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {filteredCandidates.length === 0 ? (
          <div className="text-center py-12">
            <UserPlus className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-slate-500">No candidates found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-slate-200 bg-slate-50 hover:bg-slate-50">
                  <TableHead className="text-slate-700 font-semibold">Name</TableHead>
                  <TableHead className="text-slate-700 font-semibold">Email</TableHead>
                  <TableHead className="text-slate-700 font-semibold">Score</TableHead>
                  <TableHead className="text-slate-700 font-semibold">Status</TableHead>
                  <TableHead className="text-slate-700 font-semibold">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCandidates.map((candidate) => (
                  <TableRow key={candidate.id} className="border-slate-100 hover:bg-slate-50 transition-colors">
                    <TableCell className="text-slate-900 font-medium">{candidate.name}</TableCell>
                    <TableCell className="text-slate-600">{candidate.email}</TableCell>
                    <TableCell>
                      <span className={`font-semibold ${
                        (candidate.match_score || 0) >= 75 ? 'text-green-600' :
                        (candidate.match_score || 0) >= 50 ? 'text-amber-600' :
                        'text-slate-600'
                      }`}>
                        {candidate.match_score || 0}%
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge className={`${
                        candidate.status === 'Applied' ? 'bg-blue-600' :
                          candidate.status === 'Scheduled' ? 'bg-purple-600' :
                            candidate.status === 'Completed' ? 'bg-green-600' :
                              candidate.status === 'Rejected' ? 'bg-red-600' : 'bg-slate-600'
                      } text-white shadow-sm`}>
                        {(candidate.status || 'Applied').charAt(0).toUpperCase() + (candidate.status || 'Applied').slice(1)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => openEditCandidate(candidate)}
                          className="border-slate-300 text-slate-700 hover:bg-slate-50"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleResetCandidateStatus(candidate.id)}
                          disabled={resettingStatus === candidate.id}
                          className="border-amber-600 text-amber-600 hover:bg-amber-50"
                        >
                          <RotateCcw className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleMatchCandidate(candidate.id)}
                          disabled={matchingCandidate === candidate.id}
                          className="border-indigo-600 text-indigo-600 hover:bg-indigo-50"
                          title="AI Match to Jobs"
                        >
                          {matchingCandidate === candidate.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Briefcase className="w-4 h-4" />}
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleDeleteCandidate(candidate.id)}
                          disabled={deletingCandidate === candidate.id}
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

export default CandidatesTab;
