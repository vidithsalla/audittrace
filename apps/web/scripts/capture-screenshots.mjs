import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "::1", "[::1]"]);
const DOCUMENT_TITLE = "ABA 97155 missing rationale synthetic note 001";
const ADVERSARIAL_TITLE = "Adversarial invalid evidence synthetic note 001";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "../../..");
const screenshotDir = path.join(repoRoot, "docs", "screenshots");

const baseUrl = parseLocalUrl(process.env.AUDITTRACE_BASE_URL || "http://localhost:3000", "AUDITTRACE_BASE_URL");
const apiBaseUrl = parseLocalUrl(
  process.env.AUDITTRACE_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  "AUDITTRACE_API_BASE_URL",
);

function parseLocalUrl(value, envName) {
  const url = new URL(value);
  if (!["http:", "https:"].includes(url.protocol)) {
    throw new Error(`${envName} must be http or https.`);
  }
  if (!LOCAL_HOSTS.has(url.hostname)) {
    throw new Error(`${envName} must point to localhost, 127.0.0.1, or ::1. Received: ${url.hostname}`);
  }
  return url;
}

function routeUrl(route) {
  return new URL(route, baseUrl).toString();
}

function apiUrl(route) {
  return new URL(route, apiBaseUrl).toString();
}

async function apiRequest(route, options = {}) {
  const response = await fetch(apiUrl(route), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${route} failed with ${response.status}: ${text}`);
  }
  return response.json();
}

async function getDocumentByTitle(title) {
  const payload = await apiRequest("/documents");
  const document = payload.documents.find((item) => item.title === title);
  if (!document) {
    throw new Error(`Could not find seeded document titled "${title}". Run backend seed first.`);
  }
  return document;
}

async function getQuestionSetVersionId(slug, versionName) {
  const payload = await apiRequest("/question-sets");
  const questionSet = payload.question_sets.find((item) => item.slug === slug);
  if (!questionSet) {
    throw new Error(`Could not find question set "${slug}". Run backend seed first.`);
  }
  const version = questionSet.versions.find((item) => item.version === versionName);
  if (!version) {
    throw new Error(`Could not find version "${versionName}" for question set "${slug}".`);
  }
  return version.id;
}

async function runAudit(documentId, questionSetVersionId) {
  return apiRequest("/audits/run", {
    method: "POST",
    body: JSON.stringify({
      document_id: documentId,
      question_set_version_id: questionSetVersionId,
      model_mode: "mock",
    }),
  });
}

async function runEval() {
  return apiRequest("/evals/run", {
    method: "POST",
    body: JSON.stringify({ model_mode: "mock" }),
  });
}

async function screenshot(page, route, waitFor, filename) {
  await page.goto(routeUrl(route), { waitUntil: "domcontentloaded" });
  await waitFor(page);
  await page.screenshot({
    path: path.join(screenshotDir, filename),
    fullPage: true,
    type: "png",
  });
  console.log(`Saved ${filename}`);
}

async function main() {
  await mkdir(screenshotDir, { recursive: true });

  const demoDocument = await getDocumentByTitle(DOCUMENT_TITLE);
  const adversarialDocument = await getDocumentByTitle(ADVERSARIAL_TITLE);
  const questionSetVersionId = await getQuestionSetVersionId("aba-97155", "v1");

  const evidenceAudit = await runAudit(demoDocument.id, questionSetVersionId);
  const insufficientEvidenceAudit = await runAudit(adversarialDocument.id, questionSetVersionId);
  const evalRun = await runEval();

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1100 },
  });
  const page = await context.newPage();

  try {
    await screenshot(page, "/", async (p) => {
      await p.getByRole("heading", { name: "AuditTrace" }).waitFor({ state: "visible" });
    }, "dashboard.png");

    await screenshot(page, "/documents", async (p) => {
      await p.getByRole("heading", { name: "Documents" }).waitFor({ state: "visible" });
    }, "documents.png");

    await screenshot(page, `/documents/${demoDocument.id}`, async (p) => {
      await p.getByRole("heading", { name: DOCUMENT_TITLE }).waitFor({ state: "visible" });
      await p.getByRole("button", { name: "Run mock audit" }).waitFor({ state: "visible" });
    }, "document-detail.png");

    await screenshot(page, `/audits/${evidenceAudit.audit_id}`, async (p) => {
      await p.getByText("Evidence validated").first().waitFor({ state: "visible" });
      await p.getByText("protocol_change_rationale").first().waitFor({ state: "visible" });
    }, "audit-detail-evidence.png");

    await screenshot(page, `/audits/${insufficientEvidenceAudit.audit_id}`, async (p) => {
      await p.getByText("Downgraded: insufficient evidence").first().waitFor({ state: "visible" });
      await p.getByText("Unsupported evidence caught").first().waitFor({ state: "visible" });
    }, "audit-detail-insufficient-evidence.png");

    await screenshot(page, `/evals?eval_run_id=${evalRun.eval_run_id}`, async (p) => {
      await p.getByRole("heading", { name: "Evals" }).waitFor({ state: "visible" });
      await p.getByText("Evidence span match rate").first().waitFor({ state: "visible" });
    }, "evals.png");

    await screenshot(page, "/question-sets", async (p) => {
      await p.getByRole("heading", { name: "Question Sets" }).waitFor({ state: "visible" });
      await p.getByText("Question-set version").first().waitFor({ state: "visible" });
    }, "question-sets.png");
  } finally {
    await context.close();
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
