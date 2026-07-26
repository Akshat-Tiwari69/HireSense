import { Button } from '../../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Input } from '../../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { TabsContent } from '../../ui/tabs';
import StatusBadge from '../../workspace/StatusBadge';
import { Briefcase, Edit, Loader2, RotateCcw, Search, Trash2, UserPlus } from 'lucide-react';

const scoreClassName = (score) => {
  if (score >= 75) return 'text-emerald-700';
  if (score >= 50) return 'text-amber-700';
  return 'text-slate-600';
};

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
    <Card>
      <CardHeader className="border-b">
        <CardTitle>Candidate directory</CardTitle>
        <CardDescription>Review applicant records, update progress, and run role matching.</CardDescription>
      </CardHeader>

      <CardContent className="pt-5">
        <div className="mb-5 grid gap-3 md:grid-cols-[minmax(0,1fr)_220px]">
          <div className="relative">
            <label htmlFor="candidate-search" className="sr-only">Search candidates</label>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="candidate-search"
              type="search"
              placeholder="Search by name or email"
              value={candidateSearch}
              onChange={(event) => setCandidateSearch(event.target.value)}
              className="pl-9"
            />
          </div>
          <div>
            <label htmlFor="candidate-status-filter" className="sr-only">Filter by candidate status</label>
            <Select value={candidateStatusFilter} onValueChange={setCandidateStatusFilter}>
              <SelectTrigger id="candidate-status-filter">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                {candidateStatuses.map((status) => (
                  <SelectItem key={status} value={status} className="capitalize">{status.replace(/_/g, ' ')}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {filteredCandidates.length === 0 ? (
          <div className="flex min-h-56 flex-col items-center justify-center rounded-lg border border-dashed px-6 text-center">
            <span className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-muted-foreground">
              <UserPlus className="h-5 w-5" />
            </span>
            <p className="font-medium text-foreground">No candidates found</p>
            <p className="mt-1 text-sm text-muted-foreground">Adjust the search or status filter to see more records.</p>
          </div>
        ) : (
          <Table className="min-w-[820px]" aria-label="Candidates">
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Match score</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCandidates.map((candidate) => {
                const matchScore = candidate.match_score || 0;
                const candidateName = candidate.name || 'Unnamed candidate';

                return (
                  <TableRow key={candidate.id}>
                    <TableCell className="font-medium text-foreground">{candidateName}</TableCell>
                    <TableCell className="text-muted-foreground">{candidate.email}</TableCell>
                    <TableCell>
                      <span className={`font-semibold tabular-nums ${scoreClassName(matchScore)}`}>
                        {matchScore}%
                      </span>
                    </TableCell>
                    <TableCell><StatusBadge status={candidate.status || 'applied'} /></TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-1.5">
                        <Button
                          type="button"
                          size="icon"
                          variant="outline"
                          onClick={() => openEditCandidate(candidate)}
                          aria-label={`Edit ${candidateName}`}
                          title="Edit candidate"
                        >
                          <Edit />
                        </Button>
                        <Button
                          type="button"
                          size="icon"
                          variant="ghost"
                          onClick={() => handleResetCandidateStatus(candidate.id)}
                          disabled={resettingStatus === candidate.id}
                          className="text-amber-700 hover:bg-amber-50 hover:text-amber-800"
                          aria-label={`Reset ${candidateName} to applied`}
                          title="Reset status to Applied"
                        >
                          {resettingStatus === candidate.id ? <Loader2 className="animate-spin" /> : <RotateCcw />}
                        </Button>
                        <Button
                          type="button"
                          size="icon"
                          variant="ghost"
                          onClick={() => handleMatchCandidate(candidate.id)}
                          disabled={matchingCandidate === candidate.id}
                          className="text-blue-700 hover:bg-blue-50 hover:text-blue-800"
                          aria-label={`Match ${candidateName} to open roles`}
                          title="Match to open roles"
                        >
                          {matchingCandidate === candidate.id ? <Loader2 className="animate-spin" /> : <Briefcase />}
                        </Button>
                        <Button
                          type="button"
                          size="icon"
                          variant="ghost"
                          onClick={() => handleDeleteCandidate(candidate.id)}
                          disabled={deletingCandidate === candidate.id}
                          className="text-red-600 hover:bg-red-50 hover:text-red-700"
                          aria-label={`Delete ${candidateName}`}
                          title="Delete candidate"
                        >
                          {deletingCandidate === candidate.id ? <Loader2 className="animate-spin" /> : <Trash2 />}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  </TabsContent>
);

export default CandidatesTab;
