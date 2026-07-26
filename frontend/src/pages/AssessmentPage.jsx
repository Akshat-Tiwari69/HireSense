import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  BookOpen,
  Check,
  Clock3,
  Code2,
  LoaderCircle,
  ShieldCheck,
  Video,
  VideoOff,
} from 'lucide-react';

import CodingSection from '../components/assessment/CodingSection';
import MCQSection from '../components/assessment/MCQSection';
import PsychometricSection from '../components/assessment/PsychometricSection';
import Logo from '../components/Logo';
import { Button } from '../components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { useToast } from '../hooks/use-toast';
import { useProctorStream } from '../hooks/useProctorStream';
import {
  finalizeAssessmentSubmission,
  formatAssessmentTime,
  getCodeLanguages,
  getStarterCode,
  normalizeSavedMcqAnswers,
  normalizeSavedPsychometricAnswers,
  resolveAssessmentToken,
} from '../lib/assessment';
import { api } from '../services/api';

const SECTION_META = {
  knowledge: { label: 'Knowledge', icon: BookOpen },
  coding: { label: 'Practical exercise', icon: Code2 },
  workstyle: { label: 'Work style', icon: ShieldCheck },
};

const getErrorMessage = (error, fallback) => error?.response?.data?.message || fallback;

const AssessmentPage = () => {
  const { toast } = useToast();
  const videoRef = useRef(null);
  const submitRef = useRef(null);
  const submittingRef = useRef(false);
  const syncingRef = useRef(false);
  const pendingSavesRef = useRef(new Set());
  const answerVersionRef = useRef(new Map());
  const questionStartedAtRef = useRef(new Map());
  const cameraErrorReportedRef = useRef('');

  const [accessToken] = useState(() => {
    const hash = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    return resolveAssessmentToken(hash.get('token'));
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [session, setSession] = useState(null);
  const [submitted, setSubmitted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [currentSection, setCurrentSection] = useState('knowledge');
  const [mcqQuestion, setMcqQuestion] = useState(0);
  const [workstyleQuestion, setWorkstyleQuestion] = useState(0);
  const [mcqAnswers, setMcqAnswers] = useState({});
  const [psychometricAnswers, setPsychometricAnswers] = useState({});
  const [savingMcqId, setSavingMcqId] = useState(null);
  const [savingPsychometricId, setSavingPsychometricId] = useState(null);
  const [language, setLanguage] = useState('python');
  const [codes, setCodes] = useState({});
  const [savedSolution, setSavedSolution] = useState(null);
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [proctoringActive, setProctoringActive] = useState(false);
  const [violationCount, setViolationCount] = useState(0);

  const assessmentId = session?.assessment_id;
  const questions = useMemo(() => session?.mcq_questions || [], [session]);
  const problem = session?.coding_problem || null;
  const scenarios = useMemo(() => session?.psychometric_scenarios || [], [session]);
  const currentCode = codes[language] || '';
  const codeSaved = savedSolution?.language === language && savedSolution?.code === currentCode;
  const isTechnical = Boolean(session?.is_technical_role && problem);

  const sections = useMemo(() => [
    ...(questions.length ? ['knowledge'] : []),
    ...(isTechnical ? ['coding'] : []),
    ...(scenarios.length ? ['workstyle'] : []),
  ], [isTechnical, questions.length, scenarios.length]);

  const { mediaStream, isStreaming, streamError } = useProctorStream(
    assessmentId,
    accessToken,
    Boolean(proctoringActive && !submitted),
  );

  useEffect(() => {
    if (window.location.hash) {
      window.history.replaceState(null, document.title, '/assessment');
    }
  }, []);

  useEffect(() => {
    if (!mediaStream || !videoRef.current) return;
    videoRef.current.srcObject = mediaStream;
    videoRef.current.play().catch(() => {});
  }, [mediaStream]);

  useEffect(() => {
    if (!accessToken) {
      setError('This assessment link is missing its access token. Open the latest invitation from your email.');
      setLoading(false);
      return undefined;
    }

    const controller = new AbortController();
    const loadAssessment = async () => {
      try {
        const verifyResponse = await api.get('/api/interviewee/assessment/verify', {
          signal: controller.signal,
        });
        const verification = verifyResponse.data?.data || {};
        if (!verification.can_start && !verification.already_started) {
          const scheduled = verification.scheduled_time
            ? new Date(verification.scheduled_time).toLocaleString()
            : 'the scheduled time';
          throw new Error(`This assessment can be opened within 30 minutes of ${scheduled}.`);
        }

        const startResponse = await api.post('/api/interviewee/assessment/start', null, {
          signal: controller.signal,
        });
        const data = startResponse.data?.data;
        if (!data?.assessment_id) throw new Error('The assessment session could not be created.');

        const savedMcq = normalizeSavedMcqAnswers(data.saved_mcq_answers);
        const savedWorkstyle = normalizeSavedPsychometricAnswers(data.saved_psychometric_answers);
        const availableProblem = data.is_technical_role ? data.coding_problem : null;
        const savedCoding = data.saved_coding;
        const problemLanguages = getCodeLanguages(availableProblem);
        const initialLanguage = problemLanguages.includes(savedCoding?.language)
          ? savedCoding.language
          : (problemLanguages[0] || '');
        const initialCode = savedCoding?.code || getStarterCode(availableProblem, initialLanguage);
        const initialSections = [
          ...(data.mcq_questions?.length ? ['knowledge'] : []),
          ...(availableProblem ? ['coding'] : []),
          ...(data.psychometric_scenarios?.length ? ['workstyle'] : []),
        ];

        setSession({ ...data, coding_problem: availableProblem });
        setMcqAnswers(savedMcq);
        setPsychometricAnswers(savedWorkstyle);
        setLanguage(initialLanguage);
        setCodes({ [initialLanguage]: initialCode });
        setSavedSolution(savedCoding ? { language: initialLanguage, code: initialCode } : null);
        setTimeRemaining(Math.max(0, Number(data.remaining_seconds) || 0));
        setCurrentSection(initialSections[0] || 'knowledge');
        setProctoringActive(Boolean(data.proctoring_enabled));
      } catch (loadError) {
        if (loadError?.code === 'ERR_CANCELED') return;
        const status = loadError?.response?.status;
        if ([400, 403, 404, 409].includes(status)) {
          window.sessionStorage.removeItem('assessmentToken');
        }
        setError(getErrorMessage(loadError, loadError.message || 'Unable to load this assessment.'));
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    };

    loadAssessment();
    return () => controller.abort();
  }, [accessToken]);

  const captureScreenshot = useCallback(() => {
    const video = videoRef.current;
    if (!video?.videoWidth || !video?.videoHeight) return null;
    const canvas = document.createElement('canvas');
    canvas.width = Math.min(video.videoWidth, 640);
    canvas.height = Math.round(canvas.width * (video.videoHeight / video.videoWidth));
    canvas.getContext('2d')?.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg', 0.7);
  }, []);

  const reportViolation = useCallback(async (type, description, severity = 'medium', includeScreenshot = false) => {
    if (!assessmentId || submitted) return;
    try {
      const response = await api.post(`/api/interviewee/assessment/${assessmentId}/violation`, {
        violation_type: type,
        description,
        severity,
        screenshot: includeScreenshot ? captureScreenshot() : null,
      });
      setViolationCount(Number(response.data?.data?.total_violations) || 0);
    } catch {
      // Monitoring must never erase candidate work or block assessment controls.
    }
  }, [assessmentId, captureScreenshot, submitted]);

  useEffect(() => {
    if (!assessmentId || submitted) return undefined;
    const onVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        reportViolation(
          'tab_hidden',
          'The assessment tab was hidden while the session was active.',
          'medium',
          true,
        );
      }
    };
    document.addEventListener('visibilitychange', onVisibilityChange);
    return () => document.removeEventListener('visibilitychange', onVisibilityChange);
  }, [assessmentId, reportViolation, submitted]);

  useEffect(() => {
    if (!streamError || !assessmentId || cameraErrorReportedRef.current === streamError) return;
    cameraErrorReportedRef.current = streamError;
    reportViolation('camera_interrupted', streamError, 'high');
  }, [assessmentId, reportViolation, streamError]);

  useEffect(() => {
    if (!assessmentId || submitted) return undefined;
    const warnBeforeLeaving = (event) => {
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', warnBeforeLeaving);
    return () => window.removeEventListener('beforeunload', warnBeforeLeaving);
  }, [assessmentId, submitted]);

  useEffect(() => {
    if (!assessmentId || submitted) return undefined;
    const timer = window.setInterval(() => {
      setTimeRemaining((remaining) => {
        if (remaining <= 1) {
          window.queueMicrotask(() => submitRef.current?.(true));
          return 0;
        }
        return remaining - 1;
      });
    }, 1000);
    return () => window.clearInterval(timer);
  }, [assessmentId, submitted]);

  useEffect(() => {
    if (!assessmentId || submitted) return undefined;
    const syncTime = async () => {
      if (syncingRef.current || document.visibilityState === 'hidden') return;
      syncingRef.current = true;
      try {
        const response = await api.get(`/api/interviewee/assessment/${assessmentId}/remaining-time`);
        const remaining = Math.max(0, Number(response.data?.data?.remaining_seconds) || 0);
        setTimeRemaining(remaining);
        if (remaining === 0) submitRef.current?.(true);
      } catch {
        // The local countdown continues; the next sync or submission remains server-authoritative.
      } finally {
        syncingRef.current = false;
      }
    };
    const interval = window.setInterval(syncTime, 30000);
    const onVisible = () => {
      if (document.visibilityState === 'visible') syncTime();
    };
    document.addEventListener('visibilitychange', onVisible);
    return () => {
      window.clearInterval(interval);
      document.removeEventListener('visibilitychange', onVisible);
    };
  }, [assessmentId, submitted]);

  useEffect(() => {
    const question = currentSection === 'knowledge'
      ? questions[mcqQuestion]
      : currentSection === 'workstyle'
        ? scenarios[workstyleQuestion]
        : null;
    if (question) {
      questionStartedAtRef.current.set(`${currentSection}:${question.id}`, Date.now());
    }
  }, [currentSection, mcqQuestion, questions, scenarios, workstyleQuestion]);

  const trackSave = (request) => {
    pendingSavesRef.current.add(request);
    request.then(
      () => pendingSavesRef.current.delete(request),
      () => pendingSavesRef.current.delete(request),
    );
    return request;
  };

  const handleMcqAnswer = async (questionId, answerIndex) => {
    const previous = mcqAnswers[questionId];
    const version = (answerVersionRef.current.get(`mcq:${questionId}`) || 0) + 1;
    answerVersionRef.current.set(`mcq:${questionId}`, version);
    setMcqAnswers((answers) => ({ ...answers, [questionId]: answerIndex }));
    setSavingMcqId(questionId);
    const startedAt = questionStartedAtRef.current.get(`knowledge:${questionId}`) || Date.now();
    const timeSpent = Math.min(3600, Math.max(0, Math.round((Date.now() - startedAt) / 1000)));

    try {
      await trackSave(api.post(`/api/interviewee/assessment/${assessmentId}/submit-answer`, {
        type: 'mcq',
        questionId,
        answer: String.fromCharCode(65 + answerIndex),
        timeSpent,
      }));
    } catch (saveError) {
      if (answerVersionRef.current.get(`mcq:${questionId}`) === version) {
        setMcqAnswers((answers) => {
          const next = { ...answers };
          if (previous === undefined) delete next[questionId];
          else next[questionId] = previous;
          return next;
        });
        toast({ variant: 'destructive', title: 'Answer not saved', description: getErrorMessage(saveError, 'Try selecting the answer again.') });
      }
    } finally {
      if (answerVersionRef.current.get(`mcq:${questionId}`) === version) setSavingMcqId(null);
    }
  };

  const handlePsychometricAnswer = async (questionId, answerIndex) => {
    const previous = psychometricAnswers[questionId];
    const version = (answerVersionRef.current.get(`workstyle:${questionId}`) || 0) + 1;
    answerVersionRef.current.set(`workstyle:${questionId}`, version);
    setPsychometricAnswers((answers) => ({ ...answers, [questionId]: answerIndex }));
    setSavingPsychometricId(questionId);

    try {
      await trackSave(api.post(`/api/interviewee/assessment/${assessmentId}/submit-answer`, {
        type: 'psychometric',
        questionId,
        selectedOption: answerIndex,
      }));
    } catch (saveError) {
      if (answerVersionRef.current.get(`workstyle:${questionId}`) === version) {
        setPsychometricAnswers((answers) => {
          const next = { ...answers };
          if (previous === undefined) delete next[questionId];
          else next[questionId] = previous;
          return next;
        });
        toast({ variant: 'destructive', title: 'Response not saved', description: getErrorMessage(saveError, 'Try selecting the response again.') });
      }
    } finally {
      if (answerVersionRef.current.get(`workstyle:${questionId}`) === version) setSavingPsychometricId(null);
    }
  };

  const handleLanguageChange = (nextLanguage) => {
    setCodes((values) => ({
      ...values,
      [nextLanguage]: values[nextLanguage] ?? getStarterCode(problem, nextLanguage),
    }));
    setLanguage(nextLanguage);
    setOutput('');
  };

  const updateCode = (value) => {
    setCodes((values) => ({ ...values, [language]: value }));
  };

  const executeExample = async (index) => {
    const response = await api.post('/api/interviewee/run-code', {
      language,
      code: currentCode,
      problem_id: problem.id,
      test_case_index: index,
    });
    return response.data?.data || {};
  };

  const handleRunCode = async () => {
    setIsRunning(true);
    setOutput('');
    try {
      const result = await executeExample(0);
      const body = result.stderr || result.stdout || '(No output)';
      setOutput(`${body}\n\nExpected: ${result.expected ?? '—'}\nResult: ${result.passed ? 'Passed' : 'Not passed'}`);
    } catch (runError) {
      setOutput(getErrorMessage(runError, 'Code execution is currently unavailable.'));
    } finally {
      setIsRunning(false);
    }
  };

  const handleRunTests = async (testCases) => {
    setIsRunning(true);
    setOutput('');
    try {
      const results = [];
      for (let index = 0; index < testCases.length; index += 1) {
        // Execute sequentially to avoid overloading the sandbox service.
        results.push(await executeExample(index));
      }
      setOutput(results.map((result, index) => [
        `Example ${index + 1}: ${result.passed ? 'Passed' : 'Not passed'}`,
        `Output: ${result.stderr || result.stdout || '(No output)'}`,
        `Expected: ${result.expected ?? '—'}`,
      ].join('\n')).join('\n\n'));
    } catch (runError) {
      setOutput(getErrorMessage(runError, 'Example execution is currently unavailable.'));
    } finally {
      setIsRunning(false);
    }
  };

  const saveCode = useCallback(async ({ quiet = false } = {}) => {
    if (!assessmentId || !problem || !currentCode.trim()) return false;
    setIsRunning(true);
    try {
      await api.post(`/api/interviewee/assessment/${assessmentId}/submit-answer`, {
        type: 'coding',
        questionId: problem.id,
        language,
        code: currentCode,
      });
      setSavedSolution({ language, code: currentCode });
      if (!quiet) toast({ title: 'Solution saved', description: 'Your latest code is included in the assessment.' });
      return true;
    } catch (saveError) {
      if (!quiet) toast({ variant: 'destructive', title: 'Solution not saved', description: getErrorMessage(saveError, 'Please try again.') });
      throw saveError;
    } finally {
      setIsRunning(false);
    }
  }, [assessmentId, currentCode, language, problem, toast]);

  const handleSubmit = useCallback(async (automatic = false) => {
    if (!assessmentId || submittingRef.current || submitted) return;
    submittingRef.current = true;
    setIsSubmitting(true);
    setConfirmOpen(false);
    try {
      await Promise.allSettled([...pendingSavesRef.current]);
      const { saveError } = await finalizeAssessmentSubmission({
        automatic,
        shouldSaveCode: isTechnical && Boolean(currentCode.trim()) && !codeSaved,
        saveCode,
        complete: () => api.post(`/api/interviewee/assessment/${assessmentId}/complete`),
      });
      setSubmitted(true);
      setProctoringActive(false);
      window.sessionStorage.removeItem('assessmentToken');
      toast({
        title: automatic ? 'Time ended — assessment submitted' : 'Assessment submitted',
        description: saveError
          ? 'Your saved responses were submitted; the final unsaved code could not be included.'
          : 'Your responses are safely recorded.',
      });
    } catch (submitError) {
      toast({ variant: 'destructive', title: 'Submission failed', description: getErrorMessage(submitError, 'Your work is still saved. Please try again.') });
    } finally {
      setIsSubmitting(false);
      submittingRef.current = false;
    }
  }, [assessmentId, codeSaved, currentCode, isTechnical, saveCode, submitted, toast]);

  submitRef.current = handleSubmit;

  const moveSection = (offset) => {
    const index = sections.indexOf(currentSection);
    const next = sections[index + offset];
    if (next) {
      setCurrentSection(next);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const completion = {
    knowledge: questions.length > 0 && questions.every(({ id }) => mcqAnswers[id] !== undefined),
    coding: !isTechnical || codeSaved,
    workstyle: scenarios.length > 0 && scenarios.every(({ id }) => psychometricAnswers[id] !== undefined),
  };
  const unanswered = questions.filter(({ id }) => mcqAnswers[id] === undefined).length
    + scenarios.filter(({ id }) => psychometricAnswers[id] === undefined).length;

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
        <div className="text-center">
          <Logo size="large" />
          <LoaderCircle className="mx-auto mt-8 h-6 w-6 animate-spin text-blue-600" aria-hidden="true" />
          <p className="mt-3 text-sm text-slate-600">Preparing your assessment…</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6 py-16">
        <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <Logo size="large" />
          <div className="mx-auto mt-8 flex h-11 w-11 items-center justify-center rounded-full bg-amber-50">
            <AlertTriangle className="h-5 w-5 text-amber-700" aria-hidden="true" />
          </div>
          <h1 className="mt-5 text-2xl font-semibold tracking-tight text-slate-950">Assessment unavailable</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">{error}</p>
          <Button asChild variant="outline" className="mt-7"><Link to="/">Return home</Link></Button>
        </div>
      </main>
    );
  }

  if (submitted) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6 py-16">
        <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <Logo size="large" />
          <div className="mx-auto mt-8 flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50">
            <Check className="h-6 w-6 text-emerald-700" aria-hidden="true" />
          </div>
          <h1 className="mt-5 text-2xl font-semibold tracking-tight text-slate-950">Assessment submitted</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">Thank you, {session?.candidate_name}. Your responses are recorded and the hiring team will contact you about next steps.</p>
          <Button asChild className="mt-7"><Link to="/">Return home</Link></Button>
        </div>
      </main>
    );
  }

  const timerUrgent = timeRemaining <= 300;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1480px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-4">
            <Logo size="small" />
            <div className="hidden h-6 w-px bg-slate-200 sm:block" />
            <div className="hidden min-w-0 sm:block">
              <p className="truncate text-sm font-medium text-slate-950">{session?.candidate_name}</p>
              <p className="text-xs text-slate-500">Candidate assessment</p>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-3">
            <div className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-semibold tabular-nums ${timerUrgent ? 'border-red-200 bg-red-50 text-red-700' : 'border-slate-200 bg-slate-50 text-slate-800'}`} aria-label={`${formatAssessmentTime(timeRemaining)} remaining`}>
              <Clock3 className="h-4 w-4" aria-hidden="true" />
              {formatAssessmentTime(timeRemaining)}
            </div>
            <Button type="button" size="sm" variant="outline" onClick={() => setConfirmOpen(true)}>Submit</Button>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-[1480px] gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[15rem_minmax(0,1fr)] lg:px-8 lg:py-8">
        <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <nav className="rounded-xl border border-slate-200 bg-white p-2 shadow-sm" aria-label="Assessment sections">
            {sections.map((section, index) => {
              const { label, icon: Icon } = SECTION_META[section];
              const active = section === currentSection;
              return (
                <button
                  key={section}
                  type="button"
                  onClick={() => setCurrentSection(section)}
                  aria-current={active ? 'step' : undefined}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${active ? 'bg-slate-950 font-medium text-white' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-950'}`}
                >
                  <span className={`flex h-6 w-6 items-center justify-center rounded-md text-xs ${active ? 'bg-white/15' : 'bg-slate-100'}`}>{index + 1}</span>
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  <span className="min-w-0 flex-1 truncate">{label}</span>
                  {completion[section] && <Check className={`h-4 w-4 ${active ? 'text-emerald-300' : 'text-emerald-600'}`} aria-label="Complete" />}
                </button>
              );
            })}
          </nav>

          {session?.proctoring_enabled && (
            <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
              <div className="aspect-video bg-slate-950">
                {mediaStream ? (
                  <video ref={videoRef} muted playsInline className="h-full w-full object-cover [transform:scaleX(-1)]" aria-label="Your camera preview" />
                ) : (
                  <div className="flex h-full items-center justify-center"><VideoOff className="h-6 w-6 text-slate-500" /></div>
                )}
              </div>
              <div className="p-3">
                <div className="flex items-center gap-2 text-sm font-medium text-slate-900">
                  <span className={`h-2 w-2 rounded-full ${isStreaming ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                  {isStreaming ? 'Proctoring connected' : 'Connecting camera'}
                </div>
                <p className="mt-1 text-xs leading-5 text-slate-500">Camera video and tab visibility are monitored during this session.</p>
                {streamError && <p className="mt-2 text-xs leading-5 text-red-700">{streamError}</p>}
                {violationCount > 0 && <p className="mt-2 text-xs text-slate-500">Session events recorded: {violationCount}</p>}
              </div>
            </div>
          )}

          {!session?.proctoring_enabled && (
            <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600 shadow-sm">
              <div className="flex items-center gap-2 font-medium text-slate-900"><Video className="h-4 w-4" /> Camera not required</div>
              <p className="mt-1 text-xs leading-5">This assessment does not use live video proctoring.</p>
            </div>
          )}
        </aside>

        <div className="min-w-0">
          {currentSection === 'knowledge' && (
            <MCQSection
              questions={questions}
              currentQuestion={mcqQuestion}
              mcqAnswers={mcqAnswers}
              onAnswer={handleMcqAnswer}
              onNextSection={() => moveSection(1)}
              setCurrentQuestion={setMcqQuestion}
              savingQuestionId={savingMcqId}
            />
          )}
          {currentSection === 'coding' && (
            <CodingSection
              problem={problem}
              language={language}
              onLanguageChange={handleLanguageChange}
              code={currentCode}
              setCode={updateCode}
              output={output}
              isRunning={isRunning}
              codeSaved={codeSaved}
              onRunCode={handleRunCode}
              onRunTests={handleRunTests}
              onSubmitCode={() => saveCode()}
              onNextSection={() => moveSection(1)}
              onPrevSection={() => moveSection(-1)}
            />
          )}
          {currentSection === 'workstyle' && (
            <PsychometricSection
              scenarios={scenarios}
              currentQuestion={workstyleQuestion}
              psychometricAnswers={psychometricAnswers}
              onAnswer={handlePsychometricAnswer}
              onPrevSection={() => moveSection(-1)}
              onSubmit={() => setConfirmOpen(true)}
              isSubmitting={isSubmitting}
              setCurrentQuestion={setWorkstyleQuestion}
              savingQuestionId={savingPsychometricId}
            />
          )}
        </div>
      </main>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Submit assessment?</DialogTitle>
            <DialogDescription>
              Submission is final. Saved responses will be scored and you will not be able to reopen the session.
            </DialogDescription>
          </DialogHeader>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
            {unanswered > 0 ? (
              <p className="flex items-start gap-2"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />You still have {unanswered} unanswered {unanswered === 1 ? 'item' : 'items'}.</p>
            ) : (
              <p className="flex items-start gap-2"><Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />Every multiple-choice and work-style item has an answer.</p>
            )}
            {isTechnical && !codeSaved && <p className="mt-2">Your latest code will be saved automatically before submission.</p>}
          </div>
          <DialogFooter className="gap-2 sm:space-x-0">
            <Button type="button" variant="outline" onClick={() => setConfirmOpen(false)} disabled={isSubmitting}>Continue working</Button>
            <Button type="button" onClick={() => handleSubmit(false)} disabled={isSubmitting}>
              {isSubmitting && <LoaderCircle className="mr-2 h-4 w-4 animate-spin" />}
              Submit assessment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AssessmentPage;
