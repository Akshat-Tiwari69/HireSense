import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Label } from '../components/ui/label';
import { Progress } from '../components/ui/progress';
import { Clock, CheckCircle, Loader2, Play, Copy, Download } from 'lucide-react';
import { mockAssessment } from '../data/mock';
import { useToast } from '../hooks/use-toast';
import Editor from '@monaco-editor/react';
import Logo from '../components/Logo';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

const AssessmentPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [searchParams] = useSearchParams();
  const candidateId = searchParams.get('candidate');
  
  const [currentSection, setCurrentSection] = useState(0);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [mcqAnswers, setMcqAnswers] = useState({});
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('javascript');
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [psychometricAnswers, setPsychometricAnswers] = useState({});
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState(null);

  // Initialize assessment data
  useEffect(() => {
    try {
      if (!mockAssessment || !mockAssessment.sections) {
        setError('Assessment data not found');
        return;
      }
      setTimeRemaining(mockAssessment.duration * 60);
      setCode(mockAssessment.sections[1]?.problem?.starterCode || '');
    } catch (err) {
      console.error('Error initializing assessment:', err);
      setError('Failed to load assessment');
    }
  }, []);

  const handleAutoSubmit = () => {
    toast({
      title: 'Time\'s up!',
      description: 'Your assessment has been automatically submitted.',
    });
    handleSubmit();
  };

  const handleRunCode = async () => {
    setIsRunning(true);
    setOutput('Running code...\n');
    
    try {
      // For demo purposes, use a simple sandbox API or evaluate locally
      // This is a mock implementation - in production use proper code execution service
      let result = '';
      
      if (language === 'javascript') {
        try {
          // Create a function from the code and run it
          const func = new Function(code);
          const consoleOutput = [];
          const originalLog = console.log;
          console.log = (...args) => {
            consoleOutput.push(args.join(' '));
          };
          
          func();
          
          console.log = originalLog;
          result = consoleOutput.length > 0 ? consoleOutput.join('\n') : 'Code executed successfully (no output)';
        } catch (err) {
          result = `Error: ${err.message}`;
        }
      } else if (language === 'python') {
        result = 'Python execution requires backend support.\n\nTo enable Python code execution:\n1. Set up a Python sandbox (e.g., Pyodide or JupyterLite)\n2. Or use a backend service like Judge0 API';
      } else {
        result = `${language} execution not yet configured in this demo.`;
      }
      
      setOutput(result);
    } catch (err) {
      setOutput(`Error executing code: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  useEffect(() => {
    // Timer countdown
    const timer = setInterval(() => {
      setTimeRemaining(prev => {
        if (prev <= 1) {
          clearInterval(timer);
          handleAutoSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const sections = mockAssessment?.sections || [];
  const totalSections = sections.length;
  const progressPercentage = totalSections > 0 ? ((currentSection + 1) / totalSections) * 100 : 0;

  const handleMCQAnswer = (questionId, answerIndex) => {
    setMcqAnswers(prev => ({ ...prev, [questionId]: answerIndex }));
  };

  const handlePsychometricAnswer = (scenarioId, answerIndex) => {
    setPsychometricAnswers(prev => ({ ...prev, [scenarioId]: answerIndex }));
  };

  const handleNextSection = () => {
    if (currentSection < totalSections - 1) {
      setCurrentSection(prev => prev + 1);
      setCurrentQuestion(0);
    }
  };

  const handlePrevSection = () => {
    if (currentSection > 0) {
      setCurrentSection(prev => prev - 1);
      setCurrentQuestion(0);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    
    // Mock submission - will be replaced with actual API call
    setTimeout(() => {
      setIsSubmitting(false);
      setSubmitted(true);
      toast({
        title: 'Assessment submitted!',
        description: 'Your responses have been recorded.',
      });
    }, 2000);
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-6">
        <Card className="w-full max-w-md shadow-2xl border-none text-center">
          <CardContent className="pt-12 pb-12">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-12 h-12 text-emerald-600" />
              </div>
            </div>
            <h2 className="text-3xl font-bold text-slate-900 mb-4">Assessment Complete!</h2>
            <p className="text-slate-600 mb-8 text-lg">
              Your assessment is complete. Final decision pending.
            </p>
            <div className="bg-indigo-50 p-4 rounded-lg mb-6">
              <p className="text-sm text-indigo-800">
                <strong>What's Next:</strong> Our team will review your responses and contact you with the final decision within 3-5 business days.
              </p>
            </div>
            <Button
              onClick={() => navigate('/')}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              Return to Home
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-6">
        <Card className="w-full max-w-md shadow-2xl border-none">
          <CardContent className="pt-12 pb-12">
            <h2 className="text-2xl font-bold text-red-600 mb-4">Error Loading Assessment</h2>
            <p className="text-slate-600 mb-6">{error}</p>
            <Button
              onClick={() => navigate('/dashboard')}
              className="w-full bg-indigo-600 hover:bg-indigo-700"
            >
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (timeRemaining === 0 && currentSection === 0 && currentQuestion === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-6">
        <Card className="w-full max-w-md shadow-2xl border-none">
          <CardContent className="pt-12 pb-12">
            <p className="text-slate-600 text-center mb-4">Loading assessment...</p>
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-indigo-600" />
          </CardContent>
        </Card>
      </div>
    );
  }

  const renderMCQSection = () => {
    const section = sections[0];
    if (!section || section.type !== 'mcq') return null;
    const question = section.questions[currentQuestion];
    if (!question) return null;

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-slate-900">
            Question {currentQuestion + 1} of {section.questions.length}
          </h3>
        </div>

        <Card className="border-2 border-indigo-200">
          <CardContent className="pt-6">
            <p className="text-lg text-slate-800 mb-6">{question.question}</p>
            <RadioGroup
              value={mcqAnswers[question.id]?.toString()}
              onValueChange={(value) => handleMCQAnswer(question.id, parseInt(value))}
            >
              <div className="space-y-3">
                {question.options.map((option, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center space-x-3 p-4 rounded-lg border-2 transition-all cursor-pointer ${
                      mcqAnswers[question.id] === idx
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50'
                    }`}
                    onClick={() => handleMCQAnswer(question.id, idx)}
                  >
                    <RadioGroupItem value={idx.toString()} id={`option-${idx}`} />
                    <Label
                      htmlFor={`option-${idx}`}
                      className="flex-1 cursor-pointer text-base"
                    >
                      {option}
                    </Label>
                  </div>
                ))}
              </div>
            </RadioGroup>
          </CardContent>
        </Card>

        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
            disabled={currentQuestion === 0}
          >
            Previous Question
          </Button>
          {currentQuestion < section.questions.length - 1 ? (
            <Button
              onClick={() => setCurrentQuestion(prev => prev + 1)}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              Next Question
            </Button>
          ) : (
            <Button
              onClick={handleNextSection}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              Next Section
            </Button>
          )}
        </div>
      </div>
    );
  };

  const renderCodingSection = () => {
    const section = sections[1];
    if (!section || section.type !== 'coding') return null;
    const problem = section.problem;
    if (!problem) return null;

    return (
      <div className="space-y-6">
        <Card className="border-2 border-indigo-200">
          <CardHeader>
            <CardTitle className="text-xl">{problem.title}</CardTitle>
            <CardDescription className="text-base">
              Time limit: {problem.timeLimit} minutes
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-slate-50 p-4 rounded-lg mb-4 whitespace-pre-line text-slate-700">
              {problem.description}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-lg">Your Solution</CardTitle>
              <div className="w-48">
                <Select value={language} onValueChange={setLanguage}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="javascript">JavaScript</SelectItem>
                    <SelectItem value="python">Python</SelectItem>
                    <SelectItem value="java">Java</SelectItem>
                    <SelectItem value="cpp">C++</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="border-2 border-slate-200 rounded-lg overflow-hidden mb-4">
              <Editor
                height="300px"
                defaultLanguage={language}
                language={language}
                value={code}
                onChange={(value) => setCode(value || '')}
                theme="vs-light"
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                }}
              />
            </div>
            
            <Button 
              onClick={handleRunCode}
              disabled={isRunning}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              <Play className="w-4 h-4 mr-2" />
              {isRunning ? 'Running...' : 'Run Code'}
            </Button>
            
            {output && (
              <div className="mt-4 bg-slate-900 text-slate-100 p-4 rounded-lg font-mono text-sm overflow-auto max-h-40">
                <p className="text-emerald-400 mb-2">$ Output:</p>
                <pre>{output}</pre>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex justify-between">
          <Button variant="outline" onClick={handlePrevSection}>
            Previous Section
          </Button>
          <Button
            onClick={handleNextSection}
            className="bg-indigo-600 hover:bg-indigo-700"
          >
            Next Section
          </Button>
        </div>
      </div>
    );
  };

  const renderPsychometricSection = () => {
    const section = sections[2];
    if (!section || section.type !== 'psychometric') return null;
    const scenario = section.scenarios[currentQuestion];
    if (!scenario) return null;

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-slate-900">
            Scenario {currentQuestion + 1} of {section.scenarios.length}
          </h3>
        </div>

        <Card className="border-2 border-indigo-200">
          <CardContent className="pt-6">
            <div className="bg-indigo-50 p-4 rounded-lg mb-6">
              <p className="text-lg text-slate-800">{scenario.scenario}</p>
            </div>
            <RadioGroup
              value={psychometricAnswers[scenario.id]?.toString()}
              onValueChange={(value) => handlePsychometricAnswer(scenario.id, parseInt(value))}
            >
              <div className="space-y-3">
                {scenario.options.map((option, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center space-x-3 p-4 rounded-lg border-2 transition-all cursor-pointer ${
                      psychometricAnswers[scenario.id] === idx
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50'
                    }`}
                    onClick={() => handlePsychometricAnswer(scenario.id, idx)}
                  >
                    <RadioGroupItem value={idx.toString()} id={`psy-option-${idx}`} />
                    <Label
                      htmlFor={`psy-option-${idx}`}
                      className="flex-1 cursor-pointer text-base"
                    >
                      {option}
                    </Label>
                  </div>
                ))}
              </div>
            </RadioGroup>
          </CardContent>
        </Card>

        <div className="flex justify-between">
          {currentQuestion > 0 ? (
            <Button
              variant="outline"
              onClick={() => setCurrentQuestion(prev => prev - 1)}
            >
              Previous Scenario
            </Button>
          ) : (
            <Button variant="outline" onClick={handlePrevSection}>
              Previous Section
            </Button>
          )}
          {currentQuestion < section.scenarios.length - 1 ? (
            <Button
              onClick={() => setCurrentQuestion(prev => prev + 1)}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              Next Scenario
            </Button>
          ) : (
            <Button
              onClick={handleSubmit}
              className="bg-emerald-600 hover:bg-emerald-700"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                'Submit Assessment'
              )}
            </Button>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 py-6 sm:py-8 px-4 sm:px-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <Card className="mb-4 sm:mb-6 border-none shadow-md">
          <CardContent className="pt-4 sm:pt-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-3">
                <Logo variant="icon" size="default" />
                <div>
                  <h1 className="text-xl sm:text-2xl font-bold text-slate-900">Technical Assessment</h1>
                  <p className="text-sm sm:text-base text-slate-600">Section {currentSection + 1} of {totalSections}: {sections[currentSection].title}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 bg-red-100 px-3 sm:px-4 py-2 rounded-lg">
                <Clock className="w-4 h-4 sm:w-5 sm:h-5 text-red-600" />
                <span className="font-mono text-base sm:text-lg font-bold text-red-600">
                  {formatTime(timeRemaining)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Progress */}
        <Card className="mb-4 sm:mb-6 border-none shadow-md">
          <CardContent className="pt-4 sm:pt-6">
            <div className="space-y-2">
              <div className="flex justify-between text-xs sm:text-sm text-slate-600">
                <span>Overall Progress</span>
                <span>{Math.round(progressPercentage)}%</span>
              </div>
              <Progress value={progressPercentage} className="h-2" />
            </div>
          </CardContent>
        </Card>

        {/* Section Content */}
        <div>
          {currentSection === 0 && renderMCQSection()}
          {currentSection === 1 && renderCodingSection()}
          {currentSection === 2 && renderPsychometricSection()}
        </div>
      </div>
    </div>
  );
};

export default AssessmentPage;
