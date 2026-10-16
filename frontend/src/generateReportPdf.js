import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";

const PAGE_MARGIN = 16;
const CONTENT_WIDTH = 178;

function wrapText(doc, text, x, y, maxWidth, lineHeight = 5.2) {
  const lines = doc.splitTextToSize(String(text || "—"), maxWidth);
  doc.text(lines, x, y);
  return y + lines.length * lineHeight;
}

function ensureSpace(doc, y, needed = 24) {
  const pageHeight = doc.internal.pageSize.getHeight();
  if (y + needed > pageHeight - 18) {
    doc.addPage();
    drawFooter(doc);
    return 22;
  }
  return y;
}

function drawFooter(doc) {
  const pageCount = doc.internal.getNumberOfPages();
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  for (let i = 1; i <= pageCount; i += 1) {
    doc.setPage(i);
    doc.setDrawColor(210, 218, 235);
    doc.line(PAGE_MARGIN, pageHeight - 12, pageWidth - PAGE_MARGIN, pageHeight - 12);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(110, 120, 140);
    doc.text(
      "R26-IT-034  |  Career Safety and Industry Stability Analysis  |  Decision-support only",
      PAGE_MARGIN,
      pageHeight - 7
    );
    doc.text(`Page ${i} of ${pageCount}`, pageWidth - PAGE_MARGIN, pageHeight - 7, {
      align: "right",
    });
  }
}

function sectionHeading(doc, title, y) {
  y = ensureSpace(doc, y, 16);
  doc.setFillColor(47, 99, 234);
  doc.rect(PAGE_MARGIN, y - 4, 2.2, 8, "F");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.setTextColor(21, 40, 84);
  doc.text(title, PAGE_MARGIN + 7, y + 2);
  return y + 10;
}

function bulletList(doc, items, y) {
  const list = Array.isArray(items) && items.length ? items : ["No items recorded."];
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(45, 58, 86);
  list.forEach((item) => {
    y = ensureSpace(doc, y, 12);
    const lines = doc.splitTextToSize(`•  ${item}`, CONTENT_WIDTH);
    doc.text(lines, PAGE_MARGIN, y);
    y += lines.length * 5.2 + 1.5;
  });
  return y + 2;
}

export function downloadCareerReportPdf({ formData, prediction, indicators, guidance }) {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const created = new Date().toLocaleString();

  doc.setFillColor(36, 64, 148);
  doc.rect(0, 0, 210, 32, "F");
  doc.setFillColor(109, 94, 252);
  doc.rect(0, 32, 210, 2, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(16);
  doc.text("Career Safety & Industry Stability Analysis", PAGE_MARGIN, 14);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9.5);
  doc.text("Comprehensive Career Development and Recruitment Framework", PAGE_MARGIN, 21);
  doc.text(`Generated: ${created}`, PAGE_MARGIN, 27);

  let y = 44;
  doc.setTextColor(70, 80, 100);
  doc.setFontSize(9);
  y = wrapText(
    doc,
    "This report provides explainable career risk estimation for decision-support purposes. It does not predict job loss or make a final career decision.",
    PAGE_MARGIN,
    y,
    CONTENT_WIDTH,
    4.8
  );

  y = sectionHeading(doc, "1. Submitted Career Profile", y + 6);
  autoTable(doc, {
    startY: y,
    theme: "grid",
    head: [["Field", "Value"]],
    body: [
      ["Role", formData?.role || "—"],
      ["Years of experience", formData?.years_experience || "—"],
      ["Tech stack change", String(formData?.tech_stack_change ?? "—")],
      ["Weekly learning time", formData?.weekly_learning_time || "—"],
      ["Switch confidence", String(formData?.switch_confidence ?? "—")],
      ["Career strategy", formData?.career_strategy || "—"],
      ["Skill update frequency", formData?.skill_update_frequency || "—"],
    ],
    styles: { font: "helvetica", fontSize: 9, cellPadding: 2.4 },
    headStyles: { fillColor: [47, 99, 234], textColor: 255 },
    columnStyles: { 0: { cellWidth: 58, fontStyle: "bold" } },
    margin: { left: PAGE_MARGIN, right: PAGE_MARGIN },
  });
  y = doc.lastAutoTable.finalY + 10;

  y = sectionHeading(doc, "2. Model Prediction", y);
  doc.setFillColor(244, 247, 255);
  doc.setDrawColor(210, 220, 245);
  doc.roundedRect(PAGE_MARGIN, y, CONTENT_WIDTH, 16, 2, 2, "FD");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(10);
  doc.setTextColor(80, 90, 110);
  doc.text("Overall Career Risk Level", PAGE_MARGIN + 5, y + 6);
  doc.setFontSize(14);
  doc.setTextColor(29, 53, 111);
  doc.text(prediction?.value || "—", PAGE_MARGIN + 5, y + 13);
  y += 24;

  y = sectionHeading(doc, "3. System-Derived Indicators", y);
  autoTable(doc, {
    startY: y,
    theme: "striped",
    head: [["Indicator", "Value"]],
    body: [
      ["Automation exposure", indicators?.automationExposure || "—"],
      ["Industry / domain stability", indicators?.industryDomainStability || "—"],
      ["Job market trend", indicators?.jobMarketTrend || "—"],
      ["Learning activity", indicators?.learningActivity || "—"],
      ["Skill update behavior", indicators?.skillUpdateBehavior || "—"],
      ["Role-switching confidence", indicators?.roleSwitchingConfidence || "—"],
      ["Career strategy status", indicators?.careerStrategyStatus || "—"],
    ],
    styles: { font: "helvetica", fontSize: 9, cellPadding: 2.4 },
    headStyles: { fillColor: [47, 155, 181], textColor: 255 },
    columnStyles: { 0: { cellWidth: 70, fontStyle: "bold" } },
    margin: { left: PAGE_MARGIN, right: PAGE_MARGIN },
  });
  y = doc.lastAutoTable.finalY + 10;

  y = sectionHeading(doc, "4. Recommendations of Career Guidance", y);
  if (guidance?.generationStatus === "failed") {
    doc.setFont("helvetica", "italic");
    doc.setFontSize(10);
    doc.setTextColor(150, 40, 50);
    y = wrapText(
      doc,
      guidance.generationMessage || "AI guidance was not available for this report.",
      PAGE_MARGIN,
      y,
      CONTENT_WIDTH
    );
  } else {
    if (guidance?.explainableRecommendation) {
      y = ensureSpace(doc, y, 20);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10.5);
      doc.setTextColor(29, 53, 111);
      doc.text("Explainable recommendation", PAGE_MARGIN, y);
      y += 6;
      doc.setFont("helvetica", "normal");
      doc.setTextColor(45, 58, 86);
      y = wrapText(doc, guidance.explainableRecommendation, PAGE_MARGIN, y, CONTENT_WIDTH);
      y += 4;
    }

    y = ensureSpace(doc, y, 12);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(10.5);
    doc.setTextColor(29, 53, 111);
    doc.text("Main risky areas", PAGE_MARGIN, y);
    y = bulletList(doc, guidance?.mainRiskyAreas, y + 6);

    y = ensureSpace(doc, y, 12);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(10.5);
    doc.setTextColor(29, 53, 111);
    doc.text("Career strengths", PAGE_MARGIN, y);
    y = bulletList(doc, guidance?.careerStrengths, y + 6);

    const insights = [
      ["Industry stability insight", guidance?.industryStabilityInsight],
      ["Skill transferability insight", guidance?.skillTransferabilityInsight],
      ["Adaptability readiness insight", guidance?.adaptabilityReadinessInsight],
    ];
    insights.forEach(([title, text]) => {
      y = ensureSpace(doc, y, 16);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10.5);
      doc.setTextColor(29, 53, 111);
      doc.text(title, PAGE_MARGIN, y);
      y += 6;
      doc.setFont("helvetica", "normal");
      doc.setTextColor(45, 58, 86);
      y = wrapText(doc, text, PAGE_MARGIN, y, CONTENT_WIDTH) + 3;
    });

    y = ensureSpace(doc, y, 12);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(10.5);
    doc.setTextColor(29, 53, 111);
    doc.text("Recommended next steps", PAGE_MARGIN, y);
    y = bulletList(doc, guidance?.recommendedNextSteps, y + 6);

    y = ensureSpace(doc, y, 12);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(10.5);
    doc.setTextColor(29, 53, 111);
    doc.text("Why this result?", PAGE_MARGIN, y);
    y = bulletList(doc, guidance?.whyThisResult, y + 6);

    const mapping = Array.isArray(guidance?.recommendationMapping)
      ? guidance.recommendationMapping
      : [];
    if (mapping.length) {
      y = ensureSpace(doc, y, 20);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10.5);
      doc.setTextColor(29, 53, 111);
      doc.text("Recommendation mapping", PAGE_MARGIN, y);
      autoTable(doc, {
        startY: y + 4,
        theme: "grid",
        head: [["Risk factor", "Condition", "Lacking area", "Recommendation"]],
        body: mapping.map((row) => [
          row.riskFactor || "—",
          row.condition || "—",
          row.lackingArea || "—",
          row.recommendation || "—",
        ]),
        styles: { font: "helvetica", fontSize: 8, cellPadding: 2.1, overflow: "linebreak" },
        headStyles: { fillColor: [109, 94, 252], textColor: 255 },
        margin: { left: PAGE_MARGIN, right: PAGE_MARGIN },
      });
      y = doc.lastAutoTable.finalY + 8;
    }
  }

  const plan = guidance?.careerResilienceActionPlan;
  y = sectionHeading(doc, "5. AI Career Resilience Action Plan", y);
  if (!plan || (!plan.summary && !(plan.thirtyDayPlan || []).length)) {
    doc.setFont("helvetica", "italic");
    doc.setFontSize(10);
    doc.setTextColor(110, 120, 140);
    y = wrapText(
      doc,
      "Career resilience action plan is currently unavailable.",
      PAGE_MARGIN,
      y,
      CONTENT_WIDTH
    );
  } else {
    if (plan.summary) {
      y = ensureSpace(doc, y, 16);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10.5);
      doc.setTextColor(29, 53, 111);
      doc.text("Summary", PAGE_MARGIN, y);
      y += 6;
      doc.setFont("helvetica", "normal");
      doc.setTextColor(45, 58, 86);
      y = wrapText(doc, plan.summary, PAGE_MARGIN, y, CONTENT_WIDTH) + 3;
    }

    if (plan.actionPriorityLevel) {
      y = ensureSpace(doc, y, 12);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10.5);
      doc.setTextColor(29, 53, 111);
      doc.text(`Action priority level: ${plan.actionPriorityLevel}`, PAGE_MARGIN, y);
      y += 8;
    }

    const planBlocks = [
      ["30-day plan", plan.thirtyDayPlan],
      ["60-day plan", plan.sixtyDayPlan],
      ["90-day plan", plan.ninetyDayPlan],
      ["Priority skills to improve", plan.prioritySkillsToImprove],
      ["Suggested learning focus", plan.suggestedLearningFocus],
      ["Career strategy adjustment", plan.careerStrategyAdjustment],
      ["Risk reduction actions", plan.riskReductionActions],
      ["Progress tracking suggestions", plan.progressTrackingSuggestions],
    ];

    planBlocks.forEach(([title, items]) => {
      y = ensureSpace(doc, y, 12);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(10.5);
      doc.setTextColor(29, 53, 111);
      doc.text(title, PAGE_MARGIN, y);
      y = bulletList(doc, items, y + 6);
    });
  }

  drawFooter(doc);
  const stamp = new Date().toISOString().slice(0, 10);
  doc.save(`Career-Safety-Report-${stamp}.pdf`);
}
