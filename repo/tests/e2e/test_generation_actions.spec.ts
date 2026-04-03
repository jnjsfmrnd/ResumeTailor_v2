import { expect, test } from "@playwright/test";

test.describe("generation actions", () => {
  test("shows separate resume and cover-letter actions", async ({ page }) => {
    await page.setContent(`
      <section data-export-panel>
        <button data-generate-resume>Generate resume PDF</button>
        <button data-generate-cover-letter>Generate cover letter</button>
      </section>
    `);

    await expect(page.getByRole("button", { name: "Generate resume PDF" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Generate cover letter" })).toBeVisible();
  });

  test("keeps actions independent", async ({ page }) => {
    await page.setContent(`
      <section>
        <button data-generate-resume>Generate resume PDF</button>
        <button data-generate-cover-letter>Generate cover letter</button>
        <output data-last-action></output>
        <script>
          const output = document.querySelector('[data-last-action]');
          document.querySelector('[data-generate-resume]').addEventListener('click', () => {
            output.textContent = 'resume';
          });
          document.querySelector('[data-generate-cover-letter]').addEventListener('click', () => {
            output.textContent = 'cover-letter';
          });
        </script>
      </section>
    `);

    await page.getByRole("button", { name: "Generate resume PDF" }).click();
    await expect(page.locator("[data-last-action]")).toHaveText("resume");

    await page.getByRole("button", { name: "Generate cover letter" }).click();
    await expect(page.locator("[data-last-action]")).toHaveText("cover-letter");
  });
});
