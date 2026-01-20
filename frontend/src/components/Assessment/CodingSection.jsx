import React from 'react';

const CodingSection = ({ problem, code, onChange }) => {
    return (
        <div className="flex flex-col h-full bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-2 text-gray-800">{problem.title}</h3>
            <p className="text-gray-600 mb-4">{problem.description}</p>

            <div className="mb-2 flex justify-between items-center">
                <label className="text-sm font-medium text-gray-700">Code Editor (Python)</label>
            </div>

            <textarea
                value={code}
                onChange={(e) => onChange(e.target.value)}
                className="flex-1 w-full p-4 font-mono text-sm bg-gray-900 text-green-400 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                placeholder="# Write your Python code here..."
                spellCheck="false"
                onPaste={(e) => {
                    e.preventDefault();
                    alert("Paste is disabled for this assessment.");
                    // In a real app, log to parent component here
                }}
            />
        </div>
    );
};

export default CodingSection;
