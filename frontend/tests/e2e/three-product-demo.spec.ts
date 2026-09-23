import { expect, test } from "@playwright/test";

test("three-product demo streams an evidence-cited comparison", async ({ page }) => {
  test.setTimeout(720_000);
  const consoleErrors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });

  await page.goto("/");
  await page.getByRole("button", { name: "New here? Create an account" }).click();
  await page.getByRole("textbox", { name: "Email" }).fill(`demo-${Date.now()}@example.com`);
  await page.getByRole("textbox", { name: "Password" }).fill("Demo-Valid-Password-42");
  await page.getByRole("button", { name: "Create account", exact: true }).click();

  await expect(page.getByRole("status")).toContainText("3 of 5 planned products");
  await page.getByRole("button", { name: "Knowledge readiness" }).click();
  await expect(page.getByText("Development demo: 3 of 5 products available.")).toBeVisible();
  await expect(page.getByText("included in demo", { exact: true })).toHaveCount(3);

  await page.getByRole("button", { name: "＋ New conversation" }).click();
  await expect(page.getByText("3 products ready", { exact: true })).toBeVisible();
  await page.getByRole("textbox", { name: "Message CoverGuide" }).fill(
    "I am 32, live in Bengaluru, and buying this cover just for myself. My sum insured target " +
      "is about ten lakh rupees and my premium budget is about fifteen thousand rupees a year. " +
      "Compare the three available products, keep unsupported areas explicitly unknown, and " +
      "cite the policy evidence.",
  );
  await page.getByRole("button", { name: "Send →" }).click();
  await expect(page.locator(".processing")).toBeVisible({ timeout: 30_000 });
  const comparison = page.locator(".comparison-detail");
  const errorBanner = page.locator(".error-banner");
  for (let attempt = 0; attempt <= 2; attempt += 1) {
    await expect(page.locator(".comparison-detail, .error-banner")).toBeVisible({
      timeout: 220_000,
    });
    if (await comparison.isVisible()) break;
    await expect(errorBanner).toContainText("stopped safely");
    if (attempt === 2) break;
    const retry = page.getByRole("button", { name: "Retry safely" });
    await expect(retry).toBeVisible();
    await retry.click();
    await expect(errorBanner).toBeHidden();
    await expect(page.locator(".processing")).toBeVisible({ timeout: 30_000 });
  }
  await expect(comparison).toBeVisible();
  await expect(page.locator(".compared-product")).toHaveCount(3);
  await expect(page.locator(".comparison-framing")).toHaveText(
    "CoverGuide compares the reviewed products against the criteria you shared. It does not choose a policy; the decision is yours.",
  );
  await expect(page.locator(".comparison-statements")).toContainText(
    "not confirmed whether you already hold health insurance",
  );
  await expect(comparison).not.toContainText(/#\d|winner|top pick|recommended/i);

  // A product's matched amount, when the deterministic rule engine resolved one,
  // renders beside its outcome — never a "Not specified" placeholder for a null match.
  const sumInsuredMatch = page.locator(".criterion-row:has-text(\"sum insured\")").first();
  if (await sumInsuredMatch.count()) {
    await expect(sumInsuredMatch).not.toContainText("Not specified");
  }

  const citation = page.locator(".citation-button").first();
  await expect(citation).toBeVisible();
  await citation.click();
  await expect(page.getByRole("complementary", { name: "Citation source" })).toBeVisible();
  await expect
    .poll(() => page.locator(".pdf-page canvas").evaluate(
      (element) => (element as HTMLCanvasElement).width,
    ))
    .toBeGreaterThan(0);

  await page.getByRole("button", { name: "Close source" }).click();
  await page.getByRole("textbox", { name: "Message CoverGuide" }).fill(
    "Please check the same comparison again with the latest profile.",
  );
  await page.getByRole("button", { name: "Send →" }).click();
  await expect(page.locator(".processing")).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: "＋ New conversation" }).click();
  await expect(page.getByRole("button", { name: "Send →" })).toBeEnabled();
  await expect(page.locator(".processing")).toBeHidden();
  expect(consoleErrors).toEqual([]);
});
