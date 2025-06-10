from sim_scores import Results
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

    for tweet in tqdm(df["AuthorTweet"]):
        tweet_embed = model.encode(tweet, convert_to_tensor=True)
        sim = util.pytorch_cos_sim(tweet_embed, narrative_embed) 
        sim_value = sim.cpu().numpy().item()
        timeseries.append(sim_value)
    return np.array(timeseries)


# graph time on x axis and similarity on y and return the timeseries + a log of the timestamps at each point
def create_timeseries_graph(x, y, title=None):
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
    if title != None:
        plt.title(title) 
    else:
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


def graph_timeseries(df, target_narrative, sent_model, threshold="0.0"):
    times = df["Datetime"].tolist()
    timeframe = "{start} to  {end}".format(start=times[0], end=times[-1])
    timeseries = get_sim_timeseries(target_narrative, sent_model, df)
    threshold = str(threshold)
    create_timeseries_graph(times, timeseries, title="Tracing {target} from {timeframe} above {threshold} similarity".format(target=target_narrative, timeframe=timeframe, threshold=threshold))


def trace_over_time(df, sent_model, target_narrative, timeframe, sim_threshold=0.4):
    """
    Trace the tweets that have a similarity score above a certain threshold
    """
    # Filter the dataframe based on the timeframe and similarity threshold
    filtered_df = df[(df["Datetime"] >= timeframe[0]) & (df["Datetime"] <= timeframe[1])].reset_index(drop=True)
    results = Results(sent_model, filtered_df, 1000000, [target_narrative])
    filtered_df = filtered_df[results.similarities >= sim_threshold]
    index_list = filtered_df.index.tolist()
    # filtered_df["OriginalIndex"] = index_list
    filtered_df["Similarity"] = results.similarities[index_list, 0]
    filtered_df.reset_index(drop=False, inplace=True)
    return filtered_df

if __name__ == "__main__":
    target_narrative = "The 2020 election was stolen"
    file = "tweets/full_tweets.csv"
    summary_model, tokenizer = load("mlx-community/Mistral-Nemo-Instruct-2407-4bit")
    sent_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    df = read_media(file)
    df = add_datetime_column(df)
    threshold = 0.4
    filtered_df = trace_over_time(df, sent_model, target_narrative, ["2020-11-01", "2020-12-01"], sim_threshold=threshold)
    graph_timeseries(filtered_df, target_narrative, sent_model, threshold=threshold)
