"""
Fine-Tuning API — exposes dataset info and fine-tuning status.
Judges can see the LoRA configuration and maintenance dataset.
"""
from pathlib import Path
from fastapi import APIRouter
from app.fine_tuning.maintenance_dataset import get_dataset, get_dataset_stats

router = APIRouter(prefix="/api/fine-tuning", tags=["Fine-Tuning"])


@router.get("/dataset")
def get_training_dataset():
    """Return the maintenance Q&A dataset used for LoRA fine-tuning."""
    return {
        "stats": get_dataset_stats(),
        "samples": get_dataset(),
    }


@router.get("/dataset/stats")
def get_dataset_statistics():
    """Return dataset statistics."""
    return get_dataset_stats()


@router.get("/dataset/sample/{index}")
def get_sample(index: int):
    """Return a specific training sample."""
    data = get_dataset()
    if index < 0 or index >= len(data):
        from fastapi import HTTPException
        raise HTTPException(404, f"Sample {index} not found. Total: {len(data)}")
    return data[index]


@router.get("/lora-config")
def get_lora_config():
    """Return LoRA fine-tuning configuration."""
    # Check if a fine-tuned model exists
    adapter_path = Path("./models/maintenance_lora")
    model_exists = (adapter_path / "finetune_config.json").exists()

    config = {
        "base_model": "unsloth/Llama-3.2-1B-Instruct",
        "alternative_models": [
            "mistralai/Mistral-7B-Instruct-v0.3",
            "meta-llama/Llama-3.2-3B-Instruct",
        ],
        "lora_parameters": {
            "rank_r": 16,
            "alpha": 32,
            "dropout": 0.05,
            "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
            "trainable_parameters_percent": "~0.1%",
            "task_type": "CAUSAL_LM",
        },
        "training": {
            "epochs": 3,
            "batch_size": 2,
            "gradient_accumulation": 4,
            "effective_batch_size": 8,
            "learning_rate": "2e-4",
            "lr_scheduler": "cosine",
            "quantization": "4-bit NF4 (BitsAndBytes)",
            "hardware_requirement": "8GB VRAM minimum (T4/RTX 3060)",
            "estimated_training_time": "~10 minutes on T4 GPU",
        },
        "dataset": get_dataset_stats(),
        "fine_tuned_model_available": model_exists,
        "adapter_path": str(adapter_path) if model_exists else None,
        "production_fallback": "Groq API (llama-3.3-70b-versatile) used when fine-tuned model unavailable",
    }

    if model_exists:
        import json
        with open(adapter_path / "finetune_config.json") as f:
            config["trained_model_config"] = json.load(f)

    return config


@router.post("/run")
def trigger_finetuning(
    model_name: str = "unsloth/Llama-3.2-1B-Instruct",
    epochs: int = 3,
):
    """
    Trigger LoRA fine-tuning (requires GPU environment).
    In production this would be a background job.
    """
    try:
        from app.fine_tuning.lora_finetune import run_finetuning, FineTuningConfig
        config = FineTuningConfig(model_name=model_name, num_epochs=epochs)
        output = run_finetuning(config)
        return {"status": "completed", "output_dir": output}
    except ImportError as e:
        return {
            "status": "dependencies_missing",
            "message": f"Install: pip install transformers peft datasets trl accelerate bitsandbytes",
            "error": str(e),
            "note": "Fine-tuning requires GPU. In CPU-only environment, Groq API is used as production fallback."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
