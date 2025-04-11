import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.summarizer import generate_summary
from modules.translator import translate_text
from modules.ds_action_items import extract_action_items_with_deepseek

def read_transcript(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return lines

def run_tests(transcript_file="assets/transcript_1.txt", output_path="test_results.txt"):
    if not os.path.exists(transcript_file):
        print(f"❌ Transcript file not found: {transcript_file}")
        return

    transcript_lines = read_transcript(transcript_file)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=== Summary ===\n")
        summary = generate_summary("\n".join(transcript_lines))
        f.write(summary + "\n\n")

        f.write("=== Translation (French) ===\n")
        translation = translate_text("\n".join(transcript_lines), src_lang="en", tgt_lang="fr")
        f.write(translation + "\n\n")

        f.write("=== Action Items ===\n")
        actions = extract_action_items_with_deepseek(transcript_lines)
        f.write(actions + "\n")

    print(f"✅ Results saved to: {output_path}")

if __name__ == "__main__":
    run_tests()
