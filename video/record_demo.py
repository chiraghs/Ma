import os
import time
from playwright.sync_api import sync_playwright

def record_hackathon_demo():
    output_dir = "/Volumes/DiskD/Devpost/Ma/video/raw_recordings"
    os.makedirs(output_dir, exist_ok=True)
    
    # Remove any existing recordings
    for f in os.listdir(output_dir):
        if f.endswith(".webm") or f.endswith(".mp4"):
            try:
                os.remove(os.path.join(output_dir, f))
            except Exception:
                pass

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-web-security"]
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=output_dir,
            record_video_size={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        print("[0:00] Navigating to Echo Show 10 Simulator on port 8001...")
        page.goto("http://127.0.0.1:8001/")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)

        # =====================================================================
        # PART 1: (0:00 - 0:28.75 ~ 28.75s) - Introduction & Echo Show 10 Hardware
        # =====================================================================
        print("[Part 1] Presenting Echo Show 10 Glacier White display & ambient nursery...")
        try:
            page.hover("#swasthTopBar", force=True)
        except Exception:
            pass
        page.wait_for_timeout(3500)

        try:
            page.hover(".screen-status-bar", force=True)
        except Exception:
            pass
        page.wait_for_timeout(3500)

        print("[Part 1] Scrubbing 40-Week Fetal Growth stages...")
        try:
            page.hover("#growthWeekSlider", force=True)
        except Exception:
            pass
        page.wait_for_timeout(500)
        
        # Slide to week 20
        page.evaluate("document.getElementById('growthWeekSlider').value = 20; onWeekSliderChange(20);")
        page.wait_for_timeout(3500)

        # Slide to week 28
        page.evaluate("document.getElementById('growthWeekSlider').value = 28; onWeekSliderChange(28);")
        page.wait_for_timeout(3500)

        # Slide back to Week 14
        page.evaluate("document.getElementById('growthWeekSlider').value = 14; onWeekSliderChange(14);")
        page.wait_for_timeout(3500)

        try:
            page.hover(".hero-growth-card", force=True)
        except Exception:
            pass
        page.wait_for_timeout(4500)

        try:
            page.hover(".daily-activities-wrap", force=True)
        except Exception:
            pass
        page.wait_for_timeout(5750)

        # =====================================================================
        # PART 2: (0:28.75 - 1:08.28 ~ 39.53s) - FastMCP Spec 2025-11-25 & Telemetry
        # =====================================================================
        print("[Part 2] Demonstrating Self-Hosted FastMCP spec 2025-11-25 & Telemetry Drawer...")
        try:
            page.hover("#mcpStatus", force=True)
        except Exception:
            pass
        page.wait_for_timeout(3500)

        print("[Part 2] Opening Telemetry Drawer...")
        page.click("#telemetryToggleBtn", force=True)
        page.wait_for_timeout(4500)

        try:
            page.hover("#toolsTab", force=True)
        except Exception:
            pass
        page.wait_for_timeout(5500)

        print("[Part 2] Switching to Baby Timeline...")
        page.click("#tabBtnTimeline", force=True)
        page.wait_for_timeout(5500)

        print("[Part 2] Switching to Partner Night Shift Board...")
        page.click("#tabBtnPartner", force=True)
        page.wait_for_timeout(3500)

        page.fill("#newTaskInput", "Sterilize pump parts before 3 AM")
        page.wait_for_timeout(2000)
        page.press("#newTaskInput", "Enter")
        page.wait_for_timeout(4500)

        page.click("#tabBtnTools", force=True)
        page.wait_for_timeout(4500)

        page.click("#closeTelemetryBtn", force=True)
        page.wait_for_timeout(3000)

        page.evaluate("window.scrollTo({ top: 120, behavior: 'smooth' });")
        page.wait_for_timeout(3030)

        # =====================================================================
        # PART 3: (1:08.28 - 1:42.70 ~ 34.42s) - Multimodal Light Bar & Voice Logging
        # =====================================================================
        print("[Part 3] Triggering voice logging & Alexa Multimodal Light Bar...")
        page.evaluate("window.scrollTo({ top: 380, behavior: 'smooth' });")
        page.wait_for_timeout(2500)

        try:
            page.hover("#micBtn", force=True)
        except Exception:
            pass
        page.wait_for_timeout(3000)

        print("[Part 3] Simulating utterance: Maya nursed 15 min left...")
        page.evaluate("simulateUtterance('Maya nursed for 15 minutes on the left side');")
        page.wait_for_timeout(1000)
        
        page.evaluate("window.scrollTo({ top: 80, behavior: 'smooth' });")
        page.wait_for_timeout(5000)

        # Response card visible
        page.wait_for_timeout(6000)

        print("[Part 3] Activating Circadian Night Mode (Zero Blue)...")
        page.click("#nightToggleBtn", force=True)
        page.wait_for_timeout(8500)

        print("[Part 3] Restoring Day Mode...")
        page.click("#nightToggleBtn", force=True)
        page.wait_for_timeout(8420)

        # =====================================================================
        # PART 4: (1:42.70 - 2:17.74 ~ 35.04s) - 5-Pillar App Tour & Smart Health Tools
        # =====================================================================
        print("[Part 4] Touring 5-Pillar Swasth Experience on Echo Show...")
        page.click("#echoTab-plans", force=True)
        page.wait_for_timeout(4000)

        try:
            page.evaluate("openToolSheet('water');")
        except Exception:
            pass
        page.wait_for_timeout(3500)
        try:
            page.evaluate("logWater(250); closeToolSheet();")
        except Exception:
            pass
        page.wait_for_timeout(3500)

        try:
            page.evaluate("openToolSheet('audio');")
        except Exception:
            pass
        page.wait_for_timeout(4000)
        try:
            page.evaluate("closeToolSheet();")
        except Exception:
            pass
        page.wait_for_timeout(2500)

        print("[Part 4] Navigating to Birth Clubs...")
        try:
            page.click("#echoTab-community", force=True)
        except Exception:
            pass
        page.wait_for_timeout(5500)

        print("[Part 4] Navigating to Session...")
        try:
            page.click("#echoTab-ai", force=True)
        except Exception:
            pass
        page.wait_for_timeout(5500)

        print("[Part 4] Navigating to More & Privacy...")
        try:
            page.click("#echoTab-more", force=True)
        except Exception:
            pass
        page.wait_for_timeout(3500)

        print("[Part 4] Returning to Home Dashboard...")
        try:
            page.click("#echoTab-home", force=True)
        except Exception:
            pass
        page.wait_for_timeout(3040)

        # =====================================================================
        # PART 5: (2:17.74 - 2:46.42 ~ 28.68s) - Distress Safety Guardrails & Closing
        # =====================================================================
        print("[Part 5] Demonstrating distress safety guardrails & helpline triage...")
        try:
            page.evaluate("window.scrollTo({ top: 380, behavior: 'smooth' });")
        except Exception:
            pass
        page.wait_for_timeout(2000)

        try:
            page.evaluate("simulateUtterance(\"I'm feeling really exhausted and overwhelmed today\");")
        except Exception:
            pass
        page.wait_for_timeout(1000)

        try:
            page.evaluate("window.scrollTo({ top: 80, behavior: 'smooth' });")
        except Exception:
            pass
        page.wait_for_timeout(4000)

        # Highlight Tele-MANAS helpline card
        page.wait_for_timeout(11000)

        # Dismiss overlay and show serene final view
        try:
            page.evaluate("dismissVoiceOverlay();")
        except Exception:
            pass
        page.wait_for_timeout(3000)

        # Final smooth wide shot of Echo Show 10 and speaker base
        try:
            page.evaluate("window.scrollTo({ top: 50, behavior: 'smooth' });")
        except Exception:
            pass
        page.wait_for_timeout(8680)

        print("[Demo Complete] Closing browser and finalizing recording...")
        context.close()
        browser.close()

    webm_files = [f for f in os.listdir(output_dir) if f.endswith(".webm")]
    if webm_files:
        raw_video = os.path.join(output_dir, webm_files[0])
        print(f"Recorded raw video: {raw_video}")
        return raw_video
    else:
        raise RuntimeError("No recorded video found in output directory.")

if __name__ == "__main__":
    record_hackathon_demo()
