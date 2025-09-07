import socket  
import time  
import os     # Module pour interagir avec le système de fichiers (ex. : extraire l'extension)
import hashlib  # Module pour calculer le checksum (MD5) des données

# Configuration globale
SERVER_IP = None  # Adresse IP du serveur, initialisée à None jusqu'à la commande 'open'
PORT_SERVEUR = 2212  # Port sur lequel le serveur écoute
TAILLE_MORCEAU_DEFAUT = 8 * 1024  # Taille par défaut d'un morceau de fichier (8 Ko)
MORCEAUX_MAX_DEFAUT = 5  # Nombre maximal de morceaux avant accusé de réception (non utilisé ici)
DELAI_ATTENTE = 3  # Délai d'attente en secondes pour les réponses du serveur
TAILLE_TAMPON = TAILLE_MORCEAU_DEFAUT + 1024  # Taille du tampon pour recevoir les données (8 Ko + marge)
MAX_REEXPEDITIONS = 3  # Nombre maximal de tentatives de réexpédition en cas d'erreur

# Fonction pour calculer le checksum (empreinte MD5) des données
def calculer_checksum(fichier_data):
    return hashlib.md5(fichier_data).hexdigest()  # Retourne une chaîne hexadécimale du hash MD5

# Fonction pour recevoir un fichier du serveur
def recevoir_fichier(sock, nom_fichier_destination, adresse_serveur):
    # Réception du premier message du serveur
    donnees, _ = sock.recvfrom(TAILLE_TAMPON)
    if donnees.startswith(b"Erreur"):  # Vérifie si le serveur renvoie une erreur
        print(donnees.decode())  # Affiche le message d'erreur
        return False  
    elif donnees == b"FIN":  # Cas où le fichier est vide
        print("\nFichier vide ou non existant")
        return False  

    fichier_data = bytearray()  #pour stocker les données reçues sous forme de tableau d'octets
    while True:  
        if donnees.startswith(b"DONNEES"):  
            try:
                # Séparation de l'en-tête des données réelles
                entete, donnees_fichier = donnees.split(b" ", 2)[0:2], donnees.split(b" ", 2)[2]
                num_morceau = entete[1].decode()  # Extrait le numéro du morceau (ex. "0/3")
                print(f"\n\u2705 Morceau reçu : {num_morceau}")  
                fichier_data.extend(donnees_fichier)  # Ajoute les données au tableau
                sock.sendto(f"ACK {num_morceau}".encode(), adresse_serveur) # Envoie de l'accusé de réception (ACK) au serveur
                print(f"\u27A1\uFE0F ACK envoyé pour le morceau {num_morceau}")
            except Exception as e:  
                print(f"Erreur lors du traitement du morceau: {e}")
                return False  
        elif donnees.startswith(b"FIN"):  # Si le serveur indique la fin du transfert
            checksum_serveur = donnees.decode().split()[1]  #  checksum envoyé par le serveur
            print(f"\nChecksum reçu du serveur :    {checksum_serveur}")
            break  
        else:  
            print(f"Message inattendu: {donnees}")
            return False  #
        donnees, _ = sock.recvfrom(TAILLE_TAMPON)  # Reçoit le prochain message

    
    checksum_client = calculer_checksum(fichier_data)
    print(f"Checksum calculé localement :    {checksum_client}")

     
    if checksum_client == checksum_serveur:  #Verifiaction des checksums       
        with open(nom_fichier_destination, 'wb') as f:
            f.write(fichier_data)
        print(f"\nFichier reçu avec succès et enregistré sous le nom '{nom_fichier_destination}'")
        sock.sendto("OK".encode(), adresse_serveur)  # Envoie "OK" pour valider le transfert 
        return True 
    else:
        print("Erreur : Les checksums ne correspondent pas. Demande de réexpédition.")
        sock.sendto("RETRY".encode(), adresse_serveur)  # on ressaie en demandant un nouvel envoi
        return False 

# Fonction principale du client
def main():
    global SERVER_IP 
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  

    while True:  
        commande = input("\nEntrez une commande :> ").strip()  
        
        if commande.startswith('open '):    #Commande open pour etablir une connexion aevc le serveur
            SERVER_IP = commande.split()[1]  # Extrait l'adresse IP du serveur
            adresse_serveur = (SERVER_IP, PORT_SERVEUR)  # Crée un tuple (IP, port)
            print(f"\nConnexion au serveur {SERVER_IP}...")
            sock.sendto(f"open {SERVER_IP}".encode(), adresse_serveur)  # Envoie la commande d'ouverture
            donnees, _ = sock.recvfrom(TAILLE_TAMPON)  # Reçoit la réponse du serveur
            if donnees.startswith(b"POIGNEE_DE_MAIN"):  # Vérifie si c'est une poignée de main
                _, taille_morceau, taille_fenetre = donnees.decode().split()  # Extrait les paramètres
                taille_morceau = int(taille_morceau)  # Convertit en entier
                taille_fenetre = int(taille_fenetre)
                print(f"Poignée de main : Taille Morceau = {taille_morceau}, Taille de la fenêtre = {taille_fenetre}")              
                sock.sendto(f"POIGNEE_DE_MAIN {taille_morceau} {taille_fenetre}".encode(), adresse_serveur) # Confirmation de la poignée de main au serveur
                donnees, _ = sock.recvfrom(TAILLE_TAMPON)  # Reçoit la confirmation finale
                print(donnees.decode())  # Affiche "Connecté"

        # Si la connexion est établie, il traite les autres commandes
        elif SERVER_IP is not None:
            adresse_serveur = (SERVER_IP, PORT_SERVEUR)  # Définit l'adresse du serveur
            sock.sendto(commande.encode(), adresse_serveur)  # Envoie la commande au serveur

            if commande == 'ls':  # Commande pour lister les fichiers
                donnees, _ = sock.recvfrom(TAILLE_TAMPON)  # Reçoit la liste des fichiers
                print("\nFichiers :", donnees.decode())  # Affiche la liste

            elif commande.startswith('get'):  # Commande pour télécharger un fichier
                nom_fichier_original = commande.split()[1]  # Extrait le nom du fichier demandé
                _, extension = os.path.splitext(nom_fichier_original)  # Récupère l'extension
                nom_fichier_destination = f"fichierRecu{extension}"  # Définit le nom du fichier reçu
                print(f"\nTéléchargement de {nom_fichier_original} vers {nom_fichier_destination}")

                tentatives = 0  # Compteur de tentatives de réexpédition
                while tentatives < MAX_REEXPEDITIONS:  # Boucle avec limite de réexpéditions
                    if recevoir_fichier(sock, nom_fichier_destination, adresse_serveur):
                        break  # Si le fichier est reçu avec succès, sort de la boucle
                    print(f"\nTentative {tentatives + 1}/{MAX_REEXPEDITIONS} échouée. Réexpédition en cours...")
                    tentatives += 1  # Incrémente le compteur
                    sock.sendto(commande.encode(), adresse_serveur)  # Redemande le fichier
                else:  # Si la limite est atteinte sans succès
                    print(f"\nÉchec du transfert après {MAX_REEXPEDITIONS} tentatives. Abandon.")

            
            elif commande == 'bye':
                print("Demande de fermeture de la connexion...")
                sock.sendto("bye".encode(), adresse_serveur)  # Envoie 'bye' au serveur
                sock.settimeout(DELAI_ATTENTE)  # Ajoute un timeout pour attendre la réponse
                try:
                    donnees, _ = sock.recvfrom(TAILLE_TAMPON)  # Attend la confirmation du serveur
                    print(donnees.decode())  # Affiche "Au revoir" ou autre réponse
                except socket.timeout:
                    print("Aucune réponse du serveur, fermeture forcée.")
                finally:
                    sock.close()  # Ferme le socket
                    print("Connexion terminée, client arrêté.")
                    return  # Quitte la fonction main(), terminant le programme

        else:  # Si aucune connexion n'est établie
            print("\nVeuillez d'abord ouvrir une connexion avec un serveur en utilisant la commande 'open adresse_ip'.")

# Point d'entrée du programme
if __name__ == "__main__":
    main()  # Lance la fonction principale