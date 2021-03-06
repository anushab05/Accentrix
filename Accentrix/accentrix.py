import warnings
warnings.filterwarnings("ignore")
import logging
logging.getLogger('tensorflow').disabled = True # Disabling TensorFlow warnings

import os
import numpy as np

from tensorflow.python.keras.models import load_model

import matplotlib.pyplot as plt
import librosa.display
import base64
import numpy as np
import pickle as pkl

import scipy.io.wavfile as wav
from python_speech_features import mfcc

num_mfcc_coeffs = 25

converter_model_name = "converter.h5"

classifier_model_name = "classifier.h5"

converter_model = None
classifier_model = None

try : 
    converter_model = load_model("./Accentrix/final_models/" + converter_model_name)
    classifier_model = load_model("./Accentrix/final_models/" + classifier_model_name)
    with open("./Accentrix/final_models/s_func",'rb') as f1:
  	    scaler = pkl.load(f1)
except:
	print("Some error")


def preprocess_single_file(num_mfcc_coeffs, audio_file):

    """
    FastDTW is not required, as we're not trying to align source and target frames, we're just predicting
    """

    source_sample_rate, source_wav_data = None, None
    
    try:
        (source_sample_rate, source_wav_data) = wav.read(audio_file)
    except:
        raise("Can't open file")

    source_mfcc_features = np.array(mfcc(source_wav_data, samplerate=source_sample_rate, numcep=num_mfcc_coeffs))

    return source_mfcc_features





# Used by server to interface with the models.


def classify(mfcc_vectors):

    mfcc_vectors = np.array(mfcc_vectors).reshape((-1, 25))
    mfcc_vectors = scaler.transform(mfcc_vectors)
    #print("Hello")
    prediction = classifier_model.predict(x = mfcc_vectors)
    print("Hello")
    avg_pred_across_frames = np.mean(prediction,axis=0)
    return (avg_pred_across_frames[0]*100, (1-avg_pred_across_frames[0])*100)




def convert(mfcc_vectors):
        
    mfcc_vectors = np.reshape(mfcc_vectors, [-1, 25])
    converted = converter_model.predict(x = mfcc_vectors)
    converted = np.reshape(converted, [-1,25])

    return converted





def validate_classify_before_converting():
    # Based on data from demo_and_validate.py
    return (3.6373, 96.3627)



def validate_classify_after_converting():
    # Based on data from demo_and_validate.py
    return (95.9841, 4.0159)



def get_results(audio_name, from_accent, to_accent):

    # classifier returns a tuple with 2 indices, first indice is % of being to_accent, second indice is % of being from_accent

    inputs = None
    try:
        inputs = list(preprocess_single_file(num_mfcc_coeffs, audio_name))
    except:
        raise Exception("Could not process audio file, are you sure the audio file was WAV, mono channel, PCM 16 KHz at 16 bits per sample?")

    classification_before_conversion = classify(inputs)

    plt.plot()
    plt.title("MFCC Spectrogram before conversion")
    librosa.display.specshow(np.array(inputs), sr=16000, x_axis='time',hop_length=160)
    plt.savefig("./Accentrix/mfcc_graphs/before.png")

    converted = convert(inputs)

    classification_after_conversion = classify(converted)

    plt.plot()
    plt.title("MFCC Spectrogram after conversion")
    librosa.display.specshow(np.array(converted), sr=16000, x_axis='time',hop_length=160)
    plt.savefig("./Accentrix/mfcc_graphs/after.png")

    with open("./Accentrix/mfcc_graphs/before.png", "rb") as img_file:
        before_image_string = base64.b64encode(img_file.read())

    with open("./Accentrix/mfcc_graphs/after.png", "rb") as img_file:
        after_image_string = base64.b64encode(img_file.read())

    with open("./Accentrix/training_graphs/model_acc-1.png", "rb") as img_file:
        classifier1 = base64.b64encode(img_file.read())

    with open("./Accentrix/training_graphs/model_loss-1.png", "rb") as img_file:
        classifier2 = base64.b64encode(img_file.read())

    with open("./Accentrix/training_graphs/tanh-adam-0-bias-normalised-input-FINAL_1.png", "rb") as img_file:
        converter1 = base64.b64encode(img_file.read())

    with open("./Accentrix/training_graphs/tanh-adam-0-bias-normalised-input-FINAL_2.png", "rb") as img_file:
        converter2 = base64.b64encode(img_file.read())
    


    cbc=""
    cac=""
    mcbc=""
    mcac=""

    if classification_before_conversion[0] > classification_before_conversion[1]:
        cbc = to_accent  + " with a probability of " + str(round(classification_before_conversion[0], 4)) + " %"
    else:
        cbc = from_accent  + " with a probability of " + str(round(classification_before_conversion[1], 4)) + " %"

    if classification_after_conversion[0] > classification_after_conversion[1]:
        cac = to_accent  + " with a probability of " + str(round(classification_after_conversion[0], 4)) + " %"
    else:
        cac = from_accent  + " with a probability of " + str(round(classification_after_conversion[1], 4)) + " %"

    mcbc_tup = validate_classify_before_converting()
    mcac_tup = validate_classify_after_converting()

    if mcbc_tup[0] > mcbc_tup[1]:
        mcbc = to_accent  + " with a probability of " + str(mcbc_tup[0]) + " %"
    else:
        mcbc = from_accent  + " with a probability of " + str(mcbc_tup[1]) + " %"

    if mcac_tup[0] > mcac_tup[1]:
        mcac = to_accent  + " with a probability of " + str(mcac_tup[0]) + " %"
    else:
        mcac = from_accent  + " with a probability of " + str(mcac_tup[1]) + " %"

    results_dict = {'mfcc_input': before_image_string, 'mfcc_output': after_image_string, 'cbc': cbc, 'cac': cac, 'mcbc': mcbc, 'mcac': mcac, 'mcaoc': "97.26 %", 'ca': "95.4638 %", 'classifier1': classifier1, 'classifier2': classifier2, 'converter1': converter1, 'converter2': converter2 }

    return results_dict
