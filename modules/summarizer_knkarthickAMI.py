from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM


def load_local_summarizer(model_dir="models/bart-large-cnn-knkarthick-AMI"):
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_dir)
    return pipeline("summarization", model=model, tokenizer=tokenizer)


summarizer = load_local_summarizer()


def generate_summary_knkarthickAMI(transcript_text, max_words=150):
    # Truncate or chunk if text too long
    max_input_len = 1024  # BART token limit

    if len(transcript_text.split()) > max_input_len:
        transcript_text = " ".join(transcript_text.split()[:max_input_len])

    result = summarizer(
        transcript_text, max_length=max_words, min_length=30, do_sample=False
    )
    return result[0]["summary_text"]
