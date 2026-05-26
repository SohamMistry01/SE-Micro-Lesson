/**
 * create_ppt.js
 * Usage: node create_ppt.js <input.json> <output.pptx>
 *
 * Reads structured lesson data from JSON and generates a PPTX using pptxgenjs.
 *
 * Slide layout strategy:
 *   Slide 1        → Title slide (dark background)
 *   Slides 2..N    → Content slides
 *     - With image → Two-column (bullets left 55%, image right 40%)
 *     - No image   → Full-width bullets
 *   Last slide     → Closing / thank-you slide
 */

const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

// ─── Palette ─────────────────────────────────────────────────────────────────
const C = {
  navy:     "1C2B3A",   // title slide background / dark elements
  teal:     "028090",   // primary accent
  mint:     "02C39A",   // secondary accent / highlights
  white:    "FFFFFF",
  offWhite: "F4F7F9",   // content slide background
  text:     "1C2B3A",   // body text
  muted:    "64748B",   // captions / sub-text
  bullet:   "028090",   // bullet dot color
};

// ─── Typography ───────────────────────────────────────────────────────────────
const FONT_TITLE = "Trebuchet MS";
const FONT_BODY  = "Calibri";

// ─── Helpers ─────────────────────────────────────────────────────────────────
function makeShadow() {
  return { type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.12 };
}

function slideBackground(slide, color = C.offWhite) {
  slide.background = { color };
}

/** Left accent bar — subtle teal stripe on the left edge of a content slide */
function addAccentBar(slide) {
  slide.addShape("rect", {
    x: 0, y: 0, w: 0.06, h: 5.625,
    fill: { color: C.teal },
    line: { color: C.teal, width: 0 },
  });
}

/** Slide number (bottom-right, muted) */
function addSlideNumber(slide, n) {
  slide.addText(String(n), {
    x: 9.3, y: 5.2, w: 0.5, h: 0.3,
    fontSize: 9, color: C.muted, fontFace: FONT_BODY, align: "right",
  });
}

/** Footer brand label */
function addFooter(slide, label = "Scoreazy · Scoring Made Easy") {
  slide.addText(label, {
    x: 0.2, y: 5.3, w: 9.6, h: 0.2,
    fontSize: 8, color: C.muted, fontFace: FONT_BODY, align: "center",
  });
}

/** Safely add an image only if the file exists */
function tryAddImage(slide, imgPath, opts) {
  if (!imgPath) return false;
  const resolved = path.isAbsolute(imgPath) ? imgPath : path.resolve(imgPath);
  if (!fs.existsSync(resolved)) {
    console.warn(`Image not found, skipping: ${resolved}`);
    return false;
  }
  slide.addImage({ path: resolved, ...opts });
  return true;
}

// ─── Slide builders ───────────────────────────────────────────────────────────

/** Slide 1: title slide */
function buildTitleSlide(pres, title) {
  const slide = pres.addSlide();
  slideBackground(slide, C.navy);

  // Teal top strip
  slide.addShape("rect", {
    x: 0, y: 0, w: 10, h: 0.08,
    fill: { color: C.teal }, line: { color: C.teal, width: 0 },
  });

  // Mint bottom strip
  slide.addShape("rect", {
    x: 0, y: 5.545, w: 10, h: 0.08,
    fill: { color: C.mint }, line: { color: C.mint, width: 0 },
  });

  // Decorative circle (top-right)
  slide.addShape("ellipse", {
    x: 7.8, y: -1.2, w: 3.5, h: 3.5,
    fill: { color: C.teal, transparency: 80 },
    line: { color: C.teal, width: 0 },
  });

  // "MICROLESSON" label
  slide.addText("MICROLESSON", {
    x: 0.6, y: 1.6, w: 8, h: 0.4,
    fontSize: 11, bold: false, color: C.mint,
    fontFace: FONT_BODY, charSpacing: 4,
  });

  // Main title
  slide.addText(title, {
    x: 0.6, y: 2.1, w: 8.5, h: 2.2,
    fontSize: 36, bold: true, color: C.white,
    fontFace: FONT_TITLE, valign: "top",
    wrap: true,
  });

  // Teal accent rule under title
  slide.addShape("rect", {
    x: 0.6, y: 4.4, w: 1.2, h: 0.06,
    fill: { color: C.mint }, line: { color: C.mint, width: 0 },
  });

  addFooter(slide);
  return slide;
}

/** Content slide — full width bullets (no image) */
function buildTextSlide(pres, heading, bullets, slideNum) {
  const slide = pres.addSlide();
  slideBackground(slide, C.offWhite);
  addAccentBar(slide);

  // Heading background pill
  slide.addShape("rect", {
    x: 0.06, y: 0.18, w: 9.88, h: 0.85,
    fill: { color: C.white }, line: { color: C.white, width: 0 },
    shadow: makeShadow(),
  });

  // Teal left accent on heading block
  slide.addShape("rect", {
    x: 0.06, y: 0.18, w: 0.12, h: 0.85,
    fill: { color: C.teal }, line: { color: C.teal, width: 0 },
  });

  // Slide heading
  slide.addText(heading, {
    x: 0.28, y: 0.18, w: 9.4, h: 0.85, margin: 0,
    fontSize: 22, bold: true, color: C.text,
    fontFace: FONT_TITLE, valign: "middle",
  });

  // Bullet items
  if (bullets.length > 0) {
    const bulletItems = bullets.map((b, i) => ([
      {
        text: "▸  ",
        options: { color: C.teal, bold: true, fontSize: 13, fontFace: FONT_BODY },
      },
      {
        text: b.text,
        options: {
          color: C.text, bold: b.bold, fontSize: 14, fontFace: FONT_BODY,
          breakLine: i < bullets.length - 1,
        },
      },
    ])).flat();

    slide.addText(bulletItems, {
      x: 0.28, y: 1.22, w: 9.44, h: 3.9,
      valign: "top", paraSpaceAfter: 10,
    });
  }

  addSlideNumber(slide, slideNum);
  addFooter(slide);
  return slide;
}

/** Content slide — two-column with image on right */
function buildImageSlide(pres, heading, bullets, imgPath, caption, slideNum) {
  const slide = pres.addSlide();
  slideBackground(slide, C.offWhite);
  addAccentBar(slide);

  // Heading block
  slide.addShape("rect", {
    x: 0.06, y: 0.18, w: 9.88, h: 0.85,
    fill: { color: C.white }, line: { color: C.white, width: 0 },
    shadow: makeShadow(),
  });
  slide.addShape("rect", {
    x: 0.06, y: 0.18, w: 0.12, h: 0.85,
    fill: { color: C.teal }, line: { color: C.teal, width: 0 },
  });
  slide.addText(heading, {
    x: 0.28, y: 0.18, w: 9.4, h: 0.85, margin: 0,
    fontSize: 22, bold: true, color: C.text,
    fontFace: FONT_TITLE, valign: "middle",
  });

  // Left column: bullets (55% width)
  if (bullets.length > 0) {
    const bulletItems = bullets.map((b, i) => ([
      {
        text: "▸  ",
        options: { color: C.teal, bold: true, fontSize: 12, fontFace: FONT_BODY },
      },
      {
        text: b.text,
        options: {
          color: C.text, bold: b.bold, fontSize: 13, fontFace: FONT_BODY,
          breakLine: i < bullets.length - 1,
        },
      },
    ])).flat();

    slide.addText(bulletItems, {
      x: 0.28, y: 1.22, w: 5.3, h: 3.9,
      valign: "top", paraSpaceAfter: 10,
    });
  }

  // Right column: image card (40% width)
  slide.addShape("rect", {
    x: 5.85, y: 1.15, w: 3.9, h: 3.5,
    fill: { color: C.white }, line: { color: "E2E8F0", width: 1 },
    shadow: makeShadow(),
  });

  const added = tryAddImage(slide, imgPath, {
    x: 5.95, y: 1.25, w: 3.7, h: 3.0,
    sizing: { type: "contain", w: 3.7, h: 3.0 },
  });

  if (!added) {
    // Fallback placeholder if image file is missing
    slide.addShape("rect", {
      x: 5.95, y: 1.25, w: 3.7, h: 3.0,
      fill: { color: "E2E8F0" }, line: { color: "CBD5E1", width: 1 },
    });
    slide.addText("[ Image ]", {
      x: 5.95, y: 2.5, w: 3.7, h: 0.5,
      fontSize: 12, color: C.muted, fontFace: FONT_BODY, align: "center",
    });
  }

  // Caption
  if (caption) {
    slide.addText(caption, {
      x: 5.85, y: 4.25, w: 3.9, h: 0.4,
      fontSize: 9, italic: true, color: C.muted,
      fontFace: FONT_BODY, align: "center",
    });
  }

  addSlideNumber(slide, slideNum);
  addFooter(slide);
  return slide;
}

/** Final slide: closing */
function buildClosingSlide(pres, title) {
  const slide = pres.addSlide();
  slideBackground(slide, C.navy);

  slide.addShape("rect", {
    x: 0, y: 0, w: 10, h: 0.08,
    fill: { color: C.mint }, line: { color: C.mint, width: 0 },
  });
  slide.addShape("rect", {
    x: 0, y: 5.545, w: 10, h: 0.08,
    fill: { color: C.teal }, line: { color: C.teal, width: 0 },
  });

  slide.addText("That's a wrap!", {
    x: 0.6, y: 1.6, w: 8.8, h: 0.7,
    fontSize: 13, color: C.mint, fontFace: FONT_BODY, charSpacing: 3,
  });
  slide.addText(title, {
    x: 0.6, y: 2.2, w: 8.8, h: 1.6,
    fontSize: 30, bold: true, color: C.white,
    fontFace: FONT_TITLE, wrap: true,
  });
  slide.addText("Keep practising. Keep scoring.", {
    x: 0.6, y: 4.0, w: 8.8, h: 0.5,
    fontSize: 14, italic: true, color: C.muted,
    fontFace: FONT_BODY,
  });

  addFooter(slide);
  return slide;
}

// ─── Main ─────────────────────────────────────────────────────────────────────

(function main() {
  const [,, jsonPath, outputPath] = process.argv;

  if (!jsonPath || !outputPath) {
    console.error("Usage: node create_ppt.js <input.json> <output.pptx>");
    process.exit(1);
  }

  let data;
  try {
    data = JSON.parse(fs.readFileSync(jsonPath, "utf-8"));
  } catch (e) {
    console.error("Failed to read input JSON:", e.message);
    process.exit(1);
  }

  const { title, slides } = data;
  const pres = new pptxgen();
  pres.layout  = "LAYOUT_16x9";
  pres.title   = title;
  pres.author  = "Scoreazy";
  pres.subject = "Microlesson";

  // Title slide
  buildTitleSlide(pres, title);

  // Content slides
  slides.forEach((slide, i) => {
    const slideNum = i + 2; // slide 1 is the title
    if (slide.image_path) {
      buildImageSlide(pres, slide.heading, slide.bullets, slide.image_path, slide.image_caption, slideNum);
    } else {
      buildTextSlide(pres, slide.heading, slide.bullets, slideNum);
    }
  });

  // Closing slide
  buildClosingSlide(pres, title);

  pres.writeFile({ fileName: outputPath })
    .then(() => {
      console.log(`PPT saved to: ${outputPath}`);
    })
    .catch((err) => {
      console.error("Failed to write PPTX:", err.message);
      process.exit(1);
    });
})();
