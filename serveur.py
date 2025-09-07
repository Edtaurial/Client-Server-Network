import socket  
import os      
import random  
import time    
import hashlib  # Module pour calculer le checksum (MD5) des fichiers

ADRESSE_IP_SERVEUR = '127.0.0.1'    #localhost
PORT_SERVEUR = 2212  # Port utilisé par le serveur
TAILLE_MORCEAU_DEFAUT = 8 * 1024  # Taille par défaut d’un morceau de fichier (8 Ko)
TAILLE_FENETRE_DEFAUT = 5  # Taille par défaut de la fenêtre 
DELAI_ATTENTE = 3  # Délai d’attente en secondes pour recevoir un ACK ou une réponse
RETRY_MAX = 5  # Nombre maximal de tentatives pour envoyer un paquet
FIABILITE = 0.95  # Probabilité qu’un envoi réussisse : 95%

# Fonction pour simuler la fiabilité du réseau
def est_fiable():
    return random.random() < FIABILITE  # Retourne True si un nombre aléatoire est inférieur à FIABILITE, False sinon

# Fonction pour envoyer des données avec gestion des pertes simulées
def envoyer_donnees(sock, donnees, adresse):
    for _ in range(RETRY_MAX):  # Essaie jusqu’à RETRY_MAX fois
        if est_fiable():  # Si le réseau est "fiable" pour cette tentative
            sock.sendto(donnees, adresse)  # Envoie les données à l’adresse via le socket UDP
            return True  # Succès, sort de la fonction
    return False  # Échec après toutes les tentatives

# Fonction pour calculer le checksum (MD5) d’un fichier
def calculer_checksum(fichier_data):
    return hashlib.md5(fichier_data).hexdigest()  # Retourne une chaîne hexadécimale du hash MD5

# Fonction pour envoyer un fichier au client
def envoyer_fichier(sock, nom_fichier, addr):
    with open(nom_fichier, 'rb') as f:  # Ouvre le fichier en mode binaire
        donnees_fichier = f.read()  # Lit tout le contenu du fichier
        checksum = calculer_checksum(donnees_fichier)  # calcul du checksum
        print(f"Checksum calculé : {checksum}") 
        print(f"Taille du fichier : {len(donnees_fichier)} octets")  

        # Découpe le fichier en morceaux de taille TAILLE_MORCEAU_DEFAUT
        morceaux = [donnees_fichier[i:i + TAILLE_MORCEAU_DEFAUT] for i in range(0, len(donnees_fichier), TAILLE_MORCEAU_DEFAUT)]
        total_morceaux = len(morceaux)  
        print(f"Nombre total de morceaux : {total_morceaux}")  

        if total_morceaux == 0:  # Si le fichier est vide
            print("\nFichier vide, transfert terminé.")  
            envoyer_donnees(sock, "FIN".encode(), addr)  # Envoie un message FIN
            return True, checksum  

        tous_acquittes = True  # Indicateur que tous les morceaux ont été acquittés
        for i, morceau in enumerate(morceaux): 
            # Prépare le message avec un en-tête (ex. "DONNEES 0/3 ")
            morceau_avec_entete = f"DONNEES {i}/{total_morceaux} ".encode() + morceau
            print(f"\n\U0001F4E6 Envoi du morceau {i + 1}/{total_morceaux}")  # Affiche l’envoi du morceau

            # Code commenté pour simuler une corruption (optionnel)
            # if i == 1 and total_morceaux > 1:  # Si c’est le 2ème morceau et il y en a au moins 2
            #     morceau_corrompu = bytearray(morceau)  # Crée une copie modifiable du morceau
            #     morceau_corrompu[0] = (morceau_corrompu[0] + 1) % 256  # Modifie le premier octet
            #     morceau_avec_entete = f"DONNEES {i}/{total_morceaux} ".encode() + bytes(morceau_corrompu)
            #     print(f"\U0001F4A5 Simulation de corruption sur le morceau {i + 1}/{total_morceaux}")
            #     print(f"Données corrompues (premiers 10 octets) : {bytes(morceau_corrompu)[:10]}")
            # else:
            #     morceau_avec_entete = f"DONNEES {i}/{total_morceaux} ".encode() + morceau
            #     print(f"Données normales (premiers 10 octets) : {morceau[:10]}")

            ack_recu = False  
            for tentative in range(RETRY_MAX):  # Essaie d’envoyer le morceau jusqu’à RETRY_MAX fois
                if envoyer_donnees(sock, morceau_avec_entete, addr):  
                    sock.settimeout(DELAI_ATTENTE)  # Définit un délai pour attendre l’ACK
                    try:
                        ack, _ = sock.recvfrom(1024)  # Reçoit l’ACK du client
                        if ack.decode().startswith("ACK"):  # Vérifie si c’est un ACK valide
                            ack_recu = True
                            print(f"\u2705 ACK reçu pour le morceau {i + 1}")  
                            break 
                    except socket.timeout:  # Si le délai est dépassé
                        print(f"\nTimeout, réexpédition du morceau {i + 1} (tentative {tentative + 1})")
                else:  # Si l’envoi échoue à cause de la fiabilité
                    print(f"\nÉchec de l'envoi du morceau {i + 1} (tentative {tentative + 1})")

            if not ack_recu:  # Si aucun ACK n’a été reçu après toutes les tentatives
                print(f"\nÉchec du transfert après {RETRY_MAX} tentatives pour le morceau {i + 1}")
                tous_acquittes = False  # Marque le transfert comme échoué
                break  

        sock.settimeout(None)  # Réinitialise le timeout pour les opérations suivantes
        if tous_acquittes: 
            print("\nTransfert terminé avec succès, envoi de FIN avec checksum")
            envoyer_donnees(sock, f"FIN {checksum}".encode(), addr) 
        return tous_acquittes, checksum



def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    sock.bind((ADRESSE_IP_SERVEUR, PORT_SERVEUR)) 
    print(f"\nServeur en écoute sur {ADRESSE_IP_SERVEUR}:{PORT_SERVEUR}")  # Confirme le démarrage

    while True: 
        sock.settimeout(None)  # Pas de timeout pour attendre les commandes
        donnees, addr = sock.recvfrom(1024)  # Reçoit un message (max 1024 octets) et l’adresse du client
        commande = donnees.decode().split()  # Décode et découpe le message en liste
        print(f"\nCommande reçue de {addr}: {commande}")  
        
        if commande[0] == 'open':  # Commande pour ouvrir une connexion
            print(f"Connexion de {addr}")  # Affiche l’adresse du client

            envoyer_donnees(sock, f"POIGNEE_DE_MAIN {TAILLE_MORCEAU_DEFAUT} {TAILLE_FENETRE_DEFAUT}".encode(), addr)

        elif commande[0] == 'POIGNEE_DE_MAIN':  # Réponse à la poignée de main du client
            taille_morceau = int(commande[1])  # Extrait et convertit la taille des morceaux
            taille_fenetre = int(commande[2])  # Extrait et convertit la taille de la fenêtre
            print(f"\nPoignée de main terminée : Taille Morceau = {taille_morceau}, Taille de la fenêtre = {taille_fenetre}")
            envoyer_donnees(sock, "Connecté".encode(), addr)  

        elif commande[0] == 'ls':  # Commande pour lister les fichiers
            fichiers = os.listdir('.')  # Liste les fichiers dans le répertoire courant
            reponse = " ".join(fichiers)  # Concatène les noms en une chaîne
            envoyer_donnees(sock, reponse.encode(), addr)  # Envoie la liste au client

        elif commande[0] == 'get':  # Commande pour envoyer un fichier
            nom_fichier = commande[1]  # Extrait le nom du fichier demandé
            if os.path.exists(nom_fichier):  # Vérifie si le fichier existe
                print(f"\nFichier trouvé : {nom_fichier}")
                succes, checksum = envoyer_fichier(sock, nom_fichier, addr)  # Envoie le fichier
                if succes:  # Si le transfert a réussi
                    sock.settimeout(DELAI_ATTENTE)  # Définit un délai pour attendre la réponse
                    try:
                        reponse, _ = sock.recvfrom(1024)  # Reçoit la réponse du client
                        reponse_decoded = reponse.decode()
                        print(f"\nRéponse du client : {reponse_decoded}")
                        if reponse_decoded == "RETRY":  # Si le client demande une réexpédition
                            print("\nClient demande une réexpédition du fichier")
                            envoyer_fichier(sock, nom_fichier, addr)  # Renvoie le fichier
                        elif reponse_decoded == "OK":  # Si le client valide le transfert
                            print("\nTransfert validé par le client")
                    except socket.timeout:  # Si aucune réponse n’arrive
                        print("\nAucune réponse du client, transfert considéré comme terminé")
            else:  # Si le fichier n’existe pas
                print(f"\nFichier non trouvé : {nom_fichier}")
                envoyer_donnees(sock, "Erreur : Fichier non trouvé".encode(), addr)  
                
        elif commande[0] == 'bye':  # Commande pour terminer la connexion
            print(f"Déconnexion demandée par {addr}")  
            envoyer_donnees(sock, "Au revoir".encode(), addr)  
            print(f"Client {addr} déconnecté.")  # Confirme la déconnexion

        elif commande[0] == 'stop':  # Commande pour arrêter le serveur
            print("\nArrêt du serveur...")
            envoyer_donnees(sock, "Serveur en arrêt".encode(), addr)  # Informe le client
            break  # Sort de la boucle pour arrêter le serveur

    sock.close()  # Ferme le socket
    print("\nServeur arrêté.")  # Confirme l’arrêt

if __name__ == "__main__":
    main()  