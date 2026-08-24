import { useRef, useState } from 'react';
import { useFileUpload } from '../../features/document-upload/hooks/useFileUpload';

export default function Dropzone() {
  const { status, statusMessage, error, upload, reset } = useFileUpload();
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      upload(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      upload(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const isProcessing = ['validating', 'uploading', 'classifying', 'extracting'].includes(status);

  return (
    <div className="mx-auto w-full max-w-2xl py-12">
      <div 
        onClick={isProcessing ? undefined : triggerFileInput}
        onDragOver={isProcessing ? undefined : handleDragOver}
        onDragLeave={isProcessing ? undefined : handleDragLeave}
        onDrop={isProcessing ? undefined : handleDrop}
        className={`relative flex flex-col items-center justify-center rounded-3xl border-2 border-dashed bg-paper-white p-12 text-center transition-all duration-200 ${
          isProcessing ? 'cursor-default border-ink-black shadow-hard-lg' :
          isDragOver ? 'border-solid border-electric-iris shadow-hard-sm -translate-y-1 cursor-pointer' : 'border-ink-black/20 shadow-hard-lg hover-press cursor-pointer hover:border-electric-iris'
        }`}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          className="hidden" 
          accept="application/pdf"
          onChange={handleFileInputChange}
          disabled={isProcessing}
        />

        {status === 'error' && (
          <div className="mb-6 flex w-full flex-col items-center gap-3 rounded-lg border-2 border-marker-red bg-marker-red/10 p-4 text-marker-red">
            <span className="material-symbols-outlined text-3xl">error</span>
            <p className="font-haas-grot-text font-bold">{error}</p>
            <button 
              onClick={(e) => { e.stopPropagation(); reset(); }}
              className="mt-2 rounded-full border-2 border-marker-red bg-paper-white px-4 py-1 text-sm font-bold text-marker-red transition-transform hover:scale-105"
            >
              Try Again
            </button>
          </div>
        )}

        {isProcessing && (
          <div className="flex flex-col items-center gap-6 py-8">
            <div className="relative flex h-16 w-16 items-center justify-center">
              <div className="absolute inset-0 animate-ping rounded-full bg-electric-iris/20"></div>
              <span className="material-symbols-outlined animate-spin text-4xl text-electric-iris">sync</span>
            </div>
            <div className="flex flex-col gap-2">
              <h3 className="font-haas-grot-disp text-xl font-bold text-ink-black">{statusMessage}</h3>
              <p className="font-martian-mono text-sm text-ink-black/60 uppercase tracking-wider">
                Please wait while we process your document
              </p>
            </div>
          </div>
        )}

        {status === 'done' && (
          <div className="flex flex-col items-center gap-4 py-8 text-jelly-green">
            <span className="material-symbols-outlined text-5xl">check_circle</span>
            <h3 className="font-haas-grot-disp text-2xl font-bold text-ink-black">Upload Complete!</h3>
          </div>
        )}

        {(status === 'idle' || status === 'error') && (
          <>
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-frost-blue text-electric-iris border-2 border-transparent transition-colors group-hover:border-electric-iris">
              <span className="material-symbols-outlined text-3xl">upload_file</span>
            </div>
            
            <h2 className="mb-2 font-haas-grot-disp text-2xl font-bold text-ink-black">Drop Box & Syllabus Uploader</h2>
            <p className="mb-8 font-haas-grot-text text-lg text-ink-black/70">Drag and drop your PDFs here.</p>
            
            <button 
              onClick={(e) => { e.stopPropagation(); triggerFileInput(); }}
              className="hover-press mb-4 flex items-center gap-2 rounded-full border-2 border-ink-black bg-electric-iris px-8 py-3 font-haas-grot-text text-lg font-bold text-paper-white shadow-hard-md"
            >
              Process Material with Groq
              <span className="material-symbols-outlined">arrow_forward</span>
            </button>
            
            <div className="flex items-center gap-4 text-ink-black/50">
              <span className="h-px w-12 bg-ink-black/20"></span>
              <span className="font-martian-mono text-sm uppercase">or</span>
              <span className="h-px w-12 bg-ink-black/20"></span>
            </div>
            
            <button 
              onClick={(e) => { e.stopPropagation(); triggerFileInput(); }}
              className="mt-4 font-haas-grot-text text-electric-iris underline underline-offset-4 hover:text-ink-black transition-colors"
            >
              Browse Files
            </button>
          </>
        )}
      </div>
    </div>
  );
}
