from sim_scores import Results
# from generate_narratives import Narrative_Generator
from sentence_transformers import SentenceTransformer, util
from mlx_lm import load
from preprocess import *
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from tqdm import tqdm

# get narrative to graph similarity to
# get sim_scores for each tweet over time
def get_sim_timeseries(target_narrative, model, df):
    narrative_embed = model.encode(target_narrative, convert_to_tensor=True)
    timeseries = []
    for tweet in tqdm(df["Tweet"]):
        tweet_embed = model.encode(tweet, convert_to_tensor=True)
        sim = util.pytorch_cos_sim(tweet_embed, narrative_embed) 
        sim_value = sim.cpu().numpy().item()
        timeseries.append(sim_value)
    return np.array(timeseries)


# graph time on x axis and similarity on y and return the timeseries + a log of the timestamps at each point
def create_timeseries_graph(x, y):
    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.plot(x, y, marker='o', linestyle='-', color='#1f77b4')

    # Format the x-axis to show dates nicely
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.gcf().autofmt_xdate()  # Rotate date labels for better readability

    # Add labels and title
    plt.xlabel('Date')
    plt.ylabel('Similarity Score')
    plt.title('Narrative Similarity Over Time')

    # Add grid for better readability
    plt.grid(True, alpha=0.3)

    # Adjust y-axis range if needed
    # plt.ylim([min_value, max_value])

    # Tighten layout and display
    plt.tight_layout()
    plt.show()

    # If you want to save the figure
    # plt.savefig('similarity_over_time.png', dpi=300, bbox_inches='tight')


def add_datetime_column(df):
    # arrange tweets in chronological order based on "Time" column
    if "Datetime" not in df.columns:
        df["Datetime"] = pd.to_datetime(df["Date"], format="%Y-%m-%d %H:%M:%S%z")
    df = df.sort_values(by='Datetime', ascending=True) # no .reset_index(drop=True)
    return df


def graph_timeseries(df, target_narrative, sent_model):
    times = df["Datetime"].tolist()
    timeseries = get_sim_timeseries(target_narrative, sent_model, df)
    create_timeseries_graph(times, timeseries)


def trace_over_time(df, timeframe, sim_threshold=0.4):
    """
    Trace the tweets that have a similarity score above a certain threshold
    """
    # Filter the dataframe based on the timeframe and similarity threshold
    filtered_df = df[(df["Datetime"] >= timeframe[0]) & (df["Datetime"] <= timeframe[1])].reset_index(drop=True)
    results = Results(sent_model, filtered_df, 100000, [target_narrative])
    filtered_df = filtered_df[results.similarities >= sim_threshold]
    index_list = filtered_df.index.tolist()
    filtered_df["Similarity"] = results.similarities[index_list, 0]  # First column
    return filtered_df


target_narrative = "The 2020 election was a hoax"
file = "tweets/full_tweets.csv"
summary_model, tokenizer = load("mlx-community/Mistral-Nemo-Instruct-2407-4bit")
sent_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
df = read_media(file)
df = add_datetime_column(df)
filtered_df = trace_over_time(df, ["2020-11-01", "2020-12-01"], sim_threshold=0.4)
graph_timeseries(filtered_df, target_narrative, sent_model)
