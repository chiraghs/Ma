import asyncio
import os
import subprocess
import edge_tts

VOICE = "en-US-JennyNeural"
RATE = "-4%" # Gentle, soothing maternal tempo

PARTS = [
    {
        "id": "part1",
        "text": (
            "Welcome to MA, an ambient voice companion for expectant and new mothers, "
            "built for the Alexa Plus Preview hackathon on the Amazon Echo Show 10 Smart Display. "
            "When a mother is nursing at 3 AM or holding her sleeping baby with full hands, "
            "she cannot look down at a harsh, blue-lit smartphone screen. "
            "MA transforms the Echo Show into an empathetic, hands-free nursery sanctuary, "
            "combining soothing ambient intelligence with real-time maternal care."
        )
    },
    {
        "id": "part2",
        "text": (
            "At the technical core of MA is a self-hosted Model Context Protocol server, "
            "adhering strictly to the official spec 2025-11-25 using Streamable HTTP on port 8005. "
            "MCP is the open standard powering modern Alexa Plus integrations. "
            "Our architecture connects Amazon Bedrock Converse directly to self-hosted MCP tools "
            "over persistent HTTP streams, giving Alexa Plus the ability to log infant feedings, "
            "track sleep rhythms, synchronize partner chore boards, and surface sandboxed SEP-1865 visual cards "
            "directly on the Echo Show."
        )
    },
    {
        "id": "part3",
        "text": (
            "Notice the signature Alexa Multimodal Light Bar across the bottom of the screen. "
            "When a mother speaks naturally, saying: 'Alexa, Maya nursed for 15 minutes on the left side', "
            "the light bar sweeps cyan and rose-gold. "
            "The Echo Show captures the utterance, dispatches a real-time JSON-RPC 2.0 tool call to our FastMCP server, "
            "and responds in a soft, soothing voice with an on-screen visual card. "
            "In circadian night mode, responses are kept to a single calming sentence, preserving maternal melatonin."
        )
    },
    {
        "id": "part4",
        "text": (
            "Beyond ambient voice tracking, MA integrates the comprehensive 5-pillar Swasth maternal health experience. "
            "On Home, mothers explore a 40-week fetal growth scrubber and daily Garbh Sanskar habits across physical, mental, and spiritual wellness. "
            "In Plans, eight essential smart health tools provide 2.5-liter hydration reminders, a baby kick counter, "
            "and a 432-hertz Om chanting player. "
            "Clubs connect mothers with their birth cohort, and Session offers timed circuit workouts with Ayurvedic nutrition."
        )
    },
    {
        "id": "part5",
        "text": (
            "Crucially, MA is designed with compassionate clinical guardrails. "
            "If a mother expresses feelings of despair or postpartum overwhelm, "
            "MA immediately provides gentle reassurance and routes directly to confidential 24/7 care lines like Tele-MANAS. "
            "This is how brands in the Alexa Plus Preview are leveraging the open MCP standard: "
            "building secure, compassionate, ambient experiences that truly touch lives. "
            "Thank you."
        )
    }
]

async def generate():
    os.makedirs("/Volumes/DiskD/Devpost/Ma/video/audio_clips", exist_ok=True)
    file_list = []
    
    for p in PARTS:
        out_path = f"/Volumes/DiskD/Devpost/Ma/video/audio_clips/{p['id']}.mp3"
        print(f"Generating {p['id']}...")
        comm = edge_tts.Communicate(p["text"], VOICE, rate=RATE)
        await comm.save(out_path)
        file_list.append(out_path)

    # Concat all audio clips using ffmpeg
    concat_list = "/Volumes/DiskD/Devpost/Ma/video/audio_clips/concat.txt"
    with open(concat_list, "w") as f:
        for fl in file_list:
            f.write(f"file '{fl}'\n")

    full_audio = "/Volumes/DiskD/Devpost/Ma/video/narration_full.mp3"
    subprocess.run([
        "/opt/homebrew/bin/ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", concat_list, "-c", "copy", full_audio
    ], check=True)

    # Check duration
    res = subprocess.run([
        "/opt/homebrew/bin/ffprobe", "-i", full_audio,
        "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"
    ], capture_output=True, text=True)
    duration = float(res.stdout.strip())
    print(f"Total Narration Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")

if __name__ == "__main__":
    asyncio.run(generate())
