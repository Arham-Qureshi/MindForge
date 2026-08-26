import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PYQPreview from './PYQPreview';
import type { PYQAnalysisPayload } from '../../types/api.types';

const mockPayload: PYQAnalysisPayload = {
  topic_frequency: [
    { topic: 'Recursion', percentage: 0.75, question_count: 12 },
    { topic: 'Sorting', percentage: 0.5, question_count: 8 },
  ],
  predicted_questions: [
    {
      question: 'Explain the time complexity of merge sort.',
      bloom_level: 'Analyze',
      expected_marks: 10,
      probability_score: 0.85,
    },
    {
      question: 'Implement a recursive solution for Tower of Hanoi.',
      bloom_level: 'Apply',
      expected_marks: 15,
      probability_score: 0.6,
    },
  ],
};

describe('PYQPreview', () => {
  it('renders topic frequency section', () => {
    render(<PYQPreview payload={mockPayload} />);
    expect(screen.getByText('Topic Frequency')).toBeInTheDocument();
    expect(screen.getByText('Recursion')).toBeInTheDocument();
    expect(screen.getByText('Sorting')).toBeInTheDocument();
  });

  it('renders question counts and percentages', () => {
    render(<PYQPreview payload={mockPayload} />);
    expect(screen.getByText('12 questions')).toBeInTheDocument();
    expect(screen.getByText('8 questions')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('renders predicted questions section', () => {
    render(<PYQPreview payload={mockPayload} />);
    expect(screen.getByText('Predicted Questions')).toBeInTheDocument();
    expect(screen.getByText('Explain the time complexity of merge sort.')).toBeInTheDocument();
    expect(screen.getByText('Implement a recursive solution for Tower of Hanoi.')).toBeInTheDocument();
  });

  it('renders Bloom level badges', () => {
    render(<PYQPreview payload={mockPayload} />);
    expect(screen.getByText('Analyze')).toBeInTheDocument();
    expect(screen.getByText('Apply')).toBeInTheDocument();
  });

  it('renders marks and probability scores', () => {
    render(<PYQPreview payload={mockPayload} />);
    expect(screen.getByText(/10 marks · 85%/)).toBeInTheDocument();
    expect(screen.getByText(/15 marks · 60%/)).toBeInTheDocument();
  });
});
