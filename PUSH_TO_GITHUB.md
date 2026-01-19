# How to Push Veritas to GitHub

Follow these steps to upload your project to a new GitHub repository:

### 1. Initialize Git
Open a terminal in the project root (`d:\Documents\College\DTL`) and run:
```powershell
git init
```

### 2. Add Files
Add all project files (the `.gitignore` will automatically prevent sensitive files from being staged):
```powershell
git add .
```

### 3. Initial Commit
```powershell
git commit -m "Initial commit: Veritas AI Truth Verification Ecosystem"
```

### 4. Create Repository on GitHub
1. Go to [GitHub](https://github.com/new).
2. Create a new repository named `Veritas` (or your preferred name).
3. Do **NOT** initialize with a README, license, or gitignore (we already created them).

### 5. Link and Push
Replace `YOUR_USERNAME` with your GitHub username:
```powershell
git remote add origin https://github.com/YOUR_USERNAME/Veritas.git
git branch -M main
git push -u origin main
```

---

### 💡 Pro Tips for GitHub
- **Private Repository**: If you're using this for college and want to keep your API keys configuration structure private, choose "Private" during repository creation.
- **Large Files**: If you have very large models or datasets later, consider using [Git LFS](https://git-lfs.github.com/).
