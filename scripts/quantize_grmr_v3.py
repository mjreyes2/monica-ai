"""
Quantize GRMR-V3 model to INT8 for 2-3x speedup
This script creates an optimized INT8 quantized version of the GRMR-V3 model
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from pathlib import Path
import time

def quantize_grmr_v3():
    """Quantize GRMR-V3 model to INT8"""
    print("=" * 60)
    print("GRMR-V3 INT8 Quantization")
    print("=" * 60)
    
    model_id = "qingy2024/GRMR-V3-Q1.7B"
    output_dir = Path(__file__).parent / "models" / "grmr_v3_int8"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[1/4] Loading original model: {model_id}")
    print("This may take a few minutes...")
    start_time = time.time()
    
    # Load original model
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float32,  # Load as FP32 for quantization
        device_map="cpu"  # Keep on CPU for quantization
    )
    
    load_time = time.time() - start_time
    print(f" Model loaded in {load_time:.2f}s")
    
    # Get original model size
    original_size = sum(p.numel() * p.element_size() for p in model.parameters()) / (1024 * 1024)
    print(f"Original model size: {original_size:.2f} MB")
    
    print("\n[2/4] Quantizing model to INT8...")
    print("This will reduce model size and increase inference speed 2-3x")
    quant_start = time.time()
    
    # Quantize to INT8
    quantized_model = torch.quantization.quantize_dynamic(
        model,
        {torch.nn.Linear},  # Quantize all Linear layers
        dtype=torch.qint8
    )
    
    quant_time = time.time() - quant_start
    print(f" Quantization completed in {quant_time:.2f}s")
    
    # Get quantized model size
    quantized_size = sum(p.numel() * p.element_size() for p in quantized_model.parameters()) / (1024 * 1024)
    print(f"Quantized model size: {quantized_size:.2f} MB")
    print(f"Size reduction: {((original_size - quantized_size) / original_size * 100):.1f}%")
    
    print("\n[3/4] Saving quantized model...")
    save_start = time.time()
    
    # Save quantized model
    torch.save({
        'model_state_dict': quantized_model.state_dict(),
        'model_config': model.config.to_dict(),
        'quantization': 'int8',
        'original_model': model_id
    }, output_dir / "quantized_model.pt")
    
    # Save tokenizer
    tokenizer.save_pretrained(output_dir)
    
    save_time = time.time() - save_start
    print(f" Model saved to: {output_dir}")
    print(f"Save time: {save_time:.2f}s")
    
    print("\n[4/4] Testing quantized model...")
    test_start = time.time()
    
    # Test inference
    test_text = "hey monica what time is it i need to know"
    inputs = tokenizer(test_text, return_tensors="pt")
    
    # Original model inference
    with torch.no_grad():
        orig_start = time.time()
        _ = model.generate(**inputs, max_new_tokens=50)
        orig_time = time.time() - orig_start
    
    # Quantized model inference
    with torch.no_grad():
        quant_start = time.time()
        _ = quantized_model.generate(**inputs, max_new_tokens=50)
        quant_time = time.time() - quant_start
    
    speedup = orig_time / quant_time
    print(f" Original inference: {orig_time:.3f}s")
    print(f" Quantized inference: {quant_time:.3f}s")
    print(f" Speedup: {speedup:.2f}x faster")
    
    test_time = time.time() - test_start
    print(f"Test completed in {test_time:.2f}s")
    
    print("\n" + "=" * 60)
    print("QUANTIZATION COMPLETE!")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Total time: {time.time() - start_time:.2f}s")
    print(f"\nExpected benefits:")
    print(f"  - Inference speed: {speedup:.2f}x faster")
    print(f"  - Model size: {((original_size - quantized_size) / original_size * 100):.1f}% smaller")
    print(f"  - Accuracy loss: <2% (typical for INT8)")
    print(f"\nNext step: Update stt_llm_postprocessor.py to use quantized model")
    
    return output_dir

if __name__ == "__main__":
    try:
        output_dir = quantize_grmr_v3()
        print("\n SUCCESS - Quantized model ready for use!")
    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
