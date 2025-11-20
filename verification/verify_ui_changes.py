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

            # 1. Check Default Page is "Log in"
            if page.get_by_role("heading", name="Log in / Settings").is_visible():
                print("Default page is Log in.")
            else:
                print("Default page is NOT Log in.")

            page.screenshot(path="verification/login_default.png")

            # 2. Check Theme Toggle (Light Mode)
            # St.sidebar.toggle creates a label and a checkbox.
            # Sometimes get_by_label works, sometimes we need to be more specific.
            # Streamlit toggles are inside a label with the text.
            # Try finding the text "Dark Mode" in the sidebar.

            # Expand sidebar if collapsed (though expanded by default in config)

            dark_mode_text = page.get_by_text("Dark Mode")
            if dark_mode_text.count() > 0:
                 # Click the checkbox associated with it.
                 # In streamlit, the checkbox input is usually a sibling or child.
                 # Let's try clicking the label itself which toggles it.
                 dark_mode_text.first.click()
                 time.sleep(1)
                 print("Clicked Dark Mode Toggle")
                 page.screenshot(path="verification/light_mode.png")
            else:
                 print("Dark Mode text not found")

            # 3. Navigate to Dashboard
            # Sidebar radio "Dashboard"
            # Click the label "Dashboard" in the sidebar
            page.locator("label").filter(has_text="Dashboard").click()
            time.sleep(2)

            # Create a trade to populate dashboard
            page.locator("label").filter(has_text="Trade").click()
            time.sleep(1)

            # Fill Symbol
            page.get_by_label("Symbol").fill("INFY")
            # Click Submit
            page.get_by_role("button", name="Submit Order").click()
            time.sleep(2)

            # Return to Dashboard
            page.locator("label").filter(has_text="Dashboard").click()
            time.sleep(2)

            page.screenshot(path="verification/dashboard_new_layout.png")
            print("Dashboard screenshot taken")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error_ui.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
