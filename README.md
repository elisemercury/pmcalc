# Precious Metals Portfolio Value Calculator

A Streamlit application that fetches real-time prices of precious metals and calculates the total portfolio value.

## Features

- **Auto-calculates on page load** - Portfolio value is calculated immediately when you open the app
- **Recalculate on demand** - Click the button to fetch fresh prices
- Fetches current prices from ankauf.goldvorsorge.at
- Calculates total portfolio value based on quantities and current prices
- Displays breakdown table with:
  - Name of precious metal
  - Quantity held
  - Current price (€)
  - Subtotal value (€)
  - **Link column** - Click "View Source" to see the original price page
- Shows loading spinner while fetching prices

## Portfolio Items

- 1oz Gold Kangaroo (Quantity: 13)
- 100g Gold Bar (Quantity: 3)
- 20g Gold Bar (Quantity: 9)
- 1kg Silver Kookaburra Coin (Quantity: 3)
- 1oz Silver Kangaroo (Quantity: 655)
- 1oz Palladium Bar (Quantity: 1)

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the app:
```bash
streamlit run streamlit_app.py
```

3. The app will automatically open in your browser at `http://localhost:8501`

**Note:** Make sure to run the app using the `streamlit run` command, not `python streamlit_app.py`

## Deploy to Streamlit Community Cloud

1. Create a new repository on GitHub
2. Upload these files:
   - `streamlit_app.py`
   - `requirements.txt`
   - `README.md` (optional)

3. Go to [share.streamlit.io](https://share.streamlit.io)
4. Sign in with GitHub
5. Click "New app"
6. Select your repository
7. Set main file path to `streamlit_app.py`
8. Click "Deploy"

Your app will be live at: `https://[your-app-name].streamlit.app`

## File Structure

```
.
├── streamlit_app.py      # Main application file
├── requirements.txt      # Python dependencies
└── README.md            # This file
```
