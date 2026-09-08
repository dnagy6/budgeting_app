"""
File: source/services/plaid_launcher.py
Purpose: Local loopback server to orchestrate the browser-based Plaid Link flow.
"""

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from source.services.plaid_service import PlaidService

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Connect Bank Account</title>
  <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f8fafc;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
    }
    .card {
      background: #ffffff;
      padding: 36px 40px;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.06);
      text-align: center;
      max-width: 420px;
      border: 1px solid #e2e8f0;
    }
    h2 { color: #0f172a; margin-top: 0; font-size: 20px; }
    p { color: #64748b; font-size: 14px; line-height: 1.5; }
    .btn {
      background: #2563eb;
      color: white;
      border: none;
      padding: 10px 22px;
      font-size: 14px;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      margin-top: 14px;
    }
    .btn:hover { background: #1d4ed8; }
  </style>
</head>
<body>
  <div class="card">
    <h2 id="title">Connecting to Bank...</h2>
    <p id="message">Plaid Link will open automatically. If your browser blocked the popup, click below.</p>
    <button id="open-btn" class="btn" style="display: none;">Open Bank Login</button>
  </div>

  <script>
    const linkToken = "{{LINK_TOKEN}}";
    let linkHandler = null;

    function initPlaid() {
      linkHandler = Plaid.create({
        token: linkToken,
        onSuccess: function(public_token, metadata) {
          document.getElementById('title').innerText = "Account Connected!";
          document.getElementById('message').innerText = "Exchanging tokens and syncing accounts... You may close this tab shortly.";

          fetch('/callback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              public_token: public_token,
              institution_name: metadata.institution ? metadata.institution.name : "Sandbox Bank"
            })
          })
          .then(res => res.json())
          .then(data => {
            document.getElementById('title').innerText = "Bank Sync Complete!";
            document.getElementById('message').innerText = "Successfully saved accounts. You can return to the desktop app.";
          })
          .catch(err => {
            document.getElementById('title').innerText = "Error Saving";
            document.getElementById('message').innerText = err.message;
          });
        },
        onExit: function(err, metadata) {
          if (err != null) {
            console.error("Plaid Link Exit Error:", err);
          }
          document.getElementById('title').innerText = "Link Closed";
          document.getElementById('message').innerText = "You can safely close this browser tab and return to the app.";
        }
      });

      linkHandler.open();
      document.getElementById('open-btn').style.display = 'inline-block';
      document.getElementById('open-btn').onclick = () => linkHandler.open();
    }

    window.onload = initPlaid;
  </script>
</body>
</html>
"""


class PlaidLoopbackHandler(BaseHTTPRequestHandler):
    link_token = ""
    plaid_service = None
    on_success_callback = None

    def log_message(self, format, *args):
        # Suppress noisy standard HTTP access logs in terminal
        pass

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            html_content = HTML_TEMPLATE.replace("{{LINK_TOKEN}}", self.link_token)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/callback":
            content_length = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_length)
            payload = json.loads(post_body.decode("utf-8"))

            public_token = payload.get("public_token")
            inst_name = payload.get("institution_name", "Sandbox Bank")

            # Exchange public_token for access_token
            exchange_res = self.plaid_service.exchange_public_token(public_token)
            access_token = exchange_res["access_token"]
            item_id = exchange_res["item_id"]

            # Fetch and store accounts
            acc_count = self.plaid_service.fetch_and_save_accounts(
                access_token=access_token,
                item_id=item_id,
                institution_name=inst_name
            )

            # Respond to browser
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "accounts_synced": acc_count}).encode("utf-8"))

            # Trigger callback if passed
            if self.on_success_callback:
                self.on_success_callback(item_id, acc_count)

            # Shut down server in background thread once response is dispatched
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self.send_response(404)
            self.end_headers()


def launch_plaid_link(plaid_service: PlaidService, on_success=None):
    """
    Spins up loopback server on an ephemeral free port, opens browser to Plaid Link,
    and blocks until the token is exchanged or the flow completes.
    """
    link_token = plaid_service.create_link_token()

    # Port 0 selects any open OS ephemeral port
    server = HTTPServer(("127.0.0.1", 0), PlaidLoopbackHandler)
    port = server.server_address[1]

    PlaidLoopbackHandler.link_token = link_token
    PlaidLoopbackHandler.plaid_service = plaid_service
    PlaidLoopbackHandler.on_success_callback = on_success

    url = f"http://127.0.0.1:{port}"
    print(f"[Plaid Link] Loopback server running at {url}. Opening browser...")
    webbrowser.open(url)

    # Blocks thread until shutdown() is called via /callback POST
    server.serve_forever()
    server.server_close()
    print("[Plaid Link] Loopback server closed successfully.")


if __name__ == "__main__":
    service = PlaidService()
    print("[Test] Launching Plaid Link in Sandbox mode...")
    launch_plaid_link(service)