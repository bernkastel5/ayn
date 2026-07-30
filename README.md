# ayn

**ayn** is a simple CLI utility for Linux / WSL designed to save a project's directory structure and file contents into a single text document.

It is built to easily prepare clean context for **AI assistants (LLMs)**, perform quick code audits, or share source code with others.

---

## 🚀 Features

- **Structure Export:** Generates a directory tree without file contents.
- **Content Export:** Bundles the structure and source code of all files into a single `.txt` file.
- **Environment & Build Exclusion (`-ne`):** Skips heavy and generated folders (`.venv`, `node_modules`, `.git`, `dist`, `__pycache__`, etc.).
- **Sensitive Data Protection (`-ns`):** Automatically masks `.env`, SSH keys, certificates, and other secrets.
- **Flexible Filtering:** Export only specified files or exclude unwanted ones (`-ex`).
- **Smart Processing:** Smart virtual environment detection heuristics, automatic binary file skipping, and duplicate prevention.
- **Zero Dependencies:** Runs on pure Python 3.10+ without requiring a `virtualenv`.

---

## 📋 Requirements

- **OS:** Linux or WSL (Windows Subsystem for Linux)
- **Python:** Version 3.10 or newer

---

## 🛠 Installation

### Option 1. Global Installation (Recommended)

1. Clone the repository or download the script:
   ```bash
   git clone https://github.com/USERNAME/ayn.git
   cd ayn
   ```

2. Make the script executable:
   ```bash
   chmod +x ayn.py
   ```

3. Create a symbolic link (symlink):

   *For all users (requires sudo privileges):*
   ```bash
   sudo ln -s "$(pwd)/ayn.py" /usr/local/bin/ayn
   ```

   *Or for the current user only:*
   ```bash
   mkdir -p ~/.local/bin
   ln -s "$(pwd)/ayn.py" ~/.local/bin/ayn
   ```
   *(Ensure `~/.local/bin` is added to your `$PATH` variable)*.

4. Verify the installation:
   ```bash
   ayn --help
   ```

### Option 2. Direct Execution

You can also run the script directly using system Python without creating a symlink:
```bash
python3 /path/to/ayn/ayn.py struc
python3 /path/to/ayn/ayn.py cont .
```

---

## 💻 Usage & Commands

The utility always creates a `.txt` file in the **current working directory**. The output filename is generated automatically using the pattern: `ayn_<mode>_YYYYMMDD_HHMMSS_xxxxxx.txt`.

### 1. Save directory structure only
```bash
ayn struc
```
Creates a text file containing the tree of directories and files (without their contents).

*Skip environment and build directories:*
```bash
ayn struc -ne
```

### 2. Save structure and contents of all files
```bash
ayn cont .
```
Writes the project tree followed by the content of every text file.

### 3. Exclude environments, caches, and dependencies (No Environment)
```bash
ayn cont -ne
```
Ignores system and generated folders (`node_modules`, `.venv`, `.git`, `build`, etc.) during tree rendering and content processing.

### 4. Save everything except secret data (No Secrets)
```bash
ayn cont -ns
```
Works like `ayn cont .`, but skips the contents of files matching secret patterns (`.env`, `*.key`, `id_rsa`, etc.).

### 5. Perfect AI Mode (No Environment + No Secrets)
```bash
ayn cont -ne -ns
```
Flags can be combined! This is the optimal command to generate context for ChatGPT, Claude, or DeepSeek.

### 6. Save only specified files or exclude them
```bash
# Specific files only
ayn cont src/main.rs Cargo.toml

# Exclude specific files/directories (-ex)
ayn cont -ex .env secrets.txt docs/
```

---

## 💡 Common Use Cases

* **Best workflow for prompting LLMs with clean repository context:**
  ```bash
  ayn cont -ne -ns
  ```
* **Quickly inspect clean project structure without `.git` or `node_modules`:**
  ```bash
  ayn struc -ne
  ```
* **Export configuration files and entry points:**
  ```bash
  ayn cont Cargo.toml src/main.rs
  ```

---

## ⚙️ Flag Details

### `-ne` Mode (No Environment)
Automatically filters out generated directories, vendor dependencies, and build artifacts. Ignores:
- **Dependencies & Environments:** `.venv`, `venv`, `env`, `node_modules`, `pip-wheel-metadata`, `*.egg-info`.
- **Caches & Compiled files:** `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `.cache`, `.parcel-cache`.
- **Build Artifacts:** `dist`, `build`, `target`, `out`, `coverage`, `.next`, `.nuxt`, `.turbo`.
- **VCS & Configs:** `.git`, `.github`, `.gitlab`, `.svn`, `.hg`.
- **IDE Settings:** `.vscode`, `.idea`.
- **Heuristic Detection:** Even if a virtual environment folder has a custom name, `ayn` detects and skips it via internal markers (`pyvenv.cfg`, `activate`, `python.exe`, etc.).

### `-ns` Mode (No Secrets)
Protects sensitive information. Masks file contents if filenames match any of the following patterns:
- `.env`, `.env.*`, `*.env`, `*.secret`, `*credential*`
- `*.key`, `*.pem`, `*.crt`, `*.p12`, `*.pfx`
- `id_rsa`, `id_dsa`, `id_ecdsa`, `id_ed25519`
- `.npmrc`, `.git-credentials`

---

## 📄 Output Format

The output file is structured as follows:

```text
[ PROJECT TREE AND STRUCTURE ]

path/to/file1.ext

Content of file 1...


path/to/file2.ext

Content of file 2...
```

---

## 🔍 Troubleshooting

If you encounter an error when executing the command:
```text
/usr/bin/env: ‘python3\r’: No such file or directory
```
This indicates the file has Windows CRLF line endings. Fix it by converting it to Unix line endings:
```bash
dos2unix ayn.py
chmod +x ayn.py
```

---

## 📂 Repository Structure

```text
ayn/
├── ayn.py        # Main utility script
└── README.md     # Documentation
```

---

## 📌 TODO / Roadmap

- [ ] Add `.aynignore` configuration file support.
- [ ] Customizable secret and ignore pattern CLI options.
- [ ] Format output in clean Markdown.
- [ ] Add clipboard support (`--clip` flag).

---

## 📜 License

Distributed under the **MIT** License.

**Author:** [bernkastel5](https://github.com/bernkastel5)
