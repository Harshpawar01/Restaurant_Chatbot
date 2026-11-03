import re
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SmartBite AI Restaurant", page_icon="🍽️", layout="wide")

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "restaurant_menu.csv"

st.markdown("""
<style>
.main {background: #fffaf5;}
[data-testid="stChatMessage"] {border-radius: 14px;}
.dish-card {padding: 10px; border: 1px solid #eee; border-radius: 14px;}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_menu():
    df = pd.read_csv(DATA_FILE)
    for c in ["Dish_Name", "Cuisine", "Veg_NonVeg", "Image_URL"]:
        if c not in df: df[c] = ""
        df[c] = df[c].fillna("").astype(str)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    return df

df = load_menu()
menu = df.drop_duplicates("Dish_Name").copy()

def dish_image(row):
    url = str(row.get("Image_URL", "")).strip()
    if not url or url.lower() == "nan":
        url = "https://loremflickr.com/640/420/" + str(row["Dish_Name"]).replace(" ", ",") + ",food"
    return url

def show_dishes(items, limit=6):
    items = items.drop_duplicates("Dish_Name").head(limit)
    if items.empty:
        st.info("I couldn't find a matching dish. Try another name or ask to see the menu.")
        return
    cols = st.columns(3)
    for i, (_, d) in enumerate(items.iterrows()):
        with cols[i % 3]:
            st.image(dish_image(d), use_container_width=True, caption=d["Dish_Name"])
            st.markdown(f"**{d['Dish_Name']}**")
            price = f"₹{d['Price']:.0f}" if pd.notna(d["Price"]) else "Price unavailable"
            rating = f"⭐ {d['Rating']:.1f}" if pd.notna(d["Rating"]) else "Rating unavailable"
            st.write(f"{price} · {rating}")
            st.caption(f"{d['Cuisine']} · {d['Veg_NonVeg']}")

def answer_chat(message):
    q = message.lower().strip()
    result = menu.copy()
    diet = None
    if any(x in q for x in ["non veg", "non-veg", "nonveg", "chicken", "meat"]):
        diet = "Non-Veg"
    elif any(x in q for x in ["veg", "vegetarian"]):
        diet = "Veg"
    if diet:
        result = result[result["Veg_NonVeg"].str.lower() == diet.lower()]

    budget = re.search(r"(?:under|below|less than|within|upto|up to)\s*₹?\s*(\d+)", q)
    if budget:
        result = result[result["Price"].isna() | (result["Price"] <= int(budget.group(1)))]

    dish_terms = [name for name in menu["Dish_Name"].unique()
                  if name.lower() in q or name.lower().replace(" ", "") in q.replace(" ", "")]
    if dish_terms:
        result = result[result["Dish_Name"].isin(dish_terms)]
        return f"Here are the menu details and photos for **{', '.join(dish_terms)}**:", result

    cuisine_terms = [c for c in menu["Cuisine"].dropna().unique()
                     if c and c.lower() in q]
    if cuisine_terms:
        result = result[result["Cuisine"].isin(cuisine_terms)]

    if any(x in q for x in ["recommend", "suggest", "popular", "best", "what should", "hungry"]):
        result = result.sort_values(["Rating", "Price"], ascending=[False, True], na_position="last")
        return "Here are some top-rated suggestions from our menu:", result

    if any(x in q for x in ["menu", "show", "all dish", "food", "what do you have", "list"]):
        result = result.sort_values("Dish_Name")
        return "Here are dishes available in the SmartBite menu:", result

    if any(x in q for x in ["book", "table", "reservation"]):
        return ("I can help with a table-booking request. Please use the **Table Booking** section "
                "in the sidebar to enter your details."), result.iloc[0:0]

    if diet or budget or cuisine_terms:
        return "These dishes match your preferences:", result.sort_values("Rating", ascending=False)
    return ("Hi! I'm SmartBite, your restaurant assistant. Ask me for the menu, vegetarian dishes, "
            "non-veg dishes, recommendations, or something like 'pizza under 300'."), result.iloc[0:0]

st.title("🍽️ SmartBite")
st.subheader("Your AI-style restaurant assistant")
st.caption("Explore the menu, see dish photos, get recommendations and place a demo order.")

with st.sidebar:
    st.header("🔎 Explore menu")
    search = st.text_input("Search dishes", placeholder="Pizza, paneer, biryani...")
    diet_filter = st.selectbox("Food preference", ["All", "Veg", "Non-Veg"])
    cuisine_filter = st.selectbox("Cuisine", ["All"] + sorted([x for x in menu["Cuisine"].unique() if x]))
    max_price = int(menu["Price"].max()) if menu["Price"].notna().any() else 1000
    budget_filter = st.slider("Maximum price (₹)", 0, max(500, max_price), max(500, max_price))
    st.divider()
    st.subheader("📅 Table Booking (Demo)")
    guest_name = st.text_input("Your name")
    guests = st.number_input("Number of guests", 1, 20, 2)
    booking_date = st.date_input("Date")
    booking_time = st.selectbox("Time", ["12:00 PM", "1:00 PM", "7:00 PM", "8:00 PM", "9:00 PM"])
    if st.button("Request table"):
        if guest_name.strip():
            st.success(f"Demo request received for {guest_name}, {guests} guest(s), {booking_date} at {booking_time}.")
        else:
            st.warning("Please enter your name.")

filtered = menu.copy()
if search.strip():
    filtered = filtered[filtered["Dish_Name"].str.contains(search.strip(), case=False, na=False)]
if diet_filter != "All":
    filtered = filtered[filtered["Veg_NonVeg"].str.lower() == diet_filter.lower()]
if cuisine_filter != "All":
    filtered = filtered[filtered["Cuisine"] == cuisine_filter]
filtered = filtered[filtered["Price"].isna() | (filtered["Price"] <= budget_filter)]

tab_chat, tab_menu, tab_cart = st.tabs(["💬 Chat with SmartBite", "🍴 Full Menu", "🛒 Your Cart"])

with tab_chat:
    st.markdown("Try: **Show veg dishes**, **Recommend something**, **Pizza under 300**, or **Show biryani**.")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [{
            "role": "assistant",
            "content": "Namaste! 👋 Welcome to SmartBite. What would you like to eat today?"
        }]
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("show"):
                show_dishes(msg["show"], limit=6)
    prompt = st.chat_input("Ask about dishes, prices, veg/non-veg or recommendations...")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        response, matches = answer_chat(prompt)
        st.session_state.chat_history.append({
            "role": "assistant", "content": response,
            "show": matches.head(6) if not matches.empty else None
        })
        st.rerun()

with tab_menu:
    st.subheader(f"Menu items ({len(filtered.drop_duplicates('Dish_Name'))})")
    show_dishes(filtered.sort_values("Dish_Name"), limit=60)

with tab_cart:
    st.subheader("Add items to your demo cart")
    choices = sorted(menu["Dish_Name"].unique().tolist())
    selected = st.selectbox("Choose a dish", choices)
    qty = st.number_input("Quantity", min_value=1, max_value=20, value=1)
    if st.button("Add to cart"):
        if "cart" not in st.session_state: st.session_state.cart = {}
        st.session_state.cart[selected] = st.session_state.cart.get(selected, 0) + int(qty)
        st.success(f"Added {qty} × {selected}")
    cart = st.session_state.get("cart", {})
    if cart:
        total = 0
        for name, quantity in cart.items():
            row = menu[menu["Dish_Name"] == name].iloc[0]
            price = float(row["Price"]) if pd.notna(row["Price"]) else 0
            total += price * quantity
            st.write(f"**{name}** × {quantity} — ₹{price * quantity:.0f}")
        st.markdown(f"### Total: ₹{total:.0f}")
        if st.button("Place demo order"):
            st.success("Your demo order has been placed! No payment is collected.")
            st.session_state.cart = {}
    else:
        st.info("Your cart is empty. Add a dish to get started.")

st.divider()
st.caption("Demo application. Dish photos are illustrative and loaded from an external image service; an internet connection is required.")
