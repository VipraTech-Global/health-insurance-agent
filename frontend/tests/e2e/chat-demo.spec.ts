import { expect, test, type Page } from "@playwright/test";

const assistant = (page: Page) => page.locator(".msg.assistant");

async function say(page: Page, text: string) {
  const before = await assistant(page).count();
  const box = page.getByRole("textbox", { name: "Message CoverGuide" });
  await box.fill(text);
  await box.press("Enter");
  await expect(assistant(page)).toHaveCount(before + 1, { timeout: 120_000 });
  await expect(page.locator(".typing")).toHaveCount(0, { timeout: 120_000 });
}

async function openAndCloseSource(page: Page, scope: ReturnType<Page["locator"]>) {
  await scope.locator(".source-link").first().click();
  const panel = page.getByRole("complementary", { name: "Citation source" });
  await expect(panel).toBeVisible();
  await expect
    .poll(() => page.locator(".pdf-page canvas").evaluate((element) => (element as HTMLCanvasElement).width), { timeout: 60_000 })
    .toBeGreaterThan(0);
  await expect(page.locator(".citation-highlight").first()).toBeVisible();
  await page.getByRole("button", { name: "Close source" }).click();
  await expect(panel).toBeHidden();
}

// Needs the live demo stack (relay, demo_live worker); a full run takes several minutes.
test("a guided chat ends in cited comparison tables that survive a reload", async ({ page }) => {
  test.setTimeout(720_000);
  const errors: string[] = [];
  page.on("console", (message) => { if (message.type() === "error") errors.push(message.text()); });

  await page.goto("/demo");
  await page.getByRole("button", { name: "New here? Create an account" }).click();
  await page.getByRole("textbox", { name: "Email" }).fill(`chat-${Date.now()}@example.com`);
  await page.getByRole("textbox", { name: "Password" }).fill("Demo-Valid-Password-42");
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await expect(assistant(page).first()).toBeVisible({ timeout: 30_000 });

  await say(page, "Cover for me (35), my wife (33) and our son (8) in Pune. 10 lakh sum insured, budget 60,000 a year, hospital expense indemnity on a family floater. Skip the health details.");
  await say(page, "Maternity is a must-have. Room rent limits are nice to have.");
  for (let turn = 0; turn < 8 && !(await page.locator(".msg.assistant table").count()); turn += 1) await say(page, "Skip");
  const shortlist = page.locator(".msg.assistant table").first();
  await expect(shortlist).toBeVisible();
  // No fit labels or exclusion reasons unless the customer asks.
  await expect(page.locator(".transcript")).not.toContainText(/doesn.t fit|can.t tell/i);

  await say(page, "What are the waiting periods for pre-existing diseases?");
  const answer = assistant(page).last().locator(".answer-lines").first();
  await expect(answer).toBeVisible({ timeout: 600_000 });
  await expect(page.getByRole("button", { name: "Stop answering" })).toBeHidden({ timeout: 600_000 });
  await openAndCloseSource(page, assistant(page).last());

  await page.reload();
  await expect(page.locator(".answer-lines").first()).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: "New chat" }).click();
  await page.locator(".history li button").first().click();
  await expect(page.locator(".answer-lines").first()).toBeVisible({ timeout: 30_000 });
  expect(errors).toEqual([]);
});

// Fast check against a conversation that already has tables: E2E_EMAIL, E2E_PASSWORD, E2E_CONVERSATION.
test("a saved conversation reopens with its tables and sources", async ({ page }) => {
  const { E2E_EMAIL: email, E2E_PASSWORD: password, E2E_CONVERSATION: id } = process.env;
  test.skip(!email || !password || !id, "Set E2E_EMAIL, E2E_PASSWORD and E2E_CONVERSATION");
  test.setTimeout(120_000);
  await page.goto("/demo");
  await page.getByRole("textbox", { name: "Email" }).fill(email!);
  await page.getByRole("textbox", { name: "Password" }).fill(password!);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("textbox", { name: "Message CoverGuide" })).toBeVisible();
  await page.goto(`/demo?conversation=${id}`);
  const tables = page.locator(".msg.assistant .table-wrap");
  await expect(tables.first()).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Conversations" }).locator("[aria-current=page]")).toBeVisible();

  await openAndCloseSource(page, tables.first());
  await expect(page.locator(".sidebar")).not.toHaveClass(/collapsed/);

  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole("button", { name: "Show conversations" }).click();
  await expect(page.locator(".drawer-open")).toBeVisible();
});
