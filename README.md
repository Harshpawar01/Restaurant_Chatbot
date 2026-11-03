# SmartBite Restaurant Chatbot

A Streamlit restaurant assistant built from the supplied restaurant menu dataset.

## Features
- Chat-style food assistant
- Dish photos, prices, ratings, cuisine and Veg/Non-Veg labels
- Search and menu filters
- Budget-aware suggestions and top-rated recommendations
- Demo table booking request
- Demo cart and order placement

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Extract this ZIP and upload all files to a GitHub repository.
2. Open Streamlit Community Cloud and choose **New app**.
3. Select your repository and set the main file path to `app.py`.
4. Deploy.

## Images and demo limitations
Dish photos are loaded from LoremFlickr URLs, so the app needs internet access. Images are illustrative and may not exactly match the recipe. Table booking and checkout are simulations; no real booking, payment or restaurant order is submitted.
