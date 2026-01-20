import React from 'react';

const PsychometricSection = ({ questions, answers, onChange }) => {
    return (
        <div className="bg-white p-6 rounded-lg shadow-md space-y-6">
            <h3 className="text-xl font-semibold mb-4 text-gray-800">Psychometric Evaluation</h3>
            <p className="text-gray-600 mb-6">Please rate yourself on the following traits honestly.</p>

            {questions.map((q) => (
                <div key={q.id} className="space-y-2">
                    <div className="flex justify-between">
                        <label className="text-sm font-medium text-gray-700">{q.text}</label>
                        <span className="text-sm font-bold text-blue-600">{answers[q.id] || 5}/10</span>
                    </div>
                    <input
                        type="range"
                        min="1"
                        max="10"
                        value={answers[q.id] || 5}
                        onChange={(e) => onChange(q.id, parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                        <span>Strongly Disagree</span>
                        <span>Strongly Agree</span>
                    </div>
                </div>
            ))}
        </div>
    );
};

export default PsychometricSection;
