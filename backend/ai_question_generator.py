"""
AI Question Generator Module
Generates personalized assessment questions based on candidate resume
Uses OpenAI API to create MCQ, coding problems, and test cases
"""

import os
import json
import random
from openai import OpenAI
import httpx
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class AIQuestionGenerator:
    """
    AI-powered question generator for personalized assessments
    Creates MCQ, coding problems, and test cases based on candidate skills
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI Question Generator
        
        Args:
            api_key: OpenAI API key (if not provided, reads from environment)
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        
        if not self.api_key:
            logger.warning("OpenAI API key not found. Will use fallback questions.")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except TypeError as e:
                if "proxies" in str(e):
                    proxy = (
                        os.environ.get("HTTPS_PROXY")
                        or os.environ.get("https_proxy")
                        or os.environ.get("HTTP_PROXY")
                        or os.environ.get("http_proxy")
                    )
                    http_client = httpx.Client(proxies=proxy) if proxy else httpx.Client()
                    self.client = OpenAI(api_key=self.api_key, http_client=http_client)
                else:
                    raise
        
        self.model = "gpt-4o-mini"
    
    def generate_mcq_questions(self, skills: List[str], count: int = 10, difficulty: str = "mixed") -> List[Dict]:
        """
        Generate MCQ questions based on candidate skills
        
        Args:
            skills: List of skills from the candidate's resume
            count: Number of questions to generate
            difficulty: "easy", "medium", "hard", or "mixed"
            
        Returns:
            List of MCQ question dictionaries
        """
        if not self.client or not skills:
            return self._get_fallback_mcq_questions(count)
        
        skills_str = ", ".join(skills[:10])  # Limit to top 10 skills
        
        prompt = f"""Generate {count} multiple choice questions to assess a software developer with these skills: {skills_str}

Requirements:
- Questions should test practical knowledge, not just theory
- Include a mix of conceptual and problem-solving questions
- Difficulty: {difficulty}
- Each question should have exactly 4 options
- Only ONE option should be correct

Return a JSON array with this exact structure:
[
    {{
        "id": 1,
        "question": "The question text",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "The exact text of the correct option",
        "category": "skill_category",
        "difficulty": "easy|medium|hard",
        "time_limit": 60
    }}
]

Return ONLY valid JSON, no markdown or explanations."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert technical interviewer creating assessment questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content.strip()
            # Clean up potential markdown formatting
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            questions = json.loads(content)
            
            # Validate and fix IDs
            for i, q in enumerate(questions):
                q['id'] = i + 1
                if 'time_limit' not in q:
                    q['time_limit'] = 60
                if 'difficulty' not in q:
                    q['difficulty'] = 'medium'
            
            logger.info(f"Generated {len(questions)} MCQ questions for skills: {skills_str}")
            return questions[:count]
            
        except Exception as e:
            logger.error(f"Error generating MCQ questions: {e}")
            return self._get_fallback_mcq_questions(count)
    
    def generate_coding_problem(self, skills: List[str], difficulty: str = "medium") -> Dict:
        """
        Generate a coding problem based on candidate skills
        
        Args:
            skills: List of skills from the candidate's resume
            difficulty: "easy", "medium", or "hard"
            
        Returns:
            Coding problem dictionary with test cases
        """
        if not self.client or not skills:
            return self._get_fallback_coding_problem(difficulty)
        
        # Identify programming languages from skills
        languages = []
        lang_keywords = {
            'python': ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy'],
            'javascript': ['javascript', 'js', 'node', 'nodejs', 'react', 'vue', 'angular', 'typescript'],
            'java': ['java', 'spring', 'springboot', 'maven', 'gradle'],
            'cpp': ['c++', 'cpp', 'c']
        }
        
        skills_lower = [s.lower() for s in skills]
        for lang, keywords in lang_keywords.items():
            if any(kw in skill for skill in skills_lower for kw in keywords):
                languages.append(lang)
        
        if not languages:
            languages = ['python', 'javascript']
        
        skills_str = ", ".join(skills[:8])
        
        prompt = f"""Create a coding problem for a developer with these skills: {skills_str}

Difficulty: {difficulty}
Target Languages: {', '.join(languages)}

The problem should:
- Be solvable in 20-30 minutes
- Test practical coding skills relevant to the candidate's background
- Have clear input/output specifications
- Include edge cases in test cases

Return JSON with this exact structure:
{{
    "id": 1,
    "title": "Problem Title",
    "description": "Full problem description with examples",
    "example": "Input: [example]\\nOutput: [example]\\nExplanation: [brief explanation]",
    "difficulty": "{difficulty}",
    "constraints": ["Constraint 1", "Constraint 2"],
    "hints": ["Hint 1", "Hint 2"],
    "starter_code": {{
        "python": "def solution(params):\\n    # Your code here\\n    pass",
        "javascript": "function solution(params) {{\\n    // Your code here\\n}}",
        "java": "public class Solution {{\\n    public ReturnType solution(params) {{\\n        // Your code here\\n    }}\\n}}"
    }},
    "test_cases": [
        {{"input": "input_value", "expected": "expected_output", "is_hidden": false}},
        {{"input": "edge_case", "expected": "expected_output", "is_hidden": false}},
        {{"input": "hidden_test", "expected": "expected_output", "is_hidden": true}}
    ],
    "solution_approach": "Brief explanation of the optimal approach",
    "time_complexity": "O(n)",
    "space_complexity": "O(1)"
}}

Return ONLY valid JSON, no markdown."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at creating coding challenges for technical interviews."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            problem = json.loads(content)
            problem['id'] = 1
            
            logger.info(f"Generated coding problem: {problem.get('title', 'Unknown')}")
            return problem
            
        except Exception as e:
            logger.error(f"Error generating coding problem: {e}")
            return self._get_fallback_coding_problem(difficulty)
    
    def generate_test_cases(self, problem_description: str, count: int = 5) -> List[Dict]:
        """
        Generate additional test cases for a coding problem
        
        Args:
            problem_description: The coding problem description
            count: Number of test cases to generate
            
        Returns:
            List of test case dictionaries
        """
        if not self.client:
            return []
        
        prompt = f"""Given this coding problem:
{problem_description}

Generate {count} test cases including:
- 2 basic cases
- 2 edge cases (empty input, single element, large numbers, etc.)
- 1 complex case

Return JSON array:
[
    {{"input": "value", "expected": "output", "is_hidden": false, "description": "Basic case"}},
    {{"input": "value", "expected": "output", "is_hidden": true, "description": "Edge case"}}
]

Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at creating comprehensive test cases."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating test cases: {e}")
            return []
    
    def generate_psychometric_scenarios(self, job_role: str = "Software Developer", count: int = 3) -> List[Dict]:
        """
        Generate psychometric/behavioral scenarios
        
        Args:
            job_role: The role the candidate is applying for
            count: Number of scenarios to generate
            
        Returns:
            List of scenario dictionaries
        """
        if not self.client:
            return self._get_fallback_psychometric_scenarios(count)
        
        prompt = f"""Create {count} workplace scenario questions for a {job_role} position.

Each scenario should:
- Present a realistic workplace situation
- Have 4 response options showing different approaches
- Assess traits like: teamwork, problem-solving, communication, leadership, adaptability, integrity

Return JSON array:
[
    {{
        "id": 1,
        "scenario": "Detailed scenario description",
        "options": [
            "Response option 1",
            "Response option 2", 
            "Response option 3",
            "Response option 4"
        ],
        "trait": "trait_being_assessed",
        "optimal_choice": 0
    }}
]

The optimal_choice is the index (0-3) of the best response.
Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in workplace psychology and behavioral assessment."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()
            
            scenarios = json.loads(content)
            for i, s in enumerate(scenarios):
                s['id'] = i + 1
            
            return scenarios[:count]
            
        except Exception as e:
            logger.error(f"Error generating psychometric scenarios: {e}")
            return self._get_fallback_psychometric_scenarios(count)
    
    def _get_fallback_mcq_questions(self, count: int) -> List[Dict]:
        """Fallback MCQ questions when AI is unavailable"""
        questions = [
            {
                'id': 1,
                'question': 'What is the time complexity of binary search?',
                'options': ['O(n)', 'O(log n)', 'O(n²)', 'O(1)'],
                'correct_answer': 'O(log n)',
                'category': 'algorithms',
                'difficulty': 'easy',
                'time_limit': 60
            },
            {
                'id': 2,
                'question': 'Which data structure uses LIFO (Last In, First Out)?',
                'options': ['Queue', 'Stack', 'Linked List', 'Tree'],
                'correct_answer': 'Stack',
                'category': 'data-structures',
                'difficulty': 'easy',
                'time_limit': 60
            },
            {
                'id': 3,
                'question': 'What does REST stand for in web development?',
                'options': [
                    'Remote Execution Service Transfer',
                    'Representational State Transfer',
                    'Resource Execution State Transfer',
                    'Remote State Transfer'
                ],
                'correct_answer': 'Representational State Transfer',
                'category': 'web-development',
                'difficulty': 'easy',
                'time_limit': 60
            },
            {
                'id': 4,
                'question': 'Which HTTP method is idempotent?',
                'options': ['POST', 'PUT', 'PATCH', 'All of the above'],
                'correct_answer': 'PUT',
                'category': 'web-development',
                'difficulty': 'medium',
                'time_limit': 60
            },
            {
                'id': 5,
                'question': 'What is the purpose of an index in a database?',
                'options': [
                    'To store data permanently',
                    'To speed up data retrieval',
                    'To encrypt data',
                    'To normalize tables'
                ],
                'correct_answer': 'To speed up data retrieval',
                'category': 'databases',
                'difficulty': 'easy',
                'time_limit': 60
            },
            {
                'id': 6,
                'question': 'Which sorting algorithm has the best average case time complexity?',
                'options': ['Bubble Sort - O(n²)', 'Quick Sort - O(n log n)', 'Selection Sort - O(n²)', 'Insertion Sort - O(n²)'],
                'correct_answer': 'Quick Sort - O(n log n)',
                'category': 'algorithms',
                'difficulty': 'medium',
                'time_limit': 60
            },
            {
                'id': 7,
                'question': 'What is a closure in programming?',
                'options': [
                    'A function that closes the program',
                    'A function that has access to variables from its outer scope',
                    'A method to close database connections',
                    'A type of loop structure'
                ],
                'correct_answer': 'A function that has access to variables from its outer scope',
                'category': 'programming-concepts',
                'difficulty': 'medium',
                'time_limit': 60
            },
            {
                'id': 8,
                'question': 'Which of these is NOT a principle of SOLID?',
                'options': [
                    'Single Responsibility Principle',
                    'Open/Closed Principle',
                    'Liskov Substitution Principle',
                    'Data Encapsulation Principle'
                ],
                'correct_answer': 'Data Encapsulation Principle',
                'category': 'software-design',
                'difficulty': 'medium',
                'time_limit': 60
            },
            {
                'id': 9,
                'question': 'What is the difference between == and === in JavaScript?',
                'options': [
                    'No difference',
                    '=== checks both value and type, == only checks value',
                    '== checks both value and type, === only checks value',
                    '=== is faster than =='
                ],
                'correct_answer': '=== checks both value and type, == only checks value',
                'category': 'javascript',
                'difficulty': 'easy',
                'time_limit': 60
            },
            {
                'id': 10,
                'question': 'What does SQL JOIN do?',
                'options': [
                    'Combines rows from two or more tables',
                    'Deletes duplicate rows',
                    'Creates a new table',
                    'Sorts table data'
                ],
                'correct_answer': 'Combines rows from two or more tables',
                'category': 'databases',
                'difficulty': 'easy',
                'time_limit': 60
            }
        ]
        return questions[:count]
    
    def _get_fallback_coding_problem(self, difficulty: str) -> Dict:
        """Fallback coding problems when AI is unavailable"""
        problems = {
            'easy': {
                'id': 1,
                'title': 'Two Sum',
                'description': '''Given an array of integers `nums` and an integer `target`, return the indices of the two numbers that add up to `target`.

You may assume that each input has exactly one solution, and you may not use the same element twice.

You can return the answer in any order.''',
                'example': '''Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].''',
                'difficulty': 'easy',
                'constraints': [
                    '2 <= nums.length <= 10^4',
                    '-10^9 <= nums[i] <= 10^9',
                    '-10^9 <= target <= 10^9',
                    'Only one valid answer exists'
                ],
                'hints': [
                    'A brute force approach would check every pair of numbers',
                    'Can you use a hash map to improve the time complexity?'
                ],
                'starter_code': {
                    'python': 'def two_sum(nums, target):\n    # Your code here\n    pass',
                    'javascript': 'function twoSum(nums, target) {\n    // Your code here\n}',
                    'java': 'class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        // Your code here\n        return new int[]{};\n    }\n}'
                },
                'test_cases': [
                    {'input': '[2,7,11,15], 9', 'expected': '[0,1]', 'is_hidden': False},
                    {'input': '[3,2,4], 6', 'expected': '[1,2]', 'is_hidden': False},
                    {'input': '[3,3], 6', 'expected': '[0,1]', 'is_hidden': False},
                    {'input': '[1,2,3,4,5], 9', 'expected': '[3,4]', 'is_hidden': True},
                    {'input': '[-1,-2,-3,-4,-5], -8', 'expected': '[2,4]', 'is_hidden': True}
                ],
                'solution_approach': 'Use a hash map to store seen numbers and their indices',
                'time_complexity': 'O(n)',
                'space_complexity': 'O(n)'
            },
            'medium': {
                'id': 2,
                'title': 'Valid Parentheses',
                'description': '''Given a string `s` containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.

An input string is valid if:
1. Open brackets must be closed by the same type of brackets.
2. Open brackets must be closed in the correct order.
3. Every close bracket has a corresponding open bracket of the same type.''',
                'example': '''Input: s = "()[]{}"
Output: true

Input: s = "(]"
Output: false''',
                'difficulty': 'medium',
                'constraints': [
                    '1 <= s.length <= 10^4',
                    's consists of parentheses only: ()[]{}'
                ],
                'hints': [
                    'Use a stack to keep track of opening brackets',
                    'When you encounter a closing bracket, check if it matches the top of the stack'
                ],
                'starter_code': {
                    'python': 'def is_valid(s):\n    # Your code here\n    pass',
                    'javascript': 'function isValid(s) {\n    // Your code here\n}',
                    'java': 'class Solution {\n    public boolean isValid(String s) {\n        // Your code here\n        return false;\n    }\n}'
                },
                'test_cases': [
                    {'input': '"()"', 'expected': 'true', 'is_hidden': False},
                    {'input': '"()[]{}"', 'expected': 'true', 'is_hidden': False},
                    {'input': '"(]"', 'expected': 'false', 'is_hidden': False},
                    {'input': '"([)]"', 'expected': 'false', 'is_hidden': True},
                    {'input': '"{[]}"', 'expected': 'true', 'is_hidden': True},
                    {'input': '""', 'expected': 'true', 'is_hidden': True}
                ],
                'solution_approach': 'Use a stack - push opening brackets, pop and match for closing brackets',
                'time_complexity': 'O(n)',
                'space_complexity': 'O(n)'
            },
            'hard': {
                'id': 3,
                'title': 'Merge K Sorted Lists',
                'description': '''You are given an array of `k` linked-lists `lists`, each linked-list is sorted in ascending order.

Merge all the linked-lists into one sorted linked-list and return it.''',
                'example': '''Input: lists = [[1,4,5],[1,3,4],[2,6]]
Output: [1,1,2,3,4,4,5,6]
Explanation: The linked-lists are:
[1->4->5, 1->3->4, 2->6]
Merging them into one sorted list: 1->1->2->3->4->4->5->6''',
                'difficulty': 'hard',
                'constraints': [
                    'k == lists.length',
                    '0 <= k <= 10^4',
                    '0 <= lists[i].length <= 500',
                    '-10^4 <= lists[i][j] <= 10^4'
                ],
                'hints': [
                    'Consider using a min-heap/priority queue',
                    'You can also use divide and conquer approach'
                ],
                'starter_code': {
                    'python': 'def merge_k_lists(lists):\n    # Your code here\n    pass',
                    'javascript': 'function mergeKLists(lists) {\n    // Your code here\n}',
                    'java': 'class Solution {\n    public ListNode mergeKLists(ListNode[] lists) {\n        // Your code here\n        return null;\n    }\n}'
                },
                'test_cases': [
                    {'input': '[[1,4,5],[1,3,4],[2,6]]', 'expected': '[1,1,2,3,4,4,5,6]', 'is_hidden': False},
                    {'input': '[]', 'expected': '[]', 'is_hidden': False},
                    {'input': '[[]]', 'expected': '[]', 'is_hidden': True},
                    {'input': '[[1],[2],[3]]', 'expected': '[1,2,3]', 'is_hidden': True}
                ],
                'solution_approach': 'Use a min-heap to efficiently get the smallest element among k lists',
                'time_complexity': 'O(N log k) where N is total elements',
                'space_complexity': 'O(k)'
            }
        }
        return problems.get(difficulty, problems['medium'])
    
    def _get_fallback_psychometric_scenarios(self, count: int) -> List[Dict]:
        """Fallback psychometric scenarios when AI is unavailable"""
        scenarios = [
            {
                'id': 1,
                'scenario': 'Your teammate misses a critical deadline that affects your work. How do you respond?',
                'options': [
                    'Immediately escalate to management',
                    'Have a private conversation to understand what happened and offer help',
                    'Take over their work without discussing',
                    'Ignore it and adjust your timeline'
                ],
                'trait': 'teamwork',
                'optimal_choice': 1
            },
            {
                'id': 2,
                'scenario': 'You discover a potential security vulnerability in production code during a routine review. What do you do?',
                'options': [
                    'Fix it immediately and deploy without review',
                    'Document it and report to the security team and your manager immediately',
                    'Wait until the next sprint to address it',
                    'Ignore it if it seems unlikely to be exploited'
                ],
                'trait': 'responsibility',
                'optimal_choice': 1
            },
            {
                'id': 3,
                'scenario': 'You strongly disagree with a technical decision made by a senior developer. How do you handle this?',
                'options': [
                    'Accept their decision without question since they are more senior',
                    'Respectfully present your concerns with data and alternative solutions',
                    'Go over their head to management',
                    'Implement your preferred solution anyway'
                ],
                'trait': 'communication',
                'optimal_choice': 1
            },
            {
                'id': 4,
                'scenario': 'You are assigned a task using a technology you have never worked with before. What is your approach?',
                'options': [
                    'Tell your manager you cannot do it',
                    'Research and learn the technology, asking for help when needed',
                    'Pretend you know it and figure it out as you go',
                    'Delegate it to someone else'
                ],
                'trait': 'adaptability',
                'optimal_choice': 1
            },
            {
                'id': 5,
                'scenario': 'During a code review, you notice a colleague has made the same mistake you pointed out before. How do you respond?',
                'options': [
                    'Reject the PR with a harsh comment',
                    'Point out the issue constructively and offer to pair program to help',
                    'Approve it anyway to avoid conflict',
                    'Report them to management for repeated mistakes'
                ],
                'trait': 'leadership',
                'optimal_choice': 1
            }
        ]
        return scenarios[:count]


# Singleton instance
_generator_instance = None

def get_ai_question_generator() -> AIQuestionGenerator:
    """Get or create the AI question generator singleton"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = AIQuestionGenerator()
    return _generator_instance
