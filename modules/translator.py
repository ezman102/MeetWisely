# modules/translator.py
from transformers import MarianMTModel, MarianTokenizer

def load_translation_model(src_lang="en", tgt_lang="fr"):
    model_name = f"Helsinki-NLP/opus-mt-{src_lang}-{tgt_lang}"
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)
    return tokenizer, model

def translate_text(text, src_lang="en", tgt_lang="fr"):
    tokenizer, model = load_translation_model(src_lang, tgt_lang)
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    translated = model.generate(**inputs)
    output = tokenizer.batch_decode(translated, skip_special_tokens=True)
    return output[0]
