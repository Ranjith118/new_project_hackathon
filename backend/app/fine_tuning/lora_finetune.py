"""
LoRA Fine-Tuning Script for Steel Plant Maintenance LLM.

This script demonstrates how to fine-tune a small LLM (e.g., Llama-3.2-1B or Mistral-7B)
using LoRA (Low-Rank Adaptation) on the steel plant maintenance Q&A dataset.

LoRA is parameter-efficient — only ~0.1% of model weights are trained,
making fine-tuning feasible on a single GPU (even T4/RTX 3060).

DEPENDENCIES (install if running):
    pip install transformers peft datasets trl accelerate bitsandbytes

USAGE:
    python -m app.fine_tuning.lora_finetune --model_name unsloth/Llama-3.2-1B-Instruct
    python -m app.fine_tuning.lora_finetune --model_name mistralai/Mistral-7B-Instruct-v0.3
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.fine_tuning.maintenance_dataset import get_dataset, get_dataset_stats


# ─────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────

@dataclass
class FineTuningConfig:
    """LoRA fine-tuning configuration."""
    # Model
    model_name: str = "unsloth/Llama-3.2-1B-Instruct"   # Lightweight 1B — fine-tunes in ~10 min on T4
    output_dir: str = "./models/maintenance_lora"

    # LoRA parameters
    lora_r: int = 16            # Rank — controls adapter capacity (8–64 typical)
    lora_alpha: int = 32        # Scaling factor — usually 2x rank
    lora_dropout: float = 0.05
    target_modules: tuple = ("q_proj", "v_proj", "k_proj", "o_proj")  # Attention layers

    # Training
    num_epochs: int = 3
    batch_size: int = 2
    gradient_accumulation: int = 4   # effective batch = 2 * 4 = 8
    learning_rate: float = 2e-4
    max_seq_length: int = 1024
    warmup_steps: int = 10
    save_steps: int = 50
    logging_steps: int = 10

    # Quantization (reduces VRAM — enables fine-tuning on 8GB GPU)
    load_in_4bit: bool = True

    # Dataset
    dataset_format: str = "alpaca"   # instruction / context / response


# ─────────────────────────────────────────────────────────────
# Prompt Formatter
# ─────────────────────────────────────────────────────────────

ALPACA_PROMPT = """Below is an instruction from a steel plant maintenance engineer. \
Use the provided context to give a specific, technical, and actionable response.

### Instruction:
{instruction}

### Context:
{context}

### Response:
{response}"""


def format_prompt(sample: dict, include_response: bool = True) -> str:
    """Format a dataset sample into the Alpaca prompt template."""
    return ALPACA_PROMPT.format(
        instruction=sample["instruction"],
        context=sample.get("context", "No additional context provided."),
        response=sample["response"] if include_response else "",
    )


def prepare_dataset(tokenizer, config: FineTuningConfig):
    """Convert Q&A pairs into tokenized training dataset."""
    try:
        from datasets import Dataset
    except ImportError:
        raise ImportError("Run: pip install datasets")

    raw_data = get_dataset()

    # Format all samples
    formatted = [
        {"text": format_prompt(sample)}
        for sample in raw_data
    ]

    dataset = Dataset.from_list(formatted)

    def tokenize(sample):
        return tokenizer(
            sample["text"],
            truncation=True,
            max_length=config.max_seq_length,
            padding="max_length",
        )

    return dataset.map(tokenize, batched=True, remove_columns=["text"])


# ─────────────────────────────────────────────────────────────
# LoRA Fine-Tuning Pipeline
# ─────────────────────────────────────────────────────────────

def run_finetuning(config: Optional[FineTuningConfig] = None):
    """
    Full LoRA fine-tuning pipeline.
    Trains a domain-specific maintenance LLM using the steel plant dataset.
    """
    if config is None:
        config = FineTuningConfig()

    print("=" * 60)
    print("STEEL PLANT MAINTENANCE LLM — LoRA FINE-TUNING")
    print("=" * 60)

    stats = get_dataset_stats()
    print(f"Dataset: {stats['total_samples']} Q&A samples")
    print(f"Domain: {stats['domain']}")
    print(f"Equipment: {', '.join(stats['equipment_covered'])}")
    print(f"Base model: {config.model_name}")
    print(f"LoRA rank: {config.lora_r} | Alpha: {config.lora_alpha}")
    print()

    # ── Step 1: Load base model ───────────────────────────────
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        import torch
    except ImportError:
        raise ImportError("Run: pip install transformers bitsandbytes accelerate")

    print("Loading base model...")

    bnb_config = None
    if config.load_in_4bit:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        config.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.float16,
    )

    # ── Step 2: Apply LoRA adapters ───────────────────────────
    try:
        from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
    except ImportError:
        raise ImportError("Run: pip install peft")

    print("Applying LoRA adapters...")

    if config.load_in_4bit:
        model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        target_modules=list(config.target_modules),
        lora_dropout=config.lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()  # Shows ~0.1% trainable

    # ── Step 3: Prepare dataset ───────────────────────────────
    print("Preparing maintenance dataset...")
    train_dataset = prepare_dataset(tokenizer, config)
    print(f"  Training samples: {len(train_dataset)}")

    # ── Step 4: Training ──────────────────────────────────────
    try:
        from transformers import TrainingArguments, Trainer, DataCollatorForLanguageModeling
    except ImportError:
        raise ImportError("Run: pip install transformers")

    print("Starting LoRA fine-tuning...")

    training_args = TrainingArguments(
        output_dir=config.output_dir,
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        gradient_accumulation_steps=config.gradient_accumulation,
        learning_rate=config.learning_rate,
        fp16=True,
        logging_steps=config.logging_steps,
        save_steps=config.save_steps,
        warmup_steps=config.warmup_steps,
        lr_scheduler_type="cosine",
        report_to="none",
        save_total_limit=2,
        load_best_model_at_end=False,
    )

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=data_collator,
    )

    trainer.train()

    # ── Step 5: Save LoRA adapters ────────────────────────────
    output_path = Path(config.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    model.save_pretrained(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)

    # Save config for evidence
    with open(output_path / "finetune_config.json", "w") as f:
        json.dump({
            "base_model": config.model_name,
            "lora_r": config.lora_r,
            "lora_alpha": config.lora_alpha,
            "target_modules": list(config.target_modules),
            "domain": "Steel Plant Industrial Maintenance",
            "dataset_samples": len(get_dataset()),
            "num_epochs": config.num_epochs,
        }, f, indent=2)

    print()
    print("=" * 60)
    print(f"Fine-tuning complete. LoRA adapters saved to: {config.output_dir}")
    print("=" * 60)
    return config.output_dir


# ─────────────────────────────────────────────────────────────
# Inference with Fine-Tuned Model
# ─────────────────────────────────────────────────────────────

def load_finetuned_model(adapter_path: str = "./models/maintenance_lora"):
    """Load the fine-tuned LoRA model for inference."""
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from peft import PeftModel
        import torch
    except ImportError:
        raise ImportError("Run: pip install transformers peft")

    config_path = Path(adapter_path) / "finetune_config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"No fine-tuned model found at {adapter_path}. Run fine-tuning first.")

    with open(config_path) as f:
        ft_config = json.load(f)

    base_model_name = ft_config["base_model"]

    print(f"Loading fine-tuned maintenance model from {adapter_path}...")
    tokenizer = AutoTokenizer.from_pretrained(adapter_path)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=torch.float16,
        device_map="auto",
    )
    model = PeftModel.from_pretrained(base_model, adapter_path)
    model.eval()

    return model, tokenizer


def inference(
    question: str,
    context: str = "",
    adapter_path: str = "./models/maintenance_lora",
    max_new_tokens: int = 512,
) -> str:
    """
    Run inference using the fine-tuned maintenance model.
    Falls back to Groq API if fine-tuned model not available.
    """
    import torch

    try:
        model, tokenizer = load_finetuned_model(adapter_path)

        prompt = format_prompt(
            {"instruction": question, "context": context, "response": ""},
            include_response=False,
        )

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.2,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )

        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Extract only the response part
        response = response.split("### Response:")[-1].strip()
        return response

    except FileNotFoundError:
        # Fallback to Groq API (production path)
        from app.config import settings
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        resp = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert industrial maintenance engineer for a steel plant."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
            ],
            temperature=0.2,
            max_tokens=512,
        )
        return resp.choices[0].message.content


# ─────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fine-tune LLM on maintenance data")
    parser.add_argument("--model_name", default="unsloth/Llama-3.2-1B-Instruct")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lora_r", type=int, default=16)
    parser.add_argument("--output_dir", default="./models/maintenance_lora")
    parser.add_argument("--inference_only", action="store_true")
    parser.add_argument("--question", default="Why is the Rolling Mill Motor overheating?")
    args = parser.parse_args()

    if args.inference_only:
        answer = inference(args.question, adapter_path=args.output_dir)
        print("\nAnswer:", answer)
    else:
        config = FineTuningConfig(
            model_name=args.model_name,
            num_epochs=args.epochs,
            lora_r=args.lora_r,
            output_dir=args.output_dir,
        )
        run_finetuning(config)
