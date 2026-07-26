import { useRef } from 'react';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { TabsContent } from '../../ui/tabs';
import StatusBadge from '../../workspace/StatusBadge';
import {
  BookOpen,
  Eye,
  FileQuestion,
  FileText,
  Loader2,
  RefreshCw,
  ToggleLeft,
  ToggleRight,
  Trash2,
  Upload,
  X,
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
}) => {
  const fileInputRef = useRef(null);

  const selectQuestionFile = (file) => {
    if (!file) return;
    const filename = file.name.toLowerCase();
    if (filename.endsWith('.pdf') || filename.endsWith('.docx')) setQbFile(file);
  };

  return (
    <TabsContent value="question-bank">
      <div className="space-y-5">
        <Card>
          <CardHeader className="border-b">
            <div className="flex items-start gap-3">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
                <FileQuestion className="h-4 w-4" />
              </span>
              <div className="space-y-1.5">
                <CardTitle>Upload assessment questions</CardTitle>
                <CardDescription>Import a PDF or DOCX question set for use in future assessments.</CardDescription>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-5 pt-6">
            <div className="grid gap-5 lg:grid-cols-2">
              <div
                className="rounded-xl border border-dashed p-5"
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => {
                  event.preventDefault();
                  selectQuestionFile(event.dataTransfer.files[0]);
                }}
              >
                <Label>Question document</Label>
                <p className="mt-1 text-sm text-muted-foreground">PDF or DOCX files only.</p>
                <input
                  ref={fileInputRef}
                  id="question-bank-file"
                  type="file"
                  accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  className="sr-only"
                  onChange={(event) => selectQuestionFile(event.target.files[0])}
                />
                {qbFile ? (
                  <div className="mt-4 flex items-center justify-between gap-3 rounded-lg border bg-slate-50 p-4">
                    <div className="flex min-w-0 items-center gap-2">
                      <FileText className="h-4 w-4 shrink-0 text-blue-700" />
                      <span className="truncate text-sm font-medium text-foreground">{qbFile.name}</span>
                    </div>
                    <Button
                      type="button"
                      size="icon"
                      variant="ghost"
                      onClick={() => {
                        setQbFile(null);
                        if (fileInputRef.current) fileInputRef.current.value = '';
                      }}
                      aria-label="Remove selected question document"
                      title="Remove file"
                    >
                      <X />
                    </Button>
                  </div>
                ) : (
                  <Button type="button" variant="outline" className="mt-4" onClick={() => fileInputRef.current?.click()}>
                    <Upload />
                    Choose document
                  </Button>
                )}
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="question-bank-description">Description <span className="font-normal text-muted-foreground">(optional)</span></Label>
                  <Input
                    id="question-bank-description"
                    placeholder="Example: Java and Spring Boot interview questions"
                    value={qbDescription}
                    onChange={(event) => setQbDescription(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="question-bank-tags">Tags <span className="font-normal text-muted-foreground">(optional)</span></Label>
                  <Input
                    id="question-bank-tags"
                    placeholder="java, spring, backend"
                    value={qbTags}
                    onChange={(event) => setQbTags(event.target.value)}
                  />
                </div>
              </div>
            </div>
            <Button type="button" onClick={handleQbUpload} disabled={!qbFile || qbUploading}>
              {qbUploading ? <Loader2 className="animate-spin" /> : <Upload />}
              {qbUploading ? 'Parsing questions' : 'Upload and parse'}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="gap-4 border-b sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2">
                <CardTitle>Question library</CardTitle>
                <Badge variant="outline" className="border-slate-200 bg-slate-50 text-slate-600">{questionBanks.length}</Badge>
              </div>
              <CardDescription>Review imported questions and control which banks are active.</CardDescription>
            </div>
            <Button type="button" variant="outline" onClick={fetchQuestionBanks} disabled={qbLoading}>
              <RefreshCw className={qbLoading ? 'animate-spin' : ''} />
              Refresh
            </Button>
          </CardHeader>

          <CardContent className="pt-5">
            {qbLoading ? (
              <div className="flex min-h-56 items-center justify-center text-muted-foreground" role="status">
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Loading question banks
              </div>
            ) : questionBanks.length === 0 ? (
              <div className="flex min-h-56 flex-col items-center justify-center rounded-lg border border-dashed px-6 text-center">
                <span className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                  <BookOpen className="h-5 w-5" />
                </span>
                <p className="font-medium text-foreground">No question banks uploaded</p>
                <p className="mt-1 text-sm text-muted-foreground">Upload a document to build the shared assessment library.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {questionBanks.map((questionBank) => (
                  <article key={questionBank.id} className="rounded-xl border bg-card p-4 sm:p-5">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="flex min-w-0 items-start gap-3">
                        <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${questionBank.is_active ? 'bg-blue-50 text-blue-700' : 'bg-muted text-muted-foreground'}`}>
                          <FileText className="h-5 w-5" />
                        </span>
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="break-all font-semibold text-foreground">{questionBank.filename}</h3>
                            <StatusBadge status={questionBank.is_active ? 'active' : 'inactive'} />
                            <Badge variant="outline" className="border-slate-200 bg-slate-50 text-slate-700">
                              {questionBank.questions_count} questions
                            </Badge>
                          </div>
                          {questionBank.description ? <p className="mt-2 text-sm text-slate-700">{questionBank.description}</p> : null}
                          <p className="mt-2 text-xs text-muted-foreground">
                            Uploaded by {questionBank.uploaded_by || 'Unknown'}
                            {questionBank.created_at ? ` · ${new Date(questionBank.created_at).toLocaleDateString()}` : ''}
                            {questionBank.tags ? ` · ${questionBank.tags}` : ''}
                          </p>
                        </div>
                      </div>
                      <div className="flex shrink-0 gap-1.5">
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          onClick={() => handleQbPreview(questionBank.id)}
                          aria-label={`Preview ${questionBank.filename}`}
                          aria-expanded={qbPreview?.id === questionBank.id}
                          title="Preview questions"
                        >
                          <Eye />
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => handleQbToggle(questionBank.id)}
                          aria-label={`${questionBank.is_active ? 'Deactivate' : 'Activate'} ${questionBank.filename}`}
                          title={questionBank.is_active ? 'Deactivate bank' : 'Activate bank'}
                        >
                          {questionBank.is_active ? <ToggleRight className="text-blue-700" /> : <ToggleLeft />}
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => handleQbDelete(questionBank.id)}
                          className="text-red-600 hover:bg-red-50 hover:text-red-700"
                          aria-label={`Delete ${questionBank.filename}`}
                          title="Delete question bank"
                        >
                          <Trash2 />
                        </Button>
                      </div>
                    </div>

                    {qbPreview?.id === questionBank.id ? (
                      <div className="mt-5 border-t pt-5">
                        {qbPreviewLoading ? (
                          <div className="flex items-center gap-2 text-sm text-muted-foreground" role="status">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Loading preview
                          </div>
                        ) : (
                          <div className="space-y-4">
                            <p className="text-sm font-medium text-foreground">Parsed questions ({qbPreview.questions_count})</p>
                            <div className="max-h-96 space-y-3 overflow-y-auto pr-1">
                              {(qbPreview.parsed_questions || []).map((question, index) => (
                                <article key={`${question.question || 'question'}-${index}`} className="rounded-lg border bg-slate-50/60 p-4 text-sm">
                                  <p className="font-medium text-foreground">{index + 1}. {question.question}</p>
                                  {question.options ? (
                                    <div className="mt-3 grid gap-2 sm:grid-cols-2">
                                      {question.options.map((option, optionIndex) => (
                                        <div
                                          key={`${option}-${optionIndex}`}
                                          className={`rounded-md border px-3 py-2 text-xs ${option === question.correct_answer ? 'border-emerald-200 bg-emerald-50 font-medium text-emerald-700' : 'border-slate-200 bg-card text-slate-600'}`}
                                        >
                                          {String.fromCharCode(65 + optionIndex)}. {option}
                                        </div>
                                      ))}
                                    </div>
                                  ) : null}
                                  {question.correct_answer && !question.options ? (
                                    <p className="mt-2 text-xs font-medium text-emerald-700">Answer: {question.correct_answer}</p>
                                  ) : null}
                                  <div className="mt-3 flex flex-wrap gap-2">
                                    {question.category ? <Badge variant="outline">{question.category}</Badge> : null}
                                    {question.difficulty ? <Badge variant="outline">{question.difficulty}</Badge> : null}
                                  </div>
                                </article>
                              ))}
                            </div>
                            {qbPreview.raw_text_preview ? (
                              <details className="rounded-lg border bg-card p-3 text-xs text-muted-foreground">
                                <summary className="cursor-pointer font-medium text-foreground">Raw text preview</summary>
                                <pre className="mt-3 max-h-48 overflow-auto whitespace-pre-wrap rounded-md bg-slate-50 p-3 font-mono text-xs">{qbPreview.raw_text_preview}</pre>
                              </details>
                            ) : null}
                          </div>
                        )}
                      </div>
                    ) : null}
                  </article>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </TabsContent>
  );
};

export default QuestionBankTab;
