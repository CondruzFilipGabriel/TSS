# Proiect Testarea Sistemelor Software

## Cuprins
* [Tema: imbunatatirea testarii unitare cu IA](#tema-imbunatatirea-testarii-unitare-cu-ia)
* [Sistem de calcul utilizat](#sistem-de-calcul-utilizat)
* [Solutia software implementata](#solutia-software-implementata)
* [Ollama](#ollama)
* [Aider](#aider)
* [Git](#git)
* [Utilitare](#utilitare)
* [Testarea functionarii initiale](#testarea-functionarii-initiale)
* [Functionalitati](#functionalitati)
* [Utilizare](#utilizare)
* [Autor](#autor)

## Tema: imbunatatirea testarii unitare cu IA

[<< Cuprins](#cuprins)

    Utilizarea IA pentru imbunatatirea testelor unitare existente,
    asigurand o acoperire cat mai eficienta a codului sursa (de exemplu, 
    marirea scorului de acoperire la nivel de instructiune, decizie, 
    conditie, mutatie generata de un framework de testare unitara) 
    
    Implementarea unui sistem care sa identifice automat punctele critice 
    ale codului si sa prioritizeze testele in functie de acestea.

## Sistem de calcul utilizat

[<< Cuprins](#cuprins)

    Laptop producator: 
        LENOVO IdeaPad Pro 5 14AHP9
    processor:         
        AMD Ryzen 7 8845HS Radeon (8 nuclee, frecventa 3.8 - 5.1 GHz)
    RAM:               
        16GB LPDDR5x
    SSD:               
        512GB SSD, AMD Radeon™
    Sistem de operare: 
        Ubuntu 24.04.4 LTS

## Solutia software implementata

[<< Cuprins](#cuprins)

    Sistem baza pe AI local (offline):

        Ollama (AI language agent) cu Qwen2.5-Coder pe 7B

        Aider ("Ai pair programming": edit & run files)

    Tools:

        pytest (tester automat)

        cosmic-ray (mutant testing & branch coverage)

## Ollama

[<< Cuprins](#cuprins)

* **INSTALARE**

    curl -fsSL https://ollama.com/install.sh | sh

        The Ollama API is now available at 127.0.0.1:11434.
        Install complete. Run "ollama" from the command line.
        AMD GPU ready.

    ollama -v

        ollama version is 0.20.2

    ollama pull qwen2.5-coder:7b

        verifying sha256 digest 
        writing manifest 
        success

    sudo systemctl status ollama

        ollama.service - Ollama Service
        Loaded: loaded (/etc/systemd/system/ollama.service; enabled preset: enabl>
        Active: active (running) since Sun 2026-04-05 11:06:34 EEST 15min ago
        Main PID: 6219 (ollama)
        Tasks: 23 (limit: 16336)
        Memory: 2.2G (peak: 4.3G)
            CPU: 33.402s
        CGroup: /system.slice/ollama.service
                └─6219 /usr/local/bin/ollama serve

        // Ollama rulează ca serviciu systemd


* **CONFIGURARE**

    **Crestem contextul la 16k (Aider cere 8k doar pentru raspuns; default e 2k; max 32k):** 
    
        sudo systemctl edit ollama

            [Service]
            Environment="OLLAMA_CONTEXT_LENGTH=16384"

        sudo systemctl daemon-reload
        sudo systemctl restart ollama        
        sudo systemctl status ollama

    **Setam variabilele:**

        export PATH="$HOME/.local/bin:$PATH"
        export OLLAMA_API_BASE=http://127.0.0.1:11434
        aider --version

    **Permanentizam:**

        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo 'export OLLAMA_API_BASE=http://127.0.0.1:11434' >> ~/.bashrc
        source ~/.bashrc


## AIDER

[<< Cuprins](#cuprins)

**INSTALARE**

    curl -LsSf https://aider.chat/install.sh | sh

        Installed 1 executable: aider

    export PATH="$HOME/.local/bin:$PATH"

    aider --version

        aider 0.86.2


**CONFIGURARE**

* Scriem fisierul **.aider.conf.yml** pentru configurarea pornirii (fisierele care trebuiesc incarcate doar in citire), care se incarca automat de Aider.
* Scriem fisierul **AutoTesting.py** pentru a rula comenzile de start automat si a inchide Ollama si Aider la final.

## GIT

[<< Cuprins](#cuprins)

* **INSTALARE**

    sudo apt install git

    git -v

        git version 2.43.0

    git init

        Initialized empty Git repository in /home/f/Desktop/TSS/.git/

    git remote add origin https://github.com/CondruzFilipGabriel/TSS.git

    git remote -v

        origin	https://github.com/CondruzFilipGabriel/TSS.git (fetch)
        origin	https://github.com/CondruzFilipGabriel/TSS.git (push)

    ssh-keygen -t ed25519 -C "\*@\*.\*"

    eval "$(ssh-agent -s)"

    ssh-add ~/.ssh/id_ed25519

    cat ~/.ssh/id_ed25519.pub

    (*copiem cheia pe GitHub si o adaugam cu drepturi de scriere*)

    git add .

    git branch -M main

    git commit -m "Initial commit"

    git remote set-url origin git@github.com:CondruzFilipGabriel/TSS.git

    git config --global user.name "*******"

    git config --global user.email "\*@\*.\*"

    git push -u origin main

* **UPDATE / UTILIZARE**

    git status

    git add .

    git commit - m "Eticheta privind noul update"

    git push


## UTILITARE

[<< Cuprins](#cuprins)

**pytest, cosmic-ray si coverage**

    python3 -m pip install --user --break-system-packages --upgrade --force-reinstall pytest cosmic-ray coverage

    pytest --version

        pytest 9.0.2

    cosmic-ray --version

        cosmic-ray, version 8.4.6

    coverage --version

        Coverage.py, version 7.13.5 with C extension
        Full documentation is at https://coverage.readthedocs.io/en/7.13.5

    * cream fisierele de configurare: pytest.ini si cosmic-ray.toml


## TESTAREA FUNCTIONARII INITIALE

[<< Cuprins](#cuprins)

    cd /****/TSS

    aider --model ollama_chat/qwen2.5-coder:7b array5.py

        ────────────────────────────────────────────────────────────────────────────────
        Aider v0.86.2
        Model: ollama_chat/qwen2.5-coder:7b with whole edit format
        Git repo: none
        Repo-map: disabled
        Added array5.py to the chat.
        ────────────────────────────────────────────────────────────────────────────────
        array5.py                                                                       
        > hello                                                                         

        Understood. I will follow the provided guidelines for suggesting changes to     
        files. Please let me know what changes you would like made.                     


        Tokens: 654 sent, 26 received.
        ────────────────────────────────────────────────────────────────────────────────
        > tell me a bit about yourself                                                  

        I am an AI language model designed to assist with programming tasks. I can help 
        answer questions, provide explanations, and suggest changes to code. How can I  
        assist you today?                                                               


        Tokens: 626 sent, 35 received.
        ────────────────────────────────────────────────────────────────────────────────


## FUNCTIONALITATI

[<< Cuprins](#cuprins)

* Instructiunile sunt in limba engleza (performanta mai buna).
* verifica existenta fisierelor si configuratiilor minime necesare pentru rulare: `to_test.py`, `.aider.conf.yml`, `Rules.md`, fisiere `testing_*.md` si folderul `arh`

* creeaza automat fisierele de test corespunzatoare categoriilor definite in `testing_*.md`, sub forma `test_*.py`

* porneste si controleaza local un flux AI bazat pe **Ollama + Aider**, folosit pentru generarea automata de teste Python

* citeste reguli generale si reguli specifice pe categorii din fisiere Markdown si le transforma in prompturi pentru AI

* genereaza initial teste de baza pentru fiecare categorie definita in fisierele `testing_*.md`

* valideaza fiecare functie de test generata de AI astfel incat:

  * sa fie o functie `test_*`
  * sa poata fi colectata de `pytest`
  * sa poata fi rulata fara erori tehnice

* foloseste un mecanism iterativ de corectare: daca testul generat este invalid, transmite AI-ului eroarea bruta si cere o versiune corectata

* masoara calitatea suitei de teste existente prin:

  * **pytest** pentru procentul de teste care trec
  * **branch coverage** pentru acoperirea structurala a codului din `to_test.py`
  * **Cosmic Ray** pentru mutation testing si detectarea mutantilor ucisi de teste

* adauga un test nou in fisierul categoriei sale doar daca acesta imbunatateste cel putin unul dintre scorurile de testare existente

* elimina automat testele noi care nu aduc nicio imbunatatire, pentru a evita redundanta

* cauta ulterior reguli noi de testare, diferite de cele initiale, care pot creste performanta suitei existente

* reseteaza contextul AI intre etape sau categorii pentru a evita contaminarea contextului cu informatii irelevante din sarcinile anterioare

* inregistreaza in `Logs.jsonl` fiecare regula noua acceptata, impreuna cu:

  * categoria
  * regula noua
  * motivarea
  * imbunatatirea obtinuta
  * data si autorul

* afiseaza la final regulile noi adaugate in sesiunea curenta sau mentioneaza explicit daca nu au fost identificate teste noi utile

* arhiveaza la final fisierul `to_test.py` si toate fisierele `test_*.py` intr-un subfolder numerotat si datat din `/arh`

* realizeaza, per ansamblu, un proces de **testare automata asistata de AI**, orientat spre:

  * generare de teste `pytest`
  * validare tehnica automata
  * optimizare prin eliminarea redundantei
  * crestere progresiva a acoperirii si a fortei de detectare a defectelor


## UTILIZARE

[<< Cuprins](#cuprins)

* **Start Aider + Ollama (in folderul /****/TSS)**
    
        ./python3 AutoTesting.py

* **Exit Aider + oprire model Ollama** - se executa automat la finalizare.

* La final sunt afisate testele adaugate.

* In fisierul Logs.jsonl se vor regasi toate schimbarile (testele adaugate) de la toate rularile

* In folderul /arh se vor muta, intr-un subfolder cu numele format din data si ziua curenta, fisierele to_test.py si test_*.py pentru a putea fi consultate ulterior.


## AUTOR

[<< Cuprins](#cuprins)

    Condruz Filip Gabriel

    Univesitatea Bucuresti, Facultatea de Matematica si Informatica, anul 3 ID