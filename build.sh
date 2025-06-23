cd "$(dirname "$0")"

source .venv/Scripts/activate

python -m pip install . --upgrade

 read -p "Press Enter to continue..."