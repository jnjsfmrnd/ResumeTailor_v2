import { expect, test } from "@playwright/test";

test.describe("generation actions", () => {
  test("shows upload, job target, and generation controls on one page", async ({ page }) => {
    await page.setContent(`
      <main>
        <form data-upload-form>
          <label for="resume-file">Resume file</label>
          <input id="resume-file" type="file" name="file" />
        </form>

        <form data-job-target-form>
          <label for="description-text">Job description</label>
          <textarea id="description-text" name="descriptionText"></textarea>
        </form>

        <section data-export-panel>
          <button data-start-tailoring>Generate Tailored Draft</button>
          <button data-generate-resume disabled>Generate Resume PDF</button>
          <button data-generate-cover-letter disabled>Generate Cover Letter</button>
        </section>
      </main>
    `);

    await expect(page.locator("[data-upload-form]")).toBeVisible();
    await expect(page.locator("[data-job-target-form]")).toBeVisible();
    await expect(page.getByRole("button", { name: "Generate Tailored Draft" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Generate Resume PDF" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Generate Cover Letter" })).toBeDisabled();
  });

  test("blocks all generation buttons and shows loading during async run", async ({ page }) => {
    await page.setContent(`
      <section>
        <button data-start-tailoring>Generate Tailored Draft</button>
        <button data-generate-resume disabled>Generate Resume PDF</button>
        <button data-generate-cover-letter disabled>Generate Cover Letter</button>
        <div data-loading-disc hidden>Working...</div>
        <script>
          const buttons = Array.from(document.querySelectorAll('button'));
          const loadingDisc = document.querySelector('[data-loading-disc]');
          document.querySelector('[data-start-tailoring]').addEventListener('click', async () => {
            buttons.forEach((btn) => { btn.disabled = true; });
            loadingDisc.hidden = false;
            await Promise.resolve();
            loadingDisc.hidden = true;
            document.querySelector('[data-generate-resume]').disabled = false;
            document.querySelector('[data-generate-cover-letter]').disabled = false;
          });
        </script>
      </section>
    `);

    await page.getByRole("button", { name: "Generate Tailored Draft" }).click();

    await expect(page.locator("[data-loading-disc]")).toBeHidden();
    await expect(page.getByRole("button", { name: "Generate Resume PDF" })).toBeEnabled();
    await expect(page.getByRole("button", { name: "Generate Cover Letter" })).toBeEnabled();
  });
});
