# Client-Server-Network
Protocole de Transfert de Fichiers sur UDP

Ce dépôt contient une implémentation en Python d'un protocole de transfert de fichiers fiable utilisant UDP. Le système est composé de deux programmes principaux : un client (client.py) et un serveur (serveur.py), 
conçus pour transférer des fichiers avec gestion des erreurs, accusés de réception (ACK), réexpéditions et vérification d'intégrité via checksum MD5.





Fonctionnalités




Communication Client-Serveur : Établit une connexion via une poignée de main, prend en charge des commandes comme ls (lister les fichiers), get (télécharger un fichier) et bye (fermer la connexion).



Transfert UDP Fiable : Implémente la fiabilité sur UDP avec des ACK, des réexpéditions (jusqu'à 3 pour le client, 5 pour le serveur) et une simulation de fiabilité réseau à 95 %.



Intégrité des Fichiers : Utilise des checksums MD5 pour vérifier l'intégrité des fichiers, avec réexpédition en cas de non-concordance.



Fragmentation des Fichiers : Découpe les fichiers en morceaux de 8 Ko pour un transfert efficace.



Gestion des Erreurs : Gère les cas de fichier non trouvé, les délais d'attente et les pertes de paquets.





Utilisation


Lancer le serveur : python serveur.py

Lancer le client : python client.py

Commandes du client :





open <adresse_ip_serveur> : Se connecter au serveur.

ls : Lister les fichiers disponibles sur le serveur.

get <nom_fichier> : Télécharger un fichier.

bye : Fermer la connexion.





Limites



Gestion d'un seul client à la fois (pas de concurrence).

La taille de la fenêtre n'est pas utilisée (protocole de type "stop-and-wait").

Absence d'authentification ou de chiffrement.





Améliorations Possibles



Implémenter une fenêtre glissante pour améliorer le débit.

Ajouter la prise en charge de plusieurs clients avec des threads/asyncio.

Renforcer la sécurité avec authentification et chiffrement.

Supporter des noms de fichiers dynamiques et la compression.
