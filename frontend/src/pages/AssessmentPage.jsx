import React from 'react';
import { useParams } from 'react-router-dom';

const AssessmentPage = () => {
    const { candidateId } = useParams();

    return (
        <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
            <h1 className="text-3xl font-bold text-blue-600 mb-4">Assessment Page</h1>
            <p>Candidate ID: {candidateId}</p>
            <p>Assessment interface will be implemented here.</p>
        </div>
    );
};

export default AssessmentPage;
