import os
import tensorflow as tf
import keras
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

def create_model(input_shape):
    model = keras.Sequential([
        keras.Input(shape=input_shape),
        keras.layers.Dense(9, activation='relu'),
        keras.layers.Dense(9, activation='relu'),
        keras.layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'])
    return model