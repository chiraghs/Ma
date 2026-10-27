import asyncio
import os
import subprocess
import edge_tts

VOICE = "en-US-JennyNeural"
RATE = "-3%"  # Soothing maternal tempo

PARTS = [
    {
        "id": "part1",
        "text": (
            "Welcome to MA, an ambient voice companion for mothers built for the Alexa Plus Preview on the Amazon Echo Show 10. "
            "When nursing at 3 AM with full hands, harsh phone screens disrupt rest. "
            "MA transforms the Echo Show into a hands-free nursery sanctuary, pairing soothing intelligence with real-time maternal care."
        )
    },
    {
        "id": "part2",
        "text": (
            "At MA's technical core is a self-hosted Model Context Protocol server adhering to spec 2025-11-25 over Streamable HTTP on port 8005. "
            "MCP is the open standard powering modern Alexa Plus integrations. "
            "Connected to Amazon Bedrock Converse, our agent logs feedings, monitors sleep rhythms, and synchronizes partner chores via live JSON-RPC tools."
        )
    },
    {
        "id": "part3",
        "text": (
            "When mom speaks naturally: 'Alexa, Maya nursed for 15 minutes on the left side', the multimodal light bar sweeps cyan and rose-gold. "
            "Our FastMCP server records the event instantly. "
            "In circadian night mode, blue light is eliminated, and Alexa whispers in a single calming sentence to protect maternal melatonin."
        )
    },
    {
        "id": "part4",
        "text": (
            "Beyond voice rhythms, MA embeds the complete 5-pillar Swasth maternal suite on Echo Show. "
            "On Home, mothers explore a 40-week fetal growth scrubber and daily Garbh Sanskar habits. "
            "In Plans, eight smart health tools provide hydration tracking, a baby kick counter, and a 432-hertz Om chanting player. "
            "Birth Clubs connect mothers with their cohort, and Session offers guided prenatal recovery."
        )
    },
    {
        "id": "part5",
        "text": (
            "Crucially, MA includes compassionate clinical guardrails. "
            "When detecting postpartum distress, MA provides warm empathy and routes directly to confidential 24/7 care lines like Tele-MANAS. "
            "This is how brands in the Alexa Plus Preview leverage the open MCP standard to care for mothers. Thank you."
        )
    }
]

async def generate():
    audio_dir = "/Volumes/DiskD/Devpost/Ma/video/audio_clips"
    os.makedirs(audio_dir, exist_ok=True)
    file_list = []
    
    for p in PARTS:
        out_path = f"{audio_dir}/{p['id']}.mp3"
        print(f"Generating {p['id']}...")
        comm = edge_tts.Communicate(p["text"], VOICE, rate=RATE)
        await comm.save(out_path)
        file_list.append(out_path)

    # Concat all audio clips using ffmpeg
    concat_list = f"{audio_dir}/concat.txt"
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
