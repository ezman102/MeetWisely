# modules/ds_action_items.py
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
import os

MODEL_ID = "deepseek-ai/deepseek-llm-7b-chat"

print("🔁 Loading DeepSeek model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    device_map="auto",
    torch_dtype=torch.float16,
    offload_folder="offload" 
)

generator = pipeline("text-generation", model=model, tokenizer=tokenizer)

def extract_action_items_with_deepseek(transcript_lines):
    transcript_text = "\n".join(transcript_lines)

    prompt = f"""
You are a smart AI meeting assistant. Read the following transcript and extract action items.
Group the action items by speaker. For each speaker, list the tasks they committed to, along with due dates if available.

Format:
Speaker: [Name]
- Task: [What they will do]
  Due: [Due date if mentioned]
- Task: [Another task]
  Due: [Due date if mentioned]

Transcript:
\"\"\"
{transcript_text}
\"\"\"

Grouped Action Items:
"""

    result = generator(prompt, max_new_tokens=512, do_sample=False)
    output = result[0]['generated_text']

    # Extract content after "Grouped Action Items:"
    if "Grouped Action Items:" in output:
        output = output.split("Grouped Action Items:")[-1].strip()

    return output

