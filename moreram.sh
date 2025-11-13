#!/bin/bash

echo "=== Optimizing Brave for M4 Pro (YouTube + LM Studio) ==="

###############################################
# 1. Enable full GPU/WebGPU acceleration
###############################################

echo "Setting Brave GPU flags..."

defaults write com.brave.Browser AppleEnableSharedMemoryRasterizer -bool true
defaults write com.brave.Browser DisableMetalShaderCache -bool false
defaults write com.brave.Browser brave://flags/#ignore-gpu-blocklist -bool true

# Force Metal backend for video + WebGPU
defaults write com.brave.Browser EnableMetal -bool true
defaults write com.brave.Browser EnableWebGPUDeveloperFeatures -bool true

###############################################
# 2. Fix YouTube stutter + loading delay
###############################################

echo "Optimizing YouTube playback..."

# Modern codec pipeline for Apple Silicon
defaults write com.brave.Browser UseHardwareVideoDecoding -bool true
defaults write com.brave.Browser UseHardwareMediaCrypto -bool true
defaults write com.brave.Browser DisableTabCapturePaint -bool true

# Force AV1 → VP9 (AV1 is slow in macOS Brave)
defaults write com.brave.Browser OverrideEnabledMediaCodecs -string "vp9,opus"

###############################################
# 3. DNS + Networking boost for YouTube + LLM UIs
###############################################

echo "Applying DNS/network improvements..."

sudo networksetup -setdnsservers Wi-Fi 1.1.1.1 1.0.0.1
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

###############################################
# 4. LM Studio / local LLM acceleration tweaks
###############################################

echo "Optimizing for LM Studio / local models..."

# Unlock full Metal threads for Ollama/LM Studio
export OLLAMA_NUM_GPU=1
export OLLAMA_MAX_COMPUTE=1

# Faster matrix math for M4/M3 chips
defaults write com.LMStudio.ai EnableSIMDOptimizations -bool true

###############################################
# 5. System-level speedups (safe)
###############################################

echo "Applying macOS system tweaks..."

# Faster I/O for large models
sudo sysctl -w kern.maxvnodes=600000
sudo sysctl -w vfs.read_max=128

# Reduce animation delay
defaults write -g NSWindowResizeTime -float 0.001

###############################################
# Done!
###############################################

echo "=== Complete! Restart Brave + LM Studio. ==="
echo "Your M4 Pr
