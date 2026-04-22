# WhatsApp Bulk Sender

A robust, web-based WhatsApp bulk messaging automation tool built with Streamlit and Selenium. 

Designed to mimic human behavior to reduce ban rates, this tool allows you to send personalized text and image messages in bulk with advanced features like contact grouping and stealth mode.

## 🚀 Features

* **Anti-Ban Stealth Mode**: Uses `selenium-stealth` and removes `cdc_` variables to evade WhatsApp's bot detection tools.
* **Human-like Behavior**: Types messages with human-like keystroke delays and randomizes wait times between messages.
* **Image & Text Delivery**: Sends texts and images together reliably. Uses Windows Clipboard via PowerShell to paste images smoothly, bypassing dynamic and easily broken DOM interactions.
* **Smart Contact Grouping**: If multiple names belong to the same phone number, it groups them in a single message (e.g., "Hello Ram & Shyam") to minimize message volume and avoid rate-limiting.
* **Clean UI**: User-friendly Streamlit interface with live progress tracking, debug logs, and real-time status updates.
* **Session Persistence**: Saves your WhatsApp login session so you don't need to scan the QR code every time.

## 🛠️ Requirements

* Python 3.8+
* Google Chrome installed on your system
* Windows OS (Required for the PowerShell clipboard image functioning)

## 📦 Installation

1. Clone this repository (or download the source):
   ```bash
   git clone <your-repo-url>
   cd WhatsappBulk
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install streamlit pandas selenium webdriver-manager selenium-stealth pywhatkit pyautogui openpyxl
   ```
   *(Note: `pywhatkit` and `pyautogui` are used in the alternative `app1.py` implementation if needed.)*

## 🚄 Usage

1. Start the Streamlit application:
   ```bash
   streamlit run app.py
   or
   python -m streamlit run app.py
   ``` 
   Use python -m streamlit run app.py if you get error "streamlit is not recognized as an internal or external command, operable program or batch file"  

2. Access the Web UI provided in your terminal (usually `http://localhost:8501`).

3. **In the Web UI**:
   * Upload an Excel (`.xlsx`) or CSV (`.csv`) file containing your contacts. It **must** have `Name` and `Phone` columns.
   * Customize your message template (use `{{Name}}` for personalization).
   * Optionally upload an image.
   * Adjust the delay interval (recommend 15+ seconds to prevent account flags).
   * Click **Start Sending Messages**!

## ⚠️ Important Anti-Ban Tips

* **Don't use your primary personal number** for bulk sending if possible.
* Use a **Mobile Hotspot** instead of home WiFi if you get flagged; changing IPs helps reset reputation.
* Warm up fresh WhatsApp accounts manually before using automated bulk senders.
* Maintain a minimum 15-20 second gap between each message. 

## 📁 Project Structure

* `app.py`: Main application utilizing advanced Selenium stealth and Chrome bindings.
* `app1.py`: Alternative implementation using `pywhatkit`.
* `.gitignore`: Pre-configured to track only essential files and keep cache, sessions, and uploads out of Git.

## 📄 License

This project is made for educational and utility purposes. Use responsibly according to WhatsApp's Terms of Service.
