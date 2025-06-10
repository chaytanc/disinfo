from flask import Flask, request, jsonify
from flask_cors import CORS
from generate_narratives import Narrative_Generator
from impact_analysis import PolarityTester
import pandas as pd
from sentence_transformers import SentenceTransformer
from mlx_lm import load
from preprocess import read_media
from graph_sims import trace_over_time, graph_timeseries
import os
import numpy as np
import json
import datetime
import mlx.core as mx
from transformers import AutoModelForCausalLM
import gc
import contextlib

# Set MLX to use GPU
mx.set_default_device(mx.gpu)

# Verify GPU is being used
print(f"MLX is using device: {mx.default_device()}")

tweets_dir = 'tweets'

# Load models using MLX with explicit GPU configuration
summary_model, tokenizer = load("mlx-community/Mistral-Nemo-Instruct-2407-4bit")
# summary_model, tokenizer = load("mlx-community/Mistral-Small-24B-Instruct-2501-4bit")
sent_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
polarity_model, pol_tokenizer = load("mlx-community/Mistral-Small-24B-Instruct-2501-4bit")

# Configure SentenceTransformer to use MPS (Metal Performance Shaders)
# This enables GPU acceleration for PyTorch-based models on Mac
import torch
if torch.backends.mps.is_available():
    sent_model = sent_model.to('mps')
    print("SentenceTransformer using MPS (GPU)")
else:
    print("MPS not available, SentenceTransformer using CPU")

app = Flask(__name__)
# CORS(app)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": "*"}})

@app.route('/post-datasets', methods=['POST'])
def api_post_datasets():
    """ Assumes every csv file in tweets_dir is compatible w analysis 
    (has Tweet, Datetime cols). Returns these in a jsonified list."""
    files = [
        os.path.relpath(os.path.join(root, f), tweets_dir)
        for root, _, filenames in os.walk(tweets_dir)
        for f in filenames
        if f.endswith('.csv')
    ]
    result = {
        'files': files 
    }
    
    return jsonify(result)

@app.route('/trace-over-time', methods=['POST'])
def api_trace_over_time():
    gc.collect()
    try:
        # Get parameters from request
        data = request.json
        file = os.path.join(tweets_dir, data.get('file1'))
        df = read_media(file)
        
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        target_narrative = data.get('targetNarrative')
        threshold = data.get('threshold', 0.5)
        
        # Call your trace_over_time function
        filtered_df = trace_over_time(df, sent_model, target_narrative, [start_date, end_date], sim_threshold=threshold)
        
        # Replace NaN values with None (which becomes null in JSON)
        filtered_df = filtered_df.replace({np.nan: None})
        # Use a context manager to ensure proper cleanup
        # p = PolarityTester(polarity_model, pol_tokenizer, filtered_df, target_narrative)
        # p.check_polarity()
        # p.multiply_similarity_and_polarity()
        # filtered_df = p.df
        gc.collect()
        
        # Convert DataFrame to records
        records = filtered_df.to_dict('records')
        
        # Return the filtered data
        result = {
            'filteredData': records,
            'summary': {
                'totalTweets': len(filtered_df),
                'dateRange': f"{start_date} to {end_date}",
                'threshold': threshold,
                'targetNarrative': target_narrative
            }
        }
        
        return jsonify(result)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/generate-narratives', methods=['POST'])
def api_generate_narratives():
    data = request.json
    
    filtered_df = pd.DataFrame(data['filteredData'])
    # Get number of narratives to generate
    num_narratives = data.get('numNarratives', 3)
    
    # Use your Narrative_Generator
    narrative_generator = Narrative_Generator(summary_model, tokenizer, sent_model, filtered_df, num_narratives)
    narratives_obj, *_ = narrative_generator.generate_narratives()
    
    # Return the results as an array
    return jsonify({'narratives': narratives_obj})


@app.route('/save-filtered-data', methods=['POST'])
def save_filtered_data():
    try:
        # Get data from request
        data = request.json
        filtered_data = data.get('filteredData')
        
        if not filtered_data:
            return jsonify({'error': 'No filtered data provided'}), 400
            
        # Convert to DataFrame
        df = pd.DataFrame(filtered_data)
        
        # Create a save directory if it doesn't exist
        save_dir = os.path.join('saved_data')
        os.makedirs(save_dir, exist_ok=True)
        
        # Generate unique filename based on timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"filtered_data_{timestamp}.pkl"
        filepath = os.path.join(save_dir, filename)
        
        # Save as pickle
        df.to_pickle(filepath)
        
        # Also save as CSV for easier access if needed
        csv_filepath = os.path.join(save_dir, f"filtered_data_{timestamp}.csv")
        df.to_csv(csv_filepath, index=False)
        
        return jsonify({
            'success': True,
            'message': f'Data saved successfully as {filename}',
            'filename': filename,
            'rowCount': len(df)
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'error': str(e)
        }), 500


# Optional: Add an endpoint to list saved datasets
@app.route('/list-saved-data', methods=['GET'])
def list_saved_data():
    try:
        save_dir = os.path.join('saved_data')
        if not os.path.exists(save_dir):
            return jsonify({'datasets': []})
            
        files = [f for f in os.listdir(save_dir) if f.endswith('.pkl')]
        files.sort(reverse=True)  # Most recent first
        
        return jsonify({'datasets': files})
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/load-saved-data', methods=['POST'])
def load_saved_data():
    try:
        # Get filename from request
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
            
        # Build path to saved file
        save_dir = os.path.join('saved_data')
        filepath = os.path.join(save_dir, filename)
        
        # Check if file exists
        if not os.path.exists(filepath):
            return jsonify({'error': f'File {filename} not found'}), 404
        
        # Load pickle file
        df = pd.read_pickle(filepath)
        
        # Replace NaN values with None for JSON serialization
        df = df.replace({np.nan: None})
        
        # Convert DataFrame to records
        records = df.to_dict('records')
        
        return jsonify({
            'success': True,
            'filename': filename,
            'data': records,
            'rowCount': len(records)
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True)