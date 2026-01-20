import React from 'react';

const MCQSection = ({ question, onAnswer, currentAnswer }) => {
    return (
        <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-4 text-gray-800">{question.text}</h3>
            <div className="space-y-3">
                {question.options.map((option, index) => (
                    <label key={index} className={`flex items-center p-4 border rounded-lg cursor-pointer transition-colors ${currentAnswer === option ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'}`}>
                        <input
                            type="radio"
                            name="mcq-option"
                            value={option}
                            checked={currentAnswer === option}
                            onChange={() => onAnswer(option)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                        />
                        <span className="ml-3 text-gray-700">{option}</span>
                    </label>
                ))}
            </div>
        </div>
    );
};

export default MCQSection;
