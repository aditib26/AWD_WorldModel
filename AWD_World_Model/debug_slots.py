from slot_extractor import SlotExtractor
from farm_state import FarmState

extractor = SlotExtractor()
state = FarmState()

test_sentences = [
    "18 cm using tube and heavy rain is coming",
    "the area of my field is 15ha",
    "I see cracks",
    "water level in my field is 20cm below soil surface my village is dublin"
]

print(f"{'Input Sentence':<60} | {'Extracted Updates'}")
print("-" * 100)

for sentence in test_sentences:
    updates = extractor.extract_all(sentence)
    print(f"{sentence:<60} | {updates}")
