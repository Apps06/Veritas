"""
Train Fakebuster CNN-LSTM Model
Downloads GloVe embeddings and trains the model on news dataset.
Based on: https://github.com/Shubhang-Kuber/Fakebuster
"""
import os
import numpy as np
import pandas as pd
import pickle
import urllib.request
import zipfile

def download_glove():
    """Download GloVe embeddings if not present"""
    glove_dir = os.path.join(os.path.dirname(__file__), 'model', 'glove')
    glove_file = os.path.join(glove_dir, 'glove.6B.50d.txt')
    
    if os.path.exists(glove_file):
        print("✓ GloVe embeddings already downloaded")
        return glove_file
    
    os.makedirs(glove_dir, exist_ok=True)
    zip_path = os.path.join(glove_dir, 'glove.6B.zip')
    
    print("Downloading GloVe embeddings (~862MB)... This may take a while.")
    url = "https://downloads.cs.stanford.edu/nlp/data/glove.6B.zip"
    
    try:
        urllib.request.urlretrieve(url, zip_path)
        print("Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extract('glove.6B.50d.txt', glove_dir)
        os.remove(zip_path)
        print("✓ GloVe embeddings ready")
        return glove_file
    except Exception as e:
        print(f"Error downloading GloVe: {e}")
        return None

def train_fakebuster():
    """Train the Fakebuster CNN-LSTM model"""
    import tensorflow as tf
    from sklearn import preprocessing
    from tensorflow.keras.preprocessing.text import Tokenizer
    from tensorflow.keras.preprocessing.sequence import pad_sequences
    
    # Config
    embedding_dim = 50
    max_length = 54
    padding_type = 'post'
    trunc_type = 'post'
    oov_tok = "<OOV>"
    training_size = 3000
    test_portion = 0.1
    
    # Download GloVe
    glove_file = download_glove()
    if not glove_file:
        print("Cannot train without GloVe embeddings")
        return
    
    # Load data
    data_path = os.path.join(os.path.dirname(__file__), 'news.csv')
    if not os.path.exists(data_path):
        print(f"Training data not found: {data_path}")
        print("Please download news.csv from https://github.com/Shubhang-Kuber/Fakebuster")
        return
    
    print("Loading training data...")
    data = pd.read_csv(data_path)
    
    # Clean data
    if 'Unnamed: 0' in data.columns:
        data = data.drop(['Unnamed: 0'], axis=1)
    
    # Encode labels
    le = preprocessing.LabelEncoder()
    le.fit(data['label'])
    data['label'] = le.transform(data['label'])
    
    # Prepare data
    title = data['title'].tolist()[:training_size]
    labels = data['label'].tolist()[:training_size]
    
    # Tokenize
    tokenizer = Tokenizer(oov_token=oov_tok)
    tokenizer.fit_on_texts(title)
    word_index = tokenizer.word_index
    vocab_size = len(word_index)
    
    sequences = tokenizer.texts_to_sequences(title)
    padded = pad_sequences(sequences, maxlen=max_length, padding=padding_type, truncating=trunc_type)
    
    # Split
    split = int(test_portion * training_size)
    training_sequences = np.array(padded[split:])
    test_sequences = np.array(padded[:split])
    training_labels = np.array(labels[split:])
    test_labels = np.array(labels[:split])
    
    # Load GloVe embeddings
    print("Loading GloVe embeddings...")
    embedding_index = {}
    with open(glove_file, 'r', encoding='utf-8') as f:
        for line in f:
            values = line.split()
            word = values[0]
            coefs = np.asarray(values[1:], dtype='float32')
            embedding_index[word] = coefs
    
    # Create embedding matrix
    embedding_matrix = np.zeros((vocab_size + 1, embedding_dim))
    for word, i in word_index.items():
        if i < vocab_size:
            embedding_vector = embedding_index.get(word)
            if embedding_vector is not None:
                embedding_matrix[i] = embedding_vector
    
    # Build model
    print("Building CNN-LSTM model...")
    model = tf.keras.Sequential([
        tf.keras.layers.Embedding(vocab_size + 1, embedding_dim, input_length=max_length,
                                  weights=[embedding_matrix], trainable=False),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Conv1D(64, 5, activation='relu'),
        tf.keras.layers.MaxPooling1D(pool_size=4),
        tf.keras.layers.LSTM(64),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
    model.summary()
    
    # Train
    print("\nTraining model (50 epochs)...")
    history = model.fit(
        training_sequences, training_labels,
        epochs=50,
        validation_data=(test_sequences, test_labels),
        verbose=2
    )
    
    # Save model and tokenizer
    model_dir = os.path.join(os.path.dirname(__file__), 'model')
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, 'fakebuster_model.h5')
    tokenizer_path = os.path.join(model_dir, 'fakebuster_tokenizer.pkl')
    
    model.save(model_path)
    with open(tokenizer_path, 'wb') as f:
        pickle.dump(tokenizer, f)
    
    print(f"\n✓ Model saved to {model_path}")
    print(f"✓ Tokenizer saved to {tokenizer_path}")
    print("\nFakebuster is now ready to use!")

if __name__ == "__main__":
    train_fakebuster()
