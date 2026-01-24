import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Label } from '../components/ui/label';
import { Progress } from '../components/ui/progress';
import { Clock, CheckCircle, Loader2 } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import Editor from '@monaco-editor/react';
import Logo from '../components/Logo';
import { startAssessment, submitMCQ, submitCode, submitPsychometric, completeAssessment } from '../services/api';

const AssessmentPage = () => {
    const navigate = useNavigate();
    const { candidateId } = useParams(); // Get from URL param
    const { toast } = useToast();

    const [assessmentId, setAssessmentId] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Assessment Data
    const [mcqQuestions, setMcqQuestions] = useState([]);
    const [codingProblem, setCodingProblem] = useState(null);
    const [psychometricScenarios, setPsychometricScenarios] = useState([]);

    // State
    const [currentSection, setCurrentSection] = useState(0);
    const [currentQuestion, setCurrentQuestion] = useState(0);
    const [mcqAnswers, setMcqAnswers] = useState({});
    const [code, setCode] = useState('// Write your solution here\n');
    const [codeLanguage, setCodeLanguage] = useState('python');
    const [psychometricAnswers, setPsychometricAnswers] = useState({});
    const [timeRemaining, setTimeRemaining] = useState(3600); // Default 60 mins
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitted, setSubmitted] = useState(false);

    // Fetch Assessment Data on Mount
    useEffect(() => {
        const initAssessment = async () => {
            try {
                if (!candidateId) {
                    throw new Error("Candidate ID is missing");
                }
                const data = await startAssessment(candidateId);
                if (data.status === 'success' && data.data) {
                    setAssessmentId(data.data.assessment_id);
                    setMcqQuestions(data.data.mcq_questions || []);
                    setCodingProblem(data.data.coding_problem || null);
                    setPsychometricScenarios(data.data.psychometric_scenarios || []);
                    // Reset code if needed
                    setCode(data.data.coding_problem?.starter_code || '// Write your solution here\n');
                } else {
                    throw new Error("Failed to load assessment data");
                }
            } catch (err) {
                console.error(err);
                setError(err.message || "Failed to start assessment");
                toast({
                    variant: 'destructive',
                    title: "Error",
                    description: err.message || "Could not start assessment"
                });
            } finally {
                setLoading(false);
            }
        };

        initAssessment();
    }, [candidateId, toast]);

    const handleAutoSubmit = () => {
        toast({
            title: 'Time\'s up!',
            description: 'Your assessment has been automatically submitted.',
        });
        handleFinalSubmit();
    };

    useEffect(() => {
        if (loading || submitted) return;

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
    }, [loading, submitted]);

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    // 3 Sections: MCQ, Coding, Psychometric
    const totalSections = 3;
    const progressPercentage = ((currentSection + 1) / totalSections) * 100;

    const handleMCQAnswer = async (questionId, answerIndex) => {
        setMcqAnswers(prev => ({ ...prev, [questionId]: answerIndex }));

        // Submit answer to backend
        try {
            await submitMCQ({
                assessment_id: assessmentId,
                question_id: questionId,
                answer: answerIndex,
                time_taken: 30 // Mock time taken for this interaction
            });
        } catch (err) {
            console.error("Failed to submit MCQ answer", err);
        }
    };

    const handlePsychometricAnswer = async (scenarioId, trait, score) => {
        // For simplicity in this UI, we assume one score per scenario or map answer index to score
        // The design had radio buttons (options). API expects trait_scores { trait: score }.
        // We need to map options to scores/traits. 
        // Simplified: We'll send the selected index as 'response_index' and let backend handle or just mock 'adaptability': score

        setPsychometricAnswers(prev => ({ ...prev, [scenarioId]: score }));

        try {
            await submitPsychometric({
                assessment_id: assessmentId,
                scenario_id: scenarioId,
                trait_scores: { "adaptability": score * 2 }, // Mock mapping: option 0-4 * 2 = 0-8 score
                response_text: "Selected option " + score
            });
        } catch (err) {
            console.error("Failed to submit psychometric answer", err);
        }
    };

    const handleNextSection = async () => {
        if (currentSection === 1) {
            // Leaving coding section, submit code
            try {
                await submitCode({
                    assessment_id: assessmentId,
                    problem_id: codingProblem.id,
                    code: code,
                    language: codeLanguage
                });
                toast({ title: "Code saved", description: "Your solution has been submitted." });
            } catch (err) {
                toast({ variant: 'destructive', title: "Error saving code", description: "Could not save solution." });
                return; // Don't proceed if save fails? Optional.
            }
        }

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

    const handleFinalSubmit = async () => {
        setIsSubmitting(true);
        try {
            await completeAssessment(assessmentId);
            setSubmitted(true);
            toast({
                title: 'Assessment submitted!',
                description: 'Your responses have been recorded.',
            });
        } catch (err) {
            toast({
                variant: 'destructive',
                title: 'Submission failed',
                description: 'Could not complete assessment. Please try again.',
            });
            setIsSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-12 h-12 animate-spin text-indigo-600" />
                <span className="ml-4 text-lg text-slate-600">Loading Assessment...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Card className="max-w-md p-6">
                    <h2 className="text-xl text-red-600 font-bold mb-4">Error</h2>
                    <p>{error}</p>
                    <Button onClick={() => navigate('/')} className="mt-4">Back to Home</Button>
                </Card>
            </div>
        );
    }

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

    const renderMCQSection = () => {
        const question = mcqQuestions[currentQuestion];
        if (!question) return <div>No questions available.</div>;

        return (
            <div className="space-y-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold text-slate-900">
                        Question {currentQuestion + 1} of {mcqQuestions.length}
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
                                        className={`flex items-center space-x-3 p-4 rounded-lg border-2 transition-all cursor-pointer ${mcqAnswers[question.id] === idx
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
                    {currentQuestion < mcqQuestions.length - 1 ? (
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
        if (!codingProblem) return <div>No coding problem available.</div>;

        return (
            <div className="space-y-6">
                <Card className="border-2 border-indigo-200">
                    <CardHeader>
                        <CardTitle className="text-xl">{codingProblem.title}</CardTitle>
                        <CardDescription className="text-base">
                            Difficulty: {codingProblem.difficulty}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="bg-slate-50 p-4 rounded-lg mb-4 whitespace-pre-line text-slate-700">
                            {codingProblem.description}
                        </div>
                        {codingProblem.example && (
                            <div className="bg-slate-100 p-2 rounded text-sm font-mono mt-2">
                                Example: {codingProblem.example}
                            </div>
                        )}
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Your Solution</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="border-2 border-slate-200 rounded-lg overflow-hidden">
                            <Editor
                                height="400px"
                                defaultLanguage="python"
                                value={code}
                                onChange={(value) => setCode(value)}
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
        const scenario = psychometricScenarios[currentQuestion];
        if (!scenario) return <div>No scenarios available.</div>;

        return (
            <div className="space-y-6">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-semibold text-slate-900">
                        Scenario {currentQuestion + 1} of {psychometricScenarios.length}
                    </h3>
                </div>

                <Card className="border-2 border-indigo-200">
                    <CardContent className="pt-6">
                        <div className="bg-indigo-50 p-4 rounded-lg mb-6">
                            <p className="text-lg text-slate-800">{scenario.scenario}</p>
                        </div>
                        <RadioGroup
                            value={psychometricAnswers[scenario.id]?.toString()}
                            onValueChange={(value) => handlePsychometricAnswer(scenario.id, 'adaptability', parseInt(value))}
                        >
                            <div className="space-y-3">
                                {scenario.options.map((option, idx) => (
                                    <div
                                        key={idx}
                                        className={`flex items-center space-x-3 p-4 rounded-lg border-2 transition-all cursor-pointer ${psychometricAnswers[scenario.id] === idx + 1 // Assuming 1-indexed scores for now
                                                ? 'border-indigo-600 bg-indigo-50'
                                                : 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50'
                                            }`}
                                        onClick={() => handlePsychometricAnswer(scenario.id, 'adaptability', idx + 1)}
                                    >
                                        <RadioGroupItem value={(idx + 1).toString()} id={`psy-option-${idx}`} />
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
                    {currentQuestion < psychometricScenarios.length - 1 ? (
                        <Button
                            onClick={() => setCurrentQuestion(prev => prev + 1)}
                            className="bg-indigo-600 hover:bg-indigo-700"
                        >
                            Next Scenario
                        </Button>
                    ) : (
                        <Button
                            onClick={handleFinalSubmit}
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
                                    <p className="text-sm sm:text-base text-slate-600">
                                        Section {currentSection + 1} of {totalSections}: {
                                            currentSection === 0 ? "Multiple Choice" :
                                                currentSection === 1 ? "Coding Challenge" : "Situational Judgment"
                                        }
                                    </p>
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
