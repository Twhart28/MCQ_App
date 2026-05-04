# MCQ App

Desktop multiple choice question tester used with a custom GPT question-generation workflow.

## Current apps

- `MCQ_Test_App.py`: original Tkinter draft.
- `mcq_qt_app.py`: new PySide6 desktop app prototype.

## New Qt app behavior

The Qt version supports three quiz modes:

- Study mode: answer one question, submit it, see correct/incorrect feedback and the explanation, then move on.
- Test mode: answer one question at a time, move between questions, and grade everything at the end.
- Full page test: answer all questions on one scrollable page and grade at the end.

It also keeps the existing JSON import/paste flow and supports randomized question order and randomized answer choices.

## GPT output workflow

The Qt app can keep the Custom GPT separate while making import smoother:

- Paste clipboard: paste the latest GPT output directly into the JSON editor.
- Start: automatically cleans common GPT wrappers and validates the required question fields before the test begins.
- Save test: save the current cleaned test JSON.
- Load saved: load a previous test from `saved_tests` while running from source, or from the user's local app data folder in the packaged app.

## Run locally

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe .\mcq_qt_app.py
```

## Packaging direction

For a GitHub Release, build both artifacts:

- `dist\MCQ_Tester_v1.0.0_windows.zip`: portable app folder.
- `dist\installer\MCQ_Tester_Setup_v1.0.0.exe`: Windows installer with Start menu entry and optional desktop shortcut.

Run the release build script:

```powershell
.\scripts\build_release.ps1 -Version 1.0.0
```

The script uses PyInstaller for the app bundle and Inno Setup for the installer. The direct PyInstaller command is:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --name "MCQ Tester" --windowed --icon .\assets\mcq_tester_icon.ico --add-data ".\assets;assets" .\mcq_qt_app.py
```
