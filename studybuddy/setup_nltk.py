"""
setup_nltk.py
-------------
Run this once after `pip install -r requirements.txt`:
    python setup_nltk.py
"""
import nltk

PACKAGES = [
    "punkt",
    "punkt_tab",
    "averaged_perceptron_tagger",
    "averaged_perceptron_tagger_eng",
    "stopwords",
    "wordnet",
]

for pkg in PACKAGES:
    print(f"Downloading NLTK package: {pkg}")
    nltk.download(pkg)

print("Done. You can now run: python app.py")
