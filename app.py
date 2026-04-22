import streamlit as st
import pandas as pd
import os
import time
import subprocess
import random
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium_stealth import stealth

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="WhatsApp Bulk Sender",
    page_icon="📱",
    layout="wide"
)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def initialize_session_state():
    defaults = {
        'sent_count': 0,
        'failed_count': 0,
        'last_sent': None,
        'stop_requested': False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


import re

def clean_name(name):
    """Remove numbers and special characters from names, make Title Case."""
    # Remove digits and extra spaces, but keep letters and spaces
    cleaned = re.sub(r'[\d_]', '', str(name))
    return " ".join(cleaned.split()).title()

def validate_phone_number(phone):
    cleaned = ''.join(filter(str.isdigit, str(phone)))
    if not cleaned:
        return None
    cleaned = cleaned.lstrip('0')
    if len(cleaned) == 10:
        return f"91{cleaned}"
    return cleaned


def save_uploaded_file(uploaded_file, directory):
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def copy_image_to_clipboard(image_path: str) -> bool:
    """
    Copy an image file to the Windows clipboard using PowerShell.
    No extra Python packages needed. Returns True on success.
    """
    abs_path = os.path.abspath(image_path).replace("\\", "\\\\")
    ps_script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "Add-Type -AssemblyName System.Drawing; "
        f'$img = [System.Drawing.Image]::FromFile("{abs_path}"); '
        "[System.Windows.Forms.Clipboard]::SetImage($img); "
        "$img.Dispose()"
    )
    result = subprocess.run(
        ["powershell", "-Command", ps_script],
        capture_output=True, timeout=15
    )
    return result.returncode == 0


def js_click(driver, element):
    driver.execute_script("arguments[0].click();", element)


# ─────────────────────────────────────────────
# Selenium Initializer
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# JavaScript to remove Chrome DevTools Protocol
# leak variables (window.cdc_*) that WhatsApp
# uses to detect Selenium-controlled browsers
# ─────────────────────────────────────────────
STEALTH_JS = """
// Remove cdc_ variables injected by chromedriver
let domProps = Object.getOwnPropertyNames(window);
for (let i = 0; i < domProps.length; i++) {
    if (domProps[i].startsWith('cdc_') || domProps[i].startsWith('$cdc_')) {
        delete window[domProps[i]];
    }
}

// Override navigator.webdriver to return undefined
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// Spoof navigator.plugins to look like a real browser
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

// Spoof navigator.languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});

// Fix permissions query for notifications
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
    Promise.resolve({ state: Notification.permission }) :
    originalQuery(parameters)
);
"""

def init_selenium_driver(headless: bool):
    st.info("🚀 Starting Chrome browser...")
    opts = Options()

    user_data_dir = os.path.join(os.getcwd(), "whatsapp_session")
    opts.add_argument(f"--user-data-dir={user_data_dir}")
    opts.add_argument("--profile-directory=Default")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1400,900")
    opts.add_argument("--log-level=3")
    opts.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    opts.add_experimental_option('useAutomationExtension', False)
    opts.add_argument('--disable-blink-features=AutomationControlled')

    if headless:
        opts.add_argument("--headless=new")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)

    # ── Apply selenium-stealth (spoofs webdriver, plugins, WebGL, etc.) ──
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    # ── Inject additional stealth JS on every page load ──────────────────
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': STEALTH_JS
    })

    st.info("🌐 Opening WhatsApp Web...")
    driver.get("https://web.whatsapp.com")

    # ── Inject stealth JS immediately after page loads ───────────────────
    try:
        driver.execute_script(STEALTH_JS)
    except Exception:
        pass

    try:
        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located(
                (By.XPATH, '//canvas[@aria-label="Scan me!"] | //div[@id="pane-side"]')
            )
        )
        qr = driver.find_elements(By.XPATH, '//canvas[@aria-label="Scan me!"]')
        if qr:
            if headless:
                st.error("❌ Not logged in! Uncheck 'Headless Mode' and restart to scan QR code.")
                driver.quit()
                return None
            else:
                st.warning("📷 Scan the QR code in the browser. Waiting up to 120 seconds...")
                WebDriverWait(driver, 120).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@id="pane-side"]'))
                )
                st.success("✅ Logged in successfully!")
        else:
            st.success("✅ Already logged in!")
    except Exception:
        st.warning("⚠️ Could not verify login. Proceeding anyway...")

    time.sleep(3)
    return driver


# ─────────────────────────────────────────────
# Find Message Box — tries multiple stable XPaths
# ─────────────────────────────────────────────
MSG_BOX_XPATHS = [
    '//div[@contenteditable="true"][@data-tab="10"]',
    '//div[@title="Type a message"]',
    '//div[@aria-label="Type a message"]',
    '//div[@contenteditable="true"][@role="textbox"]',
    '//footer//div[@contenteditable="true"]',
]

def find_msg_box(driver, timeout=35):
    start_time = time.time()
    while time.time() - start_time < timeout:
        for xpath in MSG_BOX_XPATHS:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                interactable = [e for e in elements if e.is_displayed() and e.is_enabled()]
                if interactable:
                    return interactable[-1]
            except Exception:
                pass
        time.sleep(0.5)
    return None


# ─────────────────────────────────────────────
# Type multi-line text into a focused element
# ─────────────────────────────────────────────
def human_type(driver, element, text: str):
    """
    Type text character-by-character with random human-like delays.
    This prevents WhatsApp from detecting instant paste-like typing.
    """
    for char in text:
        element.send_keys(char)
        # Random delay between keystrokes: 30ms to 120ms (typical human range)
        time.sleep(random.uniform(0.03, 0.12))


def type_message(driver, element, message: str):
    # Try a few times to click in case of overlay/animation intercept
    for _ in range(5):
        try:
            element.click()
            break
        except Exception:
            time.sleep(0.4)
            
    time.sleep(random.uniform(0.3, 0.7))  # Human-like pause before typing
    lines = message.split('\n')
    for i, line in enumerate(lines):
        human_type(driver, element, line)
        if i < len(lines) - 1:
            time.sleep(random.uniform(0.1, 0.3))  # Pause before newline
            ActionChains(driver)\
                .key_down(Keys.SHIFT)\
                .send_keys(Keys.ENTER)\
                .key_up(Keys.SHIFT)\
                .perform()
            time.sleep(random.uniform(0.1, 0.3))  # Pause after newline
    time.sleep(random.uniform(0.2, 0.5))


# ─────────────────────────────────────────────
# Core Send Function
# ─────────────────────────────────────────────
def send_message_selenium(driver, phone: str, message: str,
                          image_path: str = None, log=None):
    def step(msg):
        print(f"  [{phone}] {msg}")
        if log:
            log(f"&nbsp;&nbsp;↳ {msg}")

    try:
        # ── 1. Navigate to the chat ───────────────────────────────────────
        step("Opening chat...")
        driver.get(f"https://web.whatsapp.com/send?phone={phone}")

        msg_box = find_msg_box(driver, timeout=35)
        if not msg_box:
            return False, "❌ Failed — could not open chat (check phone number)"

        step("✅ Chat loaded.")
        time.sleep(random.uniform(1.0, 2.5))  # Random pause after chat loads

        # ── 2. Send Image (clipboard paste approach) ──────────────────────
        if image_path:
            step("📋 Copying image to clipboard...")
            ok = copy_image_to_clipboard(image_path)
            if not ok:
                step("⚠️ Clipboard copy failed — skipping image.")
            else:
                # Click on the chat input area and paste the image
                msg_box.click()
                time.sleep(random.uniform(0.5, 1.2))
                ActionChains(driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
                step("📤 Pasted image. Waiting for preview...")

                # Wait for the image preview / caption box to appear
                # We look for either the caption box or the Send button in the preview
                preview_appeared = False
                CAPTION_XPATHS = [
                    '//div[@data-testid="media-caption-input"]',
                    '//div[@aria-label="Add a caption…"]',
                    '//div[@aria-label="Add a caption"]',
                    '//div[@contenteditable="true"][@data-tab="11"]',
                ]
                SEND_IN_PREVIEW_XPATHS = [
                    '//div[@aria-label="Send"]',
                    '//span[@data-icon="send"]/..',
                    '//button[@aria-label="Send"]',
                ]

                caption_box = None
                start_time = time.time()
                while time.time() - start_time < 15:
                    for cp_xpath in CAPTION_XPATHS:
                        try:
                            elements = driver.find_elements(By.XPATH, cp_xpath)
                            interactable = [e for e in elements if e.is_displayed() and e.is_enabled()]
                            if interactable:
                                caption_box = interactable[-1]
                                preview_appeared = True
                                step("✅ Preview appeared with caption box.")
                                break
                        except Exception:
                            pass
                    if preview_appeared: break
                    
                    # Alternatively, if there are MULTIPLE text boxes, the last one is the modal!
                    try:
                        elements = driver.find_elements(By.XPATH, '//div[@contenteditable="true"]')
                        interactable = [e for e in elements if e.is_displayed() and e.is_enabled()]
                        if len(interactable) >= 2:
                            caption_box = interactable[-1]
                            preview_appeared = True
                            step("✅ Preview appeared with caption box (modal detected).")
                            break
                    except Exception:
                        pass
                    if preview_appeared: break

                    for sp_xpath in SEND_IN_PREVIEW_XPATHS:
                        try:
                            elements = driver.find_elements(By.XPATH, sp_xpath)
                            if [e for e in elements if e.is_displayed()]:
                                preview_appeared = True
                                step("✅ Preview appeared (send button visible).")
                                break
                        except Exception:
                            pass
                    if preview_appeared: break
                    time.sleep(0.5)

                if not preview_appeared:
                    step("⚠️ Image preview did not appear — will send text only.")
                else:
                    # Type caption if caption box is available
                    if caption_box:
                        step("✏️ Typing caption...")
                        type_message(driver, caption_box, message)
                        time.sleep(0.5)

                    # Click Send in the preview
                    sent_img = False
                    start_time = time.time()
                    while time.time() - start_time < 8:
                        for sp_xpath in SEND_IN_PREVIEW_XPATHS:
                            try:
                                elements = driver.find_elements(By.XPATH, sp_xpath)
                                clickable = [e for e in elements if e.is_displayed() and e.is_enabled()]
                                if clickable:
                                    js_click(driver, clickable[-1])
                                    sent_img = True
                                    step("✅ Image sent from preview.")
                                    break
                            except Exception:
                                pass
                        if sent_img: break
                        time.sleep(0.5)

                    if not sent_img:
                        # Fallback: press Enter
                        ActionChains(driver).send_keys(Keys.ENTER).perform()
                        step("✅ Sent via Enter key.")

                    time.sleep(1.5)

                    # If caption was already typed above, we're done
                    if caption_box:
                        return True, "✅ Success (image + caption)"

                    # If no caption box existed, send text as a separate message
                    step("Sending text as follow-up message...")
                    msg_box = find_msg_box(driver, timeout=10)
                    if msg_box:
                        type_message(driver, msg_box, message)
                        msg_box.send_keys(Keys.ENTER)
                        time.sleep(1)
                        step("✅ Text sent.")
                    return True, "✅ Success (image + text)"

        # ── 3. Text-only message ──────────────────────────────────────────
        step("✏️ Typing text message...")
        msg_box = find_msg_box(driver, timeout=10)
        if not msg_box:
            return False, "❌ Failed — lost message box after image send"

        type_message(driver, msg_box, message)
        time.sleep(random.uniform(0.4, 1.0))
        msg_box.send_keys(Keys.ENTER)
        time.sleep(random.uniform(0.8, 1.5))
        step("✅ Text message sent.")
        return True, "✅ Success"

    except Exception as e:
        err = str(e).split('\n')[0][:100]
        step(f"❌ Exception: {err}")
        return False, f"❌ Failed — {err}"


# ─────────────────────────────────────────────
# Streamlit UI
# ─────────────────────────────────────────────
def main():
    initialize_session_state()

    st.title("📱 WhatsApp Bulk Message Sender")
    st.markdown("Send personalised messages with optional images — smoothly and silently.")

    with st.sidebar:
        st.header("⚙️ Configuration")

        headless_mode = st.checkbox(
            "Run in Headless Mode (Invisible)",
            value=False,
            help="Keep UNCHECKED on first run so you can scan the WhatsApp QR code."
        )
        
        group_contacts = st.checkbox(
            "Merge Same Numbers",
            value=True,
            help="If multiple contacts have the same phone number, combine their names and send ONE message to that number."
        )
        
        show_debug = st.checkbox("Show debug steps", value=True)

        uploaded_file = st.file_uploader(
            "📂 Contacts File (Excel / CSV)",
            type=["xlsx", "csv"],
            help="Must have 'Name' and 'Phone' columns."
        )

        message_type = st.radio("Message Type", ["Text Only", "Text with Image"])
        uploaded_image = None
        if message_type == "Text with Image":
            uploaded_image = st.file_uploader(
                "🖼️ Upload Image",
                type=["jpg", "jpeg", "png"],
            )

        message_template = st.text_area(
            "📝 Message Template",
            "Hello {{Name}},\n\nThis is a test message.\n\nBest regards,\nTeam",
            height=160,
            help="Use {{Name}} for personalisation."
        )

        delay = st.slider("⏱️ Delay between messages (s)", 15, 60, 20,
                          help="Min 15s recommended. WhatsApp flags accounts that send too fast.")

        st.markdown("---")
        if st.button("🛑 Stop After Current", type="secondary"):
            st.session_state.stop_requested = True
            st.warning("Stop requested.")

    if not uploaded_file:
        st.info("📌 Upload a contacts file in the sidebar to begin.")
        return

    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') \
             else pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Could not read file: {e}")
        return

    if not {'Name', 'Phone'}.issubset(df.columns):
        st.error(f"File must have 'Name' and 'Phone' columns. Found: {list(df.columns)}")
        return

    df['Phone'] = df['Phone'].astype(str)

    st.subheader("👥 Contact Preview")
    st.dataframe(df.head(10), use_container_width=True)
    st.caption(f"Total contacts: **{len(df)}**")

    image_path = None
    if uploaded_image:
        image_path = save_uploaded_file(uploaded_image, "temp_images")
        st.image(image_path, caption="Image to be sent", width=220)

    if st.button("🚀 Start Sending Messages", type="primary"):
        st.session_state.update({'stop_requested': False, 'sent_count': 0, 'failed_count': 0})

        progress_bar = st.progress(0)
        status_text = st.empty()
        log_area = st.container()
        results = []
        total = len(df)
        
        # ── Pre-process Data ─────────────────────────
        df['ValidatedPhone'] = df['Phone'].apply(validate_phone_number)
        df['CleanedName'] = df['Name'].apply(clean_name)
        
        invalid_mask = df['ValidatedPhone'].isna()
        invalid_df = df[invalid_mask]
        
        # Log invalid ones immediately
        for _, r in invalid_df.iterrows():
            results.append((str(r['Name']), "⚠️ Invalid phone number"))
            st.session_state.failed_count += 1
            
        valid_df = df[~invalid_mask]
        
        if group_contacts:
            # Group names by phone and remove duplicates
            def unique_names(names_series):
                seen = set()
                # Use CleanedName to determine duplicates (ignoring case differences)
                return [x for x in names_series if not (x in seen or seen.add(x))]
            
            process_df = valid_df.groupby('ValidatedPhone', as_index=False).agg({'CleanedName': unique_names})
        else:
            # Send individually
            process_df = valid_df.copy()
            # Wrap in list so the processing logic below is identical
            process_df['CleanedName'] = process_df['CleanedName'].apply(lambda x: [x])
        
        total_messages = len(process_df) + len(invalid_df)
        current_progress = len(invalid_df)
        if total_messages > 0 and len(invalid_df) > 0:
            progress_bar.progress(current_progress / total_messages)

        driver = init_selenium_driver(headless=headless_mode)
        if not driver:
            return

        def debug_log(msg):
            if show_debug:
                log_area.markdown(msg, unsafe_allow_html=True)

        try:
            for idx, row in process_df.iterrows():
                if st.session_state.stop_requested:
                    status_text.warning("🛑 Stopped by user.")
                    break

                phone = row['ValidatedPhone'] if group_contacts else row['ValidatedPhone']
                names_list = row['CleanedName']
                
                # Join names: "A" or "A & B" or "A, B & C"
                if len(names_list) == 1:
                    combined_name = names_list[0]
                elif len(names_list) == 2:
                    combined_name = f"{names_list[0]} & {names_list[1]}"
                else:
                    combined_name = ", ".join(names_list[:-1]) + f" & {names_list[-1]}"

                msg = message_template.replace("{{Name}}", combined_name)
                status_text.info(f"📨 Sending {idx+1}/{len(process_df)} — **{combined_name}** (`{phone}`)")
                
                if show_debug:
                    log_area.markdown(f"**→ {combined_name}** (`{phone}`)")

                success, status_msg = send_message_selenium(
                    driver, phone, msg, image_path,
                    log=debug_log if show_debug else None
                )

                results.append((combined_name, status_msg))
                if success:
                    st.session_state.sent_count += 1
                else:
                    st.session_state.failed_count += 1

                current_progress += 1
                progress_bar.progress(current_progress / total_messages)
                st.session_state.last_sent = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if idx < len(process_df) - 1 and not st.session_state.stop_requested:
                    human_delay = delay + random.uniform(1.0, 4.0)
                    time.sleep(human_delay)

        finally:
            driver.quit()
            st.info("🔒 Browser closed.")

        st.success("✅ All done!")
        results_df = pd.DataFrame(results, columns=["Name", "Status"])
        st.dataframe(results_df, use_container_width=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Contacts", total)
        c2.metric("Messages Built", total_messages)
        c3.metric("Sent ✅", st.session_state.sent_count)
        c4.metric("Failed ❌", st.session_state.failed_count)

        st.download_button(
            "⬇️ Download Results CSV",
            data=results_df.to_csv(index=False),
            file_name="send_results.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()
