/**
 * theme_aurora.js  —  AURORA THEME
 * Palette: Midnight Indigo · Amethyst Violet · Warm Gold · Pearl White
 * Vibe: Premium, editorial, confident — great for keynotes & brand decks
 *
 * Usage: node theme_aurora.js <input.json> <output.pptx>
 */

const pptxgen = require("pptxgenjs");
const fs      = require("fs");
const path    = require("path");

// ─── Palette ──────────────────────────────────────────────────────────────────
const C = {
  midnight:  "0D0F2B",   // title / closing background
  indigo:    "1A1F6B",   // deep accent background element
  violet:    "7C3AED",   // primary accent
  lavender:  "A78BFA",   // secondary accent / highlights
  gold:      "F59E0B",   // warm pop accent
  white:     "FFFFFF",
  pearl:     "F5F3FF",   // content slide background
  text:      "1E1B4B",   // body text (deep indigo)
  muted:     "6B7280",   // captions
};

const FONT_TITLE = "Georgia";
const FONT_BODY  = "Trebuchet MS";

// ─── Helpers ──────────────────────────────────────────────────────────────────
function shadow()  { return { type: "outer", blur: 10, offset: 4, angle: 140, color: "7C3AED", opacity: 0.15 }; }
function shadow2() { return { type: "outer", blur: 6,  offset: 2, angle: 135, color: "000000", opacity: 0.10 }; }

function addSlideNumber(slide, n) {
  slide.addText(String(n), {
    x: 9.3, y: 5.18, w: 0.5, h: 0.3,
    fontSize: 9, color: C.muted, fontFace: FONT_BODY, align: "right",
  });
}

function addFooter(slide, label = "Scoreazy · Scoring Made Easy") {
  slide.addText(label, {
    x: 0.2, y: 5.3, w: 9.6, h: 0.2,
    fontSize: 8, color: C.muted, fontFace: FONT_BODY, align: "center",
  });
}

function tryAddImage(slide, imgPath, opts) {
  if (!imgPath) return false;
  const resolved = path.isAbsolute(imgPath) ? imgPath : path.resolve(imgPath);
  if (!fs.existsSync(resolved)) { console.warn(`Image not found: ${resolved}`); return false; }
  slide.addImage({ path: resolved, ...opts });
  return true;
}

// ─── Slide Builders ───────────────────────────────────────────────────────────

function buildTitleSlide(pres, title) {
  const slide = pres.addSlide();
  slide.background = { color: C.midnight };

  // Large blurred violet circle — top left atmospheric glow
  slide.addShape("ellipse", {
    x: -1.5, y: -1.0, w: 5.0, h: 5.0,
    fill: { color: C.violet, transparency: 75 },
    line: { color: C.violet, width: 0 },
  });

  // Smaller gold circle — bottom right accent
  slide.addShape("ellipse", {
    x: 7.8, y: 3.5, w: 3.2, h: 3.2,
    fill: { color: C.gold, transparency: 85 },
    line: { color: C.gold, width: 0 },
  });

  // Top horizontal gold rule
  slide.addShape("rect", {
    x: 0.6, y: 1.35, w: 1.0, h: 0.05,
    fill: { color: C.gold }, line: { color: C.gold, width: 0 },
  });

  // "MICROLESSON" label
  slide.addText("MICROLESSON", {
    x: 0.6, y: 1.5, w: 8, h: 0.4,
    fontSize: 10, bold: false, color: C.lavender,
    fontFace: FONT_BODY, charSpacing: 5,
  });

  // Main title
  slide.addText(title, {
    x: 0.6, y: 2.0, w: 8.0, h: 2.4,
    fontSize: 38, bold: true, color: C.white,
    fontFace: FONT_TITLE, valign: "top", wrap: true,
  });

  // Gold rule under title
  slide.addShape("rect", {
    x: 0.6, y: 4.45, w: 2.0, h: 0.05,
    fill: { color: C.gold }, line: { color: C.gold, width: 0 },
  });

  addFooter(slide);
}

function buildTextSlide(pres, heading, bullets, slideNum) {
  const slide = pres.addSlide();
  slide.background = { color: C.pearl };

  // Left accent bar — violet
  slide.addShape("rect", {
    x: 0, y: 0, w: 0.07, h: 5.625,
    fill: { color: C.violet }, line: { color: C.violet, width: 0 },
  });

  // Top-right decorative corner triangle feel — layered rects
  slide.addShape("rect", {
    x: 8.5, y: 0, w: 1.5, h: 0.12,
    fill: { color: C.lavender, transparency: 60 },
    line: { color: C.lavender, width: 0 },
  });
  slide.addShape("rect", {
    x: 9.0, y: 0.12, w: 1.0, h: 0.08,
    fill: { color: C.gold, transparency: 50 },
    line: { color: C.gold, width: 0 },
  });

  // Heading card
  slide.addShape("rect", {
    x: 0.07, y: 0.18, w: 9.86, h: 0.88,
    fill: { color: C.white }, line: { color: C.white, width: 0 },
    shadow: shadow(),
  });
  // Violet left accent on card
  slide.addShape("rect", {
    x: 0.07, y: 0.18, w: 0.14, h: 0.88,
    fill: { color: C.violet }, line: { color: C.violet, width: 0 },
  });
  // Gold micro-line bottom of card
  slide.addShape("rect", {
    x: 0.07, y: 1.02, w: 9.86, h: 0.04,
    fill: { color: C.gold, transparency: 50 },
    line: { color: C.gold, width: 0 },
  });

  slide.addText(heading, {
    x: 0.32, y: 0.18, w: 9.4, h: 0.88, margin: 0,
    fontSize: 22, bold: true, color: C.text,
    fontFace: FONT_TITLE, valign: "middle",
  });

  if (bullets.length > 0) {
    const bulletItems = bullets.map((b, i) => ([
      { text: "◆  ", options: { color: C.violet, bold: true, fontSize: 11, fontFace: FONT_BODY } },
      { text: b.text, options: { color: C.text, bold: b.bold, fontSize: 14, fontFace: FONT_BODY, breakLine: i < bullets.length - 1 } },
    ])).flat();

    slide.addText(bulletItems, {
      x: 0.32, y: 1.22, w: 9.4, h: 3.9,
      valign: "top", paraSpaceAfter: 12,
    });
  }

  addSlideNumber(slide, slideNum);
  addFooter(slide);
}

function buildImageSlide(pres, heading, bullets, imgPath, caption, slideNum) {
  const slide = pres.addSlide();
  slide.background = { color: C.pearl };

  // Left accent
  slide.addShape("rect", {
    x: 0, y: 0, w: 0.07, h: 5.625,
    fill: { color: C.violet }, line: { color: C.violet, width: 0 },
  });

  // Heading card
  slide.addShape("rect", {
    x: 0.07, y: 0.18, w: 9.86, h: 0.88,
    fill: { color: C.white }, line: { color: C.white, width: 0 }, shadow: shadow(),
  });
  slide.addShape("rect", {
    x: 0.07, y: 0.18, w: 0.14, h: 0.88,
    fill: { color: C.violet }, line: { color: C.violet, width: 0 },
  });
  slide.addShape("rect", {
    x: 0.07, y: 1.02, w: 9.86, h: 0.04,
    fill: { color: C.gold, transparency: 50 }, line: { color: C.gold, width: 0 },
  });
  slide.addText(heading, {
    x: 0.32, y: 0.18, w: 9.4, h: 0.88, margin: 0,
    fontSize: 22, bold: true, color: C.text,
    fontFace: FONT_TITLE, valign: "middle",
  });

  // Bullets — left column
  if (bullets.length > 0) {
    const bulletItems = bullets.map((b, i) => ([
      { text: "◆  ", options: { color: C.violet, bold: true, fontSize: 11, fontFace: FONT_BODY } },
      { text: b.text, options: { color: C.text, bold: b.bold, fontSize: 13, fontFace: FONT_BODY, breakLine: i < bullets.length - 1 } },
    ])).flat();
    slide.addText(bulletItems, {
      x: 0.32, y: 1.22, w: 5.2, h: 3.9,
      valign: "top", paraSpaceAfter: 12,
    });
  }

  // Image card — violet border
  slide.addShape("rect", {
    x: 5.8, y: 1.15, w: 3.95, h: 3.55,
    fill: { color: C.white },
    line: { color: C.lavender, width: 1.5 },
    shadow: shadow2(),
  });
  // Gold corner pip
  slide.addShape("rect", {
    x: 5.8, y: 1.15, w: 0.28, h: 0.28,
    fill: { color: C.gold }, line: { color: C.gold, width: 0 },
  });

  const added = tryAddImage(slide, imgPath, {
    x: 5.9, y: 1.25, w: 3.75, h: 3.05,
    sizing: { type: "contain", w: 3.75, h: 3.05 },
  });
  if (!added) {
    slide.addShape("rect", { x: 5.9, y: 1.25, w: 3.75, h: 3.05, fill: { color: "E8E0FF" }, line: { color: C.lavender, width: 1 } });
    slide.addText("[ Image ]", { x: 5.9, y: 2.6, w: 3.75, h: 0.5, fontSize: 12, color: C.muted, fontFace: FONT_BODY, align: "center" });
  }

  if (caption) {
    slide.addText(caption, {
      x: 5.8, y: 4.3, w: 3.95, h: 0.4,
      fontSize: 9, italic: true, color: C.muted,
      fontFace: FONT_BODY, align: "center",
    });
  }

  addSlideNumber(slide, slideNum);
  addFooter(slide);
}

function buildClosingSlide(pres, title) {
  const slide = pres.addSlide();
  slide.background = { color: C.midnight };

  // Bottom-left glow
  slide.addShape("ellipse", {
    x: -1.0, y: 3.0, w: 4.0, h: 4.0,
    fill: { color: C.indigo, transparency: 60 },
    line: { color: C.indigo, width: 0 },
  });
  // Top-right gold glow
  slide.addShape("ellipse", {
    x: 7.5, y: -1.5, w: 3.8, h: 3.8,
    fill: { color: C.gold, transparency: 82 },
    line: { color: C.gold, width: 0 },
  });

  // Horizontal gold rule
  slide.addShape("rect", {
    x: 0.6, y: 1.55, w: 1.5, h: 0.05,
    fill: { color: C.gold }, line: { color: C.gold, width: 0 },
  });

  slide.addText("That's a wrap!", {
    x: 0.6, y: 1.7, w: 8.8, h: 0.6,
    fontSize: 12, color: C.lavender, fontFace: FONT_BODY, charSpacing: 4,
  });
  slide.addText(title, {
    x: 0.6, y: 2.25, w: 8.6, h: 1.7,
    fontSize: 32, bold: true, color: C.white,
    fontFace: FONT_TITLE, wrap: true,
  });
  slide.addText("Keep practising. Keep scoring.", {
    x: 0.6, y: 4.05, w: 8.8, h: 0.5,
    fontSize: 13, italic: true, color: C.muted, fontFace: FONT_BODY,
  });

  addFooter(slide);
}

// ─── Main ─────────────────────────────────────────────────────────────────────
(function main() {
  const [,, jsonPath, outputPath] = process.argv;
  if (!jsonPath || !outputPath) { console.error("Usage: node theme_aurora.js <input.json> <output.pptx>"); process.exit(1); }

  let data;
  try { data = JSON.parse(fs.readFileSync(jsonPath, "utf-8")); }
  catch (e) { console.error("Failed to read JSON:", e.message); process.exit(1); }

  const { title, slides } = data;
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9"; pres.title = title; pres.author = "Scoreazy"; pres.subject = "Microlesson";

  buildTitleSlide(pres, title);
  slides.forEach((s, i) => {
    const n = i + 2;
    s.image_path ? buildImageSlide(pres, s.heading, s.bullets, s.image_path, s.image_caption, n)
                 : buildTextSlide(pres, s.heading, s.bullets, n);
  });
  buildClosingSlide(pres, title);

  pres.writeFile({ fileName: outputPath })
    .then(() => console.log(`Aurora theme saved: ${outputPath}`))
    .catch(e  => { console.error(e.message); process.exit(1); });
})();