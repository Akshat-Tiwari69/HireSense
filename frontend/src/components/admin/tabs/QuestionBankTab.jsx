import React from 'react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/card';
import { Badge } from '../../ui/badge';
import { Label } from '../../ui/label';
import { TabsContent } from '../../ui/tabs';
import {
  FileQuestion, Upload, Loader2, BookOpen, FileText, XCircle,
  Eye, Trash2, RefreshCw, ToggleLeft, ToggleRight
} from 'lucide-react';

const QuestionBankTab = ({
  questionBanks,
  qbLoading,
  qbUploading,
  qbFile,
  setQbFile,
  qbDescription,
  setQbDescription,
  qbTags,
  setQbTags,
  qbPreview,
  qbPreviewLoading,
  fetchQuestionBanks,
  handleQbUpload,
  handleQbDelete,
  handleQbToggle,
  handleQbPreview,
}) => (
  <TabsContent value="question-bank">
    <div className="space-y-6">
      {/* Upload Section */}
      <Card className="bg-white border-none shadow-md">
        <CardHeader className="border-b border-slate-200 pb-4">
          <CardTitle className="flex items-center gap-2 text-slate-900">
            <FileQuestion className="w-5 h-5 text-indigo-600" />
            Upload Custom Questions
          </CardTitle>
          <CardDescription>Upload a PDF or DOCX file containing your own questions. AI will parse them and blend them into future assessments.</CardDescription>
        </CardHeader>
        <CardContent className="pt-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-sm font-medium text-slate-700">File (PDF / DOCX)</Label>
              <div
                className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer ${qbFile ? 'border-indigo-400 bg-indigo-50' : 'border-slate-300 hover:border-indigo-400 bg-slate-50'}`}
                onClick={() => document.getElementById('qb-file-input').click()}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  const f = e.dataTransfer.files[0];
                  if (f && (f.name.endsWith('.pdf') || f.name.endsWith('.docx'))) setQbFile(f);
                }}
              >
                <input
                  id="qb-file-input"
                  type="file"
                  accept=".pdf,.docx"
                  className="hidden"
                  onChange={(e) => setQbFile(e.target.files[0] || null)}
                />
                {qbFile ? (
                  <div className="flex items-center justify-center gap-2 text-indigo-700">
                    <FileText className="w-5 h-5" />
                    <span className="font-medium">{qbFile.name}</span>
                    <button onClick={(e) => { e.stopPropagation(); setQbFile(null); }} className="ml-2 text-slate-400 hover:text-red-500">
                      <XCircle className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <div>
                    <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                    <p className="text-sm text-slate-500">Drop a PDF/DOCX here or click to browse</p>
                  </div>
                )}
              </div>
            </div>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label className="text-sm font-medium text-slate-700">Description (Optional)</Label>
                <Input
                  placeholder="e.g. Java & Spring Boot questions from 2024 exam"
                  value={qbDescription}
                  onChange={(e) => setQbDescription(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label className="text-sm font-medium text-slate-700">Tags (Optional)</Label>
                <Input
                  placeholder="e.g. java, spring, backend"
                  value={qbTags}
                  onChange={(e) => setQbTags(e.target.value)}
                />
              </div>
            </div>
          </div>
          <Button
            onClick={handleQbUpload}
            disabled={!qbFile || qbUploading}
            className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-md"
          >
            {qbUploading ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Parsing & Uploading...</>
            ) : (
              <><Upload className="w-4 h-4 mr-2" /> Upload & Parse Questions</>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Question Banks List */}
      <Card className="bg-white border-none shadow-md">
        <CardHeader className="border-b border-slate-200 pb-4 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-slate-900 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-indigo-600" />
              Uploaded Question Banks ({questionBanks.length})
            </CardTitle>
          </div>
          <Button variant="outline" size="sm" onClick={fetchQuestionBanks} disabled={qbLoading}>
            <RefreshCw className={`w-4 h-4 mr-1 ${qbLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </CardHeader>
        <CardContent className="pt-4">
          {qbLoading ? (
            <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-indigo-500" /></div>
          ) : questionBanks.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <BookOpen className="w-12 h-12 mx-auto mb-3 text-slate-300" />
              <p className="font-medium">No question banks uploaded yet</p>
              <p className="text-sm mt-1">Upload a PDF or DOCX to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {questionBanks.map(qb => (
                <div key={qb.id} className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-all">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${qb.is_active ? 'bg-green-100 text-green-600' : 'bg-slate-100 text-slate-400'}`}>
                        <FileText className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-800">{qb.filename}</span>
                          <Badge variant={qb.is_active ? 'default' : 'secondary'} className={qb.is_active ? 'bg-green-100 text-green-700 hover:bg-green-100' : ''}>
                            {qb.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                          <Badge variant="outline" className="text-indigo-600 border-indigo-200">
                            {qb.questions_count} questions
                          </Badge>
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5">
                          {qb.description && <span>{qb.description} · </span>}
                          Uploaded by {qb.uploaded_by || 'Unknown'} · {qb.created_at ? new Date(qb.created_at).toLocaleDateString() : ''}
                          {qb.tags && <span className="ml-2 text-indigo-500">{qb.tags}</span>}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleQbPreview(qb.id)}
                        title="Preview questions"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleQbToggle(qb.id)}
                        title={qb.is_active ? 'Deactivate' : 'Activate'}
                      >
                        {qb.is_active ? <ToggleRight className="w-4 h-4 text-green-600" /> : <ToggleLeft className="w-4 h-4 text-slate-400" />}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleQbDelete(qb.id)}
                        className="hover:text-red-600"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  {/* Expandable Preview */}
                  {qbPreview?.id === qb.id && (
                    <div className="mt-4 border-t border-slate-100 pt-4">
                      {qbPreviewLoading ? (
                        <div className="flex items-center gap-2 text-slate-500"><Loader2 className="w-4 h-4 animate-spin" /> Loading...</div>
                      ) : (
                        <div className="space-y-3">
                          <div className="text-sm font-medium text-slate-700">Parsed Questions ({qbPreview.questions_count}):</div>
                          <div className="max-h-80 overflow-y-auto space-y-2">
                            {(qbPreview.parsed_questions || []).map((q, i) => (
                              <div key={i} className="bg-slate-50 rounded-lg p-3 text-sm">
                                <div className="font-medium text-slate-800">Q{i + 1}: {q.question}</div>
                                {q.options && (
                                  <div className="mt-2 grid grid-cols-2 gap-1">
                                    {q.options.map((opt, j) => (
                                      <div key={j} className={`px-2 py-1 rounded text-xs ${opt === q.correct_answer ? 'bg-green-100 text-green-700 font-medium' : 'text-slate-600'}`}>
                                        {String.fromCharCode(65 + j)}. {opt}
                                      </div>
                                    ))}
                                  </div>
                                )}
                                {q.correct_answer && !q.options && (
                                  <div className="mt-1 text-xs text-green-600">Answer: {q.correct_answer}</div>
                                )}
                                <div className="mt-1 flex gap-2">
                                  {q.category && <Badge variant="outline" className="text-xs">{q.category}</Badge>}
                                  {q.difficulty && <Badge variant="outline" className="text-xs">{q.difficulty}</Badge>}
                                </div>
                              </div>
                            ))}
                          </div>
                          {qbPreview.raw_text_preview && (
                            <details className="text-xs text-slate-500">
                              <summary className="cursor-pointer hover:text-slate-700">Raw text preview</summary>
                              <pre className="mt-2 p-2 bg-slate-100 rounded text-xs whitespace-pre-wrap max-h-40 overflow-y-auto">{qbPreview.raw_text_preview}</pre>
                            </details>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  </TabsContent>
);

export default QuestionBankTab;
