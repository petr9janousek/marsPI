# marsPI Project
Verze python GUI vytvořená na RPI.
***
ToDo úlohy jsou označeny podle důležitosti "+num", vyšší číslo => vyšší priorita;
~~Škrtnuté~~ znamená vyřešeno, v příští revizi může být smazáno;
***
#### ToDo tasks
* +1 - Minikarta připojení - není potřeba vybírat port. Pouze tlačítko Připojit/Odpojit, Status, případně nastavení - mohlo by odkazovat na kartu nastavení.
* +5 - PLA comboboxy - Upravit kód MCU aby spolupracoval, změna hodnot ve switch
* +4 - System - Zhodnotit zda je potřeba výměna Threading za Multiprocessing

#### Dependencies 
"pacman -Syuu"
"pacman -S mingw-w64-x86_64-gtk3"
"pacman -S mingw-w64-x86_64-glade"

"pacman -S mingw-w64-x86_64-python-matplotlib"
"pacman -S mingw-w64-x86_64-python-pyserial"

#### Tools
C:\msys64\usr\bin\bash 	-lc

#### Setting bashrc
alias vi=vim
export PATH=$PATH:/mingw64/bin
cd Code/marsPI