import gradio as gr
from generate_narratives import Narrative_Generator
from sentence_transformers import SentenceTransformer
import pandas as pd
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
                gr.Markdown(label="Generated Narratives"),
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

iface.launch()

