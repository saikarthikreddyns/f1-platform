cd C:\Users\saika\OneDrive\Desktop\Personal projects\f1-platform\ml

if (!(Test-Path ".venv")) {
    py -m venv .venv
}

& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
}

Write-Host "Virtual environment setup completed!"

