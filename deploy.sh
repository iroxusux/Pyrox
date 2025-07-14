source ./build.sh

pyinstaller --name "Pyrox" --noconfirm --noconsole --onedir --icon="pyrox/ui/icons/_def.ico" --add-data "pyrox/ui/icons:pyrox/ui/icons" --add-data "pyrox/tasks:pyrox/tasks" --add-data "pyrox/applications/mod:pyrox/applications/mod"  __main__.py

 read -p "Press Enter to continue..."