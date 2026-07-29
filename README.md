# ayn

**ayn** is a simple CLI utility for Linux / WSL designed to save a project's directory structure and file contents into a single text document.

It is built to easily prepare context for **AI assistants (LLM)**, perform quick code audits, or share source code with others.

---

## 🚀 Features

- **Structure Export:** Generates a directory tree without file contents.
- **Content Export:** Bundles the structure and source code of all files into a single `.txt` file.
- **Sensitive Data Protection (`-ns`):** Automatically masks `.env`, SSH keys, certificates, and other secrets.
- **Flexible Filtering:** Export only specified files or exclude unwanted ones (`-ex`).
- **Smart Processing:** Automatically skips binary files and prevents duplicate entries.
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

### 2. Save structure and contents of all files
```bash
ayn cont .
```
Writes the project tree followed by the content of every text file.

### 3. Save everything except secret data (No Secrets)
```bash
ayn cont -ns
```
Works like `ayn cont .`, but skips the contents of files matching secret patterns (`.env`, `*.key`, `id_rsa`, etc.).

### 4. Save only specified files
```bash
ayn cont src/main.rs Cargo.toml
```
Writes the overall project structure, but appends the content of **only** the listed files.

### 5. Exclude specified files
```bash
ayn cont -ex .env secrets.txt docs/
```
Writes the project structure and contents of all files, **except** those passed as arguments.

---

## 💡 Common Use Cases

* **Prepare project context for ChatGPT / Claude:**
  ```bash
  ayn cont -ns
  ```
* **Quickly share project structure with a teammate:**
  ```bash
  ayn struc
  ```
* **Export only configuration files and entry points:**
  ```bash
  ayn cont Cargo.toml src/main.rs
  ```

---

## 🛡 Security & `-ns` Mode

When using the `-ns` (No Secrets) flag, the utility checks filenames and automatically redacts file contents if they match any of the following patterns:

- `.env`, `.env.*`
- `*.key`, `*.pem`, `*.crt`, `*.p12`, `*.pfx`
- `id_rsa`, `id_ed25519`
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
- [ ] Customizable secret pattern list.
- [ ] Custom folder exclusion using glob patterns.
- [ ] Format output in clean Markdown.
- [ ] Add clipboard support (`--clip` flag).
- [ ] Render directory trees in standard `tree` format.

---

## 📜 License

Distributed under the **MIT** License.

**Author:** [bernkastel5](https://github.com/bernkastel5)
