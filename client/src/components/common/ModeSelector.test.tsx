import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ModeSelector from './ModeSelector';

describe('ModeSelector', () => {
  it('renders all three tabs', () => {
    render(<ModeSelector activeMode="notes" onModeChange={() => {}} />);
    expect(screen.getByRole('button', { name: 'Summary' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'PYQ' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Syllabus Graph' })).toBeInTheDocument();
  });

  it('calls onModeChange when a tab is clicked', () => {
    const onModeChange = vi.fn();
    render(<ModeSelector activeMode="notes" onModeChange={onModeChange} />);
    fireEvent.click(screen.getByRole('button', { name: 'PYQ' }));
    expect(onModeChange).toHaveBeenCalledWith('pyq');
  });

  it('highlights the active tab', () => {
    render(<ModeSelector activeMode="syllabus" onModeChange={() => {}} />);
    const activeTab = screen.getByRole('button', { name: 'Syllabus Graph' });
    expect(activeTab.className).toContain('bg-electric-iris');
    expect(activeTab.className).toContain('text-paper-white');
  });
});
