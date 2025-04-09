import numpy as np
import os
from sentence_transformers import SentenceTransformer, util
from datasets import load_dataset
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy.stats import pearsonr, spearmanr
import pandas as pd
from sklearn.linear_model import LinearRegression
import random
from tqdm import tqdm

# Create the results directory if it doesn't exist
os.makedirs('glue_results', exist_ok=True)

# Load the embedding model
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Load STS-B validation set
dataset = load_dataset("glue", "stsb", split="validation")

# Process the dataset on Semantic Textual Similarity Benchmark (Cer et al., 2017)
results = []
for example in tqdm(dataset):
    sentence1 = example['sentence1']
    sentence2 = example['sentence2']
    gold_score = example['label'] / 5.0  # Normalize: human scores are [0, 5]
    
    # Encode both sentences
    emb1 = embedding_model.encode(sentence1, convert_to_tensor=True)
    emb2 = embedding_model.encode(sentence2, convert_to_tensor=True)
    
    # Cosine similarity
    cosine_score = util.pytorch_cos_sim(emb1, emb2).item()
    
    # Store all information
    results.append({
        'sentence1': sentence1,
        'sentence2': sentence2,
        'gold_score': gold_score,
        'predicted_score': cosine_score,
        'error': abs(gold_score - cosine_score)
    })

# Convert to DataFrame for easier analysis
df = pd.DataFrame(results)

# Calculate evaluation metrics
pearson_corr, p_value_pearson = pearsonr(df['gold_score'], df['predicted_score'])
spearman_corr, p_value_spearman = spearmanr(df['gold_score'], df['predicted_score'])
mse = mean_squared_error(df['gold_score'], df['predicted_score'])
mae = mean_absolute_error(df['gold_score'], df['predicted_score'])

# Print metrics
print(f"Pearson correlation: {pearson_corr:.4f} (p={p_value_pearson:.4e})")
print(f"Spearman correlation: {spearman_corr:.4f} (p={p_value_spearman:.4e})")
print(f"Mean Squared Error: {mse:.4f}")
print(f"Mean Absolute Error: {mae:.4f}")

# Visualize correlation between predicted and gold scores with regression line
plt.figure(figsize=(10, 6))
plt.scatter(df['gold_score'], df['predicted_score'], alpha=0.5)

# Add regression line
x = df['gold_score'].values.reshape(-1, 1)
y = df['predicted_score'].values
model = LinearRegression()
model.fit(x, y)
y_pred = model.predict(x)
plt.plot(x, y_pred, color='red', linestyle='--', label="Lin Reg Line")

# Add correlation coefficients to the plot
plt.annotate(f"Pearson r = {pearson_corr:.4f}\nSpearman ρ = {spearman_corr:.4f}\nMSE = {mse:.4f}\nMAE = {mae:.4f}",
            xy=(0.01, 0.85), xycoords='axes fraction',
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.8))

# Add perfect prediction line
plt.plot([0, 1], [0, 1], 'g--', alpha=0.5, label="Perfect Correlation") 

plt.xlabel('Human Score (normalized)')
plt.ylabel('Model Predicted Score')
plt.title('GLUE STS-B: Correlation between Similarity Scores')
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.grid(True)
plt.legend()
plt.savefig('glue_results/similarity_correlation.png')
plt.close()

# Generate tables with examples
# Find examples of good predictions (low error)
good_examples = df.sort_values(by='error').head(5)
print("\nExamples where model performs well:")
for _, row in good_examples.iterrows():
    print(f"Sentence 1: {row['sentence1']}")
    print(f"Sentence 2: {row['sentence2']}")
    print(f"Human score: {row['gold_score']:.4f}, Model score: {row['predicted_score']:.4f}, Error: {row['error']:.4f}")
    print("-" * 80)

# Find examples of bad predictions (high error)
bad_examples = df.sort_values(by='error', ascending=False).head(5)
print("\nExamples where model struggles:")
for _, row in bad_examples.iterrows():
    print(f"Sentence 1: {row['sentence1']}")
    print(f"Sentence 2: {row['sentence2']}")
    print(f"Human score: {row['gold_score']:.4f}, Model score: {row['predicted_score']:.4f}, Error: {row['error']:.4f}")
    print("-" * 80)

# Create error distribution histogram
plt.figure(figsize=(10, 6))
plt.hist(df['error'], bins=20, alpha=0.7)
plt.xlabel('Absolute Error')
plt.ylabel('Frequency')
plt.title('Distribution of Prediction Errors')
plt.grid(True)
plt.savefig('glue_results/error_distribution.png')
plt.close()

# Generate a comprehensive HTML report with tables
def create_html_report():
    # Calculate quartiles of error to segment performance
    df['error_category'] = pd.qcut(df['error'], 4, labels=['Excellent', 'Good', 'Fair', 'Poor'])
    
    # Get random examples from each category
    examples = pd.DataFrame()
    for category in ['Excellent', 'Good', 'Fair', 'Poor']:
        examples = pd.concat([examples, df[df['error_category'] == category].sample(min(3, sum(df['error_category'] == category)))])
    
    # Sort by error for display
    examples = examples.sort_values('error')
    
    # Create HTML table with properly escaped curly braces
    html = """
    <html>
    <head>
        <style>
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .excellent {{
                background-color: #d4edda;
            }}
            .good {{
                background-color: #d1ecf1;
            }}
            .fair {{
                background-color: #fff3cd;
            }}
            .poor {{
                background-color: #f8d7da;
            }}
            .metrics {{
                font-size: 1.2em;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <h1>Embedding Model Evaluation Report</h1>
        <div class="metrics">
            <p><strong>Pearson Correlation:</strong> {:.4f} (p={:.4e})</p>
            <p><strong>Spearman Correlation:</strong> {:.4f} (p={:.4e})</p>
            <p><strong>Mean Squared Error:</strong> {:.4f}</p>
            <p><strong>Mean Absolute Error:</strong> {:.4f}</p>
        </div>
        
        <h2>Example Predictions</h2>
        <table>
            <tr>
                <th>Performance</th>
                <th>Sentence 1</th>
                <th>Sentence 2</th>
                <th>Human Score</th>
                <th>Model Score</th>
                <th>Error</th>
            </tr>
    """.format(pearson_corr, p_value_pearson, spearman_corr, p_value_spearman, mse, mae)
    
    for _, row in examples.iterrows():
        category = row['error_category'].lower()
        html += f"""
            <tr class="{category}">
                <td>{row['error_category']}</td>
                <td>{row['sentence1']}</td>
                <td>{row['sentence2']}</td>
                <td>{row['gold_score']:.4f}</td>
                <td>{row['predicted_score']:.4f}</td>
                <td>{row['error']:.4f}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <h2>Error Analysis</h2>
        <p> TODO
        It struggles more with nuanced similarities that humans can detect.</p>
        
        <h3>Performance Summary by Error Quartile</h3>
        <table>
            <tr>
                <th>Category</th>
                <th>Error Range</th>
                <th>Count</th>
                <th>Percentage</th>
            </tr>
    """
    
    # TODO the counts are always 375 bc the categories are by definition quartiles... either make different categories by hand or get rid of the meaningless counts
    error_stats = df.groupby('error_category').agg(
        error_min=('error', 'min'),
        error_max=('error', 'max'),
        count=('error', 'count')
    )
    error_stats['percentage'] = error_stats['count'] / len(df) * 100
    
    for category, row in error_stats.iterrows():
        html += f"""
            <tr>
                <td>{category}</td>
                <td>{row['error_min']:.4f} - {row['error_max']:.4f}</td>
                <td>{row['count']}</td>
                <td>{row['percentage']:.2f}%</td>
            </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    with open('glue_results/embedding_evaluation_report.html', 'w') as f:
        f.write(html)
    
    return html

# Generate the report
html_report = create_html_report()
print("\nHTML report generated as 'glue_results/embedding_evaluation_report.html'")

# Also save results as CSV for further analysis
df.to_csv('glue_results/embedding_evaluation_results.csv', index=False)
print("Full results saved to 'glue_results/embedding_evaluation_results.csv'")

# Create a summary results file
with open('glue_results/summary_metrics.txt', 'w') as f:
    f.write(f"Model: sentence-transformers/all-MiniLM-L6-v2\n")
    f.write(f"Dataset: GLUE STS-B (validation split)\n")
    f.write(f"Pearson correlation: {pearson_corr:.4f} (p={p_value_pearson:.4e})\n")
    f.write(f"Spearman correlation: {spearman_corr:.4f} (p={p_value_spearman:.4e})\n")
    f.write(f"Mean Squared Error: {mse:.4f}\n")
    f.write(f"Mean Absolute Error: {mae:.4f}\n")
    f.write(f"Number of examples: {len(df)}\n")

print("Summary metrics saved to 'glue_results/summary_metrics.txt'")