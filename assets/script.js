document.addEventListener("DOMContentLoaded", function () {
    let narratives = {};  // Store narratives and their corresponding clustered tweets

    // Fetch the generated narratives and clustered tweets
    fetch("http://localhost:7860/api/narratives")
        .then(response => response.json())
        .then(data => {
            // Data will contain both narratives and clustered_tweets
            narratives = data;
        });

    document.body.addEventListener("mouseover", function (event) {
        if (event.target.classList.contains("narrative-block")) {
            let narrativeText = event.target.innerText;

            // Find the index of the hovered narrative
            let index = narratives.generated_narratives.findIndex(narrative => narrative.includes(narrativeText));
            
            if (index !== -1) {
                // Get the corresponding clustered tweets using the same index
                let clusteredTweets = narratives.clustered_tweets[index];

                let tweetBox = document.getElementById("tweet-display");
                if (!tweetBox) {
                    tweetBox = document.createElement("div");
                    tweetBox.id = "tweet-display";
                    tweetBox.style.position = "absolute";
                    tweetBox.style.background = "#fff";
                    tweetBox.style.border = "1px solid #ddd";
                    tweetBox.style.padding = "10px";
                    tweetBox.style.boxShadow = "2px 2px 10px rgba(0,0,0,0.1)";
                    document.body.appendChild(tweetBox);
                }
                
                // Display the clustered tweets related to the hovered narrative
                tweetBox.innerHTML = `<strong>Clustered Tweets:</strong><br>${clusteredTweets.join("<br>")}`;
                tweetBox.style.left = event.pageX + "px";
                tweetBox.style.top = event.pageY + "px";
                tweetBox.style.display = "block";
            }
        }
    });

    document.body.addEventListener("mouseout", function (event) {
        if (event.target.classList.contains("narrative-block")) {
            let tweetBox = document.getElementById("tweet-display");
            if (tweetBox) tweetBox.style.display = "none";
        }
    });
});
