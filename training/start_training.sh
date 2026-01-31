#!/bin/bash
# LoRA Fine-Tuning Execution Script

echo "🚀 Starting Ziva LoRA Fine-Tuning"
echo "=================================="

# Check CUDA availability
python3 -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"

# Check dataset
if [ ! -f "data/training/ziva_lora_dataset.json" ]; then
    echo "❌ Dataset not found!"
    exit 1
fi

DATASET_SIZE=$(jq length data/training/ziva_lora_dataset.json)
echo "📊 Dataset size: $DATASET_SIZE examples"

if [ $DATASET_SIZE -lt 10 ]; then
    echo "⚠️  Warning: Dataset is very small ($DATASET_SIZE examples)"
    echo "   Recommended: 500+ examples for production training"
    echo "   Proceeding with demonstration training..."
fi

# Start training
echo ""
echo "🏋️ Starting LoRA training..."
echo "  Base model: qwen2.5-coder:7b"
echo "  Epochs: 3"
echo "  Batch size: 2"
echo "  Learning rate: 2e-4"
echo ""

python3 training/train_lora.py \
    --base-model "qwen2.5-coder:7b" \
    --dataset "data/training/ziva_lora_dataset.json" \
    --output "models/ziva-lora-adapter" \
    --epochs 3 \
    --batch-size 2 \
    --learning-rate 2e-4

echo ""
echo "✅ Training complete!"
