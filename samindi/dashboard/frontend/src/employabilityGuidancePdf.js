import jsPDFModule from "jspdf";
import autoTable from "jspdf-autotable";

const jsPDF = jsPDFModule?.jsPDF || jsPDFModule;

const PAGE_MARGIN = 16;
const CONTENT_WIDTH = 178;

function clean(value) {
  return String(value ?? "—")
    .replace(/\u2192/g, " to ")
    .replace(/[\u2013\u2014]/g, "-")
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201c\u201d]/g, '"')
    .replace(/\s+/g, " ")
    .trim();
}

function wrapText(doc, text, x, y, maxWidth, lineHeight = 5.2) {
  const lines = doc.splitTextToSize(clean(text), maxWidth);
  doc.text(lines, x, y);
  return y + lines.length * lineHeight;
}

function ensureSpace(doc, y, needed = 24) {
  const pageHeight = doc.internal.pageSize.getHeight();
  if (y + needed > pageHeight - 18) {
    doc.addPage();
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
    doc.setDrawColor(210, 218, 230);
    doc.line(PAGE_MARGIN, pageHeight - 12, pageWidth - PAGE_MARGIN, pageHeight - 12);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(110, 120, 140);
    doc.text(
      "Employability Simulator  |  Guidance only  |  The score comes from the frozen model",
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
  doc.setFillColor(13, 148, 136);
  doc.rect(PAGE_MARGIN, y - 4, 2.2, 8, "F");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(12);
  doc.setTextColor(15, 60, 58);
  doc.text(title, PAGE_MARGIN + 7, y + 2);
  return y + 10;
}

function subheading(doc, title, y) {
  y = ensureSpace(doc, y, 14);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(10.5);
  doc.setTextColor(15, 90, 82);
  doc.text(clean(title), PAGE_MARGIN, y);
  return y + 6;
}

function paragraph(doc, text, y) {
  if (!text) {
    return y;
  }
  y = ensureSpace(doc, y, 16);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(45, 58, 86);
  return wrapText(doc, text, PAGE_MARGIN, y, CONTENT_WIDTH) + 3;
}

function bulletList(doc, items, y) {
  const list = Array.isArray(items) && items.length ? items : ["No items recorded."];
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10);
  doc.setTextColor(45, 58, 86);
  list.forEach((item) => {
    y = ensureSpace(doc, y, 12);
    const lines = doc.splitTextToSize(`-  ${clean(item)}`, CONTENT_WIDTH);
    doc.text(lines, PAGE_MARGIN, y);
    y += lines.length * 5.2 + 1.5;
  });
  return y + 2;
}

function scoreText(result) {
  const score = result?.prediction?.score ?? result?.prediction?.evs_avg;
  return Number.isFinite(Number(score)) ? Number(score).toFixed(2) : "—";
}

export function buildEmployabilityGuidancePdf({ phase, result }) {
  const doc = new jsPDF({ unit: "mm", format: "a4" });
  const created = new Date().toLocaleString();
  const recommendation = result?.ai_recommendation || {};
  const sourceLabel =
    result?.recommendation_source === "openai_api"
      ? "OpenAI-grounded guidance"
      : "Rule-based fallback guidance";

  doc.setFillColor(15, 90, 82);
  doc.rect(0, 0, 210, 34, "F");
  doc.setFillColor(13, 148, 136);
  doc.rect(0, 34, 210, 2, "F");
  doc.setTextColor(255, 255, 255);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(16);
  doc.text("Employability Development Guidance", PAGE_MARGIN, 14);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9.5);
  doc.text(clean(phase?.subtitle || phase?.title || "Employability assessment"), PAGE_MARGIN, 21);
  doc.text(`Generated: ${created}`, PAGE_MARGIN, 27);

  let y = 46;
  doc.setTextColor(70, 80, 100);
  doc.setFontSize(9);
  y = wrapText(
    doc,
    `This document records the ${clean(phase?.model || "machine learning")} prediction and the guidance prepared from that evidence. The language model does not calculate or change the employability score.`,
    PAGE_MARGIN,
    y,
    CONTENT_WIDTH,
    4.8
  );

  y = sectionHeading(doc, "1. Predicted employability", y + 6);
  doc.setFillColor(240, 253, 250);
  doc.setDrawColor(167, 219, 210);
  doc.roundedRect(PAGE_MARGIN, y, CONTENT_WIDTH, 22, 2, 2, "FD");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  doc.setTextColor(80, 90, 110);
  doc.text("Predicted score", PAGE_MARGIN + 5, y + 8);
  doc.setFontSize(16);
  doc.setTextColor(15, 90, 82);
  doc.text(`${scoreText(result)} / 5`, PAGE_MARGIN + 5, y + 16);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(70, 90, 96);
  doc.text(clean(`${phase?.model || "Model"}  |  ${sourceLabel}`), PAGE_MARGIN + 58, y + 15);
  y += 30;

  y = sectionHeading(doc, "2. Construct scores", y);
  autoTable(doc, {
    startY: y,
    theme: "grid",
    head: [["Construct", "Score", "Level"]],
    body: (result?.construct_analysis || []).map((item) => [
      clean(item.construct),
      Number(item.score).toFixed(2),
      clean(item.level),
    ]),
    styles: { font: "helvetica", fontSize: 9, cellPadding: 2.4 },
    headStyles: { fillColor: [15, 90, 82], textColor: 255 },
    columnStyles: { 0: { cellWidth: 100, fontStyle: "bold" }, 1: { cellWidth: 28 } },
    margin: { left: PAGE_MARGIN, right: PAGE_MARGIN, bottom: 18 },
  });
  y = doc.lastAutoTable.finalY + 10;

  y = sectionHeading(doc, "3. Strengths", y);
  y = bulletList(
    doc,
    (result?.strengths || []).map((item) => `${item.name} (${Number(item.score).toFixed(2)} / 5)`),
    y
  );

  y = sectionHeading(doc, "4. Development priorities", y);
  const areas = result?.areas_for_improvement || [];
  if (!areas.length) {
    y = paragraph(
      doc,
      "No development priority was identified from the current scores.",
      y
    );
  } else {
    areas.forEach((item, index) => {
      y = subheading(doc, `${index + 1}. ${item.name}`, y);
      const details = [`Current score: ${Number(item.score).toFixed(2)} / 5`];
      if (item.expected_gain > 0) {
        details.push(`Estimated gain if raised to 4.00: +${Number(item.expected_gain).toFixed(2)}`);
      }
      if (item.focus_item) {
        details.push(`Start with: ${item.focus_item}`);
      }
      y = paragraph(doc, details.join(". ") + ".", y);
      if (item.priority_reason) {
        y = paragraph(doc, item.priority_reason, y);
      }
      if (item.action) {
        y = paragraph(doc, item.action, y);
      }
    });
  }

  y = sectionHeading(doc, "5. Career readiness summary", y);
  y = paragraph(
    doc,
    recommendation.overall_career_readiness_summary ||
      "A written career-readiness summary was not available for this result.",
    y
  );

  y = sectionHeading(doc, "6. Guidance highlights", y);
  y = subheading(doc, "Top strengths from the evidence", y);
  y = bulletList(doc, recommendation.top_3_strengths, y);
  y = subheading(doc, "What to develop next", y);
  y = bulletList(doc, recommendation.top_3_areas_for_improvement, y);

  if ((recommendation.personalized_action_plan || []).length) {
    y = sectionHeading(doc, "7. Personalized action plan", y);
    y = bulletList(doc, recommendation.personalized_action_plan, y);
  }

  if ((recommendation.recommended_next_steps || []).length) {
    y = sectionHeading(doc, "8. Recommended next steps", y);
    y = bulletList(doc, recommendation.recommended_next_steps, y);
  }

  if ((recommendation.area_analysis || []).length) {
    y = sectionHeading(doc, "9. Area guidance", y);
    recommendation.area_analysis.forEach((area) => {
      y = subheading(doc, area.area || "Area", y);
      y = paragraph(doc, area.career_readiness_impact, y);
      if ((area.strengths || []).length) {
        y = paragraph(doc, "Strengths in this area:", y);
        y = bulletList(doc, area.strengths, y);
      }
      if ((area.areas_for_improvement || []).length) {
        y = paragraph(doc, "Areas to improve:", y);
        y = bulletList(doc, area.areas_for_improvement, y);
      }
      if ((area.practical_suggestions || []).length) {
        y = paragraph(doc, "Practical suggestions:", y);
        y = bulletList(doc, area.practical_suggestions, y);
      }
    });
  }

  if ((recommendation.recommended_learning_resources || []).length) {
    y = sectionHeading(doc, "10. Trusted learning sources", y);
    y = paragraph(
      doc,
      "These links are taken from a fixed library of university and official-provider sources. The language model does not create them.",
      y
    );
    recommendation.recommended_learning_resources.forEach((resource) => {
      y = subheading(doc, `${resource.topic || "Learning source"} (${resource.area || "Area"})`, y);
      y = paragraph(
        doc,
        `${resource.provider || ""} · ${resource.resource_type || ""}. ${resource.reason || ""}`,
        y
      );
      const url = String(resource.url || "");
      if (url.startsWith("https://")) {
        y = ensureSpace(doc, y, 10);
        doc.setFont("helvetica", "normal");
        doc.setFontSize(9);
        doc.setTextColor(13, 110, 180);
        const linkText = doc.splitTextToSize(url, CONTENT_WIDTH)[0];
        doc.textWithLink(linkText, PAGE_MARGIN, y, { url });
        y += 8;
      }
    });
  }

  y = sectionHeading(doc, "11. How to read this document", y);
  y = paragraph(
    doc,
    "The employability value is a continuous machine-learning prediction. Strength labels, development priorities, and written guidance organize the result. They are not separate classifications.",
    y
  );

  drawFooter(doc);
  return doc;
}

export function downloadEmployabilityGuidancePdf({ phase, result }) {
  const doc = buildEmployabilityGuidancePdf({ phase, result });
  const stamp = new Date().toISOString().slice(0, 10);
  const phaseNumber = clean(phase?.number || phase?.id || "phase").replace(/\s+/g, "-");
  doc.save(`Employability-Guidance-Phase-${phaseNumber}-${stamp}.pdf`);
}
