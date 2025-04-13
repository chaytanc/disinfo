from flask import Flask, request, jsonify
from generate_narratives import Narrative_Generator
import pandas as pd
from sentence_transformers import SentenceTransformer
from mlx_lm import load
from preprocess import read_media, add_datetime_column
from graph_sims import trace_over_time, graph_timeseries

# target_narrative = "The 2020 election was a hoax"
file = "tweets/full_tweets.csv"
summary_model, tokenizer = load("mlx-community/Mistral-Nemo-Instruct-2407-4bit")
sent_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
df = read_media(file)
df = add_datetime_column(df)


app = Flask(__name__)
@app.route('/trace-over-time', methods=['POST'])
def api_trace_over_time():
    # Get parameters from request
    data = request.json
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    target_narrative = data.get('targetNarrative')
    threshold = data.get('threshold', 0.5)  # Default threshold if not provided
    
    # Call your trace_over_time function
    filtered_df = trace_over_time(df, sent_model, target_narrative, [start_date, end_date], sim_threshold=threshold)
    
    # Optional: generate graph (or this could be done client-side)
    if 'generateGraph' in data and data['generateGraph']:
        graph_timeseries(filtered_df, target_narrative, sent_model, threshold=threshold)
    
    # Return the filtered data
    result = {
        'filteredData': filtered_df.to_dict('records'),
        'summary': {
            'totalTweets': len(filtered_df),
            'dateRange': f"{start_date} to {end_date}",
            'threshold': threshold,
            'targetNarrative': target_narrative
        }
    }
    
    return jsonify(result)

@app.route('/generate-narratives', methods=['POST'])
def api_generate_narratives():
    # Get data from the request
    data = request.json
    
    # Whether to use pre-filtered data or the raw data
    if 'useFilteredData' in data and data['useFilteredData'] and 'filteredData' in data:
        # Use the filtered data provided in the request
        filtered_df = pd.DataFrame(data['filteredData'])
    else:
        # Apply filtering based on parameters
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        target_narrative = data.get('targetNarrative')
        threshold = data.get('threshold', 0.5)
        filtered_df = trace_over_time(df, sent_model, target_narrative, [start_date, end_date], sim_threshold=threshold)
    
    # Get number of narratives to generate
    num_narratives = data.get('numNarratives', 3)
    
    # Use your Narrative_Generator
    narrative_generator = Narrative_Generator(summary_model, tokenizer, sent_model, filtered_df, num_narratives)
    narratives_obj, *_ = narrative_generator.generate_narratives()
    
    # # Convert object to array format for React
    # for 
    # narratives_array = [
    #     {"key": key, "text": value} for key, value in narratives_obj.items()
    # ]
    
    # Return the results as an array
    return jsonify({'narratives': narratives_obj})

if __name__ == '__main__':
    # Load your DataFrame here
    # df = pd.read_csv('your_tweets.csv')
    app.run(debug=True)
