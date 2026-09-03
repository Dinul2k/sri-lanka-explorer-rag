import pandas as pd
import re
import os

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9\s.,!\'"-]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def sanitize_reviews(input_path, output_path):
    print(f"Loading raw data from {input_path}...")
    
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"❌ Error: Could not find {input_path}. Please upload it to the raw_data folder.")
        return

    text_column = 'Review'
    district_column = 'District'
    
    if text_column in df.columns and district_column in df.columns:
        df = df.dropna(subset=[text_column, district_column])
        
        # Filter strictly for the 11 accepted districts
        target_districts = ["colombo", "gampaha", "galle", "matara", "badulla", "kalutara", "hatton", "rathnapura", "kurunegala", "matale", "hambantota"]
        df = df[df[district_column].astype(str).str.lower().str.strip().isin(target_districts)]
    else:
        print(f"⚠️ Warning: Missing required columns. Ensure CSV has '{text_column}' and '{district_column}'.")
        return

    initial_count = len(df)
    
    df['cleaned_review'] = df[text_column].apply(clean_text)
    df['word_count'] = df['cleaned_review'].apply(lambda x: len(x.split()))
    df = df[df['word_count'] >= 10]

    final_df = df[[district_column, 'cleaned_review']]
    final_df = final_df.rename(columns={district_column: 'district', 'cleaned_review': 'review_context'})

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False)
    
    final_count = len(final_df)
    print(f"✅ Success! Cleaned dataset saved to {output_path}. Kept {final_count} high-quality records.")

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__)
    input_file = os.path.join(base_dir, "..", "raw_data", "Destination Reviews (final).csv")
    output_file = os.path.join(base_dir, "..", "processed_data", "cleaned_reviews.csv")
    sanitize_reviews(input_file, output_file)
