# mod2fix

**The Ultimate Minecraft Mod Error Diagnostic Tool**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub release](https://img.shields.io/github/release/ArliT1-F/mod2fix.svg)](https://github.com/ArliT1-F/mod2fix/releases)

> Instantly diagnose Minecraft mod crashes, find missing dependencies, and get direct download links for the correct mod versions.

![mod2fix Screenshot](screenshots/main.png)

## 🎯 What is mod2fix?

mod2fix is a powerful diagnostic tool for Minecraft modded gameplay. It analyzes crash logs, scans your mods folder, identifies problems, and provides actionable solutions with direct download links.

### ✨ Key Features

- 🔍 **Crash Log Analysis** - Automatically detect mod errors from crash reports
- 📦 **Dependency Checking** - Find missing mod dependencies
- 🔗 **Direct Downloads** - Get links to the correct mod versions for your Minecraft version
- 🎮 **Multi-Loader Support** - Works with Fabric, Forge, and Quilt mods
- 🌐 **Web Interface** - User-friendly GUI (no command line needed!)
- ⚡ **Fast & Accurate** - Parse hundreds of mods in seconds
- 🆓 **100% Free & Open Source**

## 🚀 Quick Start

### Option 1: Web Interface (Easiest)

1. Download the latest release
2. Open `web/index.html` in your browser
3. Upload your crash log or select your mods folder
4. Get instant diagnostics!

### Option 2: Command Line

```bash
# Clone the repository
git clone "https://github.com/ArliT1-F/mod2fix.git
cl mod2fix

# Install
pip install -r requirements.txt

# Analyze crash log
python mod2fix.py crash-report.txt

# Check dependencies
python mod2fix.py --mods-folder "C:/Users/YourName/AppData/Roaming/.minecraft/mods" --find-missing

# Full analysis
python mod2fix.py latest.log -m ./mods -f