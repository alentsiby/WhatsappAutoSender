import streamlit as st
import pandas as pd
import os
import time
import pywhatkit
from datetime import datetime
import base64
import pyautogui  # For closing browser tab

# Configure Streamlit page
st.set_page_config(
    page_title="WhatsApp Bulk Sender",
    page_icon="📱",
    layout="wide"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'sent_count' not in st.session_state:
        st.session_state.sent_count = 0
    if 'failed_count' not in st.session_state:
        st.session_state.failed_count = 0
    if 'last_sent' not in st.session_state:
        st.session_state.last_sent = None

def validate_phone_number(phone):
    """Validate and format phone number"""
    cleaned = ''.join(filter(str.isdigit, str(phone)))
    if not cleaned:
        return None
    return f"+91{cleaned[-10:]}" if len(cleaned) == 10 else f"+{cleaned}"

def save_uploaded_file(uploaded_file, directory):
    """Save uploaded file to directory and return path"""
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def send_message(phone, message, image_path=None):
    """Send WhatsApp message with error handling and close tab after sending"""
    try:
        if image_path:
            pywhatkit.sendwhats_image(
                receiver=phone,
                img_path=image_path,
                caption=message,
                wait_time=18,
                tab_close=False  # We'll close manually
            )
        else:
            pywhatkit.sendwhatmsg_instantly(
                phone_no=phone,
                message=message,
                wait_time=18,
                tab_close=False
            )

        # Wait enough time for message to be sent
        time.sleep(11)  # Increase if internet is slow or image is large

        # Close the active tab
        pyautogui.hotkey('ctrl', 'w')
        time.sleep(5)  # Small wait to stabilize

        return True
    except Exception as e:
        st.error(f"Error sending to {phone}: {str(e)}")
        return False

def main():
    initialize_session_state()
    
    st.title("📱 WhatsApp Bulk Message Sender")
    st.markdown("Send personalized messages with images to multiple contacts")
    
    # Sidebar controls
    with st.sidebar:
        st.header("Configuration")
        uploaded_file = st.file_uploader(
            "Upload Contacts (Excel/CSV)",
            type=["xlsx", "csv"],
            help="File should contain 'Name' and 'Phone' columns"
        )
        
        message_type = st.radio(
            "Message Type",
            ["Text Only", "Text with Image"]
        )
        
        if message_type == "Text with Image":
            uploaded_image = st.file_uploader(
                "Upload Image",
                type=["jpg", "jpeg", "png"],
                help="Image to include with message"
            )
        else:
            uploaded_image = None
            
        message_template = st.text_area(
            "Message Template",
            "Hello {{Name}},\n\nThis is a test message.\n\nBest regards,\nTeam",
            height=150
        )
        
        delay = st.slider(
            "Delay between messages (seconds)",
            min_value=5,
            max_value=60,
            value=15,
            help="Recommended: 15-30 seconds to avoid rate limiting"
        )
        
        st.markdown("---")
        st.markdown("**Instructions:**")
        st.markdown("1. Keep WhatsApp Web open in Chrome")
        st.markdown("2. Don't close the browser tab manually")
        st.markdown("3. Don't use for spam!")

    # Main content area
    if uploaded_file:
        try:
            # Read contact data
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
                
            # Validate columns
            if not all(col in df.columns for col in ['Name', 'Phone']):
                st.error("Required columns 'Name' and 'Phone' not found")
                return
                
            # Preview data
            st.subheader("Contact Preview")
            st.dataframe(df.head())
            
            # Save image if uploaded
            image_path = None
            if uploaded_image:
                image_path = save_uploaded_file(uploaded_image, "temp_images")
                st.image(image_path, caption="Image to be sent", width=200)
                
            # Start sending process
            if st.button("Start Sending Messages", type="primary"):
                progress_bar = st.progress(0)
                status_text = st.empty()
                results = []
                
                total_contacts = len(df)
                for idx, row in df.iterrows():
                    # Format phone number
                    phone = validate_phone_number(row['Phone'])
                    if not phone:
                        results.append((row['Name'], "Invalid phone number"))
                        continue
                        
                    # Personalize message
                    message = message_template.replace("{{Name}}", str(row['Name']))
                    
                    # Send message
                    status_text.text(f"Sending to {row['Name']} ({idx+1}/{total_contacts})")
                    success = send_message(phone, message, image_path)
                    
                    # Record result
                    if success:
                        results.append((row['Name'], "✅ Success"))
                        st.session_state.sent_count += 1
                    else:
                        results.append((row['Name'], "❌ Failed"))
                        st.session_state.failed_count += 1
                    
                    # Update progress
                    progress_bar.progress((idx + 1) / total_contacts)
                    st.session_state.last_sent = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Delay between messages
                    if idx < total_contacts - 1:
                        time.sleep(delay)
                
                # Show results
                st.success("Sending completed!")
                results_df = pd.DataFrame(results, columns=["Name", "Status"])
                st.dataframe(results_df)
                
                # Statistics
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Contacts", total_contacts)
                col2.metric("Successfully Sent", st.session_state.sent_count)
                col3.metric("Failed", st.session_state.failed_count)
                
                # Download results
                csv = results_df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="send_results.csv">Download Results</a>'
                st.markdown(href, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            
    else:
        st.info("Please upload a contacts file to begin")

if __name__ == "__main__":
    main()