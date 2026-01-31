import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Label } from '../components/ui/label';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import { 
  Clock, CheckCircle, Loader2, Play, AlertTriangle, Video, VideoOff,
  Eye, ShieldAlert, Timer, Code, Brain, FileText
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import Editor from '@monaco-editor/react';
import Logo from '../components/Logo';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { api } from '../services/api';

// Piston API for code execution (free, no API key needed)
const PISTON_API = 'https://emkc.org/api/v2/piston';

const LANGUAGE_CONFIG = {
  javascript: { runtime: 'javascript', version: '18.15.0', extension: 'js' },
  python: { runtime: 'python', version: '3.10.0', extension: 'py' },
  java: { runtime: 'java', version: '15.0.2', extension: 'java' },
  cpp: { runtime: 'c++', version: '10.2.0', extension: 'cpp' },
  c: { runtime: 'c', version: '10.2.0', extension: 'c' },
};

const AssessmentPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { token } = useParams();
  
  // Assessment state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [assessmentData, setAssessmentData] = useState(null);
  const [assessmentId, setAssessmentId] = useState(null);
  const [candidateName, setCandidateName] = useState('');
  
  // Section navigation
  const [currentSection, setCurrentSection] = useState(0);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  
  // Answers
  const [mcqAnswers, setMcqAnswers] = useState({});
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('javascript');
  const [output, setOutput] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [psychometricAnswers, setPsychometricAnswers] = useState({});
  
  // Timer
  const [timeRemaining, setTimeRemaining] = useState(3600); // 60 minutes default
  
  // Submission
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  
  // Proctoring
  const [proctoringEnabled, setProctoringEnabled] = useState(true);
  const [cameraStream, setCameraStream] = useState(null);
  const [cameraError, setCameraError] = useState(null);
  const [faceDetected, setFaceDetected] = useState(true);
  const [faceCount, setFaceCount] = useState(1);
  const [violationCount, setViolationCount] = useState(0);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const faceDetectionIntervalRef = useRef(null);
  const faceDetectorRef = useRef(null);
  const lastViolationRef = useRef({});
  const lastFaceCountRef = useRef(null);

  // Verify token and load assessment
  useEffect(() => {
    if (!token) {
      setError('No assessment token provided. Please use the link from your invitation email.');
      setLoading(false);
      return;
    }
    
    verifyAndLoadAssessment();
  }, [token]);

  // Log submitted state changes
  useEffect(() => {
    console.log('Submitted state changed to:', submitted);
    if (submitted) {
      console.log('RENDERING COMPLETION SCREEN - Assessment successfully submitted!');
    }
  }, [submitted]);

  const verifyAndLoadAssessment = async () => {
    try {
      // First verify the token
      const verifyRes = await api.get(`/api/interviewee/assessment/verify/${token}`);
      const verifyData = verifyRes.data.data;
      
      setCandidateName(verifyData.candidate_name);
      setProctoringEnabled(verifyData.proctoring_enabled);
      
      if (!verifyData.can_start && !verifyData.already_started) {
        setError(`Assessment not available yet. Scheduled for ${new Date(verifyData.scheduled_time).toLocaleString()}. You can start ${verifyData.minutes_until_start > 0 ? 'in ' + verifyData.minutes_until_start + ' minutes' : 'within the 30-minute window'}.`);
        setLoading(false);
        return;
      }
      
      // Start or resume assessment
      const startRes = await api.post(`/api/interviewee/assessment/start-by-token/${token}`);
      const {data} = startRes.data;
      
      setAssessmentData(data);
      setAssessmentId(data.assessment_id);
      setTimeRemaining(data.duration_minutes * 60);
      
      // Set initial code
      if (data.coding_problem) {
        setCode(getStarterCode(data.coding_problem, 'javascript'));
      }
      
      setLoading(false);
      
      // Start proctoring if enabled
      if (verifyData.proctoring_enabled) {
        startProctoring();
      }
      
    } catch (err) {
      const message = err?.response?.data?.message || 'Failed to load assessment';
      setError(message);
      setLoading(false);
    }
  };

  const getStarterCode = (problem, lang) => {
    // Use AI-generated starter code if available
    if (problem.starter_code && problem.starter_code[lang]) {
      return problem.starter_code[lang];
    }
    
    // Fallback templates
    const templates = {
      javascript: `// ${problem.title}\n// ${problem.description?.slice(0, 100) || ''}\n\nfunction solution(input) {\n  // Write your code here\n  \n  return result;\n}\n\n// Test your solution\nconsole.log(solution("test"));`,
      python: `# ${problem.title}\n# ${problem.description?.slice(0, 100) || ''}\n\ndef solution(input):\n    # Write your code here\n    \n    return result\n\n# Test your solution\nprint(solution("test"))`,
      java: `// ${problem.title}\n// ${problem.description?.slice(0, 100) || ''}\n\npublic class Main {\n    public static void main(String[] args) {\n        // Write your code here\n        System.out.println("Hello, World!");\n    }\n}`,
      cpp: `// ${problem.title}\n// ${problem.description?.slice(0, 100) || ''}\n\n#include <iostream>\nusing namespace std;\n\nint main() {\n    // Write your code here\n    cout << "Hello, World!" << endl;\n    return 0;\n}`,
    };
    return templates[lang] || templates.javascript;
  };

  // Camera and face detection
  const startProctoring = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'user', width: 320, height: 240 } 
      });
      setCameraStream(stream);
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      
      // Start basic face detection using canvas analysis
      startFaceDetection();
      
    } catch (err) {
      console.error('Camera error:', err);
      setCameraError('Camera access denied. Proctoring cannot monitor without camera access.');
      reportViolation('camera_denied', 'Candidate denied camera access', 'high');
    }
  };

  const startFaceDetection = () => {
    // Use FaceDetector API when available; fallback to brightness analysis
    if (window.FaceDetector) {
      faceDetectorRef.current = new window.FaceDetector({ fastMode: true, maxDetectedFaces: 3 });
    }

    faceDetectionIntervalRef.current = setInterval(() => {
      if (!videoRef.current || !canvasRef.current) return;
      
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      
      canvas.width = video.videoWidth || 320;
      canvas.height = video.videoHeight || 240;
      ctx.drawImage(video, 0, 0);
      
      try {
        if (faceDetectorRef.current) {
          faceDetectorRef.current.detect(video).then((faces) => {
            const count = faces?.length || 0;
            setFaceCount(count || 0);

            if (count === 0) {
              setFaceDetected(false);
              reportViolation('no_face', 'No face detected in camera', 'high', 15000);
            } else if (count > 1) {
              setFaceDetected(true);
              reportViolation('multiple_faces', 'Multiple faces detected in camera', 'critical', 15000);
            } else {
              setFaceDetected(true);
            }

            lastFaceCountRef.current = count;
          }).catch(() => {
            // Ignore detector errors
          });
          return;
        }

        // Fallback: Get image data and analyze for face-like patterns
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const detected = analyzeForFace(imageData);

        if (!detected && faceDetected) {
          setFaceDetected(false);
          reportViolation('no_face', 'No face detected in camera', 'medium', 15000);
        } else if (detected && !faceDetected) {
          setFaceDetected(true);
        }
      } catch (e) {
        // Canvas tainted or other error
      }
    }, 3000); // Check every 3 seconds
  };

  const analyzeForFace = (imageData) => {
    // Simple brightness analysis - real production should use ML
    // This checks if there's a significant brightness pattern (face-shaped)
    const {data} = imageData;
    let skinTonePixels = 0;
    const totalPixels = data.length / 4;
    
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      
      // Basic skin tone detection (very rough approximation)
      if (r > 95 && g > 40 && b > 20 && 
          r > g && r > b && 
          Math.abs(r - g) > 15 && 
          r - b > 15) {
        skinTonePixels++;
      }
    }
    
    // If more than 5% of pixels are skin-tone, consider face detected
    return (skinTonePixels / totalPixels) > 0.05;
  };

  const shouldReportViolation = (type, cooldownMs = 30000) => {
    const now = Date.now();
    const last = lastViolationRef.current[type] || 0;
    if (now - last < cooldownMs) return false;
    lastViolationRef.current[type] = now;
    return true;
  };

  const reportViolation = async (type, description, severity = 'medium', cooldownMs = 30000) => {
    if (!assessmentId) return;
    if (!shouldReportViolation(type, cooldownMs)) return;
    
    try {
      const res = await api.post(`/api/interviewee/assessment/${assessmentId}/violation`, {
        violation_type: type,
        description: description,
        severity: severity
      });
      
      setViolationCount(res.data.data.total_violations);
      
      toast({
        variant: 'destructive',
        title: 'Warning',
        description: `Proctoring violation detected: ${description}`,
      });
    } catch (err) {
      console.error('Failed to report violation:', err);
    }
  };

  // Tab visibility and window focus monitoring
  useEffect(() => {
    if (!proctoringEnabled) return;

    const handleVisibilityChange = () => {
      if (document.hidden && assessmentId && !submitted) {
        reportViolation('tab_switch', 'Candidate switched away from assessment tab', 'high', 15000);
      }
    };

    const handleWindowBlur = () => {
      if (assessmentId && !submitted) {
        reportViolation('window_blur', 'Assessment window lost focus', 'high', 15000);
      }
    };

    const handlePaste = (event) => {
      event.preventDefault();
      reportViolation('paste_detected', 'Paste action detected', 'high', 10000);
    };

    const handleCopy = (event) => {
      event.preventDefault();
      reportViolation('copy_detected', 'Copy action detected', 'medium', 10000);
    };

    const handleCut = (event) => {
      event.preventDefault();
      reportViolation('cut_detected', 'Cut action detected', 'medium', 10000);
    };

    const handleKeyDown = (event) => {
      const key = event.key?.toLowerCase();
      if ((event.ctrlKey || event.metaKey) && key === 'v') {
        event.preventDefault();
        reportViolation('paste_shortcut', 'Ctrl/Cmd+V detected', 'high', 10000);
      }
      if (key === 'tab') {
        reportViolation('tab_key', 'Tab key pressed during assessment', 'low', 5000);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleWindowBlur);
    document.addEventListener('paste', handlePaste);
    document.addEventListener('copy', handleCopy);
    document.addEventListener('cut', handleCut);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleWindowBlur);
      document.removeEventListener('paste', handlePaste);
      document.removeEventListener('copy', handleCopy);
      document.removeEventListener('cut', handleCut);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [assessmentId, submitted, proctoringEnabled]);

  // Timer
  useEffect(() => {
    if (loading || submitted || !assessmentData) return;
    
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
  }, [loading, submitted, assessmentData]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
      if (faceDetectionIntervalRef.current) {
        clearInterval(faceDetectionIntervalRef.current);
      }
    };
  }, [cameraStream]);

  const handleAutoSubmit = () => {
    toast({
      title: "Time's up!",
      description: 'Your assessment has been automatically submitted.',
    });
    handleSubmit();
  };

  // Code execution using Piston API
  const handleRunCode = async () => {
    setIsRunning(true);
    setOutput('Running code...\n');
    
    try {
      const langConfig = LANGUAGE_CONFIG[language];
      if (!langConfig) {
        setOutput('Language not supported for execution.');
        setIsRunning(false);
        return;
      }
      
      const response = await fetch(`${PISTON_API}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language: langConfig.runtime,
          version: langConfig.version,
          files: [{
            name: `main.${langConfig.extension}`,
            content: code
          }]
        })
      });
      
      const result = await response.json();
      
      if (result.run) {
        const stdout = result.run.stdout || '';
        const stderr = result.run.stderr || '';
        const output = stdout + (stderr ? `\nErrors:\n${stderr}` : '');
        setOutput(output || 'Code executed successfully (no output)');
      } else if (result.message) {
        setOutput(`Error: ${result.message}`);
      } else {
        setOutput('Execution failed. Please try again.');
      }
    } catch (err) {
      setOutput(`Execution error: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleRunTestCases = async (testCases) => {
    setIsRunning(true);
    setOutput('Running test cases...\n\n');
    
    const langConfig = LANGUAGE_CONFIG[language];
    if (!langConfig) {
      setOutput('Language not supported for execution.');
      setIsRunning(false);
      return;
    }
    
    let results = [];
    let passed = 0;
    let failed = 0;
    
    // Filter visible test cases only
    const visibleTests = testCases.filter(tc => !tc.is_hidden);
    
    for (let i = 0; i < visibleTests.length; i++) {
      const tc = visibleTests[i];
      
      try {
        // Create test wrapper code based on language
        let testCode = code;
        
        // Add test execution based on language
        if (language === 'javascript') {
          testCode += `\n\n// Test execution\nconsole.log(JSON.stringify(${tc.input.includes(',') ? `twoSum(${tc.input})` : `solution(${tc.input})`}));`;
        } else if (language === 'python') {
          testCode += `\n\n# Test execution\nprint(${tc.input.includes(',') ? `two_sum(${tc.input})` : `solution(${tc.input})`})`;
        }
        
        const response = await fetch(`${PISTON_API}/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            language: langConfig.runtime,
            version: langConfig.version,
            files: [{
              name: `main.${langConfig.extension}`,
              content: testCode
            }]
          })
        });
        
        const result = await response.json();
        
        if (result.run) {
          const stdout = (result.run.stdout || '').trim();
          const stderr = result.run.stderr || '';
          
          // Simple comparison (could be improved)
          const expectedClean = tc.expected.replace(/'/g, '"').replace(/True/g, 'true').replace(/False/g, 'false');
          const actualClean = stdout.replace(/'/g, '"');
          
          const isPassed = actualClean === expectedClean || stdout === tc.expected;
          
          if (isPassed) {
            passed++;
            results.push(`✅ Test ${i + 1}: PASSED\n   Input: ${tc.input}\n   Expected: ${tc.expected}\n   Got: ${stdout}\n`);
          } else {
            failed++;
            results.push(`❌ Test ${i + 1}: FAILED\n   Input: ${tc.input}\n   Expected: ${tc.expected}\n   Got: ${stdout}${stderr ? `\n   Error: ${stderr}` : ''}\n`);
          }
        } else {
          failed++;
          results.push(`❌ Test ${i + 1}: ERROR\n   ${result.message || 'Execution failed'}\n`);
        }
      } catch (err) {
        failed++;
        results.push(`❌ Test ${i + 1}: ERROR\n   ${err.message}\n`);
      }
    }
    
    const summary = `\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📊 Results: ${passed}/${visibleTests.length} tests passed\n${passed === visibleTests.length ? '🎉 All tests passed!' : `⚠️ ${failed} test(s) failed`}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    
    setOutput(results.join('\n') + summary);
    setIsRunning(false);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleMCQAnswer = async (questionId, answerIndex) => {
    setMcqAnswers(prev => ({ ...prev, [questionId]: answerIndex }));
    
    // Auto-save the answer to backend
    try {
      const answerLetter = ['A', 'B', 'C', 'D'][answerIndex];
      await api.post(`/api/interviewee/assessment/${assessmentId}/submit-answer`, {
        type: 'mcq',
        questionId,
        answer: answerLetter,
        timeSpent: 0 // Could track actual time if needed
      });
    } catch (err) {
      console.error('Failed to save MCQ answer:', err);
    }
  };

  const handlePsychometricAnswer = async (scenarioId, answerIndex) => {
    setPsychometricAnswers(prev => ({ ...prev, [scenarioId]: answerIndex }));
    
    // Auto-save the answer to backend
    try {
      const scenario = assessmentData?.psychometric_scenarios?.find(s => s.id === scenarioId);
      if (scenario) {
        await api.post(`/api/interviewee/assessment/${assessmentId}/submit-answer`, {
          type: 'psychometric',
          questionId: scenarioId,
          trait: scenario.trait,
          score: answerIndex + 1, // Convert 0-9 index to 1-10 score
        });
      }
    } catch (err) {
      console.error('Failed to save psychometric answer:', err);
    }
  };

  const handleNextSection = () => {
    if (currentSection < 2) {
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
    
    try {
      console.log('Starting assessment submission for assessment ID:', assessmentId);
      
      // Save coding solution before submitting
      if (code && code.trim()) {
        console.log('Saving coding solution...');
        await api.post(`/api/interviewee/assessment/${assessmentId}/submit-answer`, {
          type: 'coding',
          questionId: 1, // Assuming single coding problem
          code: code,
          language: language,
          testsPassed: 0, // Would need to track this from test results
          totalTests: 0
        });
        console.log('Coding solution saved');
      }
      
      // Stop proctoring
      console.log('Stopping camera and proctoring...');
      if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
      }
      if (faceDetectionIntervalRef.current) {
        clearInterval(faceDetectionIntervalRef.current);
      }
      
      // Complete assessment (backend calculates scores)
      console.log('Completing assessment...');
      const response = await api.post(`/api/interviewee/assessment/${assessmentId}/complete`);
      console.log('Assessment completion response:', response);
      console.log('Response data:', response.data);
      console.log('Response status:', response.data.status);
      
      if (response.data.status === 'success') {
        console.log('✓ Assessment status is success');
        console.log('✓ Current submitted state before setSubmitted:', submitted);
        console.log('✓ About to call setSubmitted(true)');
        
        // Use a callback to verify state was set
        setSubmitted(true);
        
        console.log('✓ Called setSubmitted(true)');
        console.log('✓ Current submitted state in same block:', submitted); // Will still be false here (closure)
        
        toast({
          title: 'Assessment submitted!',
          description: 'Your responses have been recorded.',
        });
      } else {
        console.error('❌ Assessment status is not success:', response.data.status);
        throw new Error(response.data.message || 'Unknown error');
      }
    } catch (err) {
      console.error('❌ Submission error:', err);
      console.error('❌ Error response:', err.response?.data);
      console.error('❌ Error message:', err.message);
      toast({
        variant: 'destructive',
        title: 'Submission Error',
        description: err.response?.data?.message || 'Failed to submit. Please try again.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 flex items-center justify-center p-6">
        <Card className="w-full max-w-md bg-slate-800/50 border-slate-700">
          <CardContent className="pt-12 pb-12 text-center">
            <Loader2 className="w-12 h-12 animate-spin mx-auto text-indigo-400 mb-4" />
            <p className="text-white text-lg">Loading your assessment...</p>
            <p className="text-slate-400 text-sm mt-2">Please wait while we verify your access</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 flex items-center justify-center p-6">
        <Card className="w-full max-w-md bg-slate-800/50 border-slate-700">
          <CardContent className="pt-12 pb-12 text-center">
            <ShieldAlert className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-4">Assessment Unavailable</h2>
            <p className="text-slate-300 mb-6">{error}</p>
            <Button onClick={() => navigate('/')} className="bg-indigo-600 hover:bg-indigo-700">
              Return to Home
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Submitted state
  if (submitted) {
    // Auto-redirect after 5 seconds
    useEffect(() => {
      const timer = setTimeout(() => {
        console.log('Auto-redirecting to home after assessment submission');
        navigate('/');
      }, 5000);
      return () => clearTimeout(timer);
    }, [navigate]);

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 flex items-center justify-center p-6">
        <Card className="w-full max-w-md bg-slate-800/50 border-slate-700 text-center">
          <CardContent className="pt-12 pb-12">
            <div className="w-20 h-20 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-12 h-12 text-emerald-400" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">Assessment Complete!</h2>
            <p className="text-slate-300 mb-8 text-lg">
              Thank you, {candidateName}. Your assessment has been submitted successfully.
            </p>
            <div className="bg-indigo-900/50 p-4 rounded-lg mb-6">
              <p className="text-sm text-indigo-200">
                <strong>What's Next:</strong> Our team will review your responses and contact you with the final decision within 3-5 business days.
              </p>
            </div>
            <p className="text-slate-400 text-xs mb-4">
              Redirecting to home page in 5 seconds...
            </p>
            <Button onClick={() => navigate('/')} className="bg-indigo-600 hover:bg-indigo-700">
              Return to Home Now
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const sections = ['MCQ', 'Coding', 'Psychometric'];
  const progressPercentage = ((currentSection + 1) / 3) * 100;

  const renderMCQSection = () => {
    const questions = assessmentData?.mcq_questions || [];
    if (questions.length === 0) return <p className="text-slate-400">No questions available</p>;
    
    const question = questions[currentQuestion];
    if (!question) return null;

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-white">
            Question {currentQuestion + 1} of {questions.length}
          </h3>
          <Badge className="bg-indigo-600">{question.category}</Badge>
        </div>

        <Card className="bg-slate-800/50 border-slate-600">
          <CardContent className="pt-6">
            <p className="text-lg text-white mb-6">{question.question}</p>
            <RadioGroup
              value={mcqAnswers[question.id] !== undefined ? mcqAnswers[question.id].toString() : ''}
              onValueChange={(value) => handleMCQAnswer(question.id, parseInt(value))}
            >
              <div className="space-y-3">
                {question.options.map((option, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center space-x-3 p-4 rounded-lg border-2 transition-all cursor-pointer ${
                      mcqAnswers[question.id] === idx
                        ? 'border-indigo-500 bg-indigo-500/20'
                        : 'border-slate-600 hover:border-indigo-400 hover:bg-slate-700/50'
                    }`}
                    onClick={() => handleMCQAnswer(question.id, idx)}
                  >
                    <RadioGroupItem value={idx.toString()} id={`option-${idx}`} className="border-slate-400" />
                    <Label htmlFor={`option-${idx}`} className="flex-1 cursor-pointer text-slate-200">
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
            className="border-slate-600 text-slate-300 hover:bg-slate-700"
          >
            Previous
          </Button>
          {currentQuestion < questions.length - 1 ? (
            <Button onClick={() => setCurrentQuestion(prev => prev + 1)} className="bg-indigo-600 hover:bg-indigo-700">
              Next Question
            </Button>
          ) : (
            <Button onClick={handleNextSection} className="bg-indigo-600 hover:bg-indigo-700">
              Next Section →
            </Button>
          )}
        </div>
      </div>
    );
  };

  const renderCodingSection = () => {
    const problem = assessmentData?.coding_problem;
    if (!problem) return <p className="text-slate-400">No coding problem available</p>;

    return (
      <div className="space-y-6">
        <Card className="bg-slate-800/50 border-slate-600">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Code className="w-5 h-5 text-indigo-400" />
              {problem.title}
            </CardTitle>
            <CardDescription className="text-slate-400">
              Difficulty: <Badge className="bg-amber-600 ml-1">{problem.difficulty}</Badge>
              {assessmentData?.ai_generated && (
                <Badge className="bg-purple-600 ml-2">AI Generated</Badge>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-slate-900/50 p-4 rounded-lg text-slate-300 whitespace-pre-line">
              {problem.description}
            </div>
            {problem.example && (
              <div className="mt-4 bg-indigo-900/30 p-4 rounded-lg">
                <p className="text-indigo-300 font-semibold mb-2">Example:</p>
                <pre className="text-slate-300 text-sm">{problem.example}</pre>
              </div>
            )}
            
            {/* Constraints */}
            {problem.constraints && problem.constraints.length > 0 && (
              <div className="mt-4">
                <p className="text-slate-400 font-semibold mb-2">Constraints:</p>
                <ul className="text-slate-300 text-sm list-disc list-inside">
                  {problem.constraints.map((c, idx) => (
                    <li key={idx}>{c}</li>
                  ))}
                </ul>
              </div>
            )}
            
            {/* Test Cases */}
            {problem.test_cases && problem.test_cases.length > 0 && (
              <div className="mt-4">
                <p className="text-slate-400 font-semibold mb-2">Test Cases:</p>
                <div className="space-y-2">
                  {problem.test_cases.filter(tc => !tc.is_hidden).map((tc, idx) => (
                    <div key={idx} className="bg-slate-900/50 p-3 rounded-lg text-sm">
                      <div className="flex gap-4">
                        <span className="text-slate-400">Input:</span>
                        <code className="text-emerald-400">{tc.input}</code>
                      </div>
                      <div className="flex gap-4">
                        <span className="text-slate-400">Expected:</span>
                        <code className="text-blue-400">{tc.expected}</code>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Hints */}
            {problem.hints && problem.hints.length > 0 && (
              <details className="mt-4">
                <summary className="text-amber-400 cursor-pointer hover:text-amber-300">
                  💡 Show Hints
                </summary>
                <ul className="mt-2 text-slate-300 text-sm list-disc list-inside pl-4">
                  {problem.hints.map((hint, idx) => (
                    <li key={idx}>{hint}</li>
                  ))}
                </ul>
              </details>
            )}
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-600">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-white">Your Solution</CardTitle>
              <Select value={language} onValueChange={(val) => {
                setLanguage(val);
                setCode(getStarterCode(problem, val));
              }}>
                <SelectTrigger className="w-40 bg-slate-700 border-slate-600 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-600">
                  <SelectItem value="javascript">JavaScript</SelectItem>
                  <SelectItem value="python">Python</SelectItem>
                  <SelectItem value="java">Java</SelectItem>
                  <SelectItem value="cpp">C++</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            <div className="border-2 border-slate-600 rounded-lg overflow-hidden mb-4">
              <Editor
                height="350px"
                language={language}
                value={code}
                onChange={(value) => setCode(value || '')}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  lineNumbers: 'on',
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                }}
              />
            </div>
            
            <div className="flex gap-2">
              <Button 
                onClick={handleRunCode}
                disabled={isRunning}
                className="bg-emerald-600 hover:bg-emerald-700"
              >
                <Play className="w-4 h-4 mr-2" />
                {isRunning ? 'Running...' : 'Run Code'}
              </Button>
              {problem.test_cases && problem.test_cases.length > 0 && (
                <Button 
                  onClick={() => handleRunTestCases(problem.test_cases)}
                  disabled={isRunning}
                  variant="outline"
                  className="border-indigo-500 text-indigo-400 hover:bg-indigo-900/50"
                >
                  {isRunning ? 'Testing...' : 'Run Test Cases'}
                </Button>
              )}
            </div>
            
            {output && (
              <div className="mt-4 bg-slate-900 text-slate-100 p-4 rounded-lg font-mono text-sm overflow-auto max-h-48">
                <p className="text-emerald-400 mb-2">$ Output:</p>
                <pre className="whitespace-pre-wrap">{output}</pre>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex justify-between">
          <Button variant="outline" onClick={handlePrevSection} className="border-slate-600 text-slate-300 hover:bg-slate-700">
            ← Previous Section
          </Button>
          <Button onClick={handleNextSection} className="bg-indigo-600 hover:bg-indigo-700">
            Next Section →
          </Button>
        </div>
      </div>
    );
  };

  const renderPsychometricSection = () => {
    const scenarios = assessmentData?.psychometric_scenarios || [];
    if (scenarios.length === 0) return <p className="text-slate-400">No scenarios available</p>;
    
    const scenario = scenarios[currentQuestion];
    if (!scenario) return null;

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-white flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-400" />
            Scenario {currentQuestion + 1} of {scenarios.length}
          </h3>
        </div>

        <Card className="bg-slate-800/50 border-slate-600">
          <CardContent className="pt-6">
            <div className="bg-purple-900/30 p-4 rounded-lg mb-6">
              <p className="text-lg text-white">{scenario.scenario}</p>
            </div>
            <RadioGroup
              value={psychometricAnswers[scenario.id] !== undefined ? psychometricAnswers[scenario.id].toString() : ''}
              onValueChange={(value) => handlePsychometricAnswer(scenario.id, parseInt(value))}
            >
              <div className="space-y-3">
                {scenario.options.map((option, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center space-x-3 p-4 rounded-lg border-2 transition-all cursor-pointer ${
                      psychometricAnswers[scenario.id] === idx
                        ? 'border-purple-500 bg-purple-500/20'
                        : 'border-slate-600 hover:border-purple-400 hover:bg-slate-700/50'
                    }`}
                    onClick={() => handlePsychometricAnswer(scenario.id, idx)}
                  >
                    <RadioGroupItem value={idx.toString()} id={`psy-${idx}`} className="border-slate-400" />
                    <Label htmlFor={`psy-${idx}`} className="flex-1 cursor-pointer text-slate-200">
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
            <Button variant="outline" onClick={() => setCurrentQuestion(prev => prev - 1)} className="border-slate-600 text-slate-300 hover:bg-slate-700">
              Previous Scenario
            </Button>
          ) : (
            <Button variant="outline" onClick={handlePrevSection} className="border-slate-600 text-slate-300 hover:bg-slate-700">
              ← Previous Section
            </Button>
          )}
          {currentQuestion < scenarios.length - 1 ? (
            <Button onClick={() => setCurrentQuestion(prev => prev + 1)} className="bg-indigo-600 hover:bg-indigo-700">
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 py-6 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <Card className="mb-6 bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-3">
                <Logo variant="icon" size="default" />
                <div>
                  <h1 className="text-xl font-bold text-white">Technical Assessment</h1>
                  <p className="text-slate-400">Welcome, {candidateName}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                {/* Proctoring Status */}
                {proctoringEnabled && (
                  <div className="flex items-center gap-2">
                    {cameraError ? (
                      <Badge className="bg-red-600">
                        <VideoOff className="w-3 h-3 mr-1" />
                        Camera Error
                      </Badge>
                    ) : faceDetected ? (
                      <Badge className="bg-green-600">
                        <Eye className="w-3 h-3 mr-1" />
                        Proctoring Active
                      </Badge>
                    ) : (
                      <Badge className="bg-amber-600 animate-pulse">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        Face Not Detected
                      </Badge>
                    )}
                    {violationCount > 0 && (
                      <Badge className="bg-red-600">
                        {violationCount} warnings
                      </Badge>
                    )}
                  </div>
                )}
                
                {/* Timer */}
                <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${
                  timeRemaining < 300 ? 'bg-red-600/20 border border-red-500' : 'bg-slate-700'
                }`}>
                  <Clock className={`w-5 h-5 ${timeRemaining < 300 ? 'text-red-400' : 'text-slate-300'}`} />
                  <span className={`font-mono text-lg font-bold ${timeRemaining < 300 ? 'text-red-400' : 'text-white'}`}>
                    {formatTime(timeRemaining)}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Progress */}
        <Card className="mb-6 bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4 mb-4">
              {sections.map((section, idx) => (
                <div key={section} className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    idx < currentSection ? 'bg-emerald-600' :
                    idx === currentSection ? 'bg-indigo-600' : 'bg-slate-600'
                  }`}>
                    {idx < currentSection ? (
                      <CheckCircle className="w-5 h-5 text-white" />
                    ) : (
                      <span className="text-white font-semibold">{idx + 1}</span>
                    )}
                  </div>
                  <span className={`text-sm ${idx === currentSection ? 'text-white font-semibold' : 'text-slate-400'}`}>
                    {section}
                  </span>
                  {idx < 2 && <div className="w-12 h-0.5 bg-slate-600" />}
                </div>
              ))}
            </div>
            <Progress value={progressPercentage} className="h-2" />
          </CardContent>
        </Card>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Assessment Content */}
          <div className="lg:col-span-3">
            {currentSection === 0 && renderMCQSection()}
            {currentSection === 1 && renderCodingSection()}
            {currentSection === 2 && renderPsychometricSection()}
          </div>
          
          {/* Proctoring Camera Feed */}
          {proctoringEnabled && (
            <div className="lg:col-span-1">
              <Card className="bg-slate-800/50 border-slate-700 sticky top-6">
                <CardHeader className="pb-2">
                  <CardTitle className="text-white text-sm flex items-center gap-2">
                    <Video className="w-4 h-4 text-green-400" />
                    Proctoring Camera
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="relative aspect-video bg-slate-900 rounded-lg overflow-hidden">
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-full object-cover"
                    />
                    <canvas ref={canvasRef} className="hidden" />
                    {cameraError && (
                      <div className="absolute inset-0 flex items-center justify-center bg-slate-900/90">
                        <div className="text-center p-4">
                          <VideoOff className="w-8 h-8 text-red-400 mx-auto mb-2" />
                          <p className="text-red-400 text-xs">{cameraError}</p>
                        </div>
                      </div>
                    )}
                    {!faceDetected && !cameraError && (
                      <div className="absolute bottom-2 left-2 right-2">
                        <Badge className="bg-amber-600 w-full justify-center">
                          <AlertTriangle className="w-3 h-3 mr-1" />
                          Face not detected
                        </Badge>
                      </div>
                    )}
                  </div>
                  <p className="text-slate-400 text-xs mt-2 text-center">
                    Stay visible to avoid violations
                  </p>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AssessmentPage;
