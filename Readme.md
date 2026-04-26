# Proiect "Testarea Sistemelor Software"

## Cuprins
* [Tema: imbunatatirea testarii unitare cu IA](#tema-imbunatatirea-testarii-unitare-cu-ia)
* [Sistem de calcul utilizat](#sistem-de-calcul-utilizat)
* [Solutia software implementata](#solutia-software-implementata)
* [Ollama](#ollama)
* [Git](#git)
* [Utilitare](#utilitare)
* [Testarea manuala a suitei curente](#testarea-manuala-a-suitei-curente)
* [Testarea functionarii framework-ului](#testarea-functionarii-framework-ului)
* [Structura fisierelor de instructiuni](#structura-fisierelor-de-instructiuni)
* [Functionalitati](#functionalitati)
* [Flux de executie](#flux-de-executie)
* [Utilizare](#utilizare)
* [Imbunatatiri implementate pentru performanta si calitatea rezultatelor](#imbunatatiri-implementate-pentru-performanta-si-calitatea-rezultatelor)
* [Autor](#autor)

## Tema: imbunatatirea testarii unitare cu IA

[<< Cuprins](#cuprins)

    Utilizarea IA pentru imbunatatirea testelor unitare existente,
    asigurand o acoperire cat mai eficienta a codului sursa, de exemplu
    prin cresterea branch coverage si a mutation score.

    Implementarea unui sistem care identifica automat zone relevante de
    testare unitara, genereaza propuneri de teste, valideaza tehnic aceste
    propuneri si accepta doar extensiile care imbunatatesc efectiv biblioteca
    de teste existenta.

    Scopul proiectului este generarea de teste unitare valide pentru
    comportamentul curent al codului. Testele acceptate trebuie sa treaca la
    pytest. Sistemul nu are ca obiectiv principal generarea de teste care pica
    pentru a demonstra buguri de runtime.

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

    Sistem bazat pe AI local, rulat offline:

        Ollama
        Qwen2.5-Coder 7B
        AutoTesting.py

    Tools folosite pentru evaluarea testelor:

        pytest
        coverage cu branch coverage
        mutmut

    Componente principale:

        AutoTesting.py       - orchestratorul principal
        Config.py            - configurare centrala
        PromptBuilder.py     - construirea prompturilor
        OllamaClient.py      - comunicarea cu API-ul Ollama
        ResponseParser.py    - parsarea raspunsurilor AI
        TestValidator.py     - validarea propunerilor de test
        TestsPerformance.py  - scorare pytest, coverage si mutmut
        WorkspaceManager.py  - operatii pe fisierele proiectului
        Archive.py           - arhivarea artefactelor finale
        Cleanup.py           - curatarea artefactelor temporare
        Logger.py            - logging tehnic si istoric reguli
        manual_testing.py    - verificare manuala pytest, coverage si mutmut

## Ollama

[<< Cuprins](#cuprins)

* **INSTALARE**

        curl -fsSL https://ollama.com/install.sh | sh

        ollama -v

        ollama pull qwen2.5-coder:7b

        sudo systemctl status ollama

    Ollama ruleaza ca serviciu systemd.

* **CONFIGURARE**

    **Optional: marirea contextului modelului**

        sudo systemctl edit ollama

            [Service]
            Environment="OLLAMA_CONTEXT_LENGTH=20000"

        sudo systemctl daemon-reload
        sudo systemctl restart ollama
        sudo systemctl status ollama

    **Permanentizarea PATH pentru utilitarele instalate user-local**

        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        source ~/.bashrc

    Framework-ul comunica direct cu API-ul Ollama prin HTTP.
    Modelul folosit implicit este configurat in `Config.py`.

    Instructiunile transmise catre model sunt formulate in limba engleza,
    pentru a creste calitatea raspunsurilor generate de modelul local.

## Git

[<< Cuprins](#cuprins)

* **INSTALARE**

        sudo apt install git

        git -v

        git init

        git remote add origin https://github.com/CondruzFilipGabriel/TSS.git

        git remote -v

        ssh-keygen -t ed25519 -C "*@*.*"

        eval "$(ssh-agent -s)"

        ssh-add ~/.ssh/id_ed25519

        cat ~/.ssh/id_ed25519.pub

    Cheia publica se adauga in GitHub cu drepturi de scriere.

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

        mutmut --version

        coverage --version

**Comenzi utile pentru verificare manuala simpla**

        python3 -m pytest -q

        python3 -m coverage erase
        python3 -m coverage run --branch -m pytest -q
        python3 -m coverage report -m --include=to_test.py

        mutmut run
        mutmut results

    Pentru verificare manuala controlata este recomandat scriptul
    `manual_testing.py`, deoarece selecteaza fisierele de test si configureaza
    temporar mutmut in acelasi stil ca framework-ul automat.

## Testarea manuala a suitei curente

[<< Cuprins](#cuprins)

    Scriptul `manual_testing.py` ruleaza manual, asupra lui `to_test.py`,
    urmatoarele verificari:

        pytest
        coverage cu branch coverage
        mutmut

    Scriptul foloseste fisierele `test_*.py` din folderul curent si exclude
    automat fisierul temporar `test_propunere.py` atunci cand selectia este `all`.

    Comenzi:

        python3 manual_testing.py

        python3 manual_testing.py all

        python3 manual_testing.py functional

        python3 manual_testing.py structural

        python3 manual_testing.py functional --clean-after

    Selectii disponibile:

        all
            Ruleaza toate fisierele finale `test_*.py`,
            cu excluderea lui `test_propunere.py`.

        functional
            Ruleaza `test_functional.py`.

        structural
            Ruleaza `test_structural.py`.

        orice alta categorie
            Ruleaza `test_<categorie>.py`, daca fisierul exista si contine
            functii de test.

    Scriptul curata automat artefactele runtime inainte de rulare:

        .mutmut-cache
        mutants/
        __manual_testing_pyproject_backup__.tmp
        .pytest_cache/
        .coverage
        __pycache__/

    Optiunea `--clean-after` executa aceeasi curatare si dupa rulare.
    Pentru compatibilitate cu o posibila tastare gresita este acceptat si
    aliasul `--clean-afeter`.

## Testarea functionarii framework-ului

[<< Cuprins](#cuprins)

        cd /****/TSS

        python3 AutoTesting.py

    La final se verifica:

        - continutul fisierelor test_*.py
        - regulile nou adaugate in testing_*.md
        - istoricul din Logs.jsonl
        - arhivarea in folderul arh/
        - logurile tehnice din folderul logs/

## Structura fisierelor de instructiuni

[<< Cuprins](#cuprins)

    Framework-ul foloseste doua niveluri de instructiuni pentru modelul AI.

    1. `Rules.md`

        Contine reguli generale, valabile pentru toate categoriile:

            - formatul raspunsului
            - cerinta de a returna o singura functie pytest
            - modul de construire a testelor initiale
            - modul de construire a testelor noi
            - prioritatile generale
            - regulile generale pentru formularea `Rule` si `Reasoning`

        `Rules.md` este formulat concis si afirmativ, pentru a reduce
        ambiguitatea pentru modelul local. Scopul este indicarea formei
        corecte a raspunsului, nu enumerarea tuturor formelor gresite.

    2. `testing_*.md`

        Fiecare fisier defineste o categorie de testare.

        Exemple:

            testing_functional.md
            testing_structural.md

        Aceste fisiere contin:

            - sensul categoriei
            - vocabularul abstract recomandat pentru regulile acelei categorii
            - sub-categorii sau zone generale de cautare specifice categoriei
            - regulile numerotate deja acceptate

        Zonele de cautare sunt surse de idei, nu reguli acceptate.
        Regulile acceptate sunt liniile numerotate.

    Modelul poate folosi valori concrete in testul generat, dar regula
    abstracta salvata ulterior in `testing_*.md` trebuie sa foloseasca termeni
    semantici, nu valori concrete, nume de functii, nume de variabile sau
    siruri concrete de rezultat.

    Daca un test nou este acceptat, dar modelul nu poate formula o regula
    valida si reutilizabila, testul ramane in fisierul categoriei. In acest caz
    regula nu este adaugata in `testing_*.md`, pentru a evita poluarea
    bibliotecii de reguli cu fallback-uri generice.

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

* foloseste `Rules.md` pentru regulile generale si `testing_*.md` pentru instructiunile specifice fiecarei categorii

* foloseste prompturi compacte si afirmative, adaptate pentru un model local de dimensiune redusa

* separa promptul general de promptul categoriei, astfel incat conceptele functionale si structurale sa nu fie amestecate

* separa fluxul in trei etape logice:
  * etapa 1: genereaza teste pentru regulile numerotate deja existente in `testing_*.md`
  * etapa 2: cauta teste noi care imbunatatesc fiecare categorie
  * etapa 3: formuleaza separat regula generala si motivarea pentru testele noi acceptate

* valideaza fiecare functie de test generata de AI astfel incat:
  * sa fie o functie `test_*`
  * sa respecte forma ceruta
  * sa contina o singura functie de test
  * sa nu contina cod suplimentar in afara functiei
  * sa poata fi colectata de `pytest`
  * sa treaca efectiv la `pytest`

* foloseste un mecanism iterativ de corectare: daca testul generat este invalid, transmite AI-ului eroarea de validare si cere o versiune corectata

* in etapa 1, corectarea ramane legata de regula numerotata ceruta

* in etapa 2, corectarea ramane in aceeasi categorie si in aceeasi zona generala de testare, dar poate ajusta valorile concrete, rezultatul asteptat sau asertiunea

* masoara calitatea testelor prin:
  * **pytest** pentru validitatea suitei
  * **coverage** pentru branch coverage asupra `to_test.py`
  * **mutmut** pentru mutation testing asupra `to_test.py`

* in etapa 2, accepta un test nou doar daca acesta imbunatateste scorurile categoriei curente, evaluate pe testele acceptate ale categoriei impreuna cu testul candidat din `test_propunere.py`

* optimizeaza separat bibliotecile de teste pe categorii, de exemplu:
  * `test_functional.py` pentru categoria functionala
  * `test_structural.py` pentru categoria structurala

* in etapa 2, modelul primeste:
  * codul sursa din `to_test.py`
  * instructiunile generale din `Rules.md`
  * instructiunile categoriei curente din `testing_*.md`
  * regulile numerotate deja existente in categoria curenta
  * testele deja acceptate ale categoriei
  * o selectie de incercari respinse anterior

* cautarea testelor noi vizeaza zone insuficient acoperite din categoria curenta, nu doar inceputul sau finalul codului

* memoreaza propunerile respinse si foloseste hash-uri stabile pentru a evita reevaluarea aceleiasi functii deja respinse in etapa 2

* permite pornirea de la zero pentru o categorie care nu are inca teste acceptate

* dupa acceptarea unui test nou, cere separat de la AI:
  * regula generala asociata testului
  * motivarea utilitatii testului

* validarea regulii accepta punctuatie simpla in limba engleza:
  * virgula
  * punct
  * punct si virgula
  * doua puncte
  * liniuta

* validarea regulii blocheaza formularea goala, formularea generica si termenii concreti evidenti din codul curent

* daca regula valida nu poate fi formulata, testul acceptat ramane in `test_*.py`, dar nu se adauga un bullet nou in `testing_*.md`

* inregistreaza in `Logs.jsonl` regulile noi acceptate, impreuna cu:
  * categoria
  * regula
  * motivarea
  * imbunatatirea obtinuta
  * data si autorul

* elimina automat propunerile care nu aduc imbunatatire, pentru a reduce redundanta si zgomotul din biblioteca de teste

* reseteaza contextul AI intre etape, intre categorii si intre solicitari sensibile, precum corectiile sau formularile separate ale regulilor, pentru a evita contaminarea contextului cu informatii irelevante

* evita costurile inutile: daca `pytest` nu este curat, nu mai ruleaza `coverage` si `mutmut` pentru acea evaluare

* curata workspace-ul la inceputul si la finalul rularii automate

* arhiveaza la final fisierul `to_test.py` si fisierele finale `test_*.py` intr-un subfolder numerotat si datat din `arh/`, cu excluderea fisierului temporar `test_propunere.py`

* include un script separat, `manual_testing.py`, pentru verificarea manuala a scorurilor pytest, coverage si mutmut pe toate testele sau pe o categorie selectata

* realizeaza un proces de testare unitara asistata de AI, orientat spre:
  * generare de teste `pytest`
  * validare tehnica automata
  * crestere progresiva a branch coverage
  * crestere progresiva a mutation score
  * dezvoltarea unei biblioteci de reguli de testare pe categorii

## Flux de executie

[<< Cuprins](#cuprins)

1. Se curata workspace-ul de fisierele si folderele temporare.
2. Se verifica structura minima a proiectului.
3. Se identifica fisierele `testing_*.md` si se creeaza fisierele `test_*.py` lipsa.
4. Se genereaza testele initiale pentru regulile numerotate existente in `testing_*.md`.
5. Se marcheaza finalul testelor initiale in fisierele de test.
6. Se cauta teste noi pentru fiecare categorie.
7. Pentru fiecare test candidat se ruleaza validarea tehnica.
8. Pentru fiecare test valid se evalueaza scorurile pe categoria curenta plus `test_propunere.py`.
9. Daca scorurile se imbunatatesc fara regresie, testul este acceptat in fisierul categoriei.
10. Pentru fiecare test nou acceptat, se cere separat regula si motivarea.
11. Daca regula este valida si negenerica, aceasta este salvata in `Logs.jsonl` si adaugata in `testing_*.md`.
12. Daca regula nu poate fi formulata valid, testul ramane acceptat, dar nu se adauga regula in `testing_*.md`.
13. Se arhiveaza rezultatele finale.
14. Se curata fisierele si folderele temporare.
15. Se afiseaza regulile noi adaugate in sesiunea curenta.

## Utilizare

[<< Cuprins](#cuprins)

* **Pornire framework automat, in folderul proiectului**

        python3 AutoTesting.py

* **Verificare manuala globala**

        python3 manual_testing.py

* **Verificare manuala pe categoria functionala**

        python3 manual_testing.py functional

* **Verificare manuala pe categoria structurala**

        python3 manual_testing.py structural

* **Verificare manuala cu stergerea artefactelor dupa rulare**

        python3 manual_testing.py all --clean-after

* La finalul rularii automate sunt afisate regulile noi adaugate in sesiunea curenta.

* In fisierul `Logs.jsonl` se regasesc regulile acceptate de-a lungul rularilor.

* In fisierele `testing_*.md` se construieste treptat biblioteca de reguli de testare pe categorii.

* In folderul `arh/` se salveaza, intr-un subfolder numerotat si datat, fisierul `to_test.py` si fisierele finale `test_*.py`.

* In folderul `logs/` se salveaza logurile tehnice ale framework-ului si interactiunile brute cu Ollama, daca debugging-ul este activ.

## Imbunatatiri implementate pentru performanta si calitatea rezultatelor

[<< Cuprins](#cuprins)

* a fost separata arhitectura pe module specializate pentru orchestrare, prompturi, validare, scoring, logging, arhivare si lucru cu fisierele
* a fost separat clar fluxul in etapa unu, etapa doi si etapa trei, fiecare cu scop propriu
* in etapa unu se genereaza teste pentru regulile explicite deja existente in fisierele categoriei
* in etapa doi se cauta doar teste noi care aduc o imbunatatire reala categoriei curente
* in etapa trei se cere separat formularea regulii generale si a motivarii pentru testele deja acceptate
* instructiunile generale au fost mutate in `Rules.md`, iar instructiunile specifice categoriilor au fost pastrate in fisierele `testing_*.md`
* `Rules.md` a fost redus la reguli generale concise si afirmative, pentru a evita supraincarcarea modelului local
* fisierele `testing_functional.md` si `testing_structural.md` contin sensul categoriei, vocabularul abstract si zonele de cautare specifice categoriei
* zonele de cautare din fisierele categoriei sunt folosite ca surse de idei, nu ca reguli deja acceptate
* modelul este incurajat sa caute zone insuficient acoperite in categoria curenta, fara a favoriza artificial inceputul sau finalul codului
* testul concret poate folosi valori concrete din cod, dar regula abstracta salvata ulterior trebuie sa foloseasca termeni semantici
* prioritatile pentru testele noi au fost clarificate: corectitudine, zona insuficient testata, regula noua, imbunatatirea scorului si simplitate
* corectarea propunerilor invalide este formulata afirmativ si orientata spre obtinerea unui test pytest valid
* in etapa doi, corectarea poate ajusta ideea concreta in aceeasi zona generala de testare, pentru a evita blocarea pe o propunere slaba
* validarea regulilor a fost relaxata pentru a permite punctuatia naturala simpla
* filtrarea termenilor concreti din reguli a fost facuta mai permisiva, pentru a reduce respingerea regulilor utile
* fallback-urile generice de tip regula noua distincta nu mai sunt salvate ca reguli reale in `testing_*.md`
* contextul AI este resetat in punctele sensibile ale fluxului pentru a reduce contaminarea dintre solicitari diferite
* sunt folosite mesaje de validare mai utile si mai compacte, pentru a ajuta modelul sa corecteze mai bine raspunsurile invalide
* fiecare test generat este validat strict, astfel incat sa fie acceptate doar teste care trec efectiv prin `pytest`
* fiecare categorie este optimizata independent, astfel incat functionalul si structuralul sa evolueze separat
* un test nou este evaluat impreuna cu biblioteca deja acceptata a categoriei sale, nu izolat
* a fost introdus un mecanism de evitare a erorilor pentru categoriile care nu au inca teste acceptate
* este evitata reevaluarea aceleiasi propuneri deja respinse prin memorarea ei si folosirea unui hash stabil
* modelului ii sunt aratate incercarile respinse anterior, pentru a reduce repetitiile si a forta cautarea de idei noi
* modelului ii sunt aratate si regulile numerotate deja existente din categorie, pentru a evita dublurile semantice
* in etapa doi sunt acceptate doar propunerile care imbunatatesc categoria fara sa strice scorurile deja obtinute
* cautarea pe o categorie este oprita dupa un numar de iteratii consecutive fara imbunatatire, pentru a limita consumul inutil
* `coverage` si `mutmut` nu mai sunt rulate atunci cand `pytest` nu produce un rezultat curat, reducand costul evaluarilor inutile
* cererea de test este separata de cererea de regula, pentru a nu amesteca generarea codului cu abstractizarea regulii
* fisierul temporar `test_propunere.py` este exclus din arhivare, astfel incat arhiva sa contina doar artefactele finale relevante
* logarea tehnica a fost imbunatatita, astfel incat motivele de respingere si evolutia scorurilor sa poata fi urmarite mai usor
* a fost adaugat `manual_testing.py` pentru rularea manuala a pytest, coverage si mutmut pe toate testele sau pe o categorie selectata
* `manual_testing.py` curata automat artefactele runtime inainte de rulare si poate curata optional si dupa rulare cu `--clean-after`

## Autor

[<< Cuprins](#cuprins)

    Condruz Filip Gabriel

    Univesitatea Bucuresti, Facultatea de Matematica si Informatica, anul 3 ID