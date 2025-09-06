
import streamlit as st
from prod_assistant.etl.data_scrapper import FlipkartScraper
from prod_assistant.etl.data_ingestion import DataIngestion
import os

flipkart_scraper = FlipkartScraper()
output_path = "data/product_reviews.csv"
st.title("📦 Product Review Scraper")

if "product_inputs" not in st.session_state:
    st.session_state.product_inputs = [""]

def add_product_input():
    st.session_state.product_inputs.append("")

st.subheader("📝 Optional Product Description")
product_description = st.text_area("Enter product description (used as an extra search keyword):")

st.subheader("🛒 Product Names")
updated_inputs = []
for i, val in enumerate(st.session_state.product_inputs):
    input_val = st.text_input(f"Product {i+1}", value=val, key=f"product_{i}")
    updated_inputs.append(input_val)
st.session_state.product_inputs = updated_inputs

st.button("➕ Add Another Product", on_click=add_product_input)

max_products = st.number_input("How many products per search?", min_value=1, max_value=10, value=1)
review_count = st.number_input("How many reviews per product?", min_value=1, max_value=10, value=2)

if st.button("🚀 Start Scraping"):
    product_inputs = [p.strip() for p in st.session_state.product_inputs if p.strip()]
    if product_description.strip():
        product_inputs.append(product_description.strip())

    if not product_inputs:
        st.warning("⚠️ Please enter at least one product name or a product description.")
    else:
        final_data = []
        for query in product_inputs:
            st.write(f"🔍 Searching for: {query}")
            try:
                results = flipkart_scraper.scrape_flipkart_products(query, max_products=max_products, review_count=review_count)
                final_data.extend(results)
            except Exception as e:
                if "SessionNotCreatedException" in str(e):
                    st.error("❌ Scraping failed! Your Chrome browser version is incompatible with the ChromeDriver. Please update your Chrome browser to the latest version.")
                else:
                    st.error(f"❌ An error occurred during scraping: {e}")
                final_data = []
                break 

        if final_data:
            unique_products = {}
            for row in final_data:
                if len(row) > 0 and row[0] not in unique_products:
                    unique_products[row[0]] = row

            final_data = list(unique_products.values())
            st.session_state["scraped_data"] = final_data
            flipkart_scraper.save_to_csv(final_data, output_path)
            st.success("✅ Data saved to `data/product_reviews.csv`")
            if os.path.exists(output_path):
                with open(output_path, "rb") as file:
                    st.download_button("📥 Download CSV", data=file, file_name="product_reviews.csv")
            else:
                st.warning("Could not find the CSV file to download.")

if "scraped_data" in st.session_state and st.button("🧠 Store in Vector DB (AstraDB)"):
    with st.spinner("📡 Initializing ingestion pipeline..."):
        try:
            ingestion = DataIngestion()
            st.info("🚀 Running ingestion pipeline...")
            ingestion.run_pipeline()
            st.success("✅ Data successfully ingested to AstraDB!")
        except Exception as e:
            st.error("❌ Ingestion failed!")
            st.exception(e)

