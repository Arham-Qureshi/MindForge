import { useEffect } from 'react';

type KeyboardNavProps = {
  onNext: () => void;
  onPrev: () => void;
  onFlip: () => void;
};

export function useKeyboardNav({ onNext, onPrev, onFlip }: KeyboardNavProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input
      if (
        document.activeElement?.tagName === 'INPUT' ||
        document.activeElement?.tagName === 'TEXTAREA'
      ) {
        return;
      }

      switch (e.code) {
        case 'ArrowRight':
          e.preventDefault();
          onNext();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          onPrev();
          break;
        case 'Space':
        case 'Enter':
          e.preventDefault();
          onFlip();
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onNext, onPrev, onFlip]);
}
