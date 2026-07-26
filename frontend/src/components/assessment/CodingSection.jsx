import {
  Check,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  LoaderCircle,
  Play,
  Save,
  Terminal,
} from 'lucide-react';

import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { CODE_LANGUAGE_OPTIONS, getCodeLanguages } from '../../lib/assessment';

const CodingSection = ({
  problem,
  language,
  onLanguageChange,
  code,
  setCode,
  output,
  isRunning,
  codeSaved,
  onRunCode,
  onRunTests,
  onSubmitCode,
  onNextSection,
  onPrevSection,
}) => {
  if (!problem) {
    return <p className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">No coding exercise is assigned.</p>;
  }

  const visibleCases = (problem.test_cases || []).filter((testCase) => !testCase.is_hidden);
  const availableLanguages = new Set(getCodeLanguages(problem));
  const languageOptions = CODE_LANGUAGE_OPTIONS.filter(([value]) => availableLanguages.has(value));

  return (
    <section className="space-y-6" aria-labelledby="coding-heading">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">Practical exercise</p>
          <h2 id="coding-heading" className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">{problem.title}</h2>
        </div>
        <Badge variant="outline" className="capitalize">{problem.difficulty || 'Standard'}</Badge>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(17rem,0.8fr)_minmax(0,1.4fr)]">
        <aside className="space-y-5 rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-label="Problem details">
          <div>
            <h3 className="text-sm font-semibold text-slate-950">Task</h3>
            <p className="mt-2 whitespace-pre-line text-sm leading-6 text-slate-700">{problem.description}</p>
          </div>

          {problem.example && (
            <div>
              <h3 className="text-sm font-semibold text-slate-950">Example</h3>
              <pre className="mt-2 overflow-x-auto rounded-lg bg-slate-950 p-3 text-xs leading-6 text-slate-100">{problem.example}</pre>
            </div>
          )}

          {problem.constraints?.length > 0 && (
            <div>
              <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-950">
                <CircleAlert className="h-4 w-4 text-slate-500" aria-hidden="true" />
                Constraints
              </h3>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm leading-6 text-slate-600">
                {problem.constraints.map((constraint) => <li key={constraint}>{constraint}</li>)}
              </ul>
            </div>
          )}

          {visibleCases.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-slate-950">Visible examples</h3>
              <div className="mt-2 space-y-2">
                {visibleCases.map((testCase, index) => (
                  <div key={`${testCase.input}-${index}`} className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs">
                    <p><span className="font-medium text-slate-500">Input:</span> <code className="text-slate-900">{testCase.input}</code></p>
                    <p className="mt-1"><span className="font-medium text-slate-500">Expected:</span> <code className="text-slate-900">{testCase.expected}</code></p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        <div className="min-w-0 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-slate-950">Solution</p>
              <p className="text-xs text-slate-500">Changes are saved only when you select Save solution.</p>
            </div>
            <Select value={language} onValueChange={onLanguageChange} disabled={!languageOptions.length}>
              <SelectTrigger className="w-40" aria-label="Programming language">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {languageOptions.map(([value, label]) => <SelectItem key={value} value={value}>{label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>

          <textarea
            data-code-editor="true"
            value={code}
            onChange={(event) => setCode(event.target.value)}
            spellCheck="false"
            rows={19}
            maxLength={100000}
            aria-label="Code solution"
            className="block w-full resize-y border-0 bg-slate-950 px-4 py-4 font-mono text-[13px] leading-6 text-slate-100 outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
          />

          <div className="flex flex-wrap items-center gap-2 border-t border-slate-200 px-4 py-3">
            <Button type="button" variant="outline" onClick={onRunCode} disabled={isRunning || !code.trim()}>
              {isRunning ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
              Run code
            </Button>
            {visibleCases.length > 0 && (
              <Button type="button" variant="outline" onClick={() => onRunTests(visibleCases)} disabled={isRunning || !code.trim()}>
                <Check className="mr-2 h-4 w-4" />
                Run examples
              </Button>
            )}
            <Button type="button" onClick={onSubmitCode} disabled={isRunning || !code.trim() || codeSaved}>
              <Save className="mr-2 h-4 w-4" />
              {codeSaved ? 'Solution saved' : 'Save solution'}
            </Button>
          </div>

          {output && (
            <div className="border-t border-slate-200 bg-slate-950 p-4" aria-live="polite">
              <p className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.12em] text-slate-400">
                <Terminal className="h-4 w-4" aria-hidden="true" /> Output
              </p>
              <pre className="mt-2 max-h-56 overflow-auto whitespace-pre-wrap break-words font-mono text-xs leading-6 text-slate-100">{output}</pre>
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-col-reverse justify-between gap-3 sm:flex-row">
        <Button type="button" variant="outline" onClick={onPrevSection}>
          <ChevronLeft className="mr-2 h-4 w-4" />
          Previous section
        </Button>
        <Button type="button" onClick={onNextSection}>
          Continue
          <ChevronRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </section>
  );
};

export default CodingSection;
