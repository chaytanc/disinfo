import gradio as gr
from generate_narratives import Narrative_Generator
from sentence_transformers import SentenceTransformer
import pandas as pd
from mlx_lm import load 
from sim_scores import Results
from flask import Flask, jsonify

# Global variables to store results
formatted_narratives = None
clustered_tweets = None

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

def run_narrative_generation(selected_dataset, uploaded_file, num_narratives, progress=gr.Progress()):
    progress(0, desc="Generating narratives...")
    file_path = dataset_options.get(selected_dataset, None)
    if selected_dataset == "Upload Your Own":
        if uploaded_file is None:
            return "Please upload a file.", None
        file_path = uploaded_file.name

    generator = Narrative_Generator(summary_model, tokenizer, embedding_model, file_path, num_narratives)
    try:
        json_narratives, _, clustered_tweets = generator.generate_narratives(progress=progress)
        formatted_narratives = generator.get_html_formatted_outputs(json_narratives)

        html_output = "<div id='narratives-container' style='display: flex; flex-direction: column; gap: 10px;'>"
        for narrative_html in formatted_narratives:
            html_output += narrative_html 
        html_output += "</div>"
        # Store the results globally

        formatted_narratives = json_narratives 
        clustered_tweets = clustered_tweets

        return html_output, clustered_tweets
    # Show error in UI
    except ValueError as e:
        return str(e), None 


def trace_narrative(selected_dataset, narrative, max_tweets):
    """
    Runs the ranking function and returns the top k similar tweets to the selected narrative.
    """
    # Make sure the file is handled correctly
    # file_path = "trumptweets1205-127.csv"
    file_path = dataset_options.get(selected_dataset, None)

    # Load the Results object and rank the narrative
    results = Results(embedding_model, file_path, max_tweets, [narrative])
    top_k_results = results.print_top_k(k=10, narrative_ind=0)

    # Format the result as a readable string or table
    formatted_output = f"**Top 10 Most Similar Tweets to Narrative**: `{narrative}`\n\n"
    
    if isinstance(top_k_results, pd.DataFrame):
        formatted_output += top_k_results.to_markdown(index=False)
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
                gr.HTML(label="Generated Narratives"),
                gr.JSON(label="Clustered Tweets")    
            ],
            title="Trump Narrative Generator",
            description="Choose a dataset or upload a file. Select the number of narratives, then click 'Run'.",
            theme="huggingface"
        )

    with gr.Tab("Trace Narrative"):
        trace_narrative_interface = gr.Interface(
            fn=trace_narrative,
            inputs=[
                # gr.Dropdown([["Russia is an ally", "The 2020 election was stolen"]], value="Narrative", label="Select Narrative"),
                gr.Dropdown(list(dataset_options.keys()), value="Trump Tweets", label="Select Dataset"),
                gr.Textbox(label="Narrative", value="e.g. Russia is an ally"),
                gr.Slider(1, 1000, step=1, value=10, label="Max Tweets to Process"),
            ],
            outputs=[
                gr.Markdown(label="Top 10 Similar Tweets"),
            ],
            title="Rank Narrative with Tweets",
            description="Select a narrative and trace the most similar tweets to that narrative.",
            theme="huggingface"
        )

    # def get_narratives():
    #     if formatted_narratives is not None and clustered_tweets is not None:
    #         return jsonify({
    #             "generated_narratives": formatted_narratives,  # This is the narratives output from the function
    #             "clustered_tweets": clustered_tweets           # This is the corresponding tweets list
    #         })
    #     else:
    #         return jsonify({"error": "No narratives generated yet"}), 400

    gr.HTML("""
        <link rel="stylesheet" type="text/css" href="assets/style.css">
        <script src="assets/script.js"></script>
        """)

# iface.launch(share=False, inbrowser=True, server_name="localhost", server_port=7860, prevent_thread_lock=True)
iface.launch()
