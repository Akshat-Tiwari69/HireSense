import React from 'react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import Editor from '@monaco-editor/react';
import {
  Code, AlertTriangle, Zap, Terminal, Play, CheckCircle, Loader2, ChevronLeft, ChevronRight
} from 'lucide-react';

const CodingSection = ({
  problem,
  language,
  setLanguage,
  code,
  setCode,
  output,
  isRunning,
  testsPassed,
  codeSaved,
  onRunCode,
  onRunTests,
  onSubmitCode,
  onNextSection,
  onPrevSection,
  getStarterCode,
}) => {
  if (!problem) {
    return <p className="text-slate-400 text-center py-8">No coding problem available</p>;
  }

  return (
    <div className="space-y-6">
      {/* Problem Description */}
      <Card className="bg-gradient-to-br from-slate-800 to-slate-900 shadow-xl border-slate-700 hover:shadow-2xl transition-all duration-300">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-white flex items-center gap-3">
              <Code className="w-6 h-6 text-emerald-400" />
              <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                {problem.title}
              </span>
            </CardTitle>
            <Badge className={`${
              problem.difficulty === 'Easy' ? 'bg-emerald-600' :
              problem.difficulty === 'Medium' ? 'bg-amber-600' : 'bg-red-600'
            }`}>
              {problem.difficulty}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-slate-700/40 p-5 rounded-lg border border-slate-600">
            <p className="text-slate-200 whitespace-pre-line leading-relaxed">{problem.description}</p>
          </div>

          {problem.example && (
            <div className="bg-indigo-900/30 border border-indigo-700/50 p-5 rounded-lg">
              <p className="text-indigo-300 font-semibold mb-3 flex items-center gap-2">
                <Zap className="w-4 h-4" /> Example:
              </p>
              <pre className="text-slate-300 text-sm font-mono bg-slate-900/50 p-3 rounded border border-slate-700 overflow-x-auto">
                {problem.example}
              </pre>
            </div>
          )}

          {problem.constraints && problem.constraints.length > 0 && (
            <div>
              <p className="text-slate-300 font-semibold mb-3 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4" /> Constraints:
              </p>
              <ul className="text-slate-400 text-sm space-y-2 pl-6">
                {problem.constraints.map((c, idx) => (
                  <li key={idx} className="list-disc">{c}</li>
                ))}
              </ul>
            </div>
          )}

          {problem.test_cases && problem.test_cases.length > 0 && (
            <div>
              <p className="text-slate-300 font-semibold mb-3">Test Cases:</p>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {problem.test_cases.filter(tc => !tc.is_hidden).map((tc, idx) => (
                  <div key={idx} className="bg-slate-700/50 border border-slate-600 p-4 rounded-lg text-sm">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-slate-400">Input:</span>
                        <code className="text-emerald-400 ml-2 font-mono">{tc.input}</code>
                      </div>
                      <div>
                        <span className="text-slate-400">Expected:</span>
                        <code className="text-cyan-400 ml-2 font-mono">{tc.expected}</code>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Code Editor */}
      <Card className="bg-gradient-to-br from-slate-800 to-slate-900 shadow-xl border-slate-700 hover:shadow-2xl transition-all duration-300">
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle className="text-white">Your Solution</CardTitle>
            <Select value={language} onValueChange={(val) => {
              setLanguage(val);
              setCode(getStarterCode(problem, val));
            }}>
              <SelectTrigger className="w-48 bg-slate-700 border-slate-600 text-white hover:bg-slate-600">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-800 border-slate-700">
                <SelectItem value="javascript">JavaScript</SelectItem>
                <SelectItem value="python">Python</SelectItem>
                <SelectItem value="java">Java</SelectItem>
                <SelectItem value="cpp">C++</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="border-2 border-slate-700 rounded-lg overflow-hidden shadow-lg">
            <Editor
              height="380px"
              language={language}
              value={code}
              onChange={(value) => setCode(value || '')}
              theme="vs-dark"
              options={{
                minimap: { enabled: false },
                fontSize: 13,
                lineNumbers: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
                wordWrap: 'on',
                padding: { top: 12, bottom: 12 }
              }}
            />
          </div>

          <div className="flex gap-3">
            <Button
              onClick={onRunCode}
              disabled={isRunning}
              className="bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 gap-2 font-semibold"
            >
              {isRunning ? <><Loader2 className="w-4 h-4 animate-spin" />Executing...</> : <><Play className="w-4 h-4" />Run Code</>}
            </Button>

            {problem.test_cases && problem.test_cases.length > 0 && (
              <Button
                onClick={() => onRunTests(problem.test_cases)}
                disabled={isRunning}
                variant="outline"
                className="border-indigo-600 text-indigo-300 hover:bg-indigo-900/50 hover:text-indigo-100 gap-2 font-semibold"
              >
                {isRunning ? <><Loader2 className="w-4 h-4 animate-spin" />Testing...</> : <><CheckCircle className="w-4 h-4" />Run Tests</>}
              </Button>
            )}

            {testsPassed && !codeSaved && (
              <Button
                onClick={onSubmitCode}
                disabled={isRunning}
                className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 gap-2 font-semibold animate-pulse"
              >
                <CheckCircle className="w-4 h-4" />Submit Code
              </Button>
            )}

            {codeSaved && (
              <Button disabled className="bg-green-800 text-green-200 gap-2 font-semibold cursor-default">
                <CheckCircle className="w-4 h-4" />Code Saved
              </Button>
            )}
          </div>

          {output && (
            <div className="bg-slate-900/80 border-2 border-slate-700 rounded-lg p-4 font-mono text-sm overflow-auto max-h-56">
              <div className="text-emerald-400 font-semibold mb-2 flex items-center gap-2">
                <Terminal className="w-4 h-4" /> Output:
              </div>
              <pre className="text-slate-300 whitespace-pre-wrap break-words">{output}</pre>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-between gap-3 pt-4">
        <Button
          variant="outline"
          onClick={onPrevSection}
          className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white gap-2"
        >
          <ChevronLeft className="w-4 h-4" /> Previous Section
        </Button>
        <Button
          onClick={onNextSection}
          className="bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 gap-2"
        >
          Next Section <ChevronRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};

export default CodingSection;
