# Proiect Testarea Sistemelor Software

## Cuprins
* [Tema: imbunatatirea testarii unitare cu IA](#tema-imbunatatirea-testarii-unitare-cu-ia)
* [Sistem de calcul utilizat](#sistem-de-calcul-utilizat)
* [Solutia software implementata](#solutia-software-implementata)
* [Ollama](#ollama)
* [Git](#git)
* [Utilitare](#utilitare)
* [Testarea functionarii initiale](#testarea-functionarii-initiale)
* [Functionalitati](#functionalitati)
* [Flux de executie](#flux-de-executie)
* [Utilizare](#utilizare)
* [Autor](#autor)

## Tema: imbunatatirea testarii unitare cu IA

[<< Cuprins](#cuprins)

    Utilizarea IA pentru imbunatatirea testelor unitare existente,
    asigurand o acoperire cat mai eficienta a codului sursa (de exemplu,
    marirea scorului de acoperire la nivel de instructiune, decizie,
    conditie si mutatie).

    Implementarea unui sistem care sa identifice automat punctele critice
    ale codului si sa prioritizeze testele in functie de acestea.

## Sistem de calcul utilizat

[<< Cuprins](#cuprins)

    Laptop producator:
        LENOVO IdeaPad Pro 5 14AHP9
    Processor:
        AMD Ryzen 7 8845HS Radeon (8 nuclee, frecventa 3.8 - 5.1 GHz)
    RAM:
        16GB LPDDR5x
    SSD:
        512GB SSD
    Sistem de operare:
        Ubuntu 24.04.4 LTS

## Solutia software implementata

[<< Cuprins](#cuprins)

    Sistem bazat pe AI local (offline):

        Ollama (agent AI local)
        Qwen2.5-Coder 7B (modelul folosit pentru generare)
        AutoTesting.py (orchestratorul principal al framework-ului)

    Tools:

        pytest (executia si validarea testelor)
        coverage (branch coverage)
        mutmut (mutation testing)

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
        Loaded: loaded (/etc/systemd/system/ollama.service; enabled)
        Active: active (running)

        // Ollama ruleaza ca serviciu systemd

* **CONFIGURARE**

    **Optional: marim contextul modelului**

        sudo systemctl edit ollama

            [Service]
            Environment="OLLAMA_CONTEXT_LENGTH=20000"

        sudo systemctl daemon-reload
        sudo systemctl restart ollama
        sudo systemctl status ollama

    **Permanentizam PATH pentru utilitarele instalate user-local:**

        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        source ~/.bashrc

    Framework-ul comunica direct cu API-ul Ollama prin HTTP.
    Modelul folosit implicit este configurat in `Config.py`.

## Git

[<< Cuprins](#cuprins)

* **INSTALARE**

    sudo apt install git

    git -v

        git version 2.43.0

    git init

        Initialized empty Git repository in /home/f/Desktop/TSS/.git/

    git remote add origin https://github.com/CondruzFilipGabriel/TSS.git

    git remote -v

        origin  https://github.com/CondruzFilipGabriel/TSS.git (fetch)
        origin  https://github.com/CondruzFilipGabriel/TSS.git (push)

    ssh-keygen -t ed25519 -C "*@*.*"

    eval "$(ssh-agent -s)"

    ssh-add ~/.ssh/id_ed25519

    cat ~/.ssh/id_ed25519.pub

    (*copiem cheia pe GitHub si o adaugam cu drepturi de scriere*)

    git add .

    git branch -M main

    git commit -m "Initial commit"

    git remote set-url origin git@github.com:CondruzFilipGabriel/TSS.git

    git config --global user.name "*******"

    git config --global user.email "*@*.*"

    git push -u origin main

* **UPDATE / UTILIZARE**

    git status

    git add .

    git commit -m "Eticheta privind noul update"

    git push

## Utilitare

[<< Cuprins](#cuprins)

**pytest, mutmut si coverage**

    python3 -m pip install --user --break-system-packages --upgrade --force-reinstall pytest mutmut coverage

    pytest --version

        pytest 9.0.2

    mutmut --version

        mutmut, version 3.5.0

    coverage --version

        Coverage.py, version 7.13.5 with C extension

    * se creeaza fisierele de configurare necesare: pytest.ini si pyproject.toml

**Comenzi utile de verificare manuala**

    python3 -m pytest -q

    python3 -m coverage erase
    python3 -m coverage run --branch -m pytest -q
    python3 -m coverage report -m --include=to_test.py

    mutmut run
    mutmut results

## Testarea functionarii initiale

[<< Cuprins](#cuprins)

    cd /****/TSS

    python3 AutoTesting.py

    La final se verifica:
        - continutul fisierelor test_*.py
        - regulile nou adaugate in testing_*.md
        - istoricul din Logs.jsonl
        - arhivarea in folderul arh/
        - logurile tehnice din folderul logs/

## Functionalitati

[<< Cuprins](#cuprins)

* instructiunile catre AI sunt formulate in limba engleza

* verifica existenta fisierelor si configuratiilor minime necesare pentru rulare:
  * `to_test.py`
  * `Rules.md`
  * fisierele `testing_*.md`
  * folderul `arh`

* creeaza automat fisierele de test corespunzatoare categoriilor definite in `testing_*.md`, sub forma `test_*.py`

* comunica direct cu Ollama prin API HTTP pentru generarea automata de teste Python

* citeste regulile generale din `Rules.md` si specificul categoriilor din `testing_*.md`, apoi construieste prompturile corespunzatoare fiecarei etape

* genereaza initial teste de baza pentru fiecare categorie definita in fisierele `testing_*.md`

* valideaza fiecare functie de test generata de AI astfel incat:
  * sa fie o functie `test_*`
  * sa poata fi colectata de `pytest`
  * sa poata fi rulata fara erori tehnice

* foloseste un mecanism iterativ de corectare: daca testul generat este invalid, transmite AI-ului eroarea de validare si cere o versiune corectata

* masoara calitatea testelor prin:
  * **pytest** pentru validitatea suitei
  * **coverage** pentru branch coverage asupra `to_test.py`
  * **mutmut** pentru mutation testing asupra `to_test.py`

* in etapa 2, accepta un test nou doar daca acesta imbunatateste scorurile categoriei curente, evaluate pe fisierul de test al categoriei respective

* optimizeaza separat bibliotecile de teste pe categorii, de exemplu:
  * `test_functional.py` pentru categoria functionala
  * `test_structural.py` pentru categoria structurala

* dupa acceptarea unui test nou, cere separat de la AI:
  * regula generala asociata testului
  * motivarea utilitatii testului

* adauga regula acceptata in fisierul `testing_*.md` al categoriei curente

* inregistreaza in `Logs.jsonl` fiecare regula noua acceptata, impreuna cu:
  * categoria
  * regula
  * motivarea
  * imbunatatirea obtinuta
  * data si autorul

* elimina automat propunerile care nu aduc imbunatatire, pentru a reduce redundanta si zgomotul din library

* reseteaza contextul AI intre etape sau categorii pentru a evita contaminarea contextului cu informatii irelevante

* arhiveaza la final fisierul `to_test.py` si toate fisierele `test_*.py` intr-un subfolder numerotat si datat din `arh/`

* realizeaza un proces de testare automata asistata de AI, orientat spre:
  * generare de teste `pytest`
  * validare tehnica automata
  * crestere progresiva a branch coverage
  * crestere progresiva a mutation score
  * dezvoltarea unei biblioteci de reguli de testare pe categorii

## Flux de executie

[<< Cuprins](#cuprins)

1. Se curata workspace-ul de fisierele si folderele temporare.
2. Se verifica structura minima a proiectului.
3. Se genereaza testele initiale pentru regulile explicite existente in `testing_*.md`.
4. Se cauta teste noi pentru fiecare categorie.
5. Pentru fiecare test nou acceptat, se cere separat regula si motivarea.
6. Se actualizeaza fisierele `test_*.py`, `testing_*.md` si `Logs.jsonl`.
7. Se arhiveaza rezultatele si se curata fisierele si folderele temporare.

## Utilizare

[<< Cuprins](#cuprins)

* **Pornire framework (in folderul /****/TSS)**

        python3 AutoTesting.py

* La final sunt afisate regulile noi adaugate in sesiunea curenta.

* In fisierul `Logs.jsonl` se regasesc toate regulile acceptate de-a lungul rularilor.

* In fisierele `testing_*.md` se construieste treptat biblioteca de reguli de testare pe categorii.

* In folderul `arh/` se salveaza, intr-un subfolder numerotat si datat, fisierele `to_test.py` si `test_*.py`.

* In folderul `logs/` se salveaza logurile tehnice ale framework-ului si interactiunile brute cu Ollama, daca debugging-ul este activ.

## Autor

[<< Cuprins](#cuprins)

    Condruz Filip Gabriel

    Univesitatea Bucuresti, Facultatea de Matematica si Informatica, anul 3 ID