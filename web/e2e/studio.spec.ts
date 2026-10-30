import { test, expect } from '@playwright/test'

test.describe('Scheduled Scenes Studio E2E Smoke Suite', () => {
  test('boots without console errors and renders core components', async ({ page }) => {
    const errors: string[] = []
    page.on('pageerror', (err) => errors.push(err.message))

    await page.goto('/')

    // Verify page title / heading
    await expect(page.locator('h1, h2, h3').first()).toBeVisible()

    // Assert zero unhandled console exceptions
    expect(errors).toHaveLength(0)

    // Verify presence of room configuration elements
    await expect(page.locator('text=Real-Time Scrubbing & Room Simulator')).toBeVisible()

    // Verify time range input exists
    const timeScrubber = page.locator('input[type="range"][max="1439"]')
    await expect(timeScrubber).toBeVisible()

    // Verify YAML preview exists
    await expect(page.locator('text=Home Assistant YAML Configuration')).toBeVisible()
    await expect(page.locator('pre').first()).toBeVisible()
  })

  test('scrubbing time slider updates simulator display', async ({ page }) => {
    await page.goto('/')

    const scrubber = page.locator('input[type="range"][max="1439"]')
    await expect(scrubber).toBeVisible()

    // Read initial time
    const initialText = await page.locator('text=/\\d\\d:\\d\\d/').first().textContent()
    expect(initialText).toBeTruthy()

    // Move slider value
    await scrubber.fill('720') // 12:00
    await scrubber.dispatchEvent('input')

    // Verify time text shows 12:00
    await expect(page.locator('text=12:00').first()).toBeVisible()
  })
})
