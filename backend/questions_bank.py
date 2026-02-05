"""
Question bank for assessments
Provides MCQ questions, coding problems, and psychometric scenarios
"""

def get_mcq_questions(count=10):
    """Return sample MCQ questions"""
    questions = [
        {
            'id': 1,
            'question': 'What is the time complexity of binary search?',
            'options': ['O(n)', 'O(log n)', 'O(n^2)', 'O(1)'],
            'correct_answer': 'O(log n)',
            'category': 'algorithms'
        },
        {
            'id': 2,
            'question': 'Which data structure uses LIFO?',
            'options': ['Queue', 'Stack', 'Array', 'Tree'],
            'correct_answer': 'Stack',
            'category': 'data-structures'
        },
        {
            'id': 3,
            'question': 'What does REST stand for?',
            'options': [
                'Remote Execution Service Transfer',
                'Representational State Transfer',
                'Resource Execution State Transfer',
                'Remote State Transfer'
            ],
            'correct_answer': 'Representational State Transfer',
            'category': 'web-development'
        }
    ]
    return questions[:count]

def get_coding_problem(difficulty="medium"):
    """Return a sample coding problem"""
    problems = {
        'easy': {
            'id': 1,
            'title': 'Two Sum',
            'description': 'Given an array of integers and a target, return indices of two numbers that add up to target.',
            'difficulty': 'easy',
            'starter_code': {
                'python': 'def two_sum(nums, target):\n    # Your code here\n    pass',
                'javascript': 'function twoSum(nums, target) {\n    // Your code here\n}',
                'java': 'public int[] twoSum(int[] nums, int target) {\n    // Your code here\n}'
            },
            'test_cases': [
                {'input': '[2,7,11,15], 9', 'expected': '[0,1]'},
                {'input': '[3,2,4], 6', 'expected': '[1,2]'}
            ]
        },
        'medium': {
            'id': 2,
            'title': 'Valid Parentheses',
            'description': 'Given a string containing just the characters \'(\', \')\', \'{\', \'}\', \'[\' and \']\', determine if the input string is valid.',
            'difficulty': 'medium',
            'starter_code': {
                'python': 'def is_valid(s):\n    # Your code here\n    pass',
                'javascript': 'function isValid(s) {\n    // Your code here\n}',
                'java': 'public boolean isValid(String s) {\n    // Your code here\n}'
            },
            'test_cases': [
                {'input': '"()"', 'expected': 'true'},
                {'input': '"()[]{}"', 'expected': 'true'},
                {'input': '"(]"', 'expected': 'false'}
            ]
        }
    }
    return problems.get(difficulty, problems['medium'])

def get_psychometric_scenarios(count=8):
    """Return sample nuanced psychometric scenarios with option-specific trait scores"""
    scenarios = [
        {
            'id': 1,
            'scenario': 'Your team is falling behind on a deadline. A colleague suggests cutting corners on quality to meet the date. How do you approach this?',
            'options': [
                'Prioritize the deadline and follow the suggestion.',
                'Organize a team sync to re-prioritize and find a middle ground.',
                'Work extra hours alone to maintain quality and meet the deadline.',
                'Refuse to compromise and notify the project lead about the delay.'
            ],
            'option_scores': [3, 8, 7, 10],
            'trait': 'Integrity'
        },
        {
            'id': 2,
            'scenario': 'During a meeting, you realize your proposed solution has a subtle but significant flaw. The team is already leaning towards it. What do you do?',
            'options': [
                'Immediately point out the flaw and suggest starting over.',
                'Stay quiet to avoid public embarrassment and fix it later.',
                'Wait until after the meeting to discuss it with the lead.',
                'Gradually steer the conversation towards other alternatives.'
            ],
            'option_scores': [10, 2, 6, 5],
            'trait': 'Transparency'
        },
        {
            'id': 3,
            'scenario': 'A difficult client consistently changes requirements mid-sprint, causing team frustration. How do you navigate this?',
            'options': [
                'Request to be removed from the project.',
                'Strictly follow the change request process, even if it delays results.',
                'Schedule a feedback session with the client to align expectations.',
                'Deliver exactly what was last agreed, ignoring new requests.'
            ],
            'option_scores': [2, 6, 10, 4],
            'trait': 'Client Management'
        }
    ]
    return scenarios[:count]
