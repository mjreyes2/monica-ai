#!/usr/bin/env python3
"""
Install all free AI models for Monica's Multi-Model Cognitive System
This gives Monica multiple specialized capabilities working in cohesion.
"""
import subprocess
import sys
import time

def install_model(model_name):
    """Install a single model using Ollama."""
    print(f"\n📦 Installing {model_name}...")
    try:
        result = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Successfully installed {model_name}")
            return True
        else:
            print(f"❌ Failed to install {model_name}: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing {model_name}: {e}")
        return False

def main():
    """Install all recommended models for Monica."""
    print("=" * 60)
    print("🤖 Monica AI - Multi-Model Installation")
    print("=" * 60)
    print("\nThis will install multiple FREE AI models to enhance Monica's abilities:")
    print("Each model specializes in different tasks for optimal performance.\n")
    
    models = [
        {
            "name": "qwen2.5:7b",
            "description": "Best overall - excellent instruction following",
            "size": "4.7GB",
            "priority": 1
        },
        {
            "name": "phi3:mini",
            "description": "Fast responses for simple queries",
            "size": "2.2GB",
            "priority": 2
        },
        {
            "name": "mistral-nemo",
            "description": "Long context (128k) for extended conversations",
            "size": "7.1GB",
            "priority": 3
        },
        {
            "name": "gemma2:9b",
            "description": "Google's model - great reasoning",
            "size": "5.4GB",
            "priority": 4
        },
        {
            "name": "hermes3",
            "description": "Specialized for following instructions",
            "size": "4.9GB",
            "priority": 5
        },
        {
            "name": "dolphin-mistral",
            "description": "Creative and empathetic responses",
            "size": "4.1GB",
            "priority": 6
        }
    ]
    
    # Calculate total size
    total_size = sum(float(m["size"].replace("GB", "")) for m in models)
    
    print(f"📊 Models to install: {len(models)}")
    print(f"💾 Total download size: ~{total_size:.1f}GB")
    print("\nModels:")
    for model in models:
        print(f"  • {model['name']}: {model['description']} ({model['size']})")
    
    print("\n" + "=" * 60)
    response = input("\n🚀 Start installation? (yes/no): ").lower()
    
    if response not in ['yes', 'y']:
        print("Installation cancelled.")
        return
    
    print("\n🔄 Starting installation...\n")
    
    installed = []
    failed = []
    
    for i, model in enumerate(models, 1):
        print(f"\n[{i}/{len(models)}] Installing {model['name']}...")
        print(f"Purpose: {model['description']}")
        
        if install_model(model['name']):
            installed.append(model['name'])
        else:
            failed.append(model['name'])
            # Ask if user wants to continue after failure
            if i < len(models):
                cont = input(f"\n⚠️ Failed to install {model['name']}. Continue with others? (yes/no): ").lower()
                if cont not in ['yes', 'y']:
                    break
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Installation Summary")
    print("=" * 60)
    
    if installed:
        print(f"\n✅ Successfully installed ({len(installed)}):")
        for model in installed:
            print(f"  • {model}")
    
    if failed:
        print(f"\n❌ Failed to install ({len(failed)}):")
        for model in failed:
            print(f"  • {model}")
    
    if installed:
        print("\n🎉 Monica's cognitive capabilities have been enhanced!")
        print("\n🔧 How to use:")
        print("1. Monica will automatically select the best model for each task")
        print("2. Multiple models work together for complex queries")
        print("3. You can also manually select a model in config.json")
        
        print("\n📊 Model Selection Examples:")
        print("  • 'What time is it?' → Uses phi3:mini (fast)")
        print("  • 'Explain quantum physics' → Uses gemma2 (reasoning)")
        print("  • 'Write a poem' → Uses dolphin-mistral (creative)")
        print("  • Complex instructions → Uses qwen2.5 (best overall)")
    
    print("\n✨ Monica is now ready with enhanced multi-model capabilities!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Installation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
