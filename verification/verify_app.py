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

            # Take screenshot of Dashboard
            page.screenshot(path="verification/dashboard.png")
            print("Dashboard screenshot taken.")

            # Navigate to Trade
            # Streamlit sidebar radio logic is tricky in HTML.
            # Usually, we click on the label.
            page.get_by_text("Trade").click()
            time.sleep(2)
            page.screenshot(path="verification/trade.png")
            print("Trade page screenshot taken.")

            # Fill Trade Form and Buy
            page.get_by_label("Symbol").fill("TATASTEEL")
            page.get_by_role("button", name="Submit Order").click()
            time.sleep(2)
            page.screenshot(path="verification/after_trade.png")
            print("After trade screenshot taken.")

        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
