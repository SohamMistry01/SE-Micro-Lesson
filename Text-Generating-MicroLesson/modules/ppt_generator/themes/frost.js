/**
 * theme_frost.js  —  FROST THEME
 * Palette: Arctic White · Slate Charcoal · Ice Blue · Electric Cyan
 * Vibe: Clean, sharp, modern — perfect for tech, data, and STEM subjects
 *
 * Usage: node theme_frost.js <input.json> <output.pptx>
 */

const pptxgen = require("pptxgenjs");
const fs      = require("fs");
const path    = require("path");

// ─── Palette ──────────────────────────────────────────────────────────────────
const C = {
  charcoal:  "1A202C",   // title / closing background
  slate:     "2D3748",   // secondary dark
  cyan:      "00B4D8",   // primary accent
  iceCyan:   "90E0EF",   // secondary accent
  frost:     "CAF0F8",   // lightest blue highlight
  white:     "FFFFFF",
  snow:      "F7FAFC",   // content slide background
  text:      "1A202C",   // body text
  muted:     "718096",   // captions
};

const FONT_TITLE = "Segoe UI";
const FONT_BODY  = "Segoe UI";

// ─── Helpers ──────────────────────────────────────────────────────────────────
function shadow()  { return { type: "outer", blur: 10, offset: 3, angle: 135, color: "00B4D8", opacity: 0.18 }; }
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
  slide.background = { color: C.charcoal };

  // Grid of subtle dots pattern (small square grid in top-right)
  for (let col = 0; col < 6; col++) {
    for (let row = 0; row < 4; row++) {
      slide.addShape("ellipse", {
        x: 7.0 + col * 0.42, y: 0.3 + row * 0.42, w: 0.06, h: 0.06,
        fill: { color: C.cyan, transparency: 65 },
        line: { color: C.cyan, width: 0 },
      });
    }
  }

  // Bold cyan top bar
  slide.addShape("rect", {
    x: 0, y: 0, w: 10, h: 0.12,
    fill: { color: C.cyan }, line: { color: C.cyan, width: 0 },
  });

  // Ice blue bottom bar
  slide.addShape("rect", {
    x: 0, y: 5.505, w: 10, h: 0.12,
    fill: { color: C.iceCyan }, line: { color: C.iceCyan, width: 0 },
  });

  // Left column — darker panel for contrast
  slide.addShape("rect", {
    x: 0, y: 0.12, w: 0.45, h: 5.385,
    fill: { color: C.slate }, line: { color: C.slate, width: 0 },
  });

  slide.addText("MICROLESSON", {
    x: 0.65, y: 1.55, w: 8, h: 0.4,
    fontSize: 10, bold: false, color: C.iceCyan,
    fontFace: FONT_BODY, charSpacing: 5,
  });

  // Cyan underline accent
  slide.addShape("rect", {
    x: 0.65, y: 1.94, w: 1.6, h: 0.05,
    fill: { color: C.cyan }, line: { color: C.cyan, width: 0 },
  });

  slide.addText(title, {
    x: 0.65, y: 2.05, w: 8.2, h: 2.3,
    fontSize: 38, bold: true, color: C.white,
    fontFace: FONT_TITLE, valign: "top", wrap: true,
  });

  addFooter(slide);
}

function buildTextSlide(pres, heading, bullets, slideNum) {
  const slide = pres.addSlide();
  slide.background = { color: C.snow };

  // Thin cyan top bar
  slide.addShape("rect", {
    x: 0, y: 0, w: 10, h: 0.06,
    fill: { color: C.cyan }, line: { color: C.cyan, width: 0 },
  });

  // Left panel — charcoal strip
  slide.addShape("rect", {
    x: 0, y: 0.06, w: 0.07, h: 5.565,
    fill: { color: C.charcoal }, line: { color: C.charcoal, width: 0 },
  });

  // Dot grid (bottom-right decoration)
  for (let col = 0; col < 4; col++) {
    for (let row = 0; row < 3; row++) {
      slide.addShape("ellipse", {
        x: 8.9 + col * 0.32, y: 4.5 + row * 0.32, w: 0.05, h: 0.05,
        fill: { color: C.iceCyan, transparency: 50 },
        line: { color: C.iceCyan, width: 0 },
      });
    }
  }

  // Heading card
  slide.addShape("rect", {
    x: 0.07, y: 0.18, w: 9.86, h: 0.88,
    fill: { color: C.white }, line: { color: C.white, width: 0 }, shadow: shadow(),
  });
  slide.addShape("rect", {
    x: 0.07, y: 0.18, w: 0.14, h: 0.88,
    fill: { color: C.cyan }, line: { color: C.cyan, width: 0 },
  });
  // Cyan micro-line bottom of card
  slide.addShape("rect", {
    x: 0.07, y: 1.02, w: 9.86, h: 0.04,
    fill: { color: C.frost }, line: { color: C.frost, width: 0 },
  });

  slide.addText(heading, {
    x: 0.32, y: 0.18, w: 9.4, h: 0.88, margin: 0,
    fontSize: 21, bold: true, color: C.text,
    fontFace: FONT_TITLE, valign: "middle",
  });

  if (bullets.length > 0) {
    const bulletItems = bullets.map((b, i) => ([
      { text: "→  ", options: { color: C.cyan, bold: true, fontSize: 13, fontFace: FONT_BODY } },
      { text: b.text, options: { color: C.text, bold: b.bold, fontSize: 14, fontFace: FONT_BODY, breakLine: i < bullets.length - 1 } },
    ])).flat();

    slide.addText(bulletItems, {
      x: 0.32, y: 1.22, w: 9.4, h: 3.9,
      valign: "top", paraSpaceAfter: 11,
    });
  }

  addSlideNumber(slide, slideNum);
  addFooter(slide);
}

function buildImageSlide(pres, heading, bullets, imgPath, caption, slideNum) {
  const slide = pres.addSlide();
  slide.background = { color: C.snow };

  // Top bar
  slide.addShape("rect", {
    x: 0, y: 0, w: 10, h: 0.06,
    fill: { color: C.cyan }, line: { color: C.cyan, width: 0 },
  });

  // Left panel
  slide.addShape("rect", {
    x: 0, y: 0.06, w: 0.07, h: 5.565,
    fill: { color: C.charcoal }, line: { color: C.charcoal, width: 0 },
  });

  // Heading card
  slide.addShape("rect", {
    x: 0.07, y: 0.18, w: 9.86, h: 0.88,
    fill: { color: C.white }, line: { color: C.white, width: 0 }, shadow: shadow(),
  });
  slide.addShape("rect", {
    x: 0.07, y: 0.18, w: 0.14, h: 0.88,
    fill: { color: C.cyan }, line: { color: C.cyan, width: 0 },
  });
  slide.addShape("rect", {
    x: 0.07, y: 1.02, w: 9.86, h: 0.04,
    fill: { color: C.frost }, line: { color: C.frost, width: 0 },
  });
  slide.addText(heading, {
    x: 0.32, y: 0.18, w: 9.4, h: 0.88, margin: 0,
    fontSize: 21, bold: true, color: C.text,
    fontFace: FONT_TITLE, valign: "middle",
  });

  // Bullets
  if (bullets.length > 0) {
    const bulletItems = bullets.map((b, i) => ([
      { text: "→  ", options: { color: C.cyan, bold: true, fontSize: 12, fontFace: FONT_BODY } },
      { text: b.text, options: { color: C.text, bold: b.bold, fontSize: 13, fontFace: FONT_BODY, breakLine: i < bullets.length - 1 } },
    ])).flat();
    slide.addText(bulletItems, {
      x: 0.32, y: 1.22, w: 5.2, h: 3.9,
      valign: "top", paraSpaceAfter: 11,
    });
  }

  // Image card — sharp, modern with cyan border
  slide.addShape("rect", {
    x: 5.8, y: 1.15, w: 3.95, h: 3.55,
    fill: { color: C.white },
    line: { color: C.iceCyan, width: 1.5 },
    shadow: shadow2(),
  });
  // Cyan top-left corner bar
  slide.addShape("rect", {
    x: 5.8, y: 1.15, w: 3.95, h: 0.06,
    fill: { color: C.cyan }, line: { color: C.cyan, width: 0 },
  });

  const added = tryAddImage(slide, imgPath, {
    x: 5.9, y: 1.28, w: 3.75, h: 3.05,
    sizing: { type: "contain", w: 3.75, h: 3.05 },
  });
  if (!added) {
    slide.addShape("rect", { x: 5.9, y: 1.28, w: 3.75, h: 3.05, fill: { color: "E8F8FC" }, line: { color: C.iceCyan, width: 1 } });
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
  slide.background = { color: C.charcoal };

  // Dot grid top-right
  for (let col = 0; col < 8; col++) {
    for (let row = 0; row < 5; row++) {
      slide.addShape("ellipse", {
        x: 5.5 + col * 0.52, y: -0.2 + row * 0.52, w: 0.07, h: 0.07,
        fill: { color: C.cyan, transparency: 70 },
        line: { color: C.cyan, width: 0 },
      });
    }
  }

  // Top cyan bar
  slide.addShape("rect", {
    x: 0, y: 0, w: 10, h: 0.12,
    fill: { color: C.cyan }, line: { color: C.cyan, width: 0 },
  });
  // Bottom ice bar
  slide.addShape("rect", {
    x: 0, y: 5.505, w: 10, h: 0.12,
    fill: { color: C.iceCyan }, line: { color: C.iceCyan, width: 0 },
  });

  // Left panel
  slide.addShape("rect", {
    x: 0, y: 0.12, w: 0.45, h: 5.385,
    fill: { color: C.slate }, line: { color: C.slate, width: 0 },
  });

  // Cyan underline
  slide.addShape("rect", {
    x: 0.65, y: 1.93, w: 1.8, h: 0.05,
    fill: { color: C.cyan }, line: { color: C.cyan, width: 0 },
  });

  slide.addText("That's a wrap!", {
    x: 0.65, y: 1.6, w: 8.8, h: 0.5,
    fontSize: 12, color: C.iceCyan, fontFace: FONT_BODY, charSpacing: 4,
  });
  slide.addText(title, {
    x: 0.65, y: 2.1, w: 8.2, h: 1.7,
    fontSize: 32, bold: true, color: C.white,
    fontFace: FONT_TITLE, wrap: true,
  });
  slide.addText("Keep practising. Keep scoring.", {
    x: 0.65, y: 4.0, w: 8.8, h: 0.5,
    fontSize: 13, italic: true, color: C.muted, fontFace: FONT_BODY,
  });

  addFooter(slide);
}

// ─── Main ─────────────────────────────────────────────────────────────────────
(function main() {
  const [,, jsonPath, outputPath] = process.argv;
  if (!jsonPath || !outputPath) { console.error("Usage: node theme_frost.js <input.json> <output.pptx>"); process.exit(1); }

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
    .then(() => console.log(`Frost theme saved: ${outputPath}`))
    .catch(e  => { console.error(e.message); process.exit(1); });
})();