import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/playwright',
  snapshotDir: './tests/playwright/snapshots',
  outputDir: './tests/playwright-results',
  reporter: [['list'], ['html', { open: 'never', outputFolder: 'tests/playwright-report' }]],
  use: {
    baseURL: 'http://localhost:3000',
    screenshot: 'only-on-failure',
    headless: true,
  },
  webServer: {
    command: 'npx vite --port 3000',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
