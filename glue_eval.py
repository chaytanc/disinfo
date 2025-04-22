import numpy as np
import os
import base64
from io import BytesIO
from sentence_transformers import SentenceTransformer, util
from datasets import load_dataset
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy.stats import pearsonr 
import pandas as pd
from sklearn.linear_model import LinearRegression
from tqdm import tqdm
from matplotlib.gridspec import GridSpec
from scipy.stats import linregress

# Create the results directory if it doesn't exist
os.makedirs('glue_results', exist_ok=True)

# Load the embedding model
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

# Load STS-B validation set
dataset = load_dataset("glue", "stsb", split="validation")

# Process the dataset
results = []
for example in dataset:
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
        'error': abs(gold_score - cosine_score),
        'signed_error': cosine_score - gold_score  # Positive means overestimation
    })

# Convert to DataFrame for easier analysis
df = pd.DataFrame(results)

# Calculate evaluation metrics
pearson_corr, p_value_pearson = pearsonr(df['gold_score'], df['predicted_score'])
mse = mean_squared_error(df['gold_score'], df['predicted_score'])
mae = mean_absolute_error(df['gold_score'], df['predicted_score'])

# Print metrics
print(f"Pearson correlation: {pearson_corr:.4f} (p={p_value_pearson:.4e})")
print(f"Mean Squared Error: {mse:.4f}")
print(f"Mean Absolute Error: {mae:.4f}")

# Calculate error metrics for specific human score ranges
score_ranges = [0.0, 0.25, 0.5, 0.75, 1.0]
range_width = 0.124999
error_by_range = {}
examples_by_range = {}

for target in tqdm(score_ranges):
    lower_bound = max(0, target - range_width)
    upper_bound = min(1, target + range_width)
    
    # Filter for scores in this range
    in_range = df[(df['gold_score'] >= lower_bound) & (df['gold_score'] <= upper_bound)]
    
    if len(in_range) > 0:
        avg_error = in_range['error'].mean()
        avg_signed_error = in_range['signed_error'].mean()
        error_by_range[target] = {
            'avg_error': avg_error,
            'avg_signed_error': avg_signed_error,
            'count': len(in_range),
            'percent_overestimated': (in_range['signed_error'] > 0).mean() * 100,
            'percent_underestimated': (in_range['signed_error'] < 0).mean() * 100
        }
        
        # Get representative examples for this range (best and worst predictions)
        if len(in_range) >= 2:
            best_example = in_range.sort_values('error').iloc[0]
            worst_example = in_range.sort_values('error', ascending=False).iloc[0]
            examples_by_range[target] = {
                'best': best_example,
                'worst': worst_example
            }

# Print error analysis by score range
print("\nError analysis by human score range:")
for score, metrics in error_by_range.items():
    print(f"Human score ≈ {score}:")
    print(f"  Average absolute error: {metrics['avg_error']:.4f}")
    print(f"  Average signed error: {metrics['avg_signed_error']:.4f} ({'overestimation' if metrics['avg_signed_error'] > 0 else 'underestimation'})")
    print(f"  Number of examples: {metrics['count']}")
    print(f"  Overestimated: {metrics['percent_overestimated']:.1f}%, Underestimated: {metrics['percent_underestimated']:.1f}%")
    print()

# Visualize correlation between predicted and gold scores with regression line
plt.figure(figsize=(10, 6))
plt.scatter(df['gold_score'], df['predicted_score'], alpha=0.5)

# Add regression line
x = df['gold_score'].values.reshape(-1, 1)
y = df['predicted_score'].values
model = LinearRegression()
model.fit(x, y)
y_pred = model.predict(x)
plt.plot(x, y_pred, color='red', linestyle='--', label="Lin Reg")

# Add correlation coefficients to the plot
plt.annotate(f"Pearson r = {pearson_corr:.4f}\nMSE = {mse:.4f}\nMAE = {mae:.4f}",
            xy=(0.01, 0.85), xycoords='axes fraction',
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.8))

# Add perfect prediction line
plt.plot([0, 1], [0, 1], 'g--', alpha=0.5, label="Perfect Correlation") 

plt.xlabel('Human Score (normalized)')
plt.ylabel('Model Predicted Score')
plt.title('Correlation between Human and Model Similarity Scores')
plt.xlim(0, 1)
plt.ylim(0, 1)
plt.grid(True)
plt.legend()
plt.savefig('glue_results/similarity_correlation.png')

# Save the plot as a base64 string for embedding in HTML
buf = BytesIO()
plt.savefig(buf, format='png')
buf.seek(0)
img_str = base64.b64encode(buf.read()).decode('utf-8')
plt.close()

# Create error distribution histogram
plt.figure(figsize=(10, 6))
plt.hist(df['error'], bins=20, alpha=0.7)
plt.xlabel('Absolute Error')
plt.ylabel('Frequency')
plt.title('Distribution of Prediction Errors')
plt.grid(True)
plt.savefig('glue_results/error_distribution.png')
plt.close()

def plot_residual_errors(df, save_path):
    """
    Creates a scatter plot of residual errors (predicted - gold) against gold scores,
    with a histogram showing the distribution of errors.
    
    Args:
        df: DataFrame containing 'gold_score' and 'signed_error' columns
        save_path: Path to save the resulting plot
    """
        
    fig = plt.figure(figsize=(12, 8))
    gs = GridSpec(3, 3, figure=fig)
    # Create the main scatter plot
    ax_scatter = fig.add_subplot(gs[1:, :2])
    
    # Add a zero line to indicate the boundary between overestimation and underestimation
    ax_scatter.axhline(y=0, color='r', linestyle='--', alpha=0.7, label="Perfect Prediction")
    
    # Create scatter plot with coolwarm colormap
    # - Blue colors (negative values) indicate UNDERESTIMATION (model < human)
    # - Red colors (positive values) indicate OVERESTIMATION (model > human)
    scatter = ax_scatter.scatter(
        df['gold_score'], 
        df['signed_error'],
        alpha=0.5, 
        c=df['signed_error'], 
        cmap='coolwarm',
        vmin=-0.5, 
        vmax=0.5
    )
    
    # Add color bar with enhanced explanation
    cbar = plt.colorbar(scatter, ax=ax_scatter)
    cbar.set_label('Signed Error (Model - Human)')
    
    # Add annotations to explain the color scheme
    plt.figtext(0.15, 0.15, "BLUE: Model underestimates similarity", 
                color='blue', fontsize=10, bbox=dict(facecolor='white', alpha=0.8))
    plt.figtext(0.15, 0.12, "RED: Model overestimates similarity", 
                color='red', fontsize=10, bbox=dict(facecolor='white', alpha=0.8))
    
    # Add trend line with improved annotation
    slope, intercept, r_value, p_value, std_err = linregress(df['gold_score'], df['signed_error'])
    x = np.linspace(0, 1, 100)
    y = slope * x + intercept
    ax_scatter.plot(x, y, color='black', linestyle='-', linewidth=2, 
                                 label=f"Trend (slope={slope:.3f})")
    
    # Add labels and title
    ax_scatter.set_xlabel('Human Similarity Score')
    ax_scatter.set_ylabel('Signed Error (Model - Human)')
    ax_scatter.set_title('Residual Errors by Human Similarity Score')
    
    # Add only the error histogram (removing the human scores histogram)
    ax_histy = fig.add_subplot(gs[1:, 2], sharey=ax_scatter)
    
    # Make the error histogram
    ax_histy.hist(df['signed_error'], bins=20, orientation='horizontal', alpha=0.7, color='gray')
    
    # Hide the ticks on the histogram
    ax_histy.tick_params(axis="y", labelleft=False)
    
    # Add histogram label
    ax_histy.set_title('Error Distribution')
    
    # Calculate and display percentage of overestimates vs underestimates
    overestimates = (df['signed_error'] > 0).mean() * 100
    underestimates = (df['signed_error'] < 0).mean() * 100
    perfect = (np.isclose(df['signed_error'], 0, atol=0.01)).mean() * 100
    
    stats_text = (
        f"Overestimates: {overestimates:.1f}%\n"
        f"Underestimates: {underestimates:.1f}%\n"
        f"Perfect (±0.01): {perfect:.1f}%"
    )
    
    # Add text annotation with statistics
    fig.text(0.75, 0.75, stats_text, fontsize=12, 
             bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5'))
    
    # Add legend
    ax_scatter.legend(loc='upper left')
    
    plt.tight_layout()
    plt.savefig(save_path)
    print(f"Residual error plot saved to {save_path}")
    
    # Save the base64 encoded image for HTML embedding
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return img_str
# Call this function in your main code after creating the DataFrame
residual_img_str = plot_residual_errors(df, 'glue_results/residual_errors.png')

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
    
    # Create error analysis by human score range for embedding in HTML
    error_analysis_html = ""
    for score in score_ranges:
        if score in error_by_range:
            metrics = error_by_range[score]
            error_analysis_html += f"""
            <h3>Human Score ≈ {score}</h3>
            <p>
                <strong>Average absolute error:</strong> {metrics['avg_error']:.4f}<br>
                <strong>Average signed error:</strong> {metrics['avg_signed_error']:.4f} 
                ({'overestimation' if metrics['avg_signed_error'] > 0 else 'underestimation'})<br>
                <strong>Number of examples:</strong> {metrics['count']}<br>
                <strong>Overestimated:</strong> {metrics['percent_overestimated']:.1f}%, 
                <strong>Underestimated:</strong> {metrics['percent_underestimated']:.1f}%
            </p>
            """
            
            # Add examples if available
            if score in examples_by_range:
                best = examples_by_range[score]['best']
                worst = examples_by_range[score]['worst']
                
                error_analysis_html += f"""
                <h4>Example Analysis</h4>
                <table class="examples">
                    <tr>
                        <th>Type</th>
                        <th>Sentence 1</th>
                        <th>Sentence 2</th>
                        <th>Human Score</th>
                        <th>Model Score</th>
                        <th>Error</th>
                        <th>Analysis</th>
                    </tr>
                    <tr>
                        <td>Best Prediction</td>
                        <td>{best['sentence1']}</td>
                        <td>{best['sentence2']}</td>
                        <td>{best['gold_score']:.4f}</td>
                        <td>{best['predicted_score']:.4f}</td>
                        <td>{best['error']:.4f}</td>
                        <td>{get_similarity_analysis(best)}</td>
                    </tr>
                    <tr>
                        <td>Worst Prediction</td>
                        <td>{worst['sentence1']}</td>
                        <td>{worst['sentence2']}</td>
                        <td>{worst['gold_score']:.4f}</td>
                        <td>{worst['predicted_score']:.4f}</td>
                        <td>{worst['error']:.4f}</td>
                        <td>{get_similarity_analysis(worst)}</td>
                    </tr>
                </table>
                """
    
    # Create HTML table with properly escaped curly braces
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
            }}
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
            .plot-container {{
                text-align: center;
                margin: 20px 0;
            }}
            .examples {{
                font-size: 0.9em;
            }}
            .error-bands {{
                margin-top: 30px;
            }}
        </style>
    </head>
    <body>
        <h1>Embedding Model Evaluation Report</h1>
        
        <div class="metrics">
            <p><strong>Model:</strong> sentence-transformers/all-MiniLM-L6-v2</p>
            <p><strong>Dataset:</strong> GLUE STS-B (validation split)</p>
            <p><strong>Pearson Correlation:</strong> {pearson_corr:.4f} (p={p_value_pearson:.4e})</p>
            <p><strong>Mean Squared Error:</strong> {mse:.4f}</p>
            <p><strong>Mean Absolute Error:</strong> {mae:.4f}</p>
            <p><strong>Number of examples:</strong> {len(df)}</p>
        </div>
        
        <div class="plot-container">
            <h2>Correlation Plot</h2>
            <img src="data:image/png;base64,{img_str}" alt="Correlation Plot" />
        </div>
        
        <div class="plot-container">
            <h2>Residual Error Analysis</h2>
            <img src="data:image/png;base64,{residual_img_str}" alt="Residual Errors Plot" />
        </div>

        <h2>Error Analysis</h2>
        <p>The all-MiniLM-L6-v2 model from sentence transformers tends to overestimate the 
        similarity of sentences that humans find more dissimilar, while performing very well on similar and middle similarity sentences.
        The average error of the model on human similarity scores of 0 is {error_by_range[0.0]['avg_error']:.4f}, 
        while at 0.5 is {error_by_range[0.5]['avg_error']:.4f} and at 1 is {error_by_range[1.0]['avg_error']:.4f}.
        The model generally overestimates low similarity scores (signed error at 0: {error_by_range[0.0]['avg_signed_error']:.4f}) 
        and slightly underestimates very high similarity scores (signed error at 1: {error_by_range[1.0]['avg_signed_error']:.4f}).
        Therefore, the model will likely contain more false positives than false negatives, and in the context of tracing disinformation, 
        this means the model might flag legitimate differences as similar content.
        This bias should be considered when setting similarity thresholds for applications like detecting disinformation variants.
        This preference is especially true in the context of iterated trials, where we often have multiple chances to detect emerging disinformation
        through multiple tweets and variants of a narrative.
        We can also see through examining examples of the worst predictions that the model struggles with nonsensical sentences, 
        and can significantly underestimate similarity due to grammatical errors, as seen in the 1.0 human score worst prediction.
        The exact prevalence of underestimation due to grammatical errors is not clear, but the average error of the model relative to the human score
        is shown in Figure 2.
        We can also see that the model tends to overestimate the similarity of sentences with differing dates but similar structure.
        Although this behavior could be desirable in certain contexts, the discrepancy could be due to the STS-B's description of 
        0.2 similarity ratings as "The two sentences are not equivalent, but are on the same topic."
        </p>
        
        <div class="error-bands">
            {error_analysis_html}
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
    """
    
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
        
        <h3>Performance Summary by Error Quartile</h3>
        <table>
            <tr>
                <th>Category</th>
                <th>Error Range</th>
            </tr>
    """
    
    error_stats = df.groupby('error_category').agg(
        error_min=('error', 'min'),
        error_max=('error', 'max'),
    )
    
    for category, row in error_stats.iterrows():
        html += f"""
            <tr>
                <td>{category}</td>
                <td>{row['error_min']:.4f} - {row['error_max']:.4f}</td>
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

# Helper function to analyze why sentences received their similarity scores
def get_similarity_analysis(example):
    # Analyze why the model might have assigned this score
    gold = example['gold_score']
    pred = example['predicted_score']
    error = example['error']
    signed_error = example['signed_error']
    
    # For very low human scores (near 0)
    if gold < 0.2:
        if signed_error > 0:
            return "The model overestimates similarity because it likely focuses on shared common words or sentence structure rather than semantic content."
        else:
            return "The model correctly identifies these sentences as highly dissimilar, capturing the semantic difference."
    
    # For medium-low human scores (around 0.25)
    elif gold < 0.4:
        if signed_error > 0:
            return "The model may be identifying shared concepts or topics that create superficial similarity despite contextual differences."
        else:
            return "The model detects the significant semantic differences between these sentences despite some shared elements."
    
    # For medium human scores (around 0.5)
    elif gold < 0.7:
        if signed_error > 0:
            return "The model likely focuses on shared keywords or sentence structure while giving less weight to the differing context or details."
        else:
            return "The model is sensitive to differences in detail or context that reduce the overall semantic similarity."
    
    # For high human scores (around 0.75)
    elif gold < 0.9:
        if signed_error > 0:
            return "The model may be treating synonymous expressions or related concepts as more similar than human judges would."
        else:
            return "The model is distinguishing subtle differences in meaning or context that make these sentences less than perfectly similar."
    
    # For very high human scores (near 1)
    else:
        if signed_error > 0:
            return "The model sees these as perfect synonyms, possibly overlooking subtle differences that humans detect."
        else:
            return "The model is picking up on subtle linguistic differences that slightly reduce the similarity score compared to human judgment."

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
    f.write(f"Mean Squared Error: {mse:.4f}\n")
    f.write(f"Mean Absolute Error: {mae:.4f}\n")
    f.write(f"Number of examples: {len(df)}\n\n")
    
    f.write("Error metrics by human score range:\n")
    for score, metrics in error_by_range.items():
        f.write(f"Human score ≈ {score}:\n")
        f.write(f"  Average absolute error: {metrics['avg_error']:.4f}\n")
        f.write(f"  Average signed error: {metrics['avg_signed_error']:.4f}\n")
        f.write(f"  Number of examples: {metrics['count']}\n")
        f.write(f"  Overestimated: {metrics['percent_overestimated']:.1f}%, Underestimated: {metrics['percent_underestimated']:.1f}%\n\n")

print("Summary metrics saved to 'glue_results/summary_metrics.txt'")