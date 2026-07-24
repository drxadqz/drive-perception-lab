#!/usr/bin/env node

/**
 * Verify cross-device formula assets on GitHub's real public blob renderer.
 *
 * Indexed notes deliberately contain zero live MathJax regions. Equations are
 * committed as compact, content-sized 2x PNG pairs inside a <picture>: the
 * light image is the fallback <img>, while a dark image is selected through
 * prefers-color-scheme. Canonical TeX remains available separately as source.
 *
 * This smoke test opens changed notes in desktop and iPad-sized WebKit
 * contexts. It rejects missing or incorrectly themed assets, wrong intrinsic
 * density, oversized/tiny/off-centre formulas, horizontal overflow, and any
 * residual MathJax or raw mathematical code block.
 */

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import process from "node:process";
import { webkit } from "playwright";

const root = resolve(import.meta.dirname, "..");
const repository = process.env.RENDER_REPOSITORY;
const renderSha = process.env.RENDER_SHA;
const baseSha = process.env.RENDER_BASE_SHA;
const formulaPicturePattern =
  /<picture\b[^>]*>\s*<source\b[^>]*>\s*<img\b[^>]*\balt="公式：[^"]+"[^>]*>\s*<\/picture>/g;

const MIN_DISPLAY_WIDTH = 96;
const MAX_DISPLAY_WIDTH = 720;
const MIN_DISPLAY_HEIGHT = 36;
const MAX_DISPLAY_HEIGHT = 180;
const MAX_ARTICLE_WIDTH_SHARE = 0.92;
const MAX_CENTER_DELTA = 4;
const DIMENSION_TOLERANCE = 2;
const DENSITY_MIN = 1.95;
const DENSITY_MAX = 2.05;

if (!repository || !renderSha) {
  console.error(
    "RENDER_REPOSITORY and RENDER_SHA are required for the published formula-asset smoke test.",
  );
  process.exit(2);
}

function gitLines(args) {
  return execFileSync("git", args, {
    cwd: root,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  })
    .split(/\r?\n/)
    .map((value) => value.trim())
    .filter(Boolean);
}

function changedPaths() {
  const usableBase =
    baseSha && !/^0+$/.test(baseSha) && /^[0-9a-f]{7,40}$/i.test(baseSha);
  try {
    if (usableBase) {
      return gitLines(["diff", "--name-only", `${baseSha}...${renderSha}`]);
    }
    return gitLines([
      "diff-tree",
      "--no-commit-id",
      "--name-only",
      "-r",
      renderSha,
    ]);
  } catch {
    console.warn(
      "Could not resolve the event diff; checking every tracked reading note.",
    );
    return gitLines(["ls-files", "notes/**/*.md"]);
  }
}

function trackedReadingNotes() {
  return gitLines(["ls-files", "notes/**/*.md"])
    .map((path) => path.replaceAll("\\", "/"))
    .filter((path) => existsSync(resolve(root, path)));
}

function formulaCount(markdown) {
  return [...markdown.matchAll(formulaPicturePattern)].length;
}

const changed = [...new Set(changedPaths())].map((path) =>
  path.replaceAll("\\", "/"),
);
const globalFormulaChange = changed.some(
  (path) =>
    path.startsWith("assets/notes/") ||
    path === "scripts/check_published_math.mjs" ||
    path === "scripts/render_formula_assets.py" ||
    path === ".github/workflows/validate-index.yml",
);

const candidatePaths = globalFormulaChange
  ? trackedReadingNotes()
  : changed.filter(
      (path) =>
        path.startsWith("notes/") &&
        path.toLowerCase().endsWith(".md") &&
        existsSync(resolve(root, path)),
    );

const candidates = [...new Set(candidatePaths)]
  .map((path) => {
    const markdown = readFileSync(resolve(root, path), "utf8");
    return { path, expected: formulaCount(markdown) };
  })
  .filter(({ expected }) => expected > 0);

if (!candidates.length) {
  console.log("OK: no changed indexed note contains formula picture pairs");
  process.exit(0);
}

const ipadUserAgent =
  "Mozilla/5.0 (iPad; CPU OS 18_5 like Mac OS X) " +
  "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 " +
  "Mobile/15E148 Safari/604.1";

const profiles = [
  {
    name: "desktop-light",
    viewport: { width: 1440, height: 900 },
    colorScheme: "light",
    isMobile: false,
    hasTouch: false,
    deviceScaleFactor: 1,
  },
  {
    name: "desktop-dark",
    viewport: { width: 1440, height: 900 },
    colorScheme: "dark",
    isMobile: false,
    hasTouch: false,
    deviceScaleFactor: 1,
  },
  {
    name: "ipad-portrait-light",
    viewport: { width: 768, height: 1024 },
    colorScheme: "light",
    isMobile: true,
    hasTouch: true,
    deviceScaleFactor: 2,
    userAgent: ipadUserAgent,
  },
  {
    name: "ipad-landscape-dark",
    viewport: { width: 1024, height: 768 },
    colorScheme: "dark",
    isMobile: true,
    hasTouch: true,
    deviceScaleFactor: 2,
    userAgent: ipadUserAgent,
  },
];

function formatImageFailure(image) {
  const label = image.alt || "(missing alt)";
  return `${label}: ${image.issues.join("; ")}`;
}

const browser = await webkit.launch({ headless: true });
const failures = [];

try {
  for (const candidate of candidates) {
    const encodedPath = candidate.path
      .split("/")
      .map((part) => encodeURIComponent(part))
      .join("/");
    const url =
      `https://github.com/${repository}/blob/${renderSha}/${encodedPath}`;

    for (const profile of profiles) {
      const contextOptions = {
        viewport: profile.viewport,
        deviceScaleFactor: profile.deviceScaleFactor,
        isMobile: profile.isMobile,
        hasTouch: profile.hasTouch,
        colorScheme: profile.colorScheme,
      };
      if (profile.userAgent) {
        contextOptions.userAgent = profile.userAgent;
      }

      const context = await browser.newContext(contextOptions);
      const page = await context.newPage();
      try {
        const response = await page.goto(url, {
          waitUntil: "domcontentloaded",
          timeout: 45_000,
        });
        if (!response || !response.ok()) {
          failures.push(
            `${candidate.path} ${profile.name}: GitHub returned ` +
              `${response?.status() ?? "no response"}`,
          );
          continue;
        }

        try {
          await page.waitForFunction(
            ({ expected }) => {
              const article = document.querySelector(
                "article.markdown-body, .markdown-body",
              );
              const images = [
                ...(article?.querySelectorAll('img[alt^="公式："]') ?? []),
              ];
              return (
                images.length === expected &&
                images.every(
                  (image) => image.complete && image.naturalWidth > 0,
                )
              );
            },
            { expected: candidate.expected },
            { timeout: 45_000 },
          );
        } catch {
          // Collect the exact DOM state and actionable diagnostics below.
        }

        const state = await page.evaluate(
          ({
            expected,
            expectedTheme,
            minDisplayWidth,
            maxDisplayWidth,
            minDisplayHeight,
            maxDisplayHeight,
            maxArticleWidthShare,
            maxCenterDelta,
            dimensionTolerance,
            densityMin,
            densityMax,
          }) => {
            const article = document.querySelector(
              "article.markdown-body, .markdown-body",
            );
            const articleBox = article?.getBoundingClientRect();
            const images = [
              ...(article?.querySelectorAll('img[alt^="公式："]') ?? []),
            ];
            const themeSuffix = new RegExp(
              `-${expectedTheme}\\.png(?:$|[?#])`,
              "i",
            );

            const imageStates = images.map((image) => {
              const box = image.getBoundingClientRect();
              const parent = image.closest("p");
              const parentBox = parent?.getBoundingClientRect();
              const declaredWidth = Number(image.getAttribute("width"));
              const declaredHeight = Number(image.getAttribute("height"));
              const currentSrc = decodeURIComponent(image.currentSrc || "");
              const densityX =
                declaredWidth > 0 ? image.naturalWidth / declaredWidth : 0;
              const densityY =
                declaredHeight > 0 ? image.naturalHeight / declaredHeight : 0;
              const widthShare =
                articleBox?.width > 0 ? box.width / articleBox.width : 0;
              const centerDelta =
                parentBox && box.width > 0
                  ? Math.abs(
                      box.left +
                        box.width / 2 -
                        (parentBox.left + parentBox.width / 2),
                    )
                  : Number.POSITIVE_INFINITY;
              const issues = [];

              if (!image.complete || image.naturalWidth <= 0) {
                issues.push("image did not load");
              }
              if (!declaredWidth || !declaredHeight) {
                issues.push("missing positive width/height attributes");
              }
              if (!themeSuffix.test(currentSrc)) {
                issues.push(
                  `currentSrc did not select -${expectedTheme}.png (${currentSrc || "empty"})`,
                );
              }
              if (
                Math.abs(image.naturalWidth - declaredWidth * 2) >
                  dimensionTolerance ||
                densityX < densityMin ||
                densityX > densityMax
              ) {
                issues.push(
                  `intrinsic width ${image.naturalWidth}px is not approximately 2x declared ${declaredWidth}px`,
                );
              }
              if (
                Math.abs(image.naturalHeight - declaredHeight * 2) >
                  dimensionTolerance ||
                densityY < densityMin ||
                densityY > densityMax
              ) {
                issues.push(
                  `intrinsic height ${image.naturalHeight}px is not approximately 2x declared ${declaredHeight}px`,
                );
              }
              if (
                box.width < minDisplayWidth ||
                box.width > maxDisplayWidth
              ) {
                issues.push(
                  `display width ${box.width.toFixed(1)}px is outside ${minDisplayWidth}-${maxDisplayWidth}px`,
                );
              }
              if (
                box.height < minDisplayHeight ||
                box.height > maxDisplayHeight
              ) {
                issues.push(
                  `display height ${box.height.toFixed(1)}px is outside ${minDisplayHeight}-${maxDisplayHeight}px`,
                );
              }
              if (widthShare > maxArticleWidthShare + 0.002) {
                issues.push(
                  `uses ${(widthShare * 100).toFixed(1)}% of article width (limit ${(maxArticleWidthShare * 100).toFixed(0)}%)`,
                );
              }
              if (
                !articleBox ||
                box.left < articleBox.left - 1 ||
                box.right > articleBox.right + 1
              ) {
                issues.push("extends outside the article bounds");
              }
              if (!parentBox || centerDelta > maxCenterDelta) {
                issues.push(
                  `not centred in its paragraph (delta ${Number.isFinite(centerDelta) ? centerDelta.toFixed(1) : "unknown"}px)`,
                );
              }

              return {
                alt: image.getAttribute("alt") || "",
                currentSrc,
                complete: image.complete,
                naturalWidth: image.naturalWidth,
                naturalHeight: image.naturalHeight,
                declaredWidth,
                declaredHeight,
                renderedWidth: Number(box.width.toFixed(2)),
                renderedHeight: Number(box.height.toFixed(2)),
                densityX: Number(densityX.toFixed(3)),
                densityY: Number(densityY.toFixed(3)),
                widthShare: Number(widthShare.toFixed(3)),
                centerDelta: Number.isFinite(centerDelta)
                  ? Number(centerDelta.toFixed(2))
                  : null,
                issues,
              };
            });

            const mathRendererNodes = [
              ...(article?.querySelectorAll(
                "math-renderer, mjx-container, .MathJax, .MathJax_Display, script[type^='math/tex']",
              ) ?? []),
            ];
            const mathCodeBlocks = [
              ...(article?.querySelectorAll("pre code") ?? []),
            ]
              .filter((code) => {
                const className = code.className || "";
                const value = code.textContent || "";
                return (
                  /(?:language|highlight-source)-(?:math|latex|tex)/i.test(
                    className,
                  ) ||
                  /(?:^\s*\$\$|\\(?:mathcal|frac|operatorname|begin\{|left\[|right\]))/m.test(
                    value,
                  )
                );
              })
              .map((code) =>
                (code.textContent || "").replace(/\s+/g, " ").slice(0, 160),
              );

            return {
              articleFound: Boolean(article),
              expected,
              actual: images.length,
              mathRenderers: mathRendererNodes.length,
              mathCodeBlocks,
              horizontalOverflowBy: article
                ? Math.max(0, article.scrollWidth - article.clientWidth)
                : null,
              images: imageStates,
            };
          },
          {
            expected: candidate.expected,
            expectedTheme: profile.colorScheme,
            minDisplayWidth: MIN_DISPLAY_WIDTH,
            maxDisplayWidth: MAX_DISPLAY_WIDTH,
            minDisplayHeight: MIN_DISPLAY_HEIGHT,
            maxDisplayHeight: MAX_DISPLAY_HEIGHT,
            maxArticleWidthShare: MAX_ARTICLE_WIDTH_SHARE,
            maxCenterDelta: MAX_CENTER_DELTA,
            dimensionTolerance: DIMENSION_TOLERANCE,
            densityMin: DENSITY_MIN,
            densityMax: DENSITY_MAX,
          },
        );

        const profileIssues = [];
        if (!state.articleFound) {
          profileIssues.push("GitHub markdown article was not found");
        }
        if (state.actual !== state.expected) {
          profileIssues.push(
            `found ${state.actual}/${state.expected} expected formula images`,
          );
        }
        if (state.mathRenderers !== 0) {
          profileIssues.push(
            `found ${state.mathRenderers} residual MathJax renderer(s)`,
          );
        }
        if (state.mathCodeBlocks.length) {
          profileIssues.push(
            `found raw mathematical code block(s): ${state.mathCodeBlocks.join(" | ")}`,
          );
        }
        if ((state.horizontalOverflowBy ?? 0) > 2) {
          profileIssues.push(
            `article has ${state.horizontalOverflowBy}px horizontal overflow`,
          );
        }
        profileIssues.push(
          ...state.images
            .filter((image) => image.issues.length)
            .map(formatImageFailure),
        );

        if (profileIssues.length) {
          failures.push(
            `${candidate.path} ${profile.name}: ${profileIssues.join(" || ")}`,
          );
        } else {
          console.log(
            `OK: ${candidate.path} ${profile.name} loaded ` +
              `${state.actual}/${state.expected} compact ${profile.colorScheme} ` +
              "formula images at approximately 2x density, centred with no MathJax",
          );
        }
      } finally {
        await context.close();
      }
    }
  }
} finally {
  await browser.close();
}

if (failures.length) {
  console.error("ERROR: published cross-device formula rendering failed");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log(
  `OK: GitHub rendered every formula picture pair in ${candidates.length} ` +
    `changed reading note(s) across ${profiles.length} desktop/iPad profiles`,
);
