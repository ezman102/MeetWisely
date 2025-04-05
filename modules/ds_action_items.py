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
You are a smart AI meeting assistant. Extract action items from the following transcript.
Each action item should include:
- The speaker
- The task
- The due date (if mentioned)

Format:
- Speaker: [Name]
  Task: [Action they committed to]
  Due: [Due date if mentioned]

Transcript:
\"\"\"
{transcript_text}
\"\"\"

Action Items:
"""

    result = generator(prompt, max_new_tokens=256, do_sample=False)
    output = result[0]['generated_text']

    if "Action Items:" in output:
        output = output.split("Action Items:")[-1].strip()

    return output
