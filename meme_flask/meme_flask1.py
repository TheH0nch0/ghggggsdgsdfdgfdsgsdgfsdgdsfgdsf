from flask import Flask, render_template, current_app, render_template_string
import requests
import logging
import os

app = Flask(__name__)
app.config['DEBUG'] = True

def get_meme(attempts=5):
    urls = [
        "https://meme-api.com/gimme",
        "https://meme-api.herokuapp.com/gimme",
        "https://api.imgflip.com/get_memes"
    ]

    for attempt in range(attempts):
        for url in urls:
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                app.logger.info(f"API Response from {url}: {data}")

                if "gimme" in url:
                    subreddit = data.get("subreddit", "unknown")
                    meme_large = data.get("preview", [""])[-2]
                elif "imgflip" in url:
                    meme_data = data.get("data", {}).get("memes", [{}])[0]
                    subreddit = "imgflip"
                    meme_large = meme_data.get("url")
                else:
                    subreddit = data.get("subreddit", "unknown")
                    meme_large = data.get("url")

                if meme_large:
                    return meme_large, subreddit

            except requests.Timeout:
                app.logger.error(f"Request timed out for {url}")
            except requests.RequestException as e:
                app.logger.error(f"Request failed for {url}: {e}")
            except (KeyError, IndexError) as e:
                app.logger.error(f"Error processing response from {url}: {e}")

    app.logger.warning("Reached maximum attempts for getting a meme")
    return None, None

def template_exists(template_name):
    return os.path.exists(os.path.join(current_app.template_folder, template_name))

@app.route("/")
def index():
    app.logger.info(f"Template folder: {current_app.template_folder}")
    meme_pic, subreddit = get_meme()
    if meme_pic and subreddit:
        if template_exists("index.html"):
            return render_template("index.html", meme_pic=meme_pic, subreddit=subreddit)
        else:
            return render_template_string(
                """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Meme Website</title>
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        body { font-family: Arial, sans-serif; background-color: #f0f0f0; }
                        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
                        .title { text-align: center; margin-bottom: 20px; }
                        .meme-card { background-color: #fff; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); overflow: hidden; }
                        .meme-image img { width: 100%; display: block; }
                        .meme-details { padding: 20px; }
                        .subreddit { font-weight: bold; color: #0073e6; margin-bottom: 10px; }
                        .refresh-note { color: #666; }
                        .fa-bookmark, .fa-info-circle { margin-right: 5px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1 class="title">A Website for Devious Memes</h1>
                        <div class="meme-card">
                            <div class="meme-image">
                                <img src="{{ meme_pic }}" alt="Meme">
                            </div>
                            <div class="meme-details">
                                <p class="subreddit"><i class="fas fa-bookmark"></i> Current Subreddit: {{ subreddit }}</p>
                                <p class="refresh-note"><i class="fas fa-info-circle"></i> This meme will refresh in 20 seconds</p>
                            </div>
                        </div>
                    </div>
                </body>
                </html>
                """, meme_pic=meme_pic, subreddit=subreddit
            )
    else:
        if template_exists("error.html"):
            return render_template("error.html"), 500
        else:
            return render_template_string(
                """
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Error</title>
                </head>
                <body>
                    <h1>Failed to Load Meme</h1>
                    <p>There was an error fetching the meme. Please try again later.</p>
                </body>
                </html>
                """), 500
    
app.config['TEMPLATES_AUTO_RELOAD'] = True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=5000)
