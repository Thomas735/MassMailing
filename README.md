# MassMailing (EnvoiMailMultiple)

Une application de bureau moderne développée en Python (avec CustomTkinter) qui permet de gérer l'envoi d'e-mails en masse, la création de modèles personnalisés, et le suivi actif des réponses via IMAP.

## Fonctionnalités Principales
- **Envois Personnalisés** : Utilisez des variables personnalisées (ex: `{Nom}`, `{Entreprise}`) injectées directement dans le corps de vos e-mails.
- **Gestion des Modèles (Templates)** : Créez, éditez et sauvez vos modèles (HTML) pour les réutiliser facilement à l'avenir.
- **Suivi et Historique** : Conservez une trace de vos actions (Brouillons, Envoyés, Échecs). Le tableau de bord de l'historique vous permet de filtrer vos correspondances.
- **Vérification des Réponses** : Le système se connecte à votre configuration IMAP pour détecter automatiquement si un prospect a répondu à votre e-mail d'origine.
- **Réponse Directe** : Lisez les réponses et ouvrez un module de rédaction rapide pour y répondre directement depuis l'interface du logiciel.
- **Système de Profils** : Sauvegardez et chargez différentes configurations SMTP/IMAP (comptes expéditeurs différents) via le gestionnaire de profils.

## Prérequis et Installation
Le projet utilise Python 3 et un environnement virtuel (`venv`) qui installe les dépendances nécessaires listées dans `requirements.txt` (notamment `customtkinter`).

## 🚀 Comment Lancer l'Application ?

Un "bouton" interactif a été créé pour simplifier le lancement sur Mac :
1. Cherchez le fichier **`Lancer.command`** dans ce dossier.
2. **Double-cliquez** dessus.
*(Cela va lancer automatiquement l'environnement virtuel en arrière-plan et ouvrir la fenêtre de l'application.)*

> **Note :** Si vous préférez le Terminal de façon classique, vous pouvez toujours utiliser le script `sh start_app.sh`.
