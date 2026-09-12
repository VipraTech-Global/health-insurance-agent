import { expect, test } from "@playwright/test";

test("profile, active pilot answer, coverage, and source range", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await page.goto("/");
  await page.getByRole("button", { name: "New here? Create an account" }).click();
  await page.getByRole("textbox", { name: "Email" }).fill(
    `e2e-${Date.now()}@example.com`,
  );
  await page.getByRole("textbox", { name: "Password" }).fill(
    "E2E-Valid-Password-42",
  );
  await page.getByRole("button", { name: "Create account" }).click();
  await page.getByRole("button", { name: "Start a conversation" }).click();

  await page.getByRole("textbox", { name: "Who needs cover?" }).fill("Me (32)");
  await page.getByRole("textbox", { name: "Location" }).fill("Bengaluru");
  await page.getByRole("textbox", { name: "Annual budget" }).fill("₹30,000 preference");
  await page.getByRole("textbox", { name: "Medical conditions" }).fill("Unknown");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(page.getByText(/Revision 2/)).toBeVisible();
  await page.getByRole("button", { name: "Confirm profile" }).click();
  await expect(page.getByText("Confirmed", { exact: true })).toBeVisible();

  await page
    .getByRole("textbox", { name: "Ask a policy question or tell me about your needs…" })
    .fill("Which policy should I buy?");
  await page.getByRole("button", { name: "Check recommendations" }).click();
  await expect(
    page.getByText(/one-plan, evidence-backed test option/i),
  ).toBeVisible();
  await expect(page.getByText(/36-month waiting period/i)).toBeVisible();
  await page.getByRole("button", { name: "Open source 1" }).first().click();
  await expect(page.getByRole("complementary", { name: "Citation source" })).toBeVisible();
  await page.getByRole("button", { name: "Close source" }).click();
  await page.reload();
  await expect(page.getByText(/36-month waiting period/i)).toBeVisible();
  await expect(page.getByRole("button", { name: "Open source 1" }).first()).toBeVisible();

  await page.getByRole("button", { name: "Coverage & review" }).click();
  await expect(page.getByText("203", { exact: true })).toBeVisible();
  await expect(
    page.getByText("Active for test").locator("..").getByText("1", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Active evidence proof")).toBeVisible();
  await page.getByRole("button", { name: "Open exact source" }).click();
  await expect(page.getByRole("complementary", { name: "Citation source" })).toBeVisible();
  const canvas = page.locator(".pdf-page canvas");
  await expect
    .poll(() => canvas.evaluate((element) => (element as HTMLCanvasElement).width))
    .toBeGreaterThan(0);
  expect(errors).toEqual([]);
});
