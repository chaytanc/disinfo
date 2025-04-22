import numpy as np
from mlx_lm import generate
from sklearn.cluster import KMeans

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain_community.llms.mlx_pipeline import MLXPipeline

import json
import re
from dotenv import load_dotenv

# TODO do I still need this?
load_dotenv()
# Simple prompt
SYS_PROMPT = "You should find the top two dominant narratives in the following batch of tweets. Do not cite which tweets correspond to the narratives, just supply the narrative summaries. You must always return valid JSON fenced by a markdown code block. Do not return any additional text. "

smallest_batch_size = 10

class Narrative_Generator():
    def __init__(self, summary_model, tokenizer, embedding_model, data, num_narratives):
        self.summary_model = summary_model
        self.tokenizer = tokenizer
        self.embedding_model = embedding_model
        self.num_narratives = num_narratives
        self.df = data
        # You could use preprocess_context_window here instead if data is too big...


    def create_prompt(self, tokenizer, user_prompt):
        messages = [
            {"role": "system", "content": SYS_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        
        prompt = tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
        )
        return prompt


    def create_format_prompt(self, parser):
        prompt = PromptTemplate(
            template= SYS_PROMPT+"\n{format_instructions}\n{query}\n",
            input_variables=["query"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        return prompt


    def cluster_embedded_tweets(self, tweets):
        embeddings = []
        for tweet in tweets:
            embeddings.append(self.embedding_model.encode(tweet, convert_to_numpy=True))
        clusters = KMeans(n_clusters=self.num_narratives).fit(embeddings)
        unique_labels = np.unique(clusters.labels_)
        # Chunk tweets by cluster labels
        clustered_tweets = [tweets[clusters.labels_ == label] for label in unique_labels]
        return clustered_tweets


    # TODO yaml
    # TODO private functions
    def process_chunk(self, chunk, model, tokenizer):
        prompt = self.create_prompt(tokenizer, SYS_PROMPT, user_prompt=chunk)
        response = generate(
            model, tokenizer, 
            #temperature=0.9, top_p=0.8, 
            max_tokens=512, prompt=prompt, 
            verbose=True)
        return response, prompt


    def generate_narratives(self, progress=None):
        # Set up a parser + inject instructions into the prompt template.
        parser = JsonOutputParser(pydantic_object=self.NarrativeSummary)
        llm = MLXPipeline(model=self.summary_model, tokenizer=self.tokenizer, pipeline_kwargs={
            "temp": 0.9,
          })
        prompt = self.create_format_prompt(parser)
        chain = prompt | llm | self.parse_json_objects 

        # What happens when we have way more than 300 tweets? Can we still cluster 50,000 or do we chunk it by time and regen narratives?
        clustered_tweets = self.cluster_embedded_tweets(self.df["Tweet"])
        responses = []
        if progress:
            for chunk in progress.tqdm(clustered_tweets):
                resp = chain.invoke({"query": chunk})
                # TODO remove print
                print(resp)
                if not resp:
                    continue
                responses.append(resp[0])
        else:
            for chunk in (clustered_tweets):
                resp = chain.invoke({"query": chunk})
                if not resp:
                    continue
                responses.append(resp[0])
 
        return responses, prompt, clustered_tweets


    def format(self, raw_narratives):
        # Formats to markdown for direct display as a string.
        formatted_output = ""
        # Loop through the outer list (each narrative set)
        for idx, narrative_set in enumerate(raw_narratives, 1):
            if not narrative_set:  # Skip empty lists
                continue

            formatted_output += f"### Narrative Set {idx}\n"

            # Loop through each narrative (which is a dictionary)
            for key, value in narrative_set.items():
                formatted_output += f"- **{key.replace('_', ' ').capitalize()}**: {value}\n"

            formatted_output += "\n---\n\n"

        return formatted_output.strip()


    def get_html_formatted_outputs(self, raw_narratives):
        outputs = []
        for idx, narrative_set in enumerate(raw_narratives, 1):
            if not narrative_set:  # Skip empty lists
                continue
            
            # Start a container div for each narrative pair
            formatted_output = f"<div class='narrative-block' data-narrative-id='{idx}'>"
            formatted_output += "<hr class='narrative-separator'>" 

            for key, value in narrative_set.items():
                formatted_output += f"""
                <div class='narrative-item'>
                    <strong>{key.replace('_', ' ').capitalize()}:</strong>
                    <p>{value}</p>
                </div>
                """

            formatted_output += "</div>"  # Close block div
            outputs.append(formatted_output)

        return outputs


    def save_json_narratives(self, json_list):
        # Save JSON for download
        json_file = "generated_narratives.json"
        with open(json_file, "w") as f:
            json.dump(json_list, f, indent=4)
        return json_file


    def parse_json_objects(self, text):
        """
        Identifies JSON objects between curly braces and attempts to parse them.
        Returns a list of successfully parsed JSON objects.
        Raises an error if parsing any JSON object fails, but continues processing others.
        Returns a list of one JSON object with keys 'narrative_1' and 'narrative_2'.
        """
        # Regex to find JSON objects between curly braces {}
        json_objects = re.findall(r'\{.*?\}', text, re.DOTALL)
        
        parsed_json_list = []  # To store successfully parsed JSON objects

        # Loop through each potential JSON object
        for json_str in json_objects:
            try:
                # Try parsing the JSON string
                parsed_json = json.loads(json_str)
                parsed_json_list.append(parsed_json)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}. Skipping invalid JSON object.")
                continue  # Skip the invalid JSON and continue processing other objects

        return parsed_json_list


    # Define your desired data structure.
    class NarrativeSummary(BaseModel):
        narrative_1: str = Field(description="Most dominant narrative")
        narrative_2: str = Field(description="Second dominant narrative")