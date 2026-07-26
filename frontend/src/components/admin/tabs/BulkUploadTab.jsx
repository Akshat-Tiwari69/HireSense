import { useRef } from 'react';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Label } from '../../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { TabsContent } from '../../ui/tabs';
import { AlertTriangle, CheckCircle2, FileArchive, Loader2, Upload, X, XCircle } from 'lucide-react';
import { api } from '../../../services/api';
import { useToast } from '../../../hooks/use-toast';

const summaryItems = (results) => [
  { label: 'Total resumes', value: results.summary.total, className: 'text-slate-900' },
  { label: 'Added', value: results.summary.success, className: 'text-emerald-700' },
  {
    label: 'Needs details',
    value: results.results?.filter((result) => result.missing?.length > 0 && result.status === 'success').length || 0,
    className: 'text-amber-700',
  },
  { label: 'Duplicates', value: results.summary.duplicates, className: 'text-amber-700' },
  { label: 'Failed', value: results.summary.errors, className: 'text-red-700' },
];

const ResultStatus = ({ result }) => {
  if (result.status === 'success' && result.missing?.length > 0) {
    return <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-700"><AlertTriangle /> Needs details</Badge>;
  }
  if (result.status === 'success') {
    return <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700"><CheckCircle2 /> Added</Badge>;
  }
  if (result.status === 'duplicate') {
    return <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-700"><AlertTriangle /> Duplicate</Badge>;
  }
  return <Badge variant="outline" className="border-red-200 bg-red-50 text-red-700"><XCircle /> Failed</Badge>;
};

const BulkUploadTab = ({
  jobPostings,
  bulkFile,
  setBulkFile,
  bulkJobId,
  setBulkJobId,
  bulkUploading,
  setBulkUploading,
  bulkProgress,
  setBulkProgress,
  bulkResults,
  setBulkResults,
}) => {
  const { toast } = useToast();
  const fileInputRef = useRef(null);

  const selectArchive = (file) => {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.zip')) {
      toast({ title: 'Invalid file', description: 'Choose a ZIP archive containing PDF or DOCX resumes.', variant: 'destructive' });
      return;
    }
    setBulkFile(file);
    setBulkResults(null);
  };

  const uploadArchive = async () => {
    setBulkUploading(true);
    setBulkResults(null);
    setBulkProgress('Uploading the archive and processing resumes.');
    try {
      const formData = new FormData();
      formData.append('file', bulkFile);
      formData.append('job_id', bulkJobId);
      const response = await api.post('/api/admin/bulk-upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 600000,
      });
      setBulkResults(response.data);
      setBulkProgress(null);
      toast({ title: 'Resume import complete', description: response.data.message, duration: 5000 });
    } catch (error) {
      const message = error.response?.data?.message || error.message;
      setBulkProgress(null);
      toast({ title: 'Resume import failed', description: message, variant: 'destructive' });
    } finally {
      setBulkUploading(false);
    }
  };

  return (
    <TabsContent value="bulk-upload">
      <Card>
        <CardHeader className="border-b">
          <div className="flex items-start gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
              <FileArchive className="h-4 w-4" />
            </span>
            <div className="space-y-1.5">
              <CardTitle>Resume import</CardTitle>
              <CardDescription>
                Upload one ZIP archive of PDF or DOCX resumes and score every candidate against a selected role.
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6 pt-6">
          <div className="grid gap-5 lg:grid-cols-2">
            <section className="rounded-xl border p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-blue-700">Step 1</p>
              <Label htmlFor="bulk-role" className="mt-2 block text-base">Select the target role</Label>
              <p className="mb-4 mt-1 text-sm text-muted-foreground">All resumes in the archive are scored against this role.</p>
              <Select value={bulkJobId} onValueChange={setBulkJobId}>
                <SelectTrigger id="bulk-role">
                  <SelectValue placeholder="Choose an active role" />
                </SelectTrigger>
                <SelectContent position="popper">
                  {jobPostings.filter((job) => job.status === 'active').map((job) => (
                    <SelectItem key={job.id} value={String(job.id)}>
                      {job.title} — {job.department || 'General'}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </section>

            <section
              className="rounded-xl border border-dashed p-5"
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault();
                selectArchive(event.dataTransfer.files[0]);
              }}
            >
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-blue-700">Step 2</p>
              <Label className="mt-2 block text-base">Choose a resume archive</Label>
              <p className="mb-4 mt-1 text-sm text-muted-foreground">ZIP only; the archive may contain PDF and DOCX files.</p>
              <input
                ref={fileInputRef}
                id="bulk-zip-input"
                type="file"
                accept=".zip,application/zip"
                className="sr-only"
                onChange={(event) => selectArchive(event.target.files[0])}
              />
              {bulkFile ? (
                <div className="flex flex-col gap-3 rounded-lg border bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="truncate font-medium text-foreground">{bulkFile.name}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{(bulkFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => {
                      setBulkFile(null);
                      setBulkResults(null);
                      if (fileInputRef.current) fileInputRef.current.value = '';
                    }}
                  >
                    <X />
                    Remove
                  </Button>
                </div>
              ) : (
                <Button type="button" variant="outline" onClick={() => fileInputRef.current?.click()}>
                  <Upload />
                  Choose ZIP archive
                </Button>
              )}
            </section>
          </div>

          <div className="flex flex-col gap-3 border-t pt-5 sm:flex-row sm:items-center sm:justify-between">
            <p className="max-w-xl text-sm text-muted-foreground">Large batches can take several minutes to extract, parse, and score.</p>
            <Button type="button" disabled={!bulkFile || !bulkJobId || bulkUploading} onClick={uploadArchive}>
              {bulkUploading ? <Loader2 className="animate-spin" /> : <Upload />}
              {bulkUploading ? 'Processing resumes' : 'Upload and process'}
            </Button>
          </div>

          {bulkUploading && bulkProgress ? (
            <div className="flex items-start gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4 text-blue-800" role="status" aria-live="polite">
              <Loader2 className="mt-0.5 h-5 w-5 shrink-0 animate-spin" />
              <div>
                <p className="font-medium">{bulkProgress}</p>
                <p className="mt-1 text-sm text-blue-700">Keep this page open until processing completes.</p>
              </div>
            </div>
          ) : null}

          {bulkResults?.summary ? (
            <section className="space-y-5" aria-live="polite">
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
                {summaryItems(bulkResults).map((item) => (
                  <div key={item.label} className="rounded-lg border bg-card p-4">
                    <p className={`text-2xl font-semibold tabular-nums ${item.className}`}>{item.value || 0}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{item.label}</p>
                  </div>
                ))}
              </div>

              <p className="text-sm text-muted-foreground">
                Role: <span className="font-medium text-foreground">{bulkResults.summary.job?.title || 'Unknown role'}</span>
                {bulkResults.summary.job?.department ? ` · ${bulkResults.summary.job.department}` : ''}
              </p>

              {bulkResults.results?.length > 0 ? (
                <Table className="min-w-[980px]" aria-label="Resume import results">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Status</TableHead>
                      <TableHead>File</TableHead>
                      <TableHead>Candidate</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Match score</TableHead>
                      <TableHead>Recommendation</TableHead>
                      <TableHead>Details</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {bulkResults.results.map((result, index) => (
                      <TableRow key={`${result.filename || 'resume'}-${index}`}>
                        <TableCell><ResultStatus result={result} /></TableCell>
                        <TableCell className="max-w-[180px] truncate text-sm" title={result.filename}>{result.filename}</TableCell>
                        <TableCell className="font-medium text-foreground">{result.name || '—'}</TableCell>
                        <TableCell className="text-muted-foreground">{result.email || '—'}</TableCell>
                        <TableCell>
                          {result.match_score > 0 ? (
                            <span className="font-semibold tabular-nums text-foreground">{result.match_score}%</span>
                          ) : '—'}
                        </TableCell>
                        <TableCell className="text-muted-foreground">{result.recommendation || '—'}</TableCell>
                        <TableCell className="max-w-[260px] text-xs text-muted-foreground">
                          <span className="block truncate" title={result.error || ''}>
                            {result.missing?.length > 0 ? `Missing: ${result.missing.join(', ')}. ` : ''}
                            {result.error || (result.candidate_id ? `Candidate ID ${result.candidate_id}` : '—')}
                          </span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : null}
            </section>
          ) : null}
        </CardContent>
      </Card>
    </TabsContent>
  );
};

export default BulkUploadTab;
