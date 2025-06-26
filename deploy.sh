cd "$(dirname "$0")"

source .venv/Scripts/activate

python -m pip install . --upgrade

pyinstaller --name "Pyrox" --noconfirm --onedir --add-data "pyrox/ui/icons:pyrox/ui/icons" --add-data "pyrox/tasks:pyrox/tasks"  __main__.py

 read -p "Press Enter to continue..."