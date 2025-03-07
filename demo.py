# import gradio as gr
# import json
# from generate_narratives import Narrative_Generator

# dataset_options = {
#     "Trump Tweets": "trumptweets1205-127.csv",
#     "Dataset 2": "path/to/dataset2.csv",
#     "Upload Your Own": None
# }

# # Define function that Gradio calls
# def run_narrative_generation(selected_dataset, uploaded_file, num_narratives):
#     file_path = dataset_options.get(selected_dataset, None)
#     if selected_dataset == "Upload Your Own":
#         if uploaded_file is None:
#             return "Please upload a file.", None
#         file_path = uploaded_file.name

#     # Load models (modify if models are initialized elsewhere)
#     summary_model = ...  # Load your model
#     tokenizer = ...  # Load tokenizer
#     embedding_model = ...  # Load embedding model

#     generator = Narrative_Generator(summary_model, tokenizer, embedding_model, file_path, num_narratives)
#     try:
#         raw_narratives = generator.generate_narratives()
#         formatted_output = ""
#         json_list = []

#         for i, json_obj in enumerate(raw_narratives, 1):
#             json_list.append(json_obj)
#             formatted_output += f"### Narrative Set {i}\n"
#             for key, value in json_obj.items():
#                 formatted_output += f"- **{key.replace('_', ' ').capitalize()}**: {value}\n"
#             formatted_output += "\n---\n\n"

#         json_file = "generated_narratives.json"
#         with open(json_file, "w") as f:
#             json.dump(json_list, f, indent=4)

#         return formatted_output.strip(), json_file

#     except ValueError as e:
#         return str(e), None  # Show error in UI

# # Gradio UI
# iface = gr.Interface(
#     fn=run_narrative_generation,
#     inputs=[
#         gr.Dropdown(list(dataset_options.keys()), value="Trump Tweets", label="Select Dataset"),
#         gr.File(label="Upload Text File (Optional)"),
#         gr.Slider(1, 10, step=1, value=5, label="Number of Narratives"),
#     ],
#     outputs=[
#         gr.Markdown(label="Generated Narratives"),
#         gr.File(label="Download Narratives (JSON)"),
#     ],
#     title="Trump Narrative Generator",
#     description="Choose a dataset or upload a file. Select the number of narratives, then click 'Run'.",
#     theme="huggingface"
# )

# iface.launch()

import gradio as gr
import json
from generate_narratives import Narrative_Generator
from sentence_transformers import SentenceTransformer, util
import pandas as pd
import numpy as np
from mlx_lm import load 
from sim_scores import Results

dataset_options = {
    "Trump Tweets": "trumptweets1205-127.csv",
    "Dataset 2": "path/to/dataset2.csv",
    "Upload Your Own": None
}

narrative_options = {
    "0": "Russia is an ally",
    "1": "The 2020 election was stolen"
}

summary_model, tokenizer = load("mlx-community/Mistral-Nemo-Instruct-2407-4bit")
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
# Define function that Gradio calls
def run_narrative_generation(selected_dataset, uploaded_file, num_narratives):
    file_path = dataset_options.get(selected_dataset, None)
    if selected_dataset == "Upload Your Own":
        if uploaded_file is None:
            return "Please upload a file.", None
        file_path = uploaded_file.name

    generator = Narrative_Generator(summary_model, tokenizer, embedding_model, file_path, num_narratives)
    try:
        json_narratives, _ = generator.generate_narratives()
        formatted = generator.format(json_narratives)
        return formatted

    except ValueError as e:
        return str(e), None  # Show error in UI

def rank_narrative(narratives, selected_narrative, max_tweets):
    """
    Runs the ranking function and returns the top k similar tweets to the selected narrative.
    """
    # Make sure the file is handled correctly
    file_path = "trumptweets1205-127.csv"

    # Load the Results object and rank the narrative
    results = Results(embedding_model, file_path, max_tweets, narratives)
    top_k_results = results.print_top_k(k=10, narrative_ind=selected_narrative)

    # Format the result as a readable string or table
    formatted_output = f"**Top 10 Most Similar Tweets to Narrative**: `{selected_narrative}`\n\n"
    # formatted_output += top_k_results
    
    # If the top_k_results are a DataFrame (as expected in most cases)
    if isinstance(top_k_results, pd.DataFrame):
        # Format as Markdown table for Gradio
        formatted_output += top_k_results.to_markdown(index=False)  # Use to_markdown for Markdown formatting
        for index, row in top_k_results.iterrows():
            formatted_output += "\n Tweet: {}".format(row["Tweet"])
            formatted_output += "\n Similarity Score: {}".format(row["Sims"])
    
    return formatted_output

# Gradio UI Setup
with gr.Blocks() as iface:
    with gr.Tab("Narrative Generator"):
        narrative_generator_interface = gr.Interface(
            fn=run_narrative_generation,
            inputs=[
                gr.Dropdown(list(dataset_options.keys()), value="Trump Tweets", label="Select Dataset"),
                gr.File(label="Upload Text File (Optional)"),
                gr.Slider(1, 10, step=1, value=5, label="Number of Narratives"),
            ],
            outputs=[
                gr.Markdown(label="Generated Narratives"),
            ],
            title="Trump Narrative Generator",
            description="Choose a dataset or upload a file. Select the number of narratives, then click 'Run'.",
            theme="huggingface"
        )

    with gr.Tab("Rank Narrative"):
        rank_narrative_interface = gr.Interface(
            fn=rank_narrative,
            inputs=[
                gr.Dropdown([["Russia is an ally", "The 2020 election was stolen"]], value="Narrative", label="Select Narrative"),
                gr.Slider(0, 1, step=1, value=0, label="Which narrative index"),
                gr.Slider(1, 1000, step=1, value=10, label="Max Tweets to Process"),
            ],
            outputs=[
                gr.Markdown(label="Top 10 Similar Tweets"),
            ],
            title="Rank Narrative with Tweets",
            description="Select a narrative, upload a file, and rank the most similar tweets to that narrative.",
            theme="huggingface"
        )

    # Rendering the interfaces inside the tabs
    narrative_generator_interface.render()
    rank_narrative_interface.render()

iface.launch()

