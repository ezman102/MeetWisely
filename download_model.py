from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_id = "facebook/bart-large-cnn"
save_path = "models/bart-large-cnn"

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

tokenizer.save_pretrained(save_path)
model.save_pretrained(save_path)

print("✅ Model downloaded to", save_path)
