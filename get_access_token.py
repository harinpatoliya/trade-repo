from fyers_apiv3 import fyersModel
import webbrowser

def main():
    print("--- Fyres API Access Token Generator ---")
    print("This script will help you generate an Access Token for the VR Securities App.\n")

    client_id = input("Enter your Client ID (App ID): ").strip()
    secret_key = input("Enter your Secret Key: ").strip()
    redirect_uri = input("Enter your Redirect URI (e.g., https://www.google.com): ").strip()

    if not client_id or not secret_key or not redirect_uri:
        print("Error: All fields are required.")
        return

    # Create a session model
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type='code',
        grant_type='authorization_code'
    )

    # Generate the auth code URL
    response = session.generate_authcode()

    # The response from generate_authcode() is the URL string directly (based on v3 docs)
    auth_link = response

    print("\n--- Action Required ---")
    print(f"1. Please visit the following URL to login:\n\n{auth_link}\n")
    print("2. After logging in, you will be redirected to your Redirect URI.")
    print("3. Copy the 'auth_code' from the URL (e.g., from param 'auth_code=xxxxx' or just the code itself).")

    # Option to open browser automatically
    open_browser = input("Open this link in browser now? (y/n): ").lower()
    if open_browser == 'y':
        webbrowser.open(auth_link)

    auth_code = input("\nPaste the Auth Code here: ").strip()

    if not auth_code:
        print("Error: Auth Code is required.")
        return

    # Set the auth code in the session
    session.set_token(auth_code)

    # Generate the access token
    try:
        response = session.generate_token()
        # Response is usually a dict: {'s': 'ok', 'code': 200, 'message': '...', 'access_token': '...'}

        if response.get('s') == 'ok' or 'access_token' in response:
            access_token = response['access_token']
            print("\n--- Success! ---")
            print(f"Your Access Token: {access_token}")
            print("\nCopy this Access Token and paste it into the VR Securities App Settings.")
        else:
            print("\n--- Failed ---")
            print(f"Error generating token: {response}")

    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
