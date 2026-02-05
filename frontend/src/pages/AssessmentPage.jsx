import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Label } from '../components/ui/label';
import { Progress } from '../components/ui/progress';
import { Badge } from '../components/ui/badge';
import {
  Clock, CheckCircle, Loader2, Play, AlertTriangle, Video, VideoOff,
  Eye, ShieldAlert, Timer, Code, Brain, FileText, ChevronRight, ChevronLeft, Zap, Terminal
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { useProctorStream } from '../hooks/useProctorStream';
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
  
  // Coding test results
  const [testsPassed, setTestsPassed] = useState(false);
  const [codeSaved, setCodeSaved] = useState(false);
  const [testsPassedCount, setTestsPassedCount] = useState(0);
  const [totalTestsCount, setTotalTestsCount] = useState(0);

  // Timer
  const [timeRemaining, setTimeRemaining] = useState(3600); // 60 minutes default

  // Submission
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  // Proctoring
  const [proctoringEnabled, setProctoringEnabled] = useState(true);
  const [cameraStream, setCameraStream] = useState(null);
  const [cameraError, setCameraError] = useState(null);
  const [faceDetected, setFaceDetected] = useState(false);
  const [faceCount, setFaceCount] = useState(0);
  const [detectionInitialized, setDetectionInitialized] = useState(false);
  const [violationCount, setViolationCount] = useState(0);
  const [violationsList, setViolationsList] = useState([]);
  const [lastViolationType, setLastViolationType] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const screenshotCanvasRef = useRef(null);
  const faceDetectionIntervalRef = useRef(null);
  const noFaceCountRef = useRef(0);
  const multipleFaceCountRef = useRef(0);

  // Live streaming to interviewer
  const { isStreaming, streamError } = useProctorStream(
    assessmentId,
    token,
    proctoringEnabled && assessmentId != null
  );

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

  // Auto-redirect after submission
  useEffect(() => {
    if (!submitted) return;
    
    const timer = setTimeout(() => {
      console.log('Auto-redirecting to home after assessment submission');
      navigate('/');
    }, 5000);
    return () => clearTimeout(timer);
  }, [navigate, submitted]);

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
      const { data } = startRes.data;

      setAssessmentData(data);
      setAssessmentId(data.assessment_id);
      
      // Use remaining_seconds if resuming, otherwise full duration
      const remainingTime = data.remaining_seconds ?? (data.duration_minutes * 60);
      setTimeRemaining(remainingTime);
      
      if (data.is_resume) {
        console.log(`Resuming assessment, ${remainingTime} seconds remaining`);
        
        // Load saved MCQ answers (convert letter A,B,C,D to index 0,1,2,3)
        if (data.saved_mcq_answers && Object.keys(data.saved_mcq_answers).length > 0) {
          const letterToIndex = { 'A': 0, 'B': 1, 'C': 2, 'D': 3 };
          const convertedMcqAnswers = {};
          for (const [qId, letter] of Object.entries(data.saved_mcq_answers)) {
            convertedMcqAnswers[qId] = letterToIndex[letter] ?? letter;
          }
          console.log('Loading saved MCQ answers:', convertedMcqAnswers);
          setMcqAnswers(convertedMcqAnswers);
        }
        
        // Load saved psychometric answers (convert score 1-10 to index 0-9)
        if (data.saved_psychometric_answers && Object.keys(data.saved_psychometric_answers).length > 0) {
          const convertedPsychAnswers = {};
          for (const [qId, score] of Object.entries(data.saved_psychometric_answers)) {
            convertedPsychAnswers[qId] = score - 1; // Convert 1-10 score to 0-9 index
          }
          console.log('Loading saved psychometric answers:', convertedPsychAnswers);
          setPsychometricAnswers(convertedPsychAnswers);
        }
        
        // Load saved coding submission
        if (data.saved_coding) {
          console.log('Loading saved coding submission:', data.saved_coding);
          setCode(data.saved_coding.code);
          setLanguage(data.saved_coding.language);
        }
      }

      // Set initial code (only if not resuming with saved code)
      if (data.coding_problem && !data.saved_coding) {
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
        
        // Wait for video to be ready before starting face detection
        videoRef.current.onloadedmetadata = () => {
          console.log('Video metadata loaded, dimensions:', videoRef.current.videoWidth, videoRef.current.videoHeight);
          videoRef.current.play().then(() => {
            console.log('Video playing, starting face detection in 1 second...');
            // Small delay to ensure video frame is available
            setTimeout(() => {
              console.log('Starting face detection now');
              startFaceDetection();
            }, 1000);
          }).catch(err => {
            console.error('Video play error:', err);
            setTimeout(() => startFaceDetection(), 1000); // Try anyway
          });
        };
      }

    } catch (err) {
      console.error('Camera error:', err);
      setCameraError('Camera access denied. Proctoring cannot monitor without camera access.');
      reportViolation('camera_denied', 'Candidate denied camera access', 'high');
    }
  };

  const startFaceDetection = () => {
    // Enhanced face detection with multiple face and no face detection
    faceDetectionIntervalRef.current = setInterval(async () => {
      if (!videoRef.current || !canvasRef.current) {
        console.log('Refs not ready');
        return;
      }

      const video = videoRef.current;
      const canvas = canvasRef.current;
      
      // Check video dimensions - use fallback if needed
      const videoWidth = video.videoWidth || 320;
      const videoHeight = video.videoHeight || 240;
      
      if (video.readyState < 2) {
        console.log('Video not ready, readyState:', video.readyState);
        return;
      }
      
      const ctx = canvas.getContext('2d');
      canvas.width = videoWidth;
      canvas.height = videoHeight;
      ctx.drawImage(video, 0, 0, videoWidth, videoHeight);

      try {
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const detectionResult = detectFaces(imageData, canvas.width, canvas.height);
        
        console.log('Face detection result:', detectionResult.count, 'faces detected');
        setFaceCount(detectionResult.count);
        setDetectionInitialized(true);

        if (detectionResult.count === 0) {
          // No face detected
          noFaceCountRef.current++;
          multipleFaceCountRef.current = 0;
          
          if (noFaceCountRef.current >= 2) { // 2 consecutive checks (6 seconds)
            setFaceDetected(false);
            if (lastViolationType !== 'no_face') {
              const screenshot = await captureScreenshot();
              reportViolation('no_face', 'No face detected in camera - candidate may have left', 'high', screenshot);
              setLastViolationType('no_face');
            }
          }
        } else if (detectionResult.count > 1) {
          // Multiple faces detected
          multipleFaceCountRef.current++;
          noFaceCountRef.current = 0;
          
          if (multipleFaceCountRef.current >= 2) { // 2 consecutive checks
            setFaceDetected(true);
            if (lastViolationType !== 'multiple_faces') {
              const screenshot = await captureScreenshot();
              reportViolation('multiple_faces', `Multiple faces detected (${detectionResult.count} people visible) - possible assistance`, 'critical', screenshot);
              setLastViolationType('multiple_faces');
            }
          }
        } else {
          // Single face detected - normal
          noFaceCountRef.current = 0;
          multipleFaceCountRef.current = 0;
          setFaceDetected(true);
          setLastViolationType(null);
        }
      } catch (e) {
        console.error('Face detection error:', e);
      }
    }, 3000); // Check every 3 seconds
  };

  const detectFaces = (imageData, width, height) => {
    // Simplified face detection using vertical stripe analysis
    // Counts distinct skin-colored regions in horizontal bands
    const { data } = imageData;
    
    // Divide image into vertical stripes and count skin pixels in each
    const numStripes = 30;
    const stripeWidth = Math.floor(width / numStripes);
    const skinPerStripe = new Array(numStripes).fill(0);
    const totalPerStripe = new Array(numStripes).fill(0);
    
    // Only analyze upper 2/3 of image (where faces typically are)
    const analyzeHeight = Math.floor(height * 0.75);
    
    for (let y = 0; y < analyzeHeight; y++) {
      for (let x = 0; x < width; x++) {
        const stripeIdx = Math.min(Math.floor(x / stripeWidth), numStripes - 1);
        const idx = (y * width + x) * 4;
        const r = data[idx];
        const g = data[idx + 1];
        const b = data[idx + 2];
        
        totalPerStripe[stripeIdx]++;
        if (isSkinTone(r, g, b)) {
          skinPerStripe[stripeIdx]++;
        }
      }
    }
    
    // Calculate skin density per stripe
    const skinDensity = skinPerStripe.map((skin, i) => 
      totalPerStripe[i] > 0 ? skin / totalPerStripe[i] : 0
    );
    
    // Find peaks (local maxima) in skin density - these are likely faces
    const threshold = 0.08; // Minimum skin density to consider
    const peaks = [];
    
    for (let i = 2; i < numStripes - 2; i++) {
      const current = skinDensity[i];
      if (current > threshold) {
        // Check if this is a local maximum (higher than neighbors)
        const isLocalMax = current >= skinDensity[i-1] && 
                          current >= skinDensity[i+1] &&
                          current >= skinDensity[i-2] &&
                          current >= skinDensity[i+2];
        
        // Also check if it's significantly above the average nearby
        const nearby = (skinDensity[i-2] + skinDensity[i-1] + skinDensity[i+1] + skinDensity[i+2]) / 4;
        const isSignificant = current > nearby * 0.8 || current > threshold * 1.5;
        
        if (isLocalMax && isSignificant) {
          peaks.push({ stripe: i, density: current });
        }
      }
    }
    
    // Merge peaks that are too close together (same face)
    const mergedPeaks = [];
    for (const peak of peaks) {
      const lastPeak = mergedPeaks[mergedPeaks.length - 1];
      if (lastPeak && peak.stripe - lastPeak.stripe < 5) {
        // Too close, merge with previous (keep the higher one)
        if (peak.density > lastPeak.density) {
          mergedPeaks[mergedPeaks.length - 1] = peak;
        }
      } else {
        mergedPeaks.push(peak);
      }
    }
    
    // Calculate total skin coverage to determine if there's any face at all
    const totalSkinDensity = skinDensity.reduce((a, b) => a + b, 0) / numStripes;
    
    console.log('Skin density per stripe:', skinDensity.map(d => d.toFixed(2)).join(', '));
    console.log('Peaks found:', mergedPeaks.length, 'Total avg density:', totalSkinDensity.toFixed(3));
    
    // Determine face count
    let faceCount = 0;
    
    if (totalSkinDensity < 0.02) {
      // Very little skin visible - no face
      faceCount = 0;
    } else if (mergedPeaks.length === 0 && totalSkinDensity > 0.05) {
      // No clear peaks but significant skin - probably 1 face filling frame
      faceCount = 1;
    } else {
      faceCount = Math.max(mergedPeaks.length, totalSkinDensity > 0.03 ? 1 : 0);
    }
    
    return {
      count: faceCount,
      peaks: mergedPeaks,
      totalDensity: totalSkinDensity
    };
  };

  const isSkinTone = (r, g, b) => {
    // Multi-range skin detection for various skin tones
    // Based on RGB color space rules
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    
    // Rule 1: General skin tone in uniform daylight
    const rule1 = r > 95 && g > 40 && b > 20 &&
                  max - min > 15 && Math.abs(r - g) > 15 && r > g && r > b;
    
    // Rule 2: Skin tone under flashlight or lateral illumination
    const rule2 = r > 220 && g > 210 && b > 170 &&
                  Math.abs(r - g) <= 15 && r > b && g > b;
    
    // Rule 3: Darker skin tones
    const rule3 = r > 60 && g > 40 && b > 20 &&
                  r > g && r > b && (r - g) > 10 && (r - b) > 10 &&
                  max - min > 10 && max - min < 80;

    return rule1 || rule2 || rule3;
  };

  const captureScreenshot = async () => {
    if (!videoRef.current) return null;
    
    try {
      const video = videoRef.current;
      const canvas = screenshotCanvasRef.current || document.createElement('canvas');
      if (!screenshotCanvasRef.current) {
        screenshotCanvasRef.current = canvas;
      }
      
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;
      
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      
      // Add timestamp watermark
      ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
      ctx.fillRect(5, canvas.height - 25, 200, 20);
      ctx.fillStyle = '#000';
      ctx.font = '12px Arial';
      ctx.fillText(new Date().toLocaleString(), 10, canvas.height - 10);
      
      // Convert to base64 data URL
      const dataUrl = canvas.toDataURL('image/jpeg', 0.7);
      return dataUrl;
    } catch (err) {
      console.error('Failed to capture screenshot:', err);
      return null;
    }
  };

  const analyzeForFace = (imageData) => {
    // Deprecated - kept for backwards compatibility
    // Use detectFaces instead
    const result = detectFaces(imageData, imageData.width, imageData.height);
    return result.count > 0;
  };

  const reportViolation = async (type, description, severity = 'medium', screenshot = null) => {
    if (!assessmentId) return;

    try {
      const payload = {
        violation_type: type,
        description: description,
        severity: severity
      };
      
      // Include screenshot if provided
      if (screenshot) {
        payload.screenshot = screenshot;
      }

      const res = await api.post(`/api/interviewee/assessment/${assessmentId}/violation`, payload);

      setViolationCount(res.data.data.total_violations);
      
      // Add to violations list for display
      const newViolation = {
        id: res.data.data.violation_id,
        type: type,
        description: description,
        severity: severity,
        timestamp: new Date().toLocaleTimeString()
      };
      setViolationsList(prev => [...prev, newViolation]);

      // Different toast styles based on severity
      const toastConfig = {
        variant: 'destructive',
        title: severity === 'critical' ? '⚠️ Critical Violation' : 'Warning',
        description: `Proctoring violation detected: ${description}`,
      };
      
      if (type === 'multiple_faces') {
        toastConfig.title = '👥 Multiple Faces Detected';
      } else if (type === 'no_face') {
        toastConfig.title = '😶 No Face Detected';
      } else if (type === 'tab_switch') {
        toastConfig.title = '🔀 Tab Switch Detected';
      }

      toast(toastConfig);
    } catch (err) {
      console.error('Failed to report violation:', err);
    }
  };

  // Tab visibility monitoring
  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (document.hidden && assessmentId && !submitted) {
        const screenshot = await captureScreenshot();
        reportViolation('tab_switch', 'Candidate switched away from assessment tab', 'high', screenshot);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [assessmentId, submitted]);

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

  // Sync time to server every 30 seconds (for resume functionality)
  useEffect(() => {
    if (loading || submitted || !assessmentId || !assessmentData) return;

    const totalDuration = (assessmentData.duration_minutes || 60) * 60;
    
    const syncTimer = setInterval(() => {
      const elapsed = totalDuration - timeRemaining;
      if (elapsed > 0) {
        api.post(`/api/interviewee/assessment/${assessmentId}/sync-time`, {
          time_elapsed_seconds: elapsed
        }).catch(err => {
          console.warn('Failed to sync time:', err);
        });
      }
    }, 30000); // Every 30 seconds

    return () => clearInterval(syncTimer);
  }, [loading, submitted, assessmentId, assessmentData, timeRemaining]);

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
  const handleRunCode = useCallback(async () => {
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
  }, [language, code]);

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

    const allPassed = passed === visibleTests.length;
    setTestsPassed(allPassed);
    setTestsPassedCount(passed);
    setTotalTestsCount(visibleTests.length);
    
    const summary = `\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📊 Results: ${passed}/${visibleTests.length} tests passed\n${allPassed ? '🎉 All tests passed! Click "Submit Code" to save your solution.' : `⚠️ ${failed} test(s) failed`}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;

    setOutput(results.join('\n') + summary);
    setIsRunning(false);
  };

  const handleSubmitCode = async () => {
    if (!assessmentId || !assessmentData?.coding_problem) return;
    
    setIsRunning(true);
    try {
      const totalTests = assessmentData.coding_problem.test_cases?.filter(tc => !tc.is_hidden).length || 0;
      await api.post(`/api/interviewee/assessment/${assessmentId}/submit-answer`, {
        type: 'coding',
        questionId: assessmentData.coding_problem.id,
        language: language,
        code: code,
        testsPassed: testsPassedCount,
        totalTests: totalTests || totalTestsCount
      });
      
      setCodeSaved(true);
      toast({
        title: "Code Submitted!",
        description: "Your solution has been saved successfully.",
      });
    } catch (err) {
      console.error('Failed to submit code:', err);
      toast({
        title: "Submission Failed",
        description: "Failed to save your code. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsRunning(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleMCQAnswer = useCallback(async (questionId, answerIndex) => {
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
  }, [assessmentId]);

  const handlePsychometricAnswer = useCallback(async (scenarioId, answerIndex) => {
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
  }, [assessmentId, assessmentData]);

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
        const totalTests = assessmentData?.coding_problem?.test_cases?.filter(tc => !tc.is_hidden).length || totalTestsCount;
        await api.post(`/api/interviewee/assessment/${assessmentId}/submit-answer`, {
          type: 'coding',
          questionId: assessmentData?.coding_problem?.id || 1,
          code: code,
          language: language,
          testsPassed: testsPassedCount,
          totalTests: totalTests
        });
        console.log(`Coding solution saved: ${testsPassedCount}/${totalTests} tests passed`);
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

  // Define sections and progress (needed by useMemo hooks)
  const sections = ['MCQ', 'Coding', 'Psychometric'];
  const progressPercentage = ((currentSection + 1) / 3) * 100;

  const renderMCQSection = useMemo(() => () => {
    const questions = assessmentData?.mcq_questions || [];
    if (questions.length === 0) return <p className="text-slate-400 text-center py-8">No questions available</p>;

    const question = questions[currentQuestion];
    if (!question) return null;

    const answeredCount = Object.keys(mcqAnswers).length;
    const progressPercent = (answeredCount / questions.length) * 100;

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-emerald-400 bg-clip-text text-transparent">
                Question {currentQuestion + 1} of {questions.length}
              </h3>
              <Badge className="bg-gradient-to-r from-indigo-600 to-indigo-700 text-white border-0">
                {question.category}
              </Badge>
            </div>
            <div className="mt-3">
              <Progress value={progressPercent} className="h-2 bg-slate-700" />
              <p className="text-xs text-slate-400 mt-2">{answeredCount}/{questions.length} answered</p>
            </div>
          </div>
        </div>

        <Card className="bg-gradient-to-br from-slate-800 to-slate-900 shadow-xl border-slate-700 hover:shadow-2xl transition-all duration-300">
          <CardContent className="pt-8">
            <p className="text-lg text-slate-100 mb-8 leading-relaxed font-medium">{question.question}</p>
            <RadioGroup
              value={mcqAnswers[question.id] !== undefined ? mcqAnswers[question.id].toString() : ''}
              onValueChange={(value) => handleMCQAnswer(question.id, parseInt(value))}
            >
              <div className="space-y-3">
                {question.options.map((option, idx) => (
                  <div
                    key={idx}
                    className={`flex items-center space-x-4 p-5 rounded-lg border-2 transition-all duration-200 cursor-pointer ${mcqAnswers[question.id] === idx
                      ? 'border-emerald-500 bg-emerald-500/15 shadow-md'
                      : 'border-slate-600 hover:border-indigo-500 hover:bg-slate-700/40'
                      }`}
                    onClick={() => handleMCQAnswer(question.id, idx)}
                  >
                    <RadioGroupItem value={idx.toString()} id={`option-${idx}`} className="border-slate-400" />
                    <Label htmlFor={`option-${idx}`} className="flex-1 cursor-pointer text-slate-200 text-base">
                      {String.fromCharCode(65 + idx)}) {option}
                    </Label>
                  </div>
                ))}
              </div>
            </RadioGroup>
          </CardContent>
        </Card>

        <div className="flex justify-between gap-3 pt-4">
          <Button
            variant="outline"
            onClick={() => setCurrentQuestion(prev => Math.max(0, prev - 1))}
            disabled={currentQuestion === 0}
            className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white gap-2"
          >
            <ChevronLeft className="w-4 h-4" /> Previous
          </Button>
          {currentQuestion < questions.length - 1 ? (
            <Button 
              onClick={() => setCurrentQuestion(prev => prev + 1)} 
              className="bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 gap-2"
            >
              Next Question <ChevronRight className="w-4 h-4" />
            </Button>
          ) : (
            <Button 
              onClick={handleNextSection} 
              className="bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 gap-2"
            >
              Next Section <ChevronRight className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>
    );
  }, [assessmentData?.mcq_questions, currentQuestion, mcqAnswers, handleMCQAnswer, handleNextSection]);

  const renderCodingSection = useMemo(() => () => {
    const problem = assessmentData?.coding_problem;
    if (!problem) return <p className="text-slate-400 text-center py-8">No coding problem available</p>;

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
              <div className="flex gap-2">
                <Badge className={`${problem.difficulty === 'Easy' ? 'bg-emerald-600' : problem.difficulty === 'Medium' ? 'bg-amber-600' : 'bg-red-600'}`}>
                  {problem.difficulty}
                </Badge>
                {assessmentData?.ai_generated && (
                  <Badge className="bg-purple-600 border-0">✨ AI Generated</Badge>
                )}
              </div>
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
                <pre className="text-slate-300 text-sm font-mono bg-slate-900/50 p-3 rounded border border-slate-700 overflow-x-auto">{problem.example}</pre>
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
                onClick={handleRunCode}
                disabled={isRunning}
                className="bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 gap-2 font-semibold"
              >
                {isRunning ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Run Code
                  </>
                )}
              </Button>
              {problem.test_cases && problem.test_cases.length > 0 && (
                <Button
                  onClick={() => handleRunTestCases(problem.test_cases)}
                  disabled={isRunning}
                  variant="outline"
                  className="border-indigo-600 text-indigo-300 hover:bg-indigo-900/50 hover:text-indigo-100 gap-2 font-semibold"
                >
                  {isRunning ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Testing...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      Run Tests
                    </>
                  )}
                </Button>
              )}
              {testsPassed && !codeSaved && (
                <Button
                  onClick={handleSubmitCode}
                  disabled={isRunning}
                  className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 gap-2 font-semibold animate-pulse"
                >
                  <CheckCircle className="w-4 h-4" />
                  Submit Code
                </Button>
              )}
              {codeSaved && (
                <Button
                  disabled
                  className="bg-green-800 text-green-200 gap-2 font-semibold cursor-default"
                >
                  <CheckCircle className="w-4 h-4" />
                  Code Saved ✓
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
            onClick={handlePrevSection} 
            className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white gap-2"
          >
            <ChevronLeft className="w-4 h-4" /> Previous Section
          </Button>
          <Button 
            onClick={handleNextSection} 
            className="bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 gap-2"
          >
            Next Section <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>
    );
  }, [assessmentData?.coding_problem, assessmentId, language, code, output, isRunning, testsPassed, codeSaved, handleRunCode, handleSubmitCode, handleNextSection, handlePrevSection, handleRunTestCases]);

  const renderPsychometricSection = useMemo(() => () => {
    const scenarios = assessmentData?.psychometric_scenarios || [];
    if (scenarios.length === 0) return <p className="text-slate-400 text-center py-8">No scenarios available</p>;

    const scenario = scenarios[currentQuestion];
    if (!scenario) return null;

    const answeredCount = Object.keys(psychometricAnswers).length;
    const progressPercent = (answeredCount / scenarios.length) * 100;

    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent flex items-center gap-3">
                <Brain className="w-6 h-6 text-purple-400" />
                Scenario {currentQuestion + 1} of {scenarios.length}
              </h3>
              <Badge className="bg-gradient-to-r from-purple-600 to-purple-700 text-white border-0">
                Personality Assessment
              </Badge>
            </div>
            <div className="mt-3">
              <Progress value={progressPercent} className="h-2 bg-slate-700" />
              <p className="text-xs text-slate-400 mt-2">{answeredCount}/{scenarios.length} answered</p>
            </div>
          </div>
        </div>

        <Card className="bg-gradient-to-br from-slate-800 to-slate-900 shadow-xl border-slate-700 hover:shadow-2xl transition-all duration-300">
          <CardContent className="pt-8">
            <div className="bg-gradient-to-r from-purple-900/40 to-pink-900/40 border border-purple-700/50 p-6 rounded-lg mb-8">
              <p className="text-lg text-slate-100 leading-relaxed font-medium">{scenario.scenario}</p>
            </div>
            <div className="space-y-3">
              <p className="text-slate-400 text-sm font-semibold mb-4">Choose the response that best describes your reaction:</p>
              <RadioGroup
                value={psychometricAnswers[scenario.id] !== undefined ? psychometricAnswers[scenario.id].toString() : ''}
                onValueChange={(value) => handlePsychometricAnswer(scenario.id, parseInt(value))}
              >
                <div className="space-y-3">
                  {scenario.options.map((option, idx) => (
                    <div
                      key={idx}
                      className={`flex items-start space-x-4 p-5 rounded-lg border-2 transition-all duration-200 cursor-pointer ${psychometricAnswers[scenario.id] === idx
                        ? 'border-purple-500 bg-purple-500/15 shadow-md'
                        : 'border-slate-600 hover:border-purple-500 hover:bg-slate-700/40'
                        }`}
                      onClick={() => handlePsychometricAnswer(scenario.id, idx)}
                    >
                      <RadioGroupItem value={idx.toString()} id={`psy-${idx}`} className="border-slate-400 mt-1" />
                      <Label htmlFor={`psy-${idx}`} className="flex-1 cursor-pointer text-slate-200 text-base leading-relaxed">
                        {option}
                      </Label>
                    </div>
                  ))}
                </div>
              </RadioGroup>
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-between gap-3 pt-4">
          {currentQuestion > 0 ? (
            <Button 
              variant="outline" 
              onClick={() => setCurrentQuestion(prev => prev - 1)}
              className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white gap-2"
            >
              <ChevronLeft className="w-4 h-4" /> Previous Scenario
            </Button>
          ) : (
            <Button 
              variant="outline" 
              onClick={handlePrevSection}
              className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white gap-2"
            >
              <ChevronLeft className="w-4 h-4" /> Previous Section
            </Button>
          )}
          {currentQuestion < scenarios.length - 1 ? (
            <Button 
              onClick={() => setCurrentQuestion(prev => prev + 1)}
              className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 gap-2"
            >
              Next Scenario <ChevronRight className="w-4 h-4" />
            </Button>
          ) : (
            <Button
              onClick={handleSubmit}
              className="bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 gap-2 font-semibold"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Submit Assessment
                </>
              )}
            </Button>
          )}
        </div>
      </div>
    );
  }, [assessmentData?.psychometric_scenarios, currentQuestion, psychometricAnswers, handlePsychometricAnswer, handlePrevSection, handleSubmit, isSubmitting]);

  const renderSuccessScreen = useMemo(() => () => (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Card className="bg-gradient-to-br from-slate-800 to-slate-900 shadow-2xl border-emerald-600 max-w-md w-full">
        <CardContent className="pt-12 text-center pb-8">
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 bg-gradient-to-r from-emerald-400 to-cyan-400 rounded-full flex items-center justify-center animate-pulse">
              <CheckCircle className="w-12 h-12 text-white" />
            </div>
          </div>
          <h2 className="text-3xl font-bold text-white mb-2">Assessment Complete!</h2>
          <p className="text-slate-300 text-lg mb-6">Thank you for completing your assessment.</p>
          <div className="bg-slate-700/50 border border-slate-600 p-4 rounded-lg mb-6">
            <p className="text-slate-400 text-sm">Your responses have been submitted successfully.</p>
            <p className="text-emerald-400 font-semibold text-sm mt-2">Redirecting...</p>
          </div>
        </CardContent>
      </Card>
    </div>
  ), []);

  // Loading state - early return AFTER all hooks
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 flex items-center justify-center p-6">
        <Card className="w-full max-w-md bg-white shadow-md hover:shadow-xl transition-all duration-300 border-slate-200">
          <CardContent className="pt-12 pb-12 text-center">
            <Loader2 className="w-12 h-12 animate-spin mx-auto text-indigo-400 mb-4" />
            <p className="text-white text-lg">Loading your assessment...</p>
            <p className="text-slate-600 text-sm mt-2">Please wait while we verify your access</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state - early return AFTER all hooks
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 flex items-center justify-center p-6">
        <Card className="w-full max-w-md bg-white shadow-md hover:shadow-xl transition-all duration-300 border-slate-200">
          <CardContent className="pt-12 pb-12 text-center">
            <ShieldAlert className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-4">Assessment Unavailable</h2>
            <p className="text-slate-700 mb-6">{error}</p>
            <Button onClick={() => navigate('/')} className="bg-indigo-600 hover:bg-indigo-700">
              Return to Home
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Submitted state - early return AFTER all hooks
  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 flex items-center justify-center p-6">
        <Card className="w-full max-w-md bg-white shadow-md hover:shadow-xl transition-all duration-300 border-slate-200 text-center">
          <CardContent className="pt-12 pb-12">
            <div className="w-20 h-20 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-12 h-12 text-emerald-400" />
            </div>
            <h2 className="text-3xl font-bold text-white mb-4">Assessment Complete!</h2>
            <p className="text-slate-700 mb-8 text-lg">
              Thank you, {candidateName}. Your assessment has been submitted successfully.
            </p>
            <div className="bg-indigo-900/50 p-4 rounded-lg mb-6">
              <p className="text-sm text-indigo-200">
                <strong>What's Next:</strong> Our team will review your responses and contact you with the final decision within 3-5 business days.
              </p>
            </div>
            <p className="text-slate-600 text-xs mb-4">
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 py-6 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <Card className="mb-6 bg-gradient-to-r from-slate-800 to-slate-900 shadow-2xl border-slate-700 hover:shadow-2xl transition-all duration-300">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between flex-wrap gap-6">
              <div className="flex items-center gap-4">
                <Logo variant="icon" size="default" />
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-emerald-400 bg-clip-text text-transparent">
                    Technical Assessment
                  </h1>
                  <p className="text-slate-400 text-sm">Welcome, <span className="text-slate-200 font-semibold">{candidateName}</span></p>
                </div>
              </div>

              <div className="flex items-center gap-3 flex-wrap justify-end">
                {/* Proctoring Status */}
                {proctoringEnabled && (
                  <div className="flex items-center gap-2">
                    {cameraError ? (
                      <Badge className="bg-red-600/80 text-white border-0 gap-1 px-3 py-1">
                        <VideoOff className="w-3 h-3" />
                        Camera Error
                      </Badge>
                    ) : faceCount > 1 ? (
                      <Badge className="bg-red-600 animate-pulse text-white border-0 gap-1 px-3 py-1">
                        <AlertTriangle className="w-3 h-3" />
                        {faceCount} Faces Detected!
                      </Badge>
                    ) : faceDetected ? (
                      <Badge className="bg-emerald-600/80 text-white border-0 gap-1 px-3 py-1">
                        <Eye className="w-3 h-3" />
                        Monitoring Active
                      </Badge>
                    ) : (
                      <Badge className="bg-amber-600 animate-pulse text-white border-0 gap-1 px-3 py-1">
                        <AlertTriangle className="w-3 h-3" />
                        No Face Detected
                      </Badge>
                    )}
                    {isStreaming && (
                      <Badge className="bg-purple-600 animate-pulse text-white border-0 gap-1 px-3 py-1">
                        <Video className="w-3 h-3" />
                        Being Monitored
                      </Badge>
                    )}
                    {streamError && (
                      <Badge className="bg-orange-600 text-white border-0 gap-1 px-3 py-1">
                        Stream Error
                      </Badge>
                    )}
                    {violationCount > 0 && (
                      <Badge className="bg-red-600 text-white border-0 gap-1 px-3 py-1 font-semibold">
                        <ShieldAlert className="w-3 h-3" />
                        {violationCount} Warning{violationCount > 1 ? 's' : ''}
                      </Badge>
                    )}
                  </div>
                )}

                {/* Timer - More prominent when time is low */}
                <div className={`flex items-center gap-3 px-4 py-2 rounded-lg font-mono font-bold transition-all duration-300 ${
                  timeRemaining < 300 
                    ? 'bg-red-600/30 border-2 border-red-500 shadow-lg shadow-red-500/50' 
                    : timeRemaining < 600
                    ? 'bg-amber-600/30 border-2 border-amber-500'
                    : 'bg-slate-700/50 border border-slate-600'
                }`}>
                  <Timer className={`w-5 h-5 ${
                    timeRemaining < 300 ? 'text-red-400 animate-pulse' :
                    timeRemaining < 600 ? 'text-amber-400' :
                    'text-slate-300'
                  }`} />
                  <span className={`text-lg ${
                    timeRemaining < 300 ? 'text-red-400' :
                    timeRemaining < 600 ? 'text-amber-400' :
                    'text-slate-200'
                  }`}>
                    {formatTime(timeRemaining)}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Progress Section */}
        <Card className="mb-6 bg-gradient-to-r from-slate-800 to-slate-900 shadow-xl border-slate-700 hover:shadow-2xl transition-all duration-300">
          <CardContent className="pt-6">
            <div className="flex items-center gap-6 mb-5">
              {sections.map((section, idx) => (
                <div key={section} className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center font-semibold transition-all duration-300 ${
                    idx < currentSection 
                      ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 text-white' :
                      idx === currentSection 
                      ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white ring-2 ring-indigo-400' 
                      : 'bg-slate-600 text-slate-300'
                  }`}>
                    {idx < currentSection ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : (
                      <span>{idx + 1}</span>
                    )}
                  </div>
                  <span className={`text-sm font-medium transition-colors ${
                    idx === currentSection ? 'text-white font-bold' : 
                    idx < currentSection ? 'text-emerald-400' : 
                    'text-slate-400'
                  }`}>
                    {section}
                  </span>
                  {idx < 2 && <div className="w-16 h-1 bg-gradient-to-r from-slate-600 to-transparent rounded-full" />}
                </div>
              ))}
            </div>
            <div className="space-y-2">
              <Progress value={progressPercentage} className="h-2.5 bg-slate-700 rounded-full" />
              <p className="text-xs text-slate-400 text-center">{progressPercentage.toFixed(0)}% Complete</p>
            </div>
          </CardContent>
        </Card>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Assessment Content */}
          <div className="lg:col-span-3">
            {currentSection === 0 && renderMCQSection()}
            {currentSection === 1 && renderCodingSection()}
            {currentSection === 2 && renderPsychometricSection()}
            {submitted && renderSuccessScreen()}
          </div>

          {/* Proctoring Camera Feed */}
          {proctoringEnabled && (
            <div className="lg:col-span-1">
              <Card className="bg-gradient-to-br from-slate-800 to-slate-900 shadow-2xl border-slate-700 sticky top-6 hover:shadow-2xl transition-all duration-300">
                <CardHeader className="pb-3 border-b border-slate-700">
                  <CardTitle className="text-white text-sm flex items-center gap-2 font-bold">
                    <Video className="w-4 h-4 text-emerald-400" />
                    Proctoring Camera
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-4">
                  <div className="relative aspect-video bg-slate-900 rounded-lg overflow-hidden border border-slate-700 shadow-lg">
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-full object-cover"
                    />
                    <canvas ref={canvasRef} className="hidden" />
                    {cameraError && (
                      <div className="absolute inset-0 flex items-center justify-center bg-slate-900/95 backdrop-blur">
                        <div className="text-center p-4">
                          <VideoOff className="w-8 h-8 text-red-400 mx-auto mb-2" />
                          <p className="text-red-400 text-xs font-medium">{cameraError}</p>
                        </div>
                      </div>
                    )}
                    {faceCount > 1 && !cameraError && (
                      <div className="absolute inset-0 border-4 border-red-500 animate-pulse rounded-lg">
                        <div className="absolute bottom-2 left-2 right-2">
                          <Badge className="bg-red-600 w-full justify-center text-white border-0 gap-1">
                            <AlertTriangle className="w-3 h-3" />
                            {faceCount} Faces - Only 1 Allowed!
                          </Badge>
                        </div>
                      </div>
                    )}
                    {faceCount === 0 && detectionInitialized && !cameraError && (
                      <div className="absolute inset-0 border-4 border-amber-500 animate-pulse rounded-lg">
                        <div className="absolute bottom-2 left-2 right-2">
                          <Badge className="bg-amber-600 w-full justify-center text-white border-0 gap-1">
                            <AlertTriangle className="w-3 h-3" />
                            No Face Detected
                          </Badge>
                        </div>
                      </div>
                    )}
                    {faceCount === 1 && !cameraError && (
                      <div className="absolute top-2 right-2">
                        <Badge className="bg-emerald-600 text-white border-0 gap-1">
                          <CheckCircle className="w-3 h-3" />
                          ✓ 1 Face
                        </Badge>
                      </div>
                    )}
                    {/* Show detecting state when camera just started */}
                    {!detectionInitialized && !cameraError && (
                      <div className="absolute top-2 right-2">
                        <Badge className="bg-blue-600 text-white border-0 gap-1 animate-pulse">
                          Detecting...
                        </Badge>
                      </div>
                    )}
                  </div>
                  <p className="text-slate-400 text-xs mt-3 text-center font-medium">
                    Stay visible in frame • Only 1 person allowed
                  </p>
                </CardContent>
              </Card>

              {/* Violations Panel */}
              {violationsList.length > 0 && (
                <Card className="mt-4 bg-gradient-to-br from-red-900/30 to-slate-900 shadow-2xl border-red-800/50">
                  <CardHeader className="pb-2 border-b border-red-800/50">
                    <CardTitle className="text-white text-sm flex items-center gap-2 font-bold">
                      <ShieldAlert className="w-4 h-4 text-red-400" />
                      Violations ({violationsList.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-3 max-h-60 overflow-y-auto">
                    <div className="space-y-2">
                      {violationsList.map((violation, idx) => (
                        <div 
                          key={violation.id || idx} 
                          className={`p-2 rounded-lg border text-xs ${
                            violation.severity === 'high' 
                              ? 'bg-red-900/40 border-red-700 text-red-300' 
                              : violation.severity === 'medium'
                              ? 'bg-amber-900/40 border-amber-700 text-amber-300'
                              : 'bg-slate-800 border-slate-700 text-slate-300'
                          }`}
                        >
                          <div className="flex items-center justify-between mb-1">
                            <Badge className={`text-[10px] px-1.5 py-0 ${
                              violation.type === 'tab_switch' ? 'bg-blue-600' :
                              violation.type === 'multiple_faces' ? 'bg-red-600' :
                              violation.type === 'no_face' ? 'bg-amber-600' :
                              violation.type === 'face_not_detected' ? 'bg-amber-600' :
                              'bg-slate-600'
                            }`}>
                              {violation.type === 'tab_switch' ? '🔀 Tab' :
                               violation.type === 'multiple_faces' ? '👥 Multi-Face' :
                               violation.type === 'no_face' || violation.type === 'face_not_detected' ? '😶 No Face' :
                               violation.type}
                            </Badge>
                            <span className="text-[10px] text-slate-500">{violation.timestamp}</span>
                          </div>
                          <p className="text-[11px] truncate">{violation.description}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AssessmentPage;
