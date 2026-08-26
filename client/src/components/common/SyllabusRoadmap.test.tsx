import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import SyllabusRoadmap from './SyllabusRoadmap';
import type { SyllabusPayload } from '../../types/api.types';

const mockPayload: SyllabusPayload = {
  course_title: 'Data Structures & Algorithms',
  total_units: 2,
  learning_path: [
    {
      unit_number: 1,
      title: 'Arrays & Linked Lists',
      estimated_hours: 10,
      topics: ['Arrays', 'Linked Lists', 'Time Complexity'],
      cognitive_level: 'Remember',
    },
    {
      unit_number: 2,
      title: 'Trees & Graphs',
      estimated_hours: 15,
      topics: ['Binary Trees', 'Graph Traversal'],
      cognitive_level: 'Analyze',
    },
  ],
  priority_topics: [
    { topic: 'Linked Lists', weightage: 80 },
    { topic: 'Graph Traversal', weightage: 90 },
  ],
};

describe('SyllabusRoadmap', () => {
  it('renders course title and estimated hours', () => {
    render(<SyllabusRoadmap payload={mockPayload} />);
    expect(screen.getByText('Data Structures & Algorithms')).toBeInTheDocument();
    expect(screen.getByText(/2 units · 25h estimated/)).toBeInTheDocument();
  });

  it('renders unit titles', () => {
    render(<SyllabusRoadmap payload={mockPayload} />);
    expect(screen.getByText('Unit 1: Arrays & Linked Lists')).toBeInTheDocument();
    expect(screen.getByText('Unit 2: Trees & Graphs')).toBeInTheDocument();
  });

  it('renders topics for each unit', () => {
    render(<SyllabusRoadmap payload={mockPayload} />);
    expect(screen.getByText('Arrays')).toBeInTheDocument();
    expect(screen.getByText('Linked Lists')).toBeInTheDocument();
    expect(screen.getByText('Binary Trees')).toBeInTheDocument();
    expect(screen.getByText('Graph Traversal')).toBeInTheDocument();
  });

  it('renders priority stars for priority topics', () => {
    const { container } = render(<SyllabusRoadmap payload={mockPayload} />);
    const stars = container.querySelectorAll('.text-hi-yellow');
    expect(stars.length).toBe(2);
  });

  it('renders cognitive level badges', () => {
    render(<SyllabusRoadmap payload={mockPayload} />);
    expect(screen.getAllByText('Remember').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Analyze').length).toBeGreaterThanOrEqual(1);
  });

  it('renders estimated hours per unit', () => {
    render(<SyllabusRoadmap payload={mockPayload} />);
    expect(screen.getByText('10h')).toBeInTheDocument();
    expect(screen.getByText('15h')).toBeInTheDocument();
  });
});
