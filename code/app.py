import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from functions import * # Remplacez par l'importation de votre bibliothèque ML et de votre modèle


import pandas as pd
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from PIL import Image
import cv2
import joblib

from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ImagePredictionApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Application d'Authentification")

        self.load_model_OG()  # Chargez votre modèle ici
        self.load_model_OD()  # Chargez votre modèle ici
        self.load_model_ODG()  # Chargez votre modèle ici

        self.encodeur_OD = joblib.load('./joblib/encodeur_OD.joblib')
        self.encodeur_OG = joblib.load('./joblib/encodeur_OG.joblib')
        self.encodeur_ODG = joblib.load('./joblib/encodeur_ODG.joblib')
   

        self.select_button = tk.Button(root, text="Sélectionner une image", command=self.load_image)
        self.select_button.pack()
        self.imagepath_label = tk.Label(root)
        self.imagepath_label.pack()
        self.imagedisp_label = tk.Label(root)
        self.imagedisp_label.pack()
        self.predict_button = tk.Button(root, text="Lancer la Prédiction", command=self.predict_image)
        self.predict_button.pack()
        
        font_=("Helvetica", 12)
        # Oeil droit ou gauche
        self.prediction_label = tk.Label(root, text="", font=font_)
        self.prediction_label.pack()
        # Quel utilisateur
        #  font=("Helvetica", 12)
        self.prediction_label_id = tk.Label(root, text="", font=font_)
        self.prediction_label_id.pack()
        self.prediction_label_name = tk.Label(root, text="", font=font_)
        self.prediction_label_name.pack()
        self.prediction_label_annee = tk.Label(root, text="", font=font_)
        self.prediction_label_annee.pack()
        self.prediction_label_genre = tk.Label(root, text="", font=font_)
        self.prediction_label_genre.pack()
        self.prediction_label_poste = tk.Label(root, text="", font=font_)
        self.prediction_label_poste.pack()

        # Créer un cadre pour le graphique
        self.chart_frame = ttk.Frame(root)
        self.chart_frame.pack(padx=10, pady=10)

        self.chart_canvas = None


    def load_model_OG(self):
        # Chargez votre modèle ici en utilisant votre bibliothèque ML
        self.model_OG = tf.keras.models.load_model('./OG_classif')
        self.model_OG.trainable = False

    def load_model_OD(self):
        # Chargez votre modèle ici en utilisant votre bibliothèque ML
        self.model_OD = tf.keras.models.load_model('./OD_classif')
        self.model_OD.trainable = False

    def load_model_ODG(self):
        # Chargez votre modèle ici en utilisant votre bibliothèque ML
        self.model_ODG = tf.keras.models.load_model('./ODG_classif')
        self.model_ODG.trainable = False

    def load_image(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.image = cv2.imread(file_path)
            self.image_prep=preprocess_img(self.image)  # Redimensionnez l'image pour l'affichage
            self.imagepath_label.config(text=f"Image : {file_path}")
            self.photo = ImageTk.PhotoImage(Image.open(file_path))
            self.imagedisp_label.config(image=self.photo)

    def affich_user(self,prediction_user):
        id_employe=prediction_user
        nom,annee_embauche,genre,poste = recherche_ID(prediction_user)
        self.prediction_label_id.config(text=f"ID : {id_employe}")
        self.prediction_label_name.config(text=f"Nom : {nom}")
        self.prediction_label_annee.config(text=f"Année d\'embauche : {annee_embauche}")
        self.prediction_label_genre.config(text=f"Genre : {genre}")
        self.prediction_label_poste.config(text=f"Poste : {poste}")
    

    def predict_image(self):
        if hasattr(self, 'image'):            
            # Prédiction pour determiner si oeil droit ou gauche
            detect_eye,fiabilite = detect_ODG(self.image_prep)
            
            if detect_eye == 0:
                self.prediction_label.config(text=f"Oeil droit scanné avec une fiabilité de {fiabilite}%\n")
                # Utlisiation du modele model_OG 
                probs = self.model_OD.predict(np.array([self.image_prep]))
                # Recherche de l'argument qui a la meilleure performance
                prediction_user = np.argmax(probs)
                # Inversion de l'encodage
                decode_prediction_user = self.encodeur_OD.inverse_transform([prediction_user])
                # Affichage 
                    # des caractéristiques
                self.affich_user(decode_prediction_user[0])
                    # Pour le graphique des probabilités
                self.draw_bar_chart(probs)

            else:
                self.prediction_label.config(text=f"Oeil gauche scanné avec une fiabilité de {fiabilite}%\n")
                probs = self.model_OG.predict(np.array([self.image_prep]))
                prediction_user = np.argmax(probs)
                decode_prediction_user = self.encodeur_OG.inverse_transform([prediction_user])
                self.affich_user(decode_prediction_user[0])
                self.draw_bar_chart(probs)
        else:
            self.prediction_label.config(text="Aucune image sélectionnée")

    def draw_bar_chart(self,probs):
        if self.chart_canvas is not None:
            self.chart_canvas.get_tk_widget().destroy()

        top_indices = np.argsort(probs[0])[-3:]
        id_1 = self.encodeur_OD.inverse_transform([top_indices[0]])
        id_2 = self.encodeur_OD.inverse_transform([top_indices[1]])
        id_3 = self.encodeur_OD.inverse_transform([top_indices[2]])
        fiabilite_id3= round(float(probs[0][top_indices[-1]]),4)*100
        fiabilite_id2= round(float(probs[0][top_indices[-2]]),4)*100
        fiabilite_id1= round(float(probs[0][top_indices[-3]]),4)*100
        data = {
            f'ID {id_3[0]}': fiabilite_id3,
            f'ID {id_2[0]}': fiabilite_id2,
            f'ID {id_1[0]}': fiabilite_id1,
        }
        
        categories = list(data.keys())
        values = list(data.values())
        
        # Créer une figure Matplotlib
        fig = Figure(figsize=(6, 4))
        ax = fig.add_subplot(111)
        bars = ax.bar(categories, values)
        ax.set_ylabel('Valeurs')
        ax.set_xlabel('ID des employés')
        ax.set_title("Probabilités d'identificaion")

        # Masquer la ligne du haut du cadre
        ax.spines['top'].set_visible(False)
        
        for bar in bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, yval + 2, round(yval, 2), ha='center', va='bottom')
        
        
        # Intégrer la figure Matplotlib dans Tkinter
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack()

if __name__ == "__main__":
    root = tk.Tk()
    root.configure() 
    app = ImagePredictionApp(root)
    root.mainloop()
