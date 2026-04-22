# WhatsApp Bulk Sender

A robust, web-based WhatsApp bulk messaging automation tool built with Streamlit and Selenium. 

Designed to mimic human behavior to reduce ban rates, this tool allows you to send personalized text and image messages in bulk with advanced features like contact grouping and stealth mode.

## 🚀 Features

* **Anti-Ban Stealth Mode**: Uses `selenium-stealth` and dynamically removes Chrome DevTools Protocol (`cdc_`) variables to evade WhatsApp's sophisticated bot detection tools.
* **Human-like Behavior**: Simulates real user interactions by typing character-by-character with randomized keystroke delays (30ms-120ms) and naturally varied wait times between messages.
* **Image & Text Delivery**: Sends text and images together reliably. Bypasses fragile DOM interactions by using native Windows PowerShell capabilities to paste images directly via the clipboard.
* **Smart Contact Grouping**: Automatically merges contacts with identical phone numbers (e.g., combining names into "Hello Ram & Shyam") to minimize message volume, prevent rate-limiting, and avoid spamming the same recipient.
* **Intelligent Data Cleaning**: Automatically formats and sanitizes imported phone numbers (e.g., adding country codes appropriately) and cleans up names by stripping arbitrary numbers or special characters.
* **Clean UI & Real-time Analytics**: Built with Streamlit, providing a premium, user-friendly interface with live progress tracking, debug logs, success/fail metrics, and downloadable result reports in CSV format.
* **Session Persistence**: Securely saves your WhatsApp Web login session locally (`whatsapp_session`), meaning you only need to scan the QR code once across multiple app launches.
* **No-Trace Privacy**: Ensures zero evidence is left on disk by automatically purging all temporarily uploaded images after the messaging campaign finishes.

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
