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
            page.wait_for_selector("h1", timeout=10000)

            # 1. Check Auto-Redirect on Save
            # We are on Log in page by default.
            # Enter some dummy creds
            page.get_by_label("Client ID (App ID)").fill("TEST_CLIENT_ID")
            page.get_by_label("Access Token").fill("TEST_TOKEN")

            # Click Save
            print("Clicking Save Credentials...")
            page.get_by_role("button", name="Save Credentials").click()
            time.sleep(2) # Wait for rerun/redirect

            # Verify we are on Dashboard
            # Dashboard has "Available Balance" metric
            if page.get_by_text("Available Balance").is_visible():
                print("Redirected to Dashboard successfully.")
            else:
                print("Failed to redirect to Dashboard.")

            page.screenshot(path="verification/after_save_redirect.png")

            # 2. Check Light Mode Visibility
            # Toggle Dark Mode OFF
            dark_mode_text = page.get_by_text("Dark Mode")
            if dark_mode_text.count() > 0:
                 dark_mode_text.first.click()
                 time.sleep(1)
                 print("Toggled to Light Mode")

                 # Take screenshot to manually verify text contrast
                 page.screenshot(path="verification/light_mode_check.png")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error_redirect.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
