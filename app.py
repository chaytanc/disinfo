from flask import Flask, request, jsonify
from flask_cors import CORS
from generate_narratives import Narrative_Generator
import pandas as pd
from sentence_transformers import SentenceTransformer
from mlx_lm import load
from preprocess import read_media
from graph_sims import trace_over_time, graph_timeseries
import os
import numpy as np
import json

tweets_dir = 'tweets'
# file = "tweets/full_tweets.csv"
summary_model, tokenizer = load("mlx-community/Mistral-Nemo-Instruct-2407-4bit")
sent_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


app = Flask(__name__)
CORS(app)

@app.route('/post-datasets', methods=['POST'])
def api_post_datasets():
    """ Assumes every csv file in tweets_dir is compatible w analysis 
    (has Tweet, Datetime cols). Returns these in a jsonified list."""
    files = [os.path.basename(f) for f in os.listdir(tweets_dir) 
             if os.path.isfile(os.path.join(tweets_dir, f)) and f.endswith('.csv')]
    result = {
        'files': files 
    }
    
    return jsonify(result)

@app.route('/trace-over-time', methods=['POST'])
def api_trace_over_time():
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
        
        # Convert DataFrame to records
        records = filtered_df.to_dict('records')
        
        # Convert any JSON strings to proper objects
        for record in records:
            for key, value in record.items():
                if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                    try:
                        record[key] = json.loads(value)
                    except:
                        pass  # Keep as string if it's not valid JSON
        
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

if __name__ == '__main__':
    app.run(debug=True)
