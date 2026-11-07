import pandas as pd
import os

from slang_extra_terms import EXTRA_SLANG

def generate_slang_dataset():
    print("Generating Local Tourism Glossary...")
    
    slang_data = [
        # Dining
        {"term": "kade", "english_translation": "A small local shop or stall, often selling food, tea, or daily groceries.", "category": "Dining", "icon": "🍽️"},
        {"term": "kottu", "english_translation": "A popular Sri Lankan street food dish made of chopped flatbread (roti), vegetables, egg, and meat.", "category": "Dining", "icon": "🍽️"},
        {"term": "hopper", "english_translation": "A bowl-shaped crispy pancake made from fermented rice flour and coconut milk, locally called 'aappa'.", "category": "Dining", "icon": "🍽️"},
        {"term": "string hoppers", "english_translation": "Steamed rice-flour noodles (idi appa) often eaten with curry and coconut sambol for breakfast or dinner.", "category": "Dining", "icon": "🍽️"},
        {"term": "bites", "english_translation": "Spicy snacks, such as deviled cashews or fried chickpeas, traditionally eaten while drinking.", "category": "Dining", "icon": "🍽️"},
        {"term": "arrack", "english_translation": "A traditional Sri Lankan alcoholic spirit distilled from the fermented sap of the coconut flower.", "category": "Dining", "icon": "🥥"},
        {"term": "rice and curry", "english_translation": "The everyday Sri Lankan meal: steamed rice with several vegetable and/or meat curries, dhal, and sambols.", "category": "Dining", "icon": "🍛"},
        {"term": "pol sambol", "english_translation": "A spicy coconut relish with chilli, onion, lime, and often Maldive fish, served with rice or hoppers.", "category": "Dining", "icon": "🌶️"},
        {"term": "roti", "english_translation": "Flatbread made from wheat flour; used for wraps, eaten with curry, or chopped into kottu.", "category": "Dining", "icon": "🫓"},
        {"term": "lamprais", "english_translation": "A Dutch Burgher specialty: rice, curry, and sides baked together in a banana leaf.", "category": "Dining", "icon": "🍃"},
        {"term": "short eats", "english_translation": "Savory snacks such as fish buns, rolls, cutlets, and patties sold at bakeries and tea shops.", "category": "Dining", "icon": "🥟"},
        {"term": "fish bun", "english_translation": "A soft bun filled with spiced fish or potato mixture; a classic bakery short eat.", "category": "Dining", "icon": "🐟"},
        {"term": "wattalapam", "english_translation": "A steamed coconut-milk and jaggery pudding with cardamom and cashews, popular at celebrations.", "category": "Dining", "icon": "🍮"},
        {"term": "curd and treacle", "english_translation": "Buffalo curd served with kitul palm treacle; a classic dessert especially in the south and hill country.", "category": "Dining", "icon": "🍯"},
        {"term": "king coconut", "english_translation": "Orange-hued thambili coconut sold roadside for refreshing natural water; cheaper and safer than packaged drinks.", "category": "Dining", "icon": "🥥"},
        {"term": "thambili", "english_translation": "Sinhala name for king coconut; ask vendors to cut it open and drink with a straw.", "category": "Dining", "icon": "🥥"},
        {"term": "plain tea", "english_translation": "Black tea without milk, often strong and sweet; the default roadside tea-shop order.", "category": "Dining", "icon": "🍵"},
        {"term": "milk tea", "english_translation": "Strong black tea boiled with milk and sugar; the everyday cafe drink across Sri Lanka.", "category": "Dining", "icon": "🍵"},
        {"term": "devilled", "english_translation": "A spicy stir-fry style (chicken, fish, prawns, cashews) with chilli, onion, and tomato.", "category": "Dining", "icon": "🌶️"},
        {"term": "ambul thiyal", "english_translation": "Sour fish curry from the south, cooked with goraka (garcinia) for a tangy, long-keeping flavor.", "category": "Dining", "icon": "🐟"},
        {"term": "kotthu", "english_translation": "Common alternate spelling of kottu; same chopped-roti street food dish.", "category": "Dining", "icon": "🍽️"},

        # Transport
        {"term": "tuk-tuk", "english_translation": "A three-wheeled motorized vehicle used as a ubiquitous local taxi.", "category": "Transport", "icon": "🛺"},
        {"term": "three-wheeler", "english_translation": "Another common English term used locally for a tuk-tuk.", "category": "Transport", "icon": "🛺"},
        {"term": "meter", "english_translation": "Ask for a metered tuk-tuk fare when available; otherwise negotiate the price before boarding.", "category": "Transport", "icon": "🧾"},
        {"term": "Grab", "english_translation": "Popular ride-hailing app in Sri Lanka for cars and tuk-tuks; useful for transparent pricing in cities.", "category": "Transport", "icon": "📱"},
        {"term": "PickMe", "english_translation": "Local Sri Lankan ride-hailing app widely used for tuk-tuks, cars, and food delivery.", "category": "Transport", "icon": "📱"},
        {"term": "CTB", "english_translation": "Sri Lanka Transport Board public buses; cheap and frequent but often crowded.", "category": "Transport", "icon": "🚌"},
        {"term": "private bus", "english_translation": "Privately operated intercity or city buses; usually faster than CTB but can drive aggressively.", "category": "Transport", "icon": "🚌"},
        {"term": "train", "english_translation": "Scenic rail travel is popular (especially hill country); reserve seats early for Kandy–Ella routes.", "category": "Transport", "icon": "🚆"},
        {"term": "observation car", "english_translation": "Special train carriage with better views on scenic routes; tickets sell out quickly in peak season.", "category": "Transport", "icon": "🚆"},
        {"term": "coastal line", "english_translation": "The railway running south from Colombo along the coast toward Galle and Matara.", "category": "Transport", "icon": "🌊"},
        {"term": "upcountry train", "english_translation": "Hill-country rail journeys through tea estates toward Nanu Oya, Ella, and Badulla.", "category": "Transport", "icon": "🏞️"},

        # Culture & greetings
        {"term": "poya", "english_translation": "A Buddhist public holiday in Sri Lanka that occurs every full moon; alcohol and meat are typically not sold.", "category": "Culture", "icon": "🌕"},
        {"term": "machan", "english_translation": "A friendly informal term meaning 'mate' or 'brother', commonly used to address male friends.", "category": "Greeting", "icon": "👋"},
        {"term": "ayubowan", "english_translation": "Traditional Sinhala greeting meaning 'may you live long'; often said with palms pressed together.", "category": "Greeting", "icon": "🙏"},
        {"term": "vanakkam", "english_translation": "Traditional Tamil greeting; widely used especially in the north and east.", "category": "Greeting", "icon": "🙏"},
        {"term": "bo tree", "english_translation": "Sacred fig tree associated with the Buddha; many temples have a venerated bo tree.", "category": "Culture", "icon": "🌳"},
        {"term": "dagoba", "english_translation": "A Buddhist stupa or dome-shaped shrine; remove shoes and hats when visiting temple grounds.", "category": "Culture", "icon": "🛕"},
        {"term": "kovil", "english_translation": "A Hindu temple; dress modestly and follow local customs around footwear and photography.", "category": "Culture", "icon": "🛕"},
        {"term": "kovil festival", "english_translation": "Colorful Hindu temple festivals with processions, music, and offerings; major ones draw large crowds.", "category": "Culture", "icon": "🎉"},
        {"term": "perahera", "english_translation": "A traditional procession, most famously the Esala Perahera in Kandy with elephants, dancers, and drums.", "category": "Culture", "icon": "🐘"},
        {"term": "pirith", "english_translation": "Buddhist chanting for blessings; you may hear it overnight near temples or homes.", "category": "Culture", "icon": "🕉️"},
        {"term": "wesak", "english_translation": "Major Buddhist festival celebrating the Buddha's birth, enlightenment, and death; lanterns and free food stalls appear.", "category": "Culture", "icon": "🪔"},
        {"term": "dansal", "english_translation": "Free food or drink stalls set up during Wesak and other festivals as acts of generosity.", "category": "Culture", "icon": "🍲"},
        {"term": "saree", "english_translation": "Traditional women's attire; the Kandyan osariya style is distinctive to Sri Lanka.", "category": "Culture", "icon": "👗"},
        {"term": "sarong", "english_translation": "Wrapped cloth garment commonly worn by men, especially in temples, homes, and coastal areas.", "category": "Culture", "icon": "👔"},

        # Places & nature
        {"term": "tank", "english_translation": "An ancient man-made reservoir (wewa) common in the dry zone; scenic at sunset and important for irrigation.", "category": "Nature", "icon": "🏞️"},
        {"term": "wewa", "english_translation": "Sinhala word for a reservoir or tank; often good birdwatching spots.", "category": "Nature", "icon": "🐦"},
        {"term": "tea estate", "english_translation": "Hill-country plantations producing Ceylon tea; many offer factory tours and tastings.", "category": "Nature", "icon": "🍃"},
        {"term": "plucker", "english_translation": "Tea plantation worker who harvests tea leaves by hand on steep slopes.", "category": "Nature", "icon": "👩‍🌾"},
        {"term": "leech socks", "english_translation": "Protective socks recommended for rainforest walks (e.g. Sinharaja) during wet conditions.", "category": "Nature", "icon": "🧦"},
        {"term": "safari jeep", "english_translation": "Open 4x4 used for wildlife parks such as Yala, Wilpattu, Udawalawe, and Minneriya.", "category": "Nature", "icon": "🚙"},
        {"term": "gathering", "english_translation": "The Minneriya/Kaudulla elephant gathering in the dry season when herds congregate near water.", "category": "Nature", "icon": "🐘"},
        {"term": "coral sanctuary", "english_translation": "Snorkel sites such as Hikkaduwa or Polhena; use reef-safe practices and check sea conditions.", "category": "Nature", "icon": "🐠"},
        {"term": "whale watching", "english_translation": "Seasonal boat tours from Mirissa or Trincomalee for blue whales and dolphins.", "category": "Nature", "icon": "🐋"},
        {"term": "Adam's Peak", "english_translation": "Sacred mountain (Sri Pada) climbed overnight for sunrise; busy in pilgrimage season.", "category": "Nature", "icon": "⛰️"},
        {"term": "Sri Pada", "english_translation": "Sinhala name for Adam's Peak; pilgrims of multiple faiths climb to the summit footprint shrine.", "category": "Nature", "icon": "⛰️"},

        # Practical travel
        {"term": "guest house", "english_translation": "Small family-run lodging, often cheaper and more personal than hotels.", "category": "Stay", "icon": "🏠"},
        {"term": "homestay", "english_translation": "Lodging in a family home with meals; good for local food and conversation.", "category": "Stay", "icon": "🏡"},
        {"term": "rest house", "english_translation": "Government or older-style traveler lodging found in many towns; mixed quality but historic.", "category": "Stay", "icon": "🏨"},
        {"term": "LKR", "english_translation": "Sri Lankan Rupee; carry small notes for tuk-tuks, tea shops, and tips.", "category": "Practical", "icon": "💵"},
        {"term": "rupee", "english_translation": "Local currency (LKR). ATMs are common in cities; smaller towns may have limited cash access.", "category": "Practical", "icon": "💵"},
        {"term": "bargain", "english_translation": "Polite price negotiation is common for handicrafts and some tuk-tuk rides; stay friendly.", "category": "Practical", "icon": "🤝"},
        {"term": "cover up", "english_translation": "At temples, cover shoulders and knees; remove shoes and hats before entering shrine areas.", "category": "Practical", "icon": "👕"},
        {"term": "monsoon", "english_translation": "Seasonal rains vary by region: southwest monsoon roughly May–Sep; northeast around Oct–Jan.", "category": "Practical", "icon": "🌧️"},
        {"term": "intermonsoon", "english_translation": "Transitional weather periods that can bring thunderstorms; check local forecasts when island-hopping.", "category": "Practical", "icon": "⛈️"},
        {"term": "SIM", "english_translation": "Local prepaid mobile SIMs (Dialog, Mobitel, Airtel, Hutch) are easy to buy at the airport or city shops.", "category": "Practical", "icon": "📶"},
        {"term": "power cut", "english_translation": "Occasional electricity outages; hotels may have generators, so charge devices when you can.", "category": "Practical", "icon": "🔌"},
        {"term": "hot season", "english_translation": "Coastal heat peaks roughly March–May; plan midday indoor or beach shade breaks.", "category": "Practical", "icon": "☀️"},
        {"term": "hill country", "english_translation": "Cooler central highlands around Kandy, Nuwara Eliya, Ella, and Haputale; pack a light jacket.", "category": "Practical", "icon": "🧥"},
        {"term": "cultural triangle", "english_translation": "Historic region covering Anuradhapura, Polonnaruwa, Sigiriya, and Dambulla.", "category": "Practical", "icon": "🏛️"},
        {"term": "south coast", "english_translation": "Popular beach belt including Galle, Unawatuna, Mirissa, Weligama, and Matara.", "category": "Practical", "icon": "🏖️"},
        {"term": "east coast", "english_translation": "Beaches around Trincomalee, Passikudah, and Arugam Bay; best in the middle of the year for many spots.", "category": "Practical", "icon": "🏄"},
    ]

    slang_data.extend(EXTRA_SLANG)

    df = pd.DataFrame(slang_data)
    dupes = df["term"].str.lower().duplicated(keep=False)
    if dupes.any():
        dup_terms = sorted(df.loc[dupes, "term"].str.lower().unique())
        raise SystemExit(f"Duplicate terms found ({len(dup_terms)}): {dup_terms[:20]}")

    if len(EXTRA_SLANG) != 200:
        raise SystemExit(f"Expected 200 extra terms, got {len(EXTRA_SLANG)}")

    output_dir = os.path.join(os.path.dirname(__file__), "..", "processed_data")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "local_tourism_glossary.csv")
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Success! Saved {len(df)} terms ({len(EXTRA_SLANG)} newly added) to {output_path}")

if __name__ == "__main__":
    generate_slang_dataset()
