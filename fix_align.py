"""Merge translations[61] and translations[62] into a single sentence
to align with sentences_final.json (which has 503 entries)."""
import json

with open("translations.json", "r", encoding="utf-8") as f:
    t = json.load(f)

print(f"Before: {len(t)} translations")

# Merge index 61 and 62
merged = "这在今天基本解决了，看这段视频的人大都不担心被吃掉或饿死。"
new_t = t[:61] + [merged] + t[63:]

print(f"After:  {len(new_t)} translations")

with open("translations.json", "w", encoding="utf-8") as f:
    json.dump(new_t, f, ensure_ascii=False, indent=2)

# Spot-check
print()
print("t[60]:", new_t[60])
print("t[61]:", new_t[61])
print("t[62]:", new_t[62])
print("t[63]:", new_t[63])
print("t[502]:", new_t[502])
