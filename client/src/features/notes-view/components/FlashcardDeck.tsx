import { useState, useCallback } from 'react';
import type { Flashcard } from '../../../types/api.types';
import { useKeyboardNav } from '../../../hooks/useKeyboardNav';

type FlashcardDeckProps = {
  flashcards: Flashcard[];
  onGenerateMore?: (count: number) => void;
};

export default function FlashcardDeck({ flashcards, onGenerateMore }: FlashcardDeckProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [selectedCount, setSelectedCount] = useState(10);

  const handleNext = useCallback(() => {
    if (currentIndex < flashcards.length - 1) {
      setIsFlipped(false);
      // Small timeout allows the flip back animation to start before content changes
      setTimeout(() => setCurrentIndex(prev => prev + 1), 150);
    }
  }, [currentIndex, flashcards.length]);

  const handlePrev = useCallback(() => {
    if (currentIndex > 0) {
      setIsFlipped(false);
      setTimeout(() => setCurrentIndex(prev => prev - 1), 150);
    }
  }, [currentIndex]);

  const handleFlip = useCallback(() => {
    setIsFlipped(prev => !prev);
  }, []);

  useKeyboardNav({
    onNext: handleNext,
    onPrev: handlePrev,
    onFlip: handleFlip
  });

  if (!flashcards || flashcards.length === 0) {
    return <div className="text-center py-12">No flashcards available.</div>;
  }

  const currentCard = flashcards[currentIndex];

  const getDifficultyColor = (diff: Flashcard['difficulty']) => {
    switch(diff) {
      case 'Easy': return 'bg-jelly-green text-paper-white';
      case 'Medium': return 'bg-hi-yellow text-ink-black';
      case 'Hard': return 'bg-marker-red text-paper-white';
      default: return 'bg-ink-black text-paper-white';
    }
  };

  return (
    <div className="flex flex-col items-center justify-center w-full py-8">
      {/* Progress Indicator */}
      <div className="mb-8 font-martian-mono text-sm bg-frost-blue px-6 py-2 rounded-full border-2 border-ink-black shadow-hard-sm uppercase tracking-wider font-bold">
        Card {currentIndex + 1} of {flashcards.length}
      </div>

      {/* Flashcard Container */}
      <div 
        className={`w-full max-w-[600px] aspect-[4/3] perspective-1000 cursor-pointer group ${isFlipped ? 'flipped' : ''}`}
        onClick={handleFlip}
      >
        <div className="flip-card-inner relative w-full h-full text-center transform-style-3d">
          
          {/* Front */}
          <div className="absolute w-full h-full backface-hidden bg-paper-white border-2 border-ink-black rounded-[24px] shadow-hard-md flex items-center justify-center p-8 hover-press">
            <h2 className="font-haas-grot-disp text-2xl md:text-3xl font-bold text-ink-black text-center">
              {currentCard.front}
            </h2>
            <div className="absolute bottom-6 font-martian-mono text-sm text-ink-black/60 flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">touch_app</span> 
              Tap or Space to flip
            </div>
          </div>
          
          {/* Back */}
          <div className="absolute w-full h-full backface-hidden rotate-y-180 bg-frost-blue border-2 border-ink-black rounded-[24px] shadow-hard-md flex flex-col items-center justify-center p-10 hover-press overflow-y-auto">
            <p className="font-haas-grot-text text-lg md:text-xl text-ink-black text-center font-bold">
              {currentCard.back}
            </p>
            <div className="mt-8 flex gap-3 flex-wrap justify-center">
              <span className={`font-martian-mono text-xs uppercase px-3 py-1 rounded-full border-2 border-ink-black font-bold ${getDifficultyColor(currentCard.difficulty)}`}>
                {currentCard.difficulty}
              </span>
              <span className="font-martian-mono text-xs uppercase px-3 py-1 rounded-full border-2 border-ink-black bg-electric-iris text-paper-white font-bold">
                {currentCard.bloom_category}
              </span>
            </div>
          </div>
          
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-12 flex flex-wrap justify-center gap-4 w-full max-w-[600px]">
        <button
          onClick={(e) => { e.stopPropagation(); handlePrev(); }}
          disabled={currentIndex === 0}
          className="flex-1 min-w-[120px] h-[48px] rounded-full border-2 border-ink-black bg-paper-white text-ink-black font-haas-grot-text font-bold shadow-hard-sm hover-press disabled:opacity-50 disabled:shadow-none disabled:translate-y-[2px] transition-all flex items-center justify-center gap-2"
        >
          <span className="material-symbols-outlined text-[20px]">arrow_back</span>
          Prev
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); handleNext(); }}
          className="flex-1 min-w-[140px] h-[48px] rounded-full border-2 border-ink-black bg-hi-yellow text-ink-black font-haas-grot-text font-bold shadow-hard-sm hover-press transition-all flex items-center justify-center gap-2"
        >
          <span className="material-symbols-outlined text-[20px]">check_circle</span>
          Know
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); handleNext(); }}
          disabled={currentIndex === flashcards.length - 1}
          className="flex-1 min-w-[120px] h-[48px] rounded-full border-2 border-ink-black bg-paper-white text-ink-black font-haas-grot-text font-bold shadow-hard-sm hover-press disabled:opacity-50 disabled:shadow-none disabled:translate-y-[2px] transition-all flex items-center justify-center gap-2"
        >
          Next
          <span className="material-symbols-outlined text-[20px]">arrow_forward</span>
        </button>
      </div>
      {onGenerateMore && (
        <div className="mt-6 flex flex-col items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="font-haas-grot-text text-sm font-bold text-ink-black">Generate more:</span>
            {[5, 10, 15].map((count) => (
              <button
                key={count}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedCount(count);
                }}
                className={`rounded-full border-2 border-ink-black px-3 py-1 font-martian-mono text-sm font-bold transition-colors ${
                  selectedCount === count
                    ? 'bg-electric-iris text-paper-white'
                    : 'bg-paper-white text-ink-black hover:bg-frost-blue'
                }`}
              >
                {count}
              </button>
            ))}
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); onGenerateMore(selectedCount); }}
            className="hover-press rounded-full border-2 border-ink-black bg-electric-iris px-6 py-2 font-haas-grot-text text-sm font-bold text-paper-white shadow-hard-sm"
          >
            Generate More Flashcards
          </button>
        </div>
      )}
    </div>
  );
}
