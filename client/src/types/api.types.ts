export type Unit = {
  unit_number: number;
  title: string;
  estimated_hours: number;
  topics: string[];
  cognitive_level: 'Remember' | 'Understand' | 'Apply' | 'Analyze' | 'Evaluate' | 'Create';
};

export type PriorityTopic = {
  topic: string;
  weightage: number;
};

export type SyllabusPayload = {
  course_title: string;
  total_units: number;
  learning_path: Unit[];
  priority_topics: PriorityTopic[];
};

export type TopicFrequency = {
  topic: string;
  percentage: number;
  question_count: number;
};

export type PredictedQuestion = {
  question: string;
  bloom_level: 'Apply' | 'Analyze' | 'Evaluate';
  expected_marks: number;
  probability_score: number;
};

export type PYQAnalysisPayload = {
  topic_frequency: TopicFrequency[];
  predicted_questions: PredictedQuestion[];
};

export type Flashcard = {
  front: string;
  back: string;
  bloom_category: 'Remember' | 'Understand' | 'Apply' | 'Analyze' | 'Evaluate' | 'Create';
  difficulty: 'Easy' | 'Medium' | 'Hard';
};

export type QuizQuestion = {
  question: string;
  options: [string, string, string, string];
  correct_answer_index: number;
  solution: string;
};

export type NotesPayload = {
  document_summary: string;
  flashcards: Flashcard[];
  practice_exam: QuizQuestion[];
};

export type ProcessingMode = 'notes' | 'pyq' | 'syllabus';

export type DocType = 'SYLLABUS' | 'PYQ' | 'NOTES';

export type ClassificationResult = {
  doc_type: DocType;
  confidence: number;
  metrics: Record<string, number>;
};

export type EngineResponse = {
  classification: ClassificationResult;
  payload: SyllabusPayload | PYQAnalysisPayload | NotesPayload;
};

export type JobAccepted = {
  job_id: string;
  chunks_total: number;
  mode_mismatch?: boolean;
};

export type JobState = 'queued' | 'processing' | 'done' | 'failed' | 'cancelled';

export type JobStatus = {
  status: JobState;
  doc_type: DocType;
  user_mode: ProcessingMode;
  chunks_done: number;
  chunks_total: number;
  classification?: ClassificationResult;
  payload?: SyllabusPayload | PYQAnalysisPayload | NotesPayload;
  raw_chunks?: string[];
  error?: string;
};

export type UploadStatus = 'idle' | 'uploading' | 'error';
