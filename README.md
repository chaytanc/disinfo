# Disinformation Analysis Platform

A comprehensive platform for analyzing narrative similarity and disinformation spread across social media datasets using machine learning and semantic analysis.

> **🔥 Quick Start**: This project includes **shared infrastructure** for immediate access. No setup required - just clone and run! See [Usage Guidelines](USAGE_GUIDELINES.md) for terms and community expectations.

## Overview

This platform enables researchers to:
- **Upload and analyze** social media datasets (Twitter/X, etc.)
- **Track narrative similarity** over time using sentence transformers
- **Generate automated summaries** of narrative clusters using LLMs
- **Export analysis results** for further research

The system uses MLX-optimized machine learning models for Apple Silicon GPU acceleration and provides both a REST API backend and React frontend.

## ⚡ Quick Start

### Prerequisites
- **macOS** with Apple Silicon (M1/M2/M3) recommended
- **Python 3.11+** and **Node.js 18+**
- **Git**

### 1. Clone and Setup Backend
```bash
git clone https://github.com/chaytanc/disinfo.git
cd disinfo

# Create virtual environment with Python 3.11
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start backend (uses shared infrastructure automatically)
python app.py
```

### 2. Setup Frontend
```bash
cd tweet-analysis-app
npm install
npm run dev
```

### 3. Access Application
- Open `http://localhost:3000`
- **Sign in with Google/Email** (uses shared authentication)
  - NOTE: you should have an account set up through contacting Chaytan. If you don't, please contact me through first at chaytan@uw.edu
- Upload your own CSV datasets. Sample datasets may have access issues currently.
  - A sample dataset is available to download from this repository: sample_data.csv
- Run analysis and visualize results

**That's it!** No configuration needed - the shared infrastructure handles authentication and setup.

## 📋 Usage Guidelines & Terms

**IMPORTANT**: Before using this platform, please read our [**Usage Guidelines**](USAGE_GUIDELINES.md).

### Quick Summary:
- ✅ **Free for research, education, and personal use**
- ✅ **Contribute improvements back to the community**
- ✅ **Give attribution** when publishing results
- ⚠️ **Commercial use requires permission** - contact us first
- ⚠️ **High-volume usage** - please discuss with maintainer
- ❌ **Don't circumvent usage guidelines** or create competing services

**Why guidelines?** This project uses shared infrastructure (authentication, compute resources) to enable immediate access for researchers. The guidelines ensure fair use and project sustainability.

**Questions?** See [Usage Guidelines](USAGE_GUIDELINES.md) for full details or contact us via GitHub Issues.

## Data Format Requirements

Upload CSV files with these required columns:
- **Tweet** (required): Text content to analyze
- **Datetime** (required): Timestamp in YYYY-MM-DD HH:MM:SS format
- **ChannelName** (recommended): Account/user name for better analysis

Optional columns: PostId, Platform, LikesCount, SharesCount, etc.

Click the **Help** button in the dashboard for detailed formatting requirements and examples.

## Usage Workflow

### 1. Upload Data
- Click "Upload CSV File" in the dashboard
- Select a properly formatted CSV file
- Files are processed securely in your browser

### 2. Configure Analysis
- **Target Narrative**: Text to measure similarity against (e.g., "The 2020 election was stolen")
- **Date Range**: Time period to analyze
- **Similarity Threshold**: Minimum similarity score (0-1)
- **Datasets**: Select one or more for comparison

### 3. Run Analysis
- Click "Apply Filters" to analyze similarity over time
- View interactive timeline charts
- Click data points for detailed tweet information

### 4. Generate Insights
- Click "Generate Narratives" for AI-powered summaries
- Specify number of narrative clusters
- Review generated insights and themes

### 5. Save Results
- Click "Save Results" to download analysis as CSV
- Files include metadata for reproducing analysis
- Use "Load Saved Analysis" to restore previous work

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate tests
4. Submit a pull request

**Please read [Usage Guidelines](USAGE_GUIDELINES.md)** before contributing.

## License

This project is licensed under the **MIT License with Additional Terms** - see the [LICENSE](LICENSE) file for details.

### 📊 Fair Use
This project uses **shared infrastructure** to enable immediate access for researchers. Please:
- Use responsibly and respect other users
- Contribute improvements back to the project  
- Follow the [Usage Guidelines](USAGE_GUIDELINES.md)
- Give attribution when publishing results

---

**Built with ❤️ for good research**
