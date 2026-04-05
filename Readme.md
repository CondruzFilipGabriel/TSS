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
* [Utilizare](#utilitare)
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

        Ollama (AI language agent)

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

    **Crestem contextul la 8k:** 
    
        sudo systemctl edit ollama

            [Service]
            Environment="OLLAMA_CONTEXT_LENGTH=8192"

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

**pytest si cosmic-ray**

    python3 -m pip install --user --break-system-packages --upgrade --force-reinstall pytest cosmic-ray

    python3 -m pytest --version

        pytest 9.0.2

    cosmic-ray --version

        cosmic-ray, version 8.4.6

    cream fisierele de configurare: pytest.ini si cosmic-ray.toml


## TESTAREA FUNCTIONARII INITIALE

[<< Cuprins](#cuprins)

    cd /home/f/Desktop/TSS

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


## UTILIZARE

[<< Cuprins](#cuprins)


## AUTOR

[<< Cuprins](#cuprins)

    Condruz Filip Gabriel

    Univesitatea Bucuresti, Facultatea de Matematica si Informatica, anul 3 ID