import subprocess
import logging

class MailSender:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def send_email(self, to_address, subject, content_html, send_immediately=False):
        """
        Sends an email using Apple Mail via AppleScript.
        
        Args:
            to_address (str): Recipient email address.
            subject (str): Subject line.
            content_html (str): The HTML content of the email body.
            send_immediately (bool): If True, sends the email. If False, saves as draft.
        """
        # Method 6: Clipboard & Paste (The "Nuclear" Option)
        # Since 'set html content' is failing, we will:
        # 1. Convert HTML to Rich Text (RTF) using macOS 'textutil'
        # 2. Put it on the Clipboard
        # 3. Simulate Cmd+V to paste it into the Mail window
        
        try:
            # Prepare the HTML file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html', encoding='utf-8') as tmp:
                tmp.write(content_html)
                tmp_path = tmp.name

            # Use textutil to convert HTML file to RTF and pipe to pbcopy
            # cmd: textutil -convert rtf /path/to/tmp.html -stdout | pbcopy
            ps = subprocess.Popen(['textutil', '-convert', 'rtf', tmp_path, '-stdout'], stdout=subprocess.PIPE)
            subprocess.check_call(['pbcopy'], stdin=ps.stdout)
            ps.wait()
            
            # Cleanup temp file
            os.remove(tmp_path)
            
        except Exception as e:
            self.logger.error(f"Clipboard preparation failed: {e}")
            return False, f"Clipboard error: {e}"

        safe_subject = subject.replace('\\', '\\\\').replace('"', '\\"')
        safe_to = to_address.replace('\\', '\\\\').replace('"', '\\"')
        
        # Determine final action
        final_action = "send outgoing message 1" if send_immediately else "save outgoing message 1"
        
        script = f'''
        tell application "Mail"
            activate
            set theMessage to make new outgoing message with properties {{visible:true}}
            tell theMessage
                set subject to "{safe_subject}"
                make new to recipient at end of to recipients with properties {{address:"{safe_to}"}}
            end tell
            delay 0.5
        end tell
        
        tell application "System Events"
            tell process "Mail"
                set frontmost to true
                keystroke "v" using command down
            end tell
        end tell
        
        delay 1
        
        tell application "Mail"
            {final_action}
        end tell
        '''
        
        try:
            # Run osascript
            result = subprocess.run(['osascript'], input=script, capture_output=True, text=True, check=True, timeout=15)
            self.logger.info(f"Mail operation successful. Output: {result.stdout.strip()}")
            return True, "Success"
        except subprocess.TimeoutExpired:
            return False, "Timeout: Mail app too slow."
        except subprocess.CalledProcessError as e:
            return False, f"AppleScript error: {e.stderr}"

