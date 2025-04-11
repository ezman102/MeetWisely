# modules/summarizer.py
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

def load_meeting_summarizer():
    model_name = "knkarthick/MEETING_SUMMARY"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return tokenizer, model

tokenizer, model = load_meeting_summarizer()

def generate_summary(text):
    inputs = tokenizer([text], return_tensors="pt", truncation=True, max_length=1024)
    with torch.no_grad():
        summary_ids = model.generate(
            inputs["input_ids"],
            max_length=256,
            min_length=50,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True
        )
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def clean_transcript(transcript_lines):
    return " ".join(line.split("]")[-1].strip() for line in transcript_lines)
