#!/usr/bin/env node

/**
 * Verify changed mathematical Markdown with GitHub's real client renderer.
 *
 * The GitHub Markdown API stops at <math-renderer>; unsupported safe-macro
 * failures happen later in the browser.  This check opens the public blob page
 * for each changed Markdown file containing math and requires every
 * <math-renderer> to finish as MathML, with no error banner or source fallback.
 */

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import process from "node:process";
import { chromium } from "playwright";

const root = resolve(import.meta.dirname, "..");
const repository = process.env.RENDER_REPOSITORY;
const renderSha = process.env.RENDER_SHA;
const baseSha = process.env.RENDER_BASE_SHA;

if (!repository || !renderSha) {
  console.error(
    "RENDER_REPOSITORY and RENDER_SHA are required for the published render smoke test.",
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
      "Could not resolve the event diff; checking every tracked Markdown file.",
    );
    return gitLines(["ls-files", "*.md"]);
  }
}

function mathRegionCount(markdown) {
  let regions = 0;
  let activeFence = null;

  for (const line of markdown.split(/\r?\n/)) {
    if (activeFence) {
      const stripped = line.replace(/^ {0,3}/, "");
      let closingLength = 0;
      while (stripped[closingLength] === activeFence[0]) {
        closingLength += 1;
      }
      if (
        closingLength >= activeFence.length &&
        !stripped.slice(closingLength).trim()
      ) {
        activeFence = null;
      }
      continue;
    }

    const opener = line.match(
      /^ {0,3}(?<marker>`{3,}|~{3,})[ \t]*(?<info>[\w+-]*)/,
    );
    if (opener?.groups) {
      activeFence = opener.groups.marker;
      if (opener.groups.info.toLowerCase() === "math") {
        regions += 1;
      }
      continue;
    }

    regions += line.match(/\$`[^`\n]+`\$/g)?.length ?? 0;
  }

  return regions;
}

const candidates = [...new Set(changedPaths())]
  .filter((path) => path.toLowerCase().endsWith(".md"))
  .filter((path) => existsSync(resolve(root, path)))
  .map((path) => {
    const markdown = readFileSync(resolve(root, path), "utf8");
    return { path: path.replaceAll("\\", "/"), expected: mathRegionCount(markdown) };
  })
  .filter(({ expected }) => expected > 0);

if (!candidates.length) {
  console.log("OK: no changed Markdown file contains mathematical regions");
  process.exit(0);
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({
  userAgent:
    "sensorledger3d-reading-log-math-smoke/1.0 (+https://github.com/" +
    repository +
    ")",
});
const failures = [];

try {
  for (const candidate of candidates) {
    const encodedPath = candidate.path
      .split("/")
      .map((part) => encodeURIComponent(part))
      .join("/");
    const url =
      `https://github.com/${repository}/blob/${renderSha}/${encodedPath}`;

    const response = await page.goto(url, {
      waitUntil: "domcontentloaded",
      timeout: 45_000,
    });
    if (!response || !response.ok()) {
      failures.push(
        `${candidate.path}: GitHub returned ${response?.status() ?? "no response"}`,
      );
      continue;
    }

    try {
      await page.waitForFunction(
        ({ expected }) => {
          const article = document.querySelector(
            "article.markdown-body, .markdown-body",
          );
          const renderers = [...(article?.querySelectorAll("math-renderer") ?? [])];
          return (
            renderers.length === expected &&
            renderers.every((renderer) => renderer.children.length > 0)
          );
        },
        { expected: candidate.expected },
        { timeout: 45_000 },
      );
    } catch {
      // Collect the exact DOM state below so the CI error is actionable.
    }

    const state = await page.evaluate(({ expected }) => {
      const article = document.querySelector(
        "article.markdown-body, .markdown-body",
      );
      const renderers = [...(article?.querySelectorAll("math-renderer") ?? [])];
      const broken = renderers
        .map((renderer, index) => ({
          index,
          text: (renderer.innerText || renderer.textContent || "")
            .replace(/\s+/g, " ")
            .trim()
            .slice(0, 300),
          hasMathMl: Boolean(renderer.querySelector(":scope > math")),
          hasError: Boolean(renderer.querySelector(".flash-error")),
          hasFallback: Boolean(renderer.querySelector("pre")),
        }))
        .filter(
          (item) => !item.hasMathMl || item.hasError || item.hasFallback,
        );
      return {
        articleFound: Boolean(article),
        expected,
        actual: renderers.length,
        broken,
      };
    }, { expected: candidate.expected });

    if (
      !state.articleFound ||
      state.actual !== state.expected ||
      state.broken.length
    ) {
      failures.push(`${candidate.path}: ${JSON.stringify(state)}`);
    } else {
      console.log(
        `OK: ${candidate.path} rendered ${state.actual}/${state.expected} math regions`,
      );
    }
  }
} finally {
  await browser.close();
}

if (failures.length) {
  console.error("ERROR: published GitHub math rendering failed");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log(
  `OK: GitHub rendered every formula in ${candidates.length} changed Markdown file(s)`,
);
