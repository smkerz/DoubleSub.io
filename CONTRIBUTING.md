# Contributing to DoubleSub.io

Merci de votre intérêt pour contribuer à DoubleSub.io! 🎉

## Comment Contribuer

### Signaler un Bug 🐛

1. Vérifiez que le bug n'a pas déjà été signalé dans les [Issues](https://github.com/votre-repo/issues)
2. Créez une nouvelle issue avec:
   - Titre clair et descriptif
   - Description détaillée du problème
   - Étapes pour reproduire
   - Comportement attendu vs comportement actuel
   - Captures d'écran si pertinent
   - Environnement (OS, navigateur, version Python)

### Proposer une Fonctionnalité 💡

1. Créez une issue avec le label "enhancement"
2. Décrivez la fonctionnalité souhaitée
3. Expliquez pourquoi elle serait utile
4. Proposez une implémentation si possible

### Soumettre du Code 🔧

1. **Fork** le projet
2. Créez une **branche** pour votre fonctionnalité:
   ```bash
   git checkout -b feature/ma-fonctionnalite
   ```
3. **Codez** en suivant les conventions ci-dessous
4. **Testez** vos modifications
5. **Commit** avec des messages clairs:
   ```bash
   git commit -m "Add: nouvelle fonctionnalité X"
   ```
6. **Push** vers votre fork:
   ```bash
   git push origin feature/ma-fonctionnalite
   ```
7. Créez une **Pull Request**

## Conventions de Code

### Python (Backend)

- **Style:** PEP 8
- **Docstrings:** Google style
- **Type hints:** Recommandés pour les fonctions publiques

Exemple:
```python
def merge_subtitles(srt1_path: str, srt2_path: str, mode: str = 'all') -> dict:
    """
    Fusionne deux fichiers SRT.

    Args:
        srt1_path: Chemin du premier fichier
        srt2_path: Chemin du second fichier
        mode: Mode de fusion ('all', 'overlapping', 'primary')

    Returns:
        Dictionnaire avec 'success' et 'cue_count'
    """
    pass
```

### JavaScript (Frontend)

- **Style:** Vanilla JS, pas de framework
- **Variables:** camelCase
- **Fonctions:** Noms descriptifs
- **Commentaires:** Pour la logique complexe

Exemple:
```javascript
function handleFileUpload(file, fileType) {
    // Validate file type
    if (!isValidFileType(file, fileType)) {
        showError('Format de fichier invalide');
        return;
    }

    // Process upload
    uploadFile(file, fileType);
}
```

### CSS

- **Organisation:** Par composant
- **Nomenclature:** BEM ou classes descriptives
- **Variables CSS:** Utiliser `:root` pour les couleurs

Exemple:
```css
/* Button Component */
.btn-primary {
    background: var(--primary);
    color: white;
    padding: 12px 30px;
    border-radius: 8px;
}

.btn-primary:hover {
    background: var(--primary-dark);
}
```

## Structure des Commits

Utilisez des préfixes clairs:

- `Add:` Nouvelle fonctionnalité
- `Fix:` Correction de bug
- `Update:` Modification d'une fonctionnalité existante
- `Refactor:` Refactoring sans changement fonctionnel
- `Docs:` Documentation
- `Style:` Changements de style (CSS)
- `Test:` Ajout ou modification de tests

Exemples:
```
Add: support for WebVTT subtitle format
Fix: issue with overlapping mode tolerance
Update: improve error messages in French
Docs: add deployment guide for Docker
```

## Tests

Avant de soumettre une PR:

1. **Testez localement:**
   ```bash
   python app.py
   ```

2. **Testez les deux modes:**
   - Mode vidéo (si FFmpeg installé)
   - Mode SRT direct

3. **Testez responsive:**
   - Desktop
   - Mobile
   - Tablette

4. **Testez les cas d'erreur:**
   - Fichier invalide
   - Fichier trop gros
   - Pas de sous-titres

## Checklist PR

Avant de soumettre votre Pull Request:

- [ ] Le code suit les conventions du projet
- [ ] Les tests passent localement
- [ ] La documentation est à jour si nécessaire
- [ ] Les messages de commit sont clairs
- [ ] Pas de fichiers inutiles (logs, .env, etc.)
- [ ] Le code est commenté si nécessaire
- [ ] Testé sur différents navigateurs

## Questions?

N'hésitez pas à:
- Ouvrir une issue pour des questions
- Demander de l'aide dans votre PR
- Contacter: dev@doublesub.io

Merci de contribuer! 🙏
