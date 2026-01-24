// Mock data for frontend development

export const mockCandidates = [
  {
    id: '1',
    name: 'Sarah Johnson',
    email: 'sarah.johnson@email.com',
    phone: '+1-555-0123',
    aiMatchScore: 92,
    status: 'Applied',
    appliedDate: '2025-01-15',
    aiPros: [
      '8+ years of full-stack development experience',
      'Strong background in React and Node.js',
      'Led teams of 5+ developers',
      'Published technical articles and open-source contributions'
    ],
    aiCons: [
      'Limited experience with Python/Django',
      'No direct experience with our tech stack'
    ],
    resumeUrl: null,
    assessmentCompleted: false,
    assessmentScheduled: null
  },
  {
    id: '2',
    name: 'Michael Chen',
    email: 'michael.chen@email.com',
    phone: '+1-555-0124',
    aiMatchScore: 87,
    status: 'Scheduled',
    appliedDate: '2025-01-14',
    aiPros: [
      'Strong algorithm and data structure skills',
      '5 years of experience with modern frameworks',
      'Excellent problem-solving abilities'
    ],
    aiCons: [
      'Less experience in leadership roles',
      'Gap in employment history (6 months)'
    ],
    resumeUrl: null,
    assessmentCompleted: false,
    assessmentScheduled: '2025-01-20T10:00:00'
  },
  {
    id: '3',
    name: 'Emily Rodriguez',
    email: 'emily.rodriguez@email.com',
    phone: '+1-555-0125',
    aiMatchScore: 78,
    status: 'Completed',
    appliedDate: '2025-01-12',
    aiPros: [
      'Solid technical foundation',
      'Quick learner with diverse project experience',
      'Good communication skills'
    ],
    aiCons: [
      'Only 3 years of professional experience',
      'Limited exposure to large-scale systems'
    ],
    resumeUrl: null,
    assessmentCompleted: true,
    assessmentScheduled: '2025-01-18T14:00:00',
    assessmentScore: 82
  }
];

export const mockAssessment = {
  id: 'assessment-1',
  candidateId: '2',
  scheduledTime: '2025-01-20T10:00:00',
  duration: 90,
  sections: [
    {
      id: 'mcq',
      title: 'Technical Knowledge',
      type: 'mcq',
      questions: [
        {
          id: 'q1',
          question: 'What is the time complexity of binary search?',
          options: ['O(n)', 'O(log n)', 'O(n log n)', 'O(1)'],
          correctAnswer: 1
        },
        {
          id: 'q2',
          question: 'Which React hook is used for side effects?',
          options: ['useState', 'useEffect', 'useContext', 'useReducer'],
          correctAnswer: 1
        },
        {
          id: 'q3',
          question: 'What does REST stand for?',
          options: [
            'Remote Event State Transfer',
            'Representational State Transfer',
            'Resource Efficient State Transfer',
            'Rapid Execution State Transfer'
          ],
          correctAnswer: 1
        }
      ]
    },
    {
      id: 'coding',
      title: 'Coding Challenge',
      type: 'coding',
      problem: {
        title: 'Two Sum Problem',
        description: 'Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice.\n\nExample:\nInput: nums = [2,7,11,15], target = 9\nOutput: [0,1]\nExplanation: Because nums[0] + nums[1] == 9, we return [0, 1].',
        starterCode: 'function twoSum(nums, target) {\n  // Write your solution here\n  \n}',
        timeLimit: 30
      }
    },
    {
      id: 'psychometric',
      title: 'Behavioral Assessment',
      type: 'psychometric',
      scenarios: [
        {
          id: 's1',
          scenario: 'Your team is facing a tight deadline, and a critical bug is discovered. What do you do?',
          options: [
            'Work overtime to fix it immediately',
            'Assess impact and prioritize based on severity',
            'Delegate to another team member',
            'Request deadline extension'
          ]
        },
        {
          id: 's2',
          scenario: 'You disagree with a technical decision made by your team lead. How do you handle it?',
          options: [
            'Follow the decision without question',
            'Present your concerns with supporting data',
            'Escalate to higher management',
            'Implement your own solution'
          ]
        }
      ]
    }
  ]
};

export const mockInterviewer = {
  id: 'interviewer-1',
  email: 'interviewer@company.com',
  name: 'John Smith',
  role: 'Senior Recruiter'
};
