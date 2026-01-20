import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { startAssessment, logProctoringEvent, submitAssessmentResult } from '../services/api';
import MCQSection from '../components/Assessment/MCQSection';
import CodingSection from '../components/Assessment/CodingSection';
import PsychometricSection from '../components/Assessment/PsychometricSection';

const AssessmentPage = () => {
    const { candidateId } = useParams();
    const navigate = useNavigate();

    // Assessment State
    const [assessmentData, setAssessmentData] = useState(null);
    const [currentSection, setCurrentSection] = useState('mcq'); // mcq, coding, psychometric
    const [loading, setLoading] = useState(true);

    // Answers State
    const [mcqAnswers, setMcqAnswers] = useState({});
    const [codeAnswer, setCodeAnswer] = useState('');
    const [psychometricAnswers, setPsychometricAnswers] = useState({});

    // Proctoring State
    const [warnings, setWarnings] = useState(0);
    const videoRef = useRef(null);

    // Load Assessment Data
    useEffect(() => {
        const loadAssessment = async () => {
            try {
                const response = await startAssessment(candidateId);
                setAssessmentData(response.data);
                setLoading(false);
            } catch (error) {
                console.error("Failed to load assessment", error);
                setLoading(false);
            }
        };
        loadAssessment();
    }, [candidateId]);

    // Proctoring: Tab Switching & Visibility
    useEffect(() => {
        const handleVisibilityChange = () => {
            if (document.hidden) {
                const newWarnings = warnings + 1;
                setWarnings(newWarnings);
                logProctoringEvent({
                    assessment_id: assessmentData?.id,
                    event_type: 'tab_switch',
                    severity: 'medium',
                    details: `Tab hidden. Warning count: ${newWarnings}`
                });
                alert(`Warning: You switched tabs! This has been recorded. (${newWarnings}/3)`);
            }
        };

        document.addEventListener("visibilitychange", handleVisibilityChange);
        return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
    }, [warnings, assessmentData]);

    // Proctoring: Webcam Setup
    useEffect(() => {
        const startWebcam = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                }
            } catch (err) {
                console.error("Webcam access denied", err);
                logProctoringEvent({
                    assessment_id: assessmentData?.id,
                    event_type: 'webcam_denied',
                    severity: 'high',
                    details: 'User denied webcam access'
                });
                alert("Webcam access is required for this assessment.");
            }
        };
        startWebcam();

        return () => {
            // Cleanup stream
            if (videoRef.current && videoRef.current.srcObject) {
                videoRef.current.srcObject.getTracks().forEach(track => track.stop());
            }
        };
    }, [assessmentData]);

    const handleSubmit = async () => {
        setLoading(true);
        // Calculate mock scores for demo (in real app, backend calculates)
        const resultPayload = {
            candidate_id: candidateId,
            mcq_answers: mcqAnswers,
            code: codeAnswer,
            psychometric: psychometricAnswers
        };

        try {
            // For MVP demo, just log and go back to dashboard
            console.log("Submitting:", resultPayload);
            // await submitAssessmentResult(resultPayload);
            alert("Assessment Completed! Thank you.");
            navigate('/dashboard'); // Go to dashboard (Task 3.5 eventually)
        } catch (error) {
            console.error("Submission failed", error);
            alert("Failed to submit assessment.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="flex h-screen items-center justify-center">Loading Assessment...</div>;
    if (!assessmentData) return <div className="flex h-screen items-center justify-center">Failed to load assessment.</div>;

    return (
        <div className="min-h-screen bg-gray-100 flex flex-col">
            {/* Header */}
            <header className="bg-white shadow p-4 flex justify-between items-center z-10">
                <h1 className="text-xl font-bold text-gray-800">Cygnusa Assessment</h1>
                <div className="flex items-center space-x-4">
                    <div className="text-red-500 font-semibold">Warnings: {warnings}/3</div>
                    <div className="relative w-32 h-24 bg-black rounded overflow-hidden shadow border border-gray-300">
                        <video ref={videoRef} autoPlay playsInline muted className="w-full h-full object-cover" />
                        <div className="absolute bottom-0 right-0 bg-red-600 text-white text-xs px-1">REC</div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 container mx-auto p-6 max-w-4xl">
                {/* Progress Tabs */}
                <div className="flex mb-6 space-x-2 border-b border-gray-200">
                    <button
                        onClick={() => setCurrentSection('mcq')}
                        className={`px-4 py-2 font-medium ${currentSection === 'mcq' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        1. Technical MCQ
                    </button>
                    <button
                        onClick={() => setCurrentSection('coding')}
                        className={`px-4 py-2 font-medium ${currentSection === 'coding' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        2. Coding Challenge
                    </button>
                    <button
                        onClick={() => setCurrentSection('psychometric')}
                        className={`px-4 py-2 font-medium ${currentSection === 'psychometric' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        3. Personality
                    </button>
                </div>

                {/* Section Content */}
                <div className="min-h-[400px]">
                    {currentSection === 'mcq' && assessmentData.questions.mcq.map(q => (
                        <div key={q.id} className="mb-4">
                            <MCQSection
                                question={q}
                                currentAnswer={mcqAnswers[q.id]}
                                onAnswer={(ans) => setMcqAnswers({ ...mcqAnswers, [q.id]: ans })}
                            />
                        </div>
                    ))}

                    {currentSection === 'coding' && (
                        <CodingSection
                            problem={assessmentData.questions.coding}
                            code={codeAnswer}
                            onChange={setCodeAnswer}
                        />
                    )}

                    {currentSection === 'psychometric' && (
                        <PsychometricSection
                            questions={assessmentData.questions.psychometric}
                            answers={psychometricAnswers}
                            onChange={(id, val) => setPsychometricAnswers({ ...psychometricAnswers, [id]: val })}
                        />
                    )}
                </div>

                {/* Navigation Buttons */}
                <div className="flex justify-between mt-8 pt-4 border-t border-gray-200">
                    <button
                        onClick={() => {
                            if (currentSection === 'coding') setCurrentSection('mcq');
                            if (currentSection === 'psychometric') setCurrentSection('coding');
                        }}
                        disabled={currentSection === 'mcq'}
                        className="px-6 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50"
                    >
                        Previous
                    </button>

                    {currentSection !== 'psychometric' ? (
                        <button
                            onClick={() => {
                                if (currentSection === 'mcq') setCurrentSection('coding');
                                if (currentSection === 'coding') setCurrentSection('psychometric');
                            }}
                            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                            Next Section
                        </button>
                    ) : (
                        <button
                            onClick={handleSubmit}
                            className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 font-bold"
                        >
                            Complete Assessment
                        </button>
                    )}
                </div>
            </main>
        </div>
    );
};

export default AssessmentPage;
