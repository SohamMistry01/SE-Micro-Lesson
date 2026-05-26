/**
 * theme_terra.js  —  TERRA THEME
 * Palette: Warm Sand · Terracotta · Forest Green · Cream
 * Vibe: Warm, organic, human — great for science, sustainability, wellness
 *
 * Usage: node theme_terra.js <input.json> <output.pptx>
 */

const pptxgen = require("pptxgenjs");
const fs      = require("fs");
const path    = require("path");

// ─── Palette ──────────────────────────────────────────────────────────────────
const C = {
  espresso:   "2C1810",   // title / closing background (deep warm brown)
  terracotta: "C1440E",   // primary accent
  clay:       "E8825A",   // secondary accent / lighter terracotta
  forest:     "2D6A4F",   // green accent
  sage:       "74C69D",   // light green highlight
  cream:      "FEFAE0",   // content slide background
  white:      "FFFFFF",
  text:       "2C1810",   // body text
  muted:      "7C6E65",   // captions
};

const FONT_TITLE = "Palatino Linotype";
const FONT_BODY  = "Calibri";

// ─── Helpers ──────────────────────────────────────────────────────────────────
function shadow()  { return { type: "outer", blur: 8,  offset: 3, angle: 135, color: "C1440E", opacity: 0.12 }; }
function shadow2() { return { type: "outer", blur: 6,  offset: 2, angle: 135, color: "000000", opacity: 0.08 }; }

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
  slide.background = { color: C.espresso };

  // Warm texture: overlapping arcs / semicircles (terracotta tones)
  slide.addShape("ellipse", {
    x: -2.0, y: -0.5, w: 6.0, h: 6.0,
    fill: { color: C.terracotta, transparency: 80 },
    line: { color: C.terracotta, width: 0 },
  });
  slide.addShape("ellipse", {
    x: -1.2, y: 1.0, w: 4.0, h: 4.0,
    fill: { color: C.clay, transparency: 85 },
    line: { color: C.clay, width: 0 },
  });

  // Forest green bottom strip
  slide.addShape("rect", {
    x: 0, y: 5.3, w: 10, h: 0.325,
    fill: { color: C.forest }, line: { color: C.forest, width: 0 },
  });
  // Sage top of that strip
  slide.addShape("rect", {
    x: 0, y: 5.28, w: 10, h: 0.06,
    fill: { color: C.sage }, line: { color: C.sage, width: 0 },
  });

  // Terracotta horizontal rule
  slide.addShape("rect", {
    x: 0.65, y: 1.5, w: 1.8, h: 0.06,
    fill: { color: C.clay }, line: { color: C.clay, width: 0 },
  });

  slide.addText("MICROLESSON", {
    x: 0.65, y: 1.65, w: 8, h: 0.4,
    fontSize: 10, bold: false, color: C.clay,
    fontFace: FONT_BODY, charSpacing: 5,
  });

  slide.addText(title, {
    x: 0.65, y: 2.1, w: 8.2, h: 2.3,
    fontSize: 36, bold: true, color: C.cream,
    fontFace: FONT_TITLE, valign: "top", wrap: true,
  });

  addFooter(slide);
}

function buildTextSlide(pres, heading, bullets, slideNum) {
  const slide = pres.addSlide();
  slide.background = { color: C.cream };

  // Bottom green bar
  slide.addShape("rect", {
    x: 0, y: 5.28, w: 10, h: 0.345,
    fill: { color: C.forest, transparency: 85 },
    line: { color: C.forest, width: 0 },
  });

  // Left accent — terracotta
  slide.addShape("rect", {
    x: 0, y: 0, w: 0.07, h: 5.625,
    fill: { color: C.terracotta }, line: { color: C.terracotta, width: 0 },
  });

  // Heading card — warm white
  slide.addShape("rect", {
    x: 0.07, y: 0.18, w: 9.86, h: 0.88,
    fill: { color: C.white }, line: { color: C.white, width: 0 }, shadow: shadow(),
  });
  slide.addShape("rect", {
    x: 0.07, y: 0.18, w: 0.14, h: 0.88,
    fill: { color: C.terracotta }, line: { color: C.terracotta, width: 0 },
  });
  // Sage micro-line under heading
  slide.addShape("rect", {
    x: 0.07, y: 1.02, w: 9.86, h: 0.04,
    fill: { color: C.sage }, line: { color: C.sage, width: 0 },
  });

  slide.addText(heading, {
    x: 0.32, y: 0.18, w: 9.4, h: 0.88, margin: 0,
    fontSize: 22, bold: true, color: C.text,
    fontFace: FONT_TITLE, valign: "middle",
  });

  if (bullets.length > 0) {
    const bulletItems = bullets.map((b, i) => ([
      { text: "●  ", options: { color: C.terracotta, bold: true, fontSize: 10, fontFace: FONT_BODY } },
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
  slide.background = { color: C.cream };

  // Bottom green bar
  slide.addShape("rect", {
    x: 0, y: 5.28, w: 10, h: 0.345,
    fill: { color: C.forest, transparency: 85 },
    line: { color: C.forest, width: 0 },
  });

  // Left accent
  slide.addShape("rect", {
    x: 0, y: 0, w: 0.07, h: 5.625,
    fill: { color: C.terracotta }, line: { color: C.terracotta, width: 0 },
  });

  // Heading
  slide.addShape("rect", {
    x: 0.07, y: 0.18, w: 9.86, h: 0.88,
    fill: { color: C.white }, line: { color: C.white, width: 0 }, shadow: shadow(),
  });
  slide.addShape("rect", {
    x: 0.07, y: 0.18, w: 0.14, h: 0.88,
    fill: { color: C.terracotta }, line: { color: C.terracotta, width: 0 },
  });
  slide.addShape("rect", {
    x: 0.07, y: 1.02, w: 9.86, h: 0.04,
    fill: { color: C.sage }, line: { color: C.sage, width: 0 },
  });
  slide.addText(heading, {
    x: 0.32, y: 0.18, w: 9.4, h: 0.88, margin: 0,
    fontSize: 22, bold: true, color: C.text,
    fontFace: FONT_TITLE, valign: "middle",
  });

  // Bullets
  if (bullets.length > 0) {
    const bulletItems = bullets.map((b, i) => ([
      { text: "●  ", options: { color: C.terracotta, bold: true, fontSize: 10, fontFace: FONT_BODY } },
      { text: b.text, options: { color: C.text, bold: b.bold, fontSize: 13, fontFace: FONT_BODY, breakLine: i < bullets.length - 1 } },
    ])).flat();
    slide.addText(bulletItems, {
      x: 0.32, y: 1.22, w: 5.2, h: 3.9,
      valign: "top", paraSpaceAfter: 12,
    });
  }

  // Image card — forest green border
  slide.addShape("rect", {
    x: 5.8, y: 1.15, w: 3.95, h: 3.55,
    fill: { color: C.white },
    line: { color: C.forest, width: 1.5 },
    shadow: shadow2(),
  });
  // Terracotta corner pip
  slide.addShape("rect", {
    x: 5.8, y: 1.15, w: 0.28, h: 0.28,
    fill: { color: C.terracotta }, line: { color: C.terracotta, width: 0 },
  });

  const added = tryAddImage(slide, imgPath, {
    x: 5.9, y: 1.25, w: 3.75, h: 3.05,
    sizing: { type: "contain", w: 3.75, h: 3.05 },
  });
  if (!added) {
    slide.addShape("rect", { x: 5.9, y: 1.25, w: 3.75, h: 3.05, fill: { color: "FFF3ED" }, line: { color: C.clay, width: 1 } });
    slide.addText("[ Image ]", { x: 5.9, y: 2.6, w: 3.75, h: 0.5, fontSize: 12, color: C.muted, fontFace: FONT_BODY, align: "center" });
  }

  if (caption) {
    slide.addText(caption, {
      x: 5.8, y: 4.3, w: 3.95, h: 0.4,
      fontSize: 9, italic: true, color: C.muted, fontFace: FONT_BODY, align: "center",
    });
  }

  addSlideNumber(slide, slideNum);
  addFooter(slide);
}

function buildClosingSlide(pres, title) {
  const slide = pres.addSlide();
  slide.background = { color: C.espresso };

  // Layered warm circles
  slide.addShape("ellipse", {
    x: 6.5, y: 2.5, w: 5.0, h: 5.0,
    fill: { color: C.terracotta, transparency: 80 },
    line: { color: C.terracotta, width: 0 },
  });
  slide.addShape("ellipse", {
    x: 7.5, y: 3.2, w: 3.5, h: 3.5,
    fill: { color: C.clay, transparency: 85 },
    line: { color: C.clay, width: 0 },
  });

  // Forest green top strip
  slide.addShape("rect", {
    x: 0, y: 0, w: 10, h: 0.12,
    fill: { color: C.forest }, line: { color: C.forest, width: 0 },
  });
  slide.addShape("rect", {
    x: 0, y: 0.12, w: 10, h: 0.05,
    fill: { color: C.sage }, line: { color: C.sage, width: 0 },
  });

  slide.addShape("rect", {
    x: 0.65, y: 1.55, w: 1.4, h: 0.06,
    fill: { color: C.clay }, line: { color: C.clay, width: 0 },
  });

  slide.addText("That's a wrap!", {
    x: 0.65, y: 1.7, w: 8.8, h: 0.6,
    fontSize: 12, color: C.clay, fontFace: FONT_BODY, charSpacing: 4,
  });
  slide.addText(title, {
    x: 0.65, y: 2.25, w: 7.8, h: 1.7,
    fontSize: 32, bold: true, color: C.cream,
    fontFace: FONT_TITLE, wrap: true,
  });
  slide.addText("Keep practising. Keep scoring.", {
    x: 0.65, y: 4.05, w: 8.8, h: 0.5,
    fontSize: 13, italic: true, color: C.muted, fontFace: FONT_BODY,
  });

  addFooter(slide);
}

// ─── Main ─────────────────────────────────────────────────────────────────────
(function main() {
  const [,, jsonPath, outputPath] = process.argv;
  if (!jsonPath || !outputPath) { console.error("Usage: node theme_terra.js <input.json> <output.pptx>"); process.exit(1); }

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
    .then(() => console.log(`Terra theme saved: ${outputPath}`))
    .catch(e  => { console.error(e.message); process.exit(1); });
})();