import jsPDF from 'jspdf';
import type { SyllabusPayload, PYQAnalysisPayload, NotesPayload } from '../types/api.types';
import type { ExportPayload, ExportOptions } from '../types/export';

const MARGIN_LEFT = 20;
const MARGIN_TOP = 20;
const LINE_HEIGHT = 7;
const PAGE_HEIGHT = 297;
const MAX_Y = PAGE_HEIGHT - 20;

export function exportToPdf(payload: ExportPayload, options: ExportOptions): void {
  const filename = options.filename ?? `mindforge-${options.docType.toLowerCase()}-export.pdf`;
  const doc = new jsPDF();

  switch (options.docType) {
    case 'SYLLABUS':
      renderSyllabus(doc, payload as SyllabusPayload);
      break;
    case 'PYQ':
      renderPYQ(doc, payload as PYQAnalysisPayload);
      break;
    case 'NOTES':
      renderNotes(doc, payload as NotesPayload);
      break;
  }

  doc.save(filename);
}

function renderSyllabus(doc: jsPDF, payload: SyllabusPayload): void {
  let y = MARGIN_TOP;
  doc.setFontSize(18);
  doc.text('Syllabus Roadmap', MARGIN_LEFT, y);
  y += LINE_HEIGHT * 2;
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text(payload.course_title, MARGIN_LEFT, y);
  y += LINE_HEIGHT * 2;
  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  payload.learning_path.forEach((unit) => {
    if (y > MAX_Y - 20) { doc.addPage(); y = MARGIN_TOP; }
    doc.setFont('helvetica', 'bold');
    doc.text(`Unit ${unit.unit_number}: ${unit.title} (${unit.estimated_hours}h)`, MARGIN_LEFT, y);
    y += LINE_HEIGHT;
    doc.setFont('helvetica', 'normal');
    unit.topics.forEach((topic) => {
      if (y > MAX_Y) { doc.addPage(); y = MARGIN_TOP; }
      doc.text(`  \u2022 ${topic}`, MARGIN_LEFT, y);
      y += LINE_HEIGHT;
    });
    y += LINE_HEIGHT * 0.5;
  });
  if (payload.priority_topics.length > 0) {
    if (y > MAX_Y - 20) { doc.addPage(); y = MARGIN_TOP; }
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('Priority Topics', MARGIN_LEFT, y);
    y += LINE_HEIGHT * 1.5;
    doc.setFontSize(11);
    doc.setFont('helvetica', 'normal');
    payload.priority_topics.forEach((pt) => {
      if (y > MAX_Y) { doc.addPage(); y = MARGIN_TOP; }
      doc.text(`  ${pt.topic} \u2014 ${pt.weightage}%`, MARGIN_LEFT, y);
      y += LINE_HEIGHT;
    });
  }
}

function renderPYQ(doc: jsPDF, payload: PYQAnalysisPayload): void {
  let y = MARGIN_TOP;
  doc.setFontSize(18);
  doc.text('PYQ Analysis', MARGIN_LEFT, y);
  y += LINE_HEIGHT * 2;
  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  payload.topic_frequency.forEach((tf) => {
    if (y > MAX_Y) { doc.addPage(); y = MARGIN_TOP; }
    doc.text(`${tf.topic} \u2014 ${tf.percentage}% (${tf.question_count} questions)`, MARGIN_LEFT, y);
    y += LINE_HEIGHT;
  });
  if (payload.predicted_questions.length > 0) {
    y += LINE_HEIGHT;
    if (y > MAX_Y - 20) { doc.addPage(); y = MARGIN_TOP; }
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.text('Predicted Questions', MARGIN_LEFT, y);
    y += LINE_HEIGHT * 1.5;
    doc.setFontSize(11);
    doc.setFont('helvetica', 'normal');
    payload.predicted_questions.forEach((pq, i) => {
      if (y > MAX_Y - 20) { doc.addPage(); y = MARGIN_TOP; }
      doc.setFont('helvetica', 'bold');
      doc.text(`${i + 1}. [${pq.bloom_level}] ${pq.question}`, MARGIN_LEFT, y);
      y += LINE_HEIGHT;
      doc.setFont('helvetica', 'normal');
      doc.text(`   Marks: ${pq.expected_marks} | Probability: ${(pq.probability_score * 100).toFixed(0)}%`, MARGIN_LEFT, y);
      y += LINE_HEIGHT * 1.5;
    });
  }
}

function renderNotes(doc: jsPDF, payload: NotesPayload): void {
  let y = MARGIN_TOP;
  doc.setFontSize(18);
  doc.text('Practice Exam', MARGIN_LEFT, y);
  y += LINE_HEIGHT * 2;
  doc.setFontSize(11);
  payload.practice_exam.forEach((q, i) => {
    if (y > MAX_Y - 30) { doc.addPage(); y = MARGIN_TOP; }
    doc.setFont('helvetica', 'bold');
    doc.text(`${i + 1}. ${q.question}`, MARGIN_LEFT, y);
    y += LINE_HEIGHT;
    doc.setFont('helvetica', 'normal');
    const labels = ['A', 'B', 'C', 'D'];
    q.options.forEach((opt, j) => {
      doc.text(`   ${labels[j]}. ${opt}`, MARGIN_LEFT, y);
      y += LINE_HEIGHT;
    });
    y += LINE_HEIGHT * 0.5;
  });
  doc.addPage();
  y = MARGIN_TOP;
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text('Answer Key', MARGIN_LEFT, y);
  y += LINE_HEIGHT * 2;
  doc.setFontSize(11);
  doc.setFont('helvetica', 'normal');
  payload.practice_exam.forEach((q, i) => {
    if (y > MAX_Y) { doc.addPage(); y = MARGIN_TOP; }
    const label = ['A', 'B', 'C', 'D'][q.correct_answer_index];
    doc.text(`${i + 1}. ${label} \u2014 ${q.options[q.correct_answer_index]}`, MARGIN_LEFT, y);
    y += LINE_HEIGHT;
  });
}
