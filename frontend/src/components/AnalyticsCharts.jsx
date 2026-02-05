import React from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

/**
 * Candidate Pipeline Funnel Chart
 * Shows conversion rates through hiring stages
 */
export const PipelineChart = ({ data }) => {
    const COLORS = ['#4f46e5', '#6366f1', '#818cf8', '#a5b4fc', '#c7d2fe'];

    return (
        <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="stage" type="category" />
                <Tooltip />
                <Bar dataKey="count" fill="#4f46e5">
                    {data?.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
};

/**
 * Applications Over Time Chart
 * Line chart showing application trends
 */
export const ApplicationsOverTime = ({ data }) => (
    <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line
                type="monotone"
                dataKey="applications"
                stroke="#4f46e5"
                strokeWidth={2}
                dot={{ fill: '#4f46e5', r: 4 }}
            />
        </LineChart>
    </ResponsiveContainer>
);

/**
 * Status Distribution Pie Chart
 * Shows breakdown of candidate statuses
 */
export const StatusDistribution = ({ data }) => {
    const COLORS = ['#10b981', '#f59e0b', '#ef4444', '#6366f1', '#8b5cf6'];

    return (
        <ResponsiveContainer width="100%" height={300}>
            <PieChart>
                <Pie
                    data={data}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                >
                    {data?.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                </Pie>
                <Tooltip />
            </PieChart>
        </ResponsiveContainer>
    );
};

/**
 * Department Breakdown Bar Chart
 * Shows candidates by department
 */
export const DepartmentBreakdown = ({ data }) => (
    <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="department" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="candidates" fill="#4f46e5" />
            <Bar dataKey="hired" fill="#10b981" />
        </BarChart>
    </ResponsiveContainer>
);

export default {
    PipelineChart,
    ApplicationsOverTime,
    StatusDistribution,
    DepartmentBreakdown,
};
