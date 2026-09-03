import pandas as pd
import os

def generate_slang_dataset():
    print("Generating Local Tourism Glossary...")
    
    slang_data = [
        {"term": "kade", "english_translation": "A small local shop or stall, often selling food, tea, or daily groceries.", "category": "Dining", "icon": "🍽️"},
        {"term": "kottu", "english_translation": "A popular Sri Lankan street food dish made of chopped flatbread (roti), vegetables, egg, and meat.", "category": "Dining", "icon": "🍽️"},
        {"term": "hopper", "english_translation": "A bowl-shaped crispy pancake made from fermented rice flour and coconut milk, locally called 'aappa'.", "category": "Dining", "icon": "🍽️"},
        {"term": "bites", "english_translation": "Spicy snacks, such as deviled cashews or fried chickpeas, traditionally eaten while drinking.", "category": "Dining", "icon": "🍽️"},
        {"term": "arrack", "english_translation": "A traditional Sri Lankan alcoholic spirit distilled from the fermented sap of the coconut flower.", "category": "Dining", "icon": "🥥"},
        {"term": "tuk-tuk", "english_translation": "A three-wheeled motorized vehicle used as a ubiquitous local taxi.", "category": "Transport", "icon": "🛺"},
        {"term": "three-wheeler", "english_translation": "Another common English term used locally for a tuk-tuk.", "category": "Transport", "icon": "🛺"},
        {"term": "poya", "english_translation": "A Buddhist public holiday in Sri Lanka that occurs every full moon; alcohol and meat are typically not sold.", "category": "Culture", "icon": "🌕"},
        {"term": "machan", "english_translation": "A friendly informal term meaning 'mate' or 'brother', commonly used to address male friends.", "category": "Greeting", "icon": "👋"}
    ]

    df = pd.DataFrame(slang_data)
    
    output_dir = os.path.join(os.path.dirname(__file__), "..", "processed_data")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "local_tourism_glossary.csv")
    df.to_csv(output_path, index=False)
    print(f"✅ Success! Saved to {output_path}")

if __name__ == "__main__":
    generate_slang_dataset()
