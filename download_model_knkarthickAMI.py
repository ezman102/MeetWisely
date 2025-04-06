save_path = "models/bart-large-cnn-knkarthick-AMI"

from huggingface_hub import login

# login(token="YOUR_HUGGING_FACE_ACCESS_TOKEN")
login(token="YOUR_HUGGING_FACE_ACCESS_TOKEN")

import torch
from transformers import BartForConditionalGeneration, BartTokenizer
from torch.utils.data import DataLoader, Dataset
from datasets import load_dataset

# ✅ Load BART Tokenizer & Model
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")

# ✅ Load AMI Dataset
ami_dataset = load_dataset("knkarthick/AMI", split="train")

# Take the top 3 records from the AMI dataset
top_3_ami_dataset = ami_dataset  # ami_dataset.select(range(3))


class MeetingDataset(Dataset):
    def __init__(self, dataset, tokenizer, max_length=512):
        self.dataset = dataset
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        dialogue = self.dataset[idx]["dialogue"]
        summary = self.dataset[idx]["summary"]

        inputs = self.tokenizer(
            dialogue,
            max_length=self.max_length,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        labels = self.tokenizer(
            summary,
            max_length=150,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        return {
            "input_ids": inputs["input_ids"].squeeze(),
            "attention_mask": inputs["attention_mask"].squeeze(),
            "labels": labels["input_ids"].squeeze(),
        }


# ✅ Create DataLoader
# dataset = MeetingDataset(ami_dataset, tokenizer)
dataset = MeetingDataset(top_3_ami_dataset, tokenizer)
dataloader = DataLoader(dataset, batch_size=2, shuffle=True)

# ✅ Fine-Tuning Loop
optimizer = torch.optim.AdamW(model.parameters(), lr=5e-5)

for epoch in range(3):  # Train for 3 epochs
    for batch in dataloader:
        optimizer.zero_grad()
        outputs = model(**batch)
        loss = outputs.loss
        loss.backward()
        optimizer.step()
    print(f"Epoch {epoch + 1}, Loss: {loss.item()}")

tokenizer.save_pretrained(save_path)
model.save_pretrained(save_path)

print("✅ Model downloaded to", save_path)
