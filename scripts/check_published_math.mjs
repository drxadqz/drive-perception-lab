#!/usr/bin/env node

/**
 * Verify cross-device formula assets on GitHub's real public blob renderer.
 *
 * Indexed notes deliberately contain zero live MathJax regions.  Equations are
 * committed as opaque 2048 px PNGs, with ordinary-text explanations and a
 * canonical TeX source.  This smoke test opens changed notes with iPad-sized
 * WebKit viewports and rejects broken, low-density, tiny, overflowing, or
 * residual MathJax output.
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
const formulaImagePattern =
  /!\[(?<alt>公式图：[^\]]+)\]\((?<target>[^)\s]+)\)/g;

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
  return [...markdown.matchAll(formulaImagePattern)].length;
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
  console.log("OK: no changed indexed note contains formula PNGs");
  process.exit(0);
}

const profiles = [
  {
    name: "ipad-portrait-light",
    viewport: { width: 768, height: 1024 },
    colorScheme: "light",
  },
  {
    name: "ipad-landscape-dark",
    viewport: { width: 1024, height: 768 },
    colorScheme: "dark",
  },
];

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
      const context = await browser.newContext({
        viewport: profile.viewport,
        deviceScaleFactor: 2,
        isMobile: true,
        hasTouch: true,
        colorScheme: profile.colorScheme,
        userAgent:
          "Mozilla/5.0 (iPad; CPU OS 18_5 like Mac OS X) " +
          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 " +
          "Mobile/15E148 Safari/604.1",
      });
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
                ...(article?.querySelectorAll('img[alt^="公式图："]') ?? []),
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
          // Collect the exact DOM state below.
        }

        const state = await page.evaluate(({ expected, viewportHeight }) => {
          const article = document.querySelector(
            "article.markdown-body, .markdown-body",
          );
          const articleBox = article?.getBoundingClientRect();
          const images = [
            ...(article?.querySelectorAll('img[alt^="公式图："]') ?? []),
          ];
          const imageStates = images.map((image) => {
            const box = image.getBoundingClientRect();
            return {
              alt: image.getAttribute("alt") || "",
              complete: image.complete,
              naturalWidth: image.naturalWidth,
              naturalHeight: image.naturalHeight,
              renderedWidth: box.width,
              renderedHeight: box.height,
              density:
                box.width > 0 ? image.naturalWidth / box.width : 0,
              widthShare:
                articleBox?.width > 0 ? box.width / articleBox.width : 0,
              insideArticle: Boolean(
                articleBox &&
                  box.left >= articleBox.left - 1 &&
                  box.right <= articleBox.right + 1,
              ),
              heightSafe:
                box.height >= 56 && box.height <= viewportHeight * 0.8,
            };
          });
          return {
            articleFound: Boolean(article),
            expected,
            actual: images.length,
            mathRenderers:
              article?.querySelectorAll("math-renderer").length ?? -1,
            mathCodeBlocks:
              article?.querySelectorAll('pre [class*="language-math"]').length ??
              -1,
            horizontalOverflow: Boolean(
              article && article.scrollWidth > article.clientWidth + 2,
            ),
            images: imageStates,
          };
        }, {
          expected: candidate.expected,
          viewportHeight: profile.viewport.height,
        });

        const brokenImages = state.images.filter(
          (image) =>
            !image.complete ||
            image.naturalWidth !== 2048 ||
            image.naturalHeight < 192 ||
            image.naturalHeight > 1536 ||
            image.density < 1.9 ||
            image.widthShare < 0.88 ||
            !image.insideArticle ||
            !image.heightSafe,
        );
        if (
          !state.articleFound ||
          state.actual !== state.expected ||
          state.mathRenderers !== 0 ||
          state.mathCodeBlocks !== 0 ||
          state.horizontalOverflow ||
          brokenImages.length
        ) {
          failures.push(
            `${candidate.path} ${profile.name}: ` +
              JSON.stringify({ ...state, images: brokenImages }),
          );
        } else {
          console.log(
            `OK: ${candidate.path} ${profile.name} loaded ` +
              `${state.actual}/${state.expected} formula PNGs with no MathJax`,
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
  console.error("ERROR: published iPad formula rendering failed");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log(
  `OK: GitHub rendered every formula image in ${candidates.length} ` +
    "changed reading note(s) across iPad portrait and landscape profiles",
);
