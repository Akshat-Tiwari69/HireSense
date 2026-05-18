import React from 'react';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { Badge } from '../../ui/badge';
import { Label } from '../../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { TabsContent } from '../../ui/tabs';
import {
  FileArchive, Upload, Loader2, AlertTriangle, CheckCircle2, XCircle
} from 'lucide-react';
import { api } from '../../../services/api';
import { useToast } from '../../../hooks/use-toast';

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

  return (
    <TabsContent value="bulk-upload">
      <Card className="bg-white border-none shadow-md hover:shadow-lg transition-all duration-300">
        <CardHeader className="border-b border-slate-200 pb-4">
          <div>
            <CardTitle className="text-slate-900 flex items-center gap-2">
              <FileArchive className="w-5 h-5 text-indigo-600" />
              Bulk Resume Upload
            </CardTitle>
            <CardDescription className="text-slate-600">
              Upload a ZIP archive containing PDF/DOCX resumes. All resumes will be processed in parallel by multiple AI agents and scored against the selected job.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="pt-6 space-y-6">
          {/* Step 1: Select Job */}
          <div className="space-y-2">
            <Label className="text-slate-700 font-semibold">1. Select Target Job</Label>
            <p className="text-xs text-slate-500">All resumes will be AI-scored against this job position</p>
            <Select value={bulkJobId} onValueChange={setBulkJobId}>
              <SelectTrigger className="w-full max-w-md">
                <SelectValue placeholder="Choose a job posting..." />
              </SelectTrigger>
              <SelectContent position="popper">
                {jobPostings.filter(j => j.status === 'active').map(job => (
                  <SelectItem key={job.id} value={String(job.id)}>
                    {job.title} — {job.department || 'General'}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Step 2: Upload ZIP */}
          <div className="space-y-2">
            <Label className="text-slate-700 font-semibold">2. Upload Resume Archive</Label>
            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
                bulkFile
                  ? 'border-indigo-400 bg-indigo-50'
                  : 'border-slate-300 hover:border-indigo-400 hover:bg-slate-50'
              }`}
              onClick={() => document.getElementById('bulk-zip-input').click()}
              onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
              onDrop={(e) => {
                e.preventDefault();
                e.stopPropagation();
                const file = e.dataTransfer.files[0];
                const name = file?.name?.toLowerCase() || '';
                if (file && (name.endsWith('.zip') || name.endsWith('.rar'))) {
                  setBulkFile(file);
                  setBulkResults(null);
                } else {
                  toast({ title: 'Invalid file', description: 'Please drop a .zip or .rar file', variant: 'destructive' });
                }
              }}
            >
              <input
                id="bulk-zip-input"
                type="file"
                accept=".zip,.rar"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files[0]) {
                    setBulkFile(e.target.files[0]);
                    setBulkResults(null);
                  }
                }}
              />
              {bulkFile ? (
                <div className="space-y-2">
                  <FileArchive className="w-12 h-12 mx-auto text-indigo-600" />
                  <p className="text-lg font-medium text-indigo-700">{bulkFile.name}</p>
                  <p className="text-sm text-slate-500">{(bulkFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                  <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); setBulkFile(null); setBulkResults(null); }}>
                    Change file
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="w-12 h-12 mx-auto text-slate-400" />
                  <p className="text-lg font-medium text-slate-600">Drop ZIP or RAR file here or click to browse</p>
                  <p className="text-sm text-slate-400">Supports .zip and .rar archives containing .pdf and .docx resumes</p>
                </div>
              )}
            </div>
          </div>

          {/* Upload Button */}
          <Button
            className="bg-indigo-600 hover:bg-indigo-700 shadow-md px-8"
            disabled={!bulkFile || !bulkJobId || bulkUploading}
            onClick={async () => {
              setBulkUploading(true);
              setBulkResults(null);
              setBulkProgress('Uploading archive and extracting resumes...');
              try {
                const formData = new FormData();
                formData.append('file', bulkFile);
                formData.append('job_id', bulkJobId);
                const res = await api.post('/api/admin/bulk-upload', formData, {
                  headers: { 'Content-Type': 'multipart/form-data' },
                  timeout: 600000 // 10 min timeout for large batches
                });
                setBulkResults(res.data);
                setBulkProgress(null);
                toast({
                  title: 'Bulk Upload Complete',
                  description: res.data.message,
                  duration: 5000
                });
              } catch (err) {
                const msg = err.response?.data?.message || err.message;
                setBulkProgress(null);
                toast({ title: 'Bulk Upload Failed', description: msg, variant: 'destructive' });
              } finally {
                setBulkUploading(false);
              }
            }}
          >
            {bulkUploading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Processing Resumes...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                Upload & Process All
              </>
            )}
          </Button>

          {/* Progress Indicator */}
          {bulkUploading && bulkProgress && (
            <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <Loader2 className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0" />
              <div>
                <p className="font-medium text-blue-800">{bulkProgress}</p>
                <p className="text-xs text-blue-600 mt-1">Multiple AI agents are processing resumes in parallel. This may take a few minutes for large batches.</p>
              </div>
            </div>
          )}

          {/* Results */}
          {bulkResults && bulkResults.summary && (
            <div className="space-y-4">
              {/* Summary Cards */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-slate-50 rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-slate-800">{bulkResults.summary.total}</p>
                  <p className="text-sm text-slate-500">Total Resumes</p>
                </div>
                <div className="bg-green-50 rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-green-700">{bulkResults.summary.success}</p>
                  <p className="text-sm text-green-600">Successfully Added</p>
                </div>
                <div className="bg-orange-50 rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-orange-700">{bulkResults.results?.filter(r => r.missing?.length > 0 && r.status === 'success').length || 0}</p>
                  <p className="text-sm text-orange-600">Absence of Details</p>
                </div>
                <div className="bg-amber-50 rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-amber-700">{bulkResults.summary.duplicates}</p>
                  <p className="text-sm text-amber-600">Duplicates Skipped</p>
                </div>
                <div className="bg-red-50 rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-red-700">{bulkResults.summary.errors}</p>
                  <p className="text-sm text-red-600">Failed</p>
                </div>
              </div>

              <p className="text-sm text-slate-500">
                Job: <span className="font-medium text-slate-700">{bulkResults.summary.job?.title}</span>
                {bulkResults.summary.job?.department && <span> — {bulkResults.summary.job.department}</span>}
              </p>

              {/* Detailed Results Table */}
              {bulkResults.results && bulkResults.results.length > 0 && (
                <div className="overflow-x-auto rounded-lg border border-slate-200">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-slate-50">
                        <TableHead className="text-slate-700">Status</TableHead>
                        <TableHead className="text-slate-700">File</TableHead>
                        <TableHead className="text-slate-700">Name</TableHead>
                        <TableHead className="text-slate-700">Email</TableHead>
                        <TableHead className="text-slate-700">Match Score</TableHead>
                        <TableHead className="text-slate-700">AI Recommendation</TableHead>
                        <TableHead className="text-slate-700">Details</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {bulkResults.results.map((r, idx) => (
                        <TableRow key={idx} className={
                          r.status === 'success' && r.missing?.length > 0 ? 'bg-orange-50/50' :
                          r.status === 'success' ? 'bg-green-50/50' :
                          r.status === 'duplicate' ? 'bg-amber-50/50' : 'bg-red-50/50'
                        }>
                          <TableCell>
                            {r.status === 'success' && r.missing?.length > 0 && <AlertTriangle className="w-5 h-5 text-orange-500" />}
                            {r.status === 'success' && (!r.missing || r.missing.length === 0) && <CheckCircle2 className="w-5 h-5 text-green-600" />}
                            {r.status === 'duplicate' && <AlertTriangle className="w-5 h-5 text-amber-500" />}
                            {r.status === 'error' && <XCircle className="w-5 h-5 text-red-500" />}
                          </TableCell>
                          <TableCell className="text-sm text-slate-700 max-w-[200px] truncate" title={r.filename}>
                            {r.filename}
                          </TableCell>
                          <TableCell className="text-sm font-medium text-slate-800">{r.name || '—'}</TableCell>
                          <TableCell className="text-sm text-slate-600">{r.email || '—'}</TableCell>
                          <TableCell>
                            {r.match_score > 0 ? (
                              <Badge className={
                                r.match_score >= 70 ? 'bg-green-100 text-green-800' :
                                r.match_score >= 40 ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800'
                              }>
                                {r.match_score}%
                              </Badge>
                            ) : '—'}
                          </TableCell>
                          <TableCell className="text-sm text-slate-600">
                            {r.recommendation || '—'}
                            {r.missing?.length > 0 && (
                              <Badge className="ml-2 bg-orange-100 text-orange-800 text-xs">Absence of Details</Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-sm text-slate-500 max-w-[250px]">
                            <span className="truncate block" title={r.error || ''}>
                              {r.missing?.length > 0 && (
                                <span className="text-orange-600">Missing: {r.missing.join(', ')}. </span>
                              )}
                              {r.error || (r.candidate_id ? `ID: ${r.candidate_id}` : '')}
                            </span>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </TabsContent>
  );
};

export default BulkUploadTab;
