import { phase1Questions } from "./questions/phase1";
import { phase2Questions } from "./questions/phase2";
import { phase3Questions } from "./questions/phase3";

export const EMPLOYABILITY_PHASES = [
  {
    id: "phase1",
    number: "01",
    title: "Internship Experience",
    subtitle: "Internship Experience → Employability",
    description:
      "Evaluate how internship quality — objectives, support, workplace environment, and career development — predicts employability.",
    model: "XGBoost",
    metric: "OOF R² 0.469",
    items: 12,
    accent: "#0d9488",
    accentSoft: "#ccfbf1",
    questions: phase1Questions,
    assessmentTitle: "Internship Experience Assessment",
    assessmentPrompt: "Reflect on your internship experience and rate each statement.",
    heroTitle: "Internship Experience → Employability",
    heroDescription:
      "Complete the 12-item internship experience assessment to generate an employability prediction and personalized development guidance.",
  },
  {
    id: "phase2",
    number: "02",
    title: "Competence",
    subtitle: "Competence → Employability",
    description:
      "Assess life & career, learning & innovation, and IT & media skills to generate an employability prediction.",
    model: "Linear Regression",
    metric: "Test R² 0.546",
    items: 10,
    accent: "#4f46e5",
    accentSoft: "#eef2ff",
    questions: phase2Questions,
    assessmentTitle: "Competence Assessment",
    assessmentPrompt: "Select one response for every statement about your skills.",
    heroTitle: "Competence → Employability",
    heroDescription:
      "Complete the 10-item competence assessment to generate an employability prediction and personalized development guidance.",
  },
  {
    id: "phase3",
    number: "03",
    title: "Psychological Capital",
    subtitle: "PsyCap → Employability",
    description:
      "Measure hope, optimism, resilience, and self-efficacy to understand psychological drivers of employability.",
    model: "ElasticNet",
    metric: "CV R² 0.574",
    items: 12,
    accent: "#db2777",
    accentSoft: "#fce7f3",
    questions: phase3Questions,
    assessmentTitle: "Psychological Capital Assessment",
    assessmentPrompt: "Rate how much you agree with each PsyCap statement.",
    heroTitle: "Psychological Capital → Employability",
    heroDescription:
      "Complete the 12-item psychological capital assessment to generate an employability prediction and personalized development guidance.",
  },
];

export function getEmployabilityPhaseById(phaseId) {
  return EMPLOYABILITY_PHASES.find((phase) => phase.id === phaseId);
}
