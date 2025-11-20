# VR Securities Limited - Paper Trading App

VR Securities Limited is a paper trading application built with Python and Streamlit. It allows users to practice trading stocks, futures, and options on NSE, BSE, and MCX exchanges with a simulated account balance.

## Features

-   **Dashboard**: View current account balance, holdings, and live P&L.
-   **Trade**: Buy and sell securities using Market or Limit orders.
-   **History**: View detailed trade history and realized P&L.
-   **Settings**: Configure Fyres API credentials for live data or reset the account.
-   **Dark Mode**: Enabled by default for a comfortable viewing experience.
-   **Live/Mock Data**: Integrates with Fyres API for live prices. Falls back to mock data if no credentials are provided.

## Prerequisites

-   Python 3.8 or higher
-   Pip (Python package installer)

## Installation

1.  Clone the repository or download the source code.
2.  Navigate to the project directory.
3.  Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## How to Run

1.  Run the Streamlit application:

    ```bash
    streamlit run app.py
    ```

2.  The app will open in your default web browser (usually at `http://localhost:8501`).

## Configuration (Fyres API)

To use live market data:

1.  Go to the **Settings** tab in the application.
2.  Enter your **Client ID** (App ID) and **Access Token** from your Fyres API dashboard.
3.  Click **Save Credentials**.

If you do not have Fyres API credentials, simply leave them blank. The app will use mock data for prices.

## Resetting Account

You can reset your account balance to the initial ₹3,00,000 and clear all trades/holdings from the **Settings** tab.
