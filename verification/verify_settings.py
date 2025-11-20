from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Wait for Streamlit to start
        time.sleep(5)

        try:
            page.goto("http://localhost:8501")
            # Wait for content
            page.wait_for_selector("h1", timeout=10000)

            # Navigate to Settings
            page.get_by_text("Settings").click()
            time.sleep(2)

            # Check for new fields
            if page.get_by_text("Generate Access Token").is_visible():
                print("Found 'Generate Access Token' section")
            else:
                print("Did not find 'Generate Access Token' section")

            page.screenshot(path="verification/settings.png")
            print("Settings page screenshot taken.")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/settings_error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
